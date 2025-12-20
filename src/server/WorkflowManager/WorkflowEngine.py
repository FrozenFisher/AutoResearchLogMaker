"""工作流引擎（动态图）"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from server.config import settings
from server.database import update_workflow_status, get_workflow_by_wf_id
from server.models import WorkflowStatus, WorkflowGraphConfig, WorkflowNode
from .WorkflowStorage import WorkflowStorage
from server.ToolManager.ToolRegistry import tool_registry
from server.DataManager.MetadataManager import MetadataManager
from server.LLMManager.LLMService import llm_service


class WorkflowEngine:
    """根据 workflow_{timestamp}.json 动态执行工作流"""

    def __init__(self):
        self.workflow_storage = WorkflowStorage()
        self.metadata_manager = MetadataManager()

    async def execute_workflow(
        self,
        db: Session,
        project_name: str,
        date: str,
        wf_id: str,
        files: List[str] = None,
        custom_prompt: str = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        context: Dict[str, Any] = {}
        try:
            update_workflow_status(db, wf_id, WorkflowStatus.RUNNING.value)

            # 加载工作流配置
            graph_cfg_dict = self.workflow_storage.load_workflow_config(project_name, date, wf_id)
            if not graph_cfg_dict:
                raise ValueError(f"工作流配置不存在: {wf_id}")
            graph_cfg = WorkflowGraphConfig(**graph_cfg_dict)

            # 上下文
            context = {
                "project": project_name,
                "date": date,
                "wf_id": wf_id,
                "custom_prompt": custom_prompt,
                "files": files or await self._get_project_files(project_name, date),
                "aggregated_text": ""
            }

            # 预处理：如果有文件，尽量拼接文本（由工具节点进一步处理）
            context["aggregated_text"] = await self._aggregate_text_from_files(context["files"]) or ""

            # 执行图
            result = await self._run_graph(graph_cfg, context)

            # 保存输出
            output_data = {
                "summary": result.get("summary", ""),
                "context": {k: v for k, v in result.items() if k != "summary"},
                "execution_time": datetime.now().isoformat()
            }
            ok, output_path = self.workflow_storage.save_workflow_output(project_name, date, wf_id, output_data)
            if not ok:
                update_workflow_status(db, wf_id, WorkflowStatus.FAILED.value, "输出保存失败")
                return False, "输出保存失败", None

            update_workflow_status(db, wf_id, WorkflowStatus.SUCCESS.value)
            return True, "工作流执行成功", output_data
        except Exception as e:
            # 尝试在失败时也保存当前上下文，方便调试
            try:
                debug_output = {
                    "summary": context.get("summary", ""),
                    "context": context,
                    "execution_time": datetime.now().isoformat(),
                    "error": str(e),
                }
                self.workflow_storage.save_workflow_output(project_name, date, wf_id, debug_output)
            except Exception:
                # 即使保存调试输出失败，也不要影响状态更新
                pass

            update_workflow_status(db, wf_id, WorkflowStatus.FAILED.value, str(e))
            return False, f"工作流执行失败: {str(e)}", None

    async def _run_graph(self, graph: WorkflowGraphConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        node_map: Dict[str, WorkflowNode] = {n.id: n for n in graph.nodes}
        edges = graph.edges

        # 找到start节点
        start_ids = [n.id for n in graph.nodes if n.type == "start"]
        if not start_ids:
            raise ValueError("工作流缺少start节点")
        current_id = start_ids[0]

        visited_guard = 0
        while True:
            visited_guard += 1
            if visited_guard > 1000:
                raise RuntimeError("工作流可能存在循环导致超过最大步数")

            node = node_map[current_id]
            next_id = None

            if node.type == "end":
                break
            elif node.type == "tool":
                await self._exec_tool_node(node, context)
            elif node.type == "llm":
                await self._exec_llm_node(node, graph, context)
            elif node.type == "branch":
                # 分支节点不做处理，仅基于条件选择边
                pass
            elif node.type == "merge":
                # 合并节点不做特殊处理
                pass
            elif node.type == "start":
                # 起始节点
                pass
            else:
                raise ValueError(f"未知节点类型: {node.type}")

            # 选择下一条边
            outgoing = [e for e in edges if e.source == current_id]
            if not outgoing:
                # 没有后继，则结束
                break
            if len(outgoing) == 1 and not outgoing[0].condition:
                next_id = outgoing[0].target
            else:
                # 有条件的边，按条件匹配第一条为准
                chosen = None
                for e in outgoing:
                    if not e.condition:
                        continue
                    if self._eval_condition(e.condition, context):
                        chosen = e
                        break
                if chosen is None:
                    # 回退到无条件边
                    fallback = next((e for e in outgoing if not e.condition), None)
                    if not fallback:
                        raise ValueError(f"分支节点 {current_id} 未匹配到任何条件边")
                    next_id = fallback.target
                else:
                    next_id = chosen.target

            current_id = next_id

        # 结果
        result = {
            "summary": context.get("summary", ""),
            **context
        }
        return result

    async def _exec_tool_node(self, node: WorkflowNode, context: Dict[str, Any]):
        tool_name = node.tool_name or node.params.get("tool_name")
        if not tool_name:
            raise ValueError(f"tool节点缺少tool_name: {node.id}")
        # 构造输入
        payload = {}
        for k, v in (node.input_map or {}).items():
            payload[k] = self._resolve_from_context(v, context)
        # 若无映射则传递上下文
        if not payload:
            payload = context
        result = await tool_registry.process_with_tool(tool_name, payload)
        context[node.output_key or "result"] = result

    async def _exec_llm_node(self, node: WorkflowNode, graph: WorkflowGraphConfig, context: Dict[str, Any]):
        template_name = node.params.get("template") or graph.prompt_template or "default"
        model_name = graph.llm_model
        content_key = node.input_map.get("content") if node.input_map else None
        content = self._resolve_from_context(content_key, context) if content_key else context.get("aggregated_text", "")
        ok, summary_or_msg, meta = await llm_service.generate_summary(content=content, template_name=template_name, model_name=model_name, custom_prompt=context.get("custom_prompt"))
        if ok:
            context[node.output_key or "summary"] = summary_or_msg
            context["summary"] = summary_or_msg
            context.setdefault("llm_meta", []).append(meta)
        else:
            raise RuntimeError(f"LLM生成失败: {summary_or_msg}")

    def _eval_condition(self, expr: str, context: Dict[str, Any]) -> bool:
        # 支持表达式中用 ctx 引用上下文，如 ctx.get('result', {}).get('ok') == True
        safe_globals = {"__builtins__": {}}
        try:
            return bool(eval(expr, safe_globals, {"ctx": context}))
        except Exception:
            return False

    def _resolve_from_context(self, path: Optional[str], context: Dict[str, Any]):
        if not path:
            return None
        # 支持 a.b.c 访问
        cur: Any = context
        for part in path.split('.'):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return None
        return cur

    async def _aggregate_text_from_files(self, files: List[str]) -> str:
        if not files:
            return ""
        texts: List[str] = []
        for fp in files:
            path_str = str(fp)
            lower = path_str.lower()
            try:
                # 纯文本文件，直接读取
                if lower.endswith(('.txt', '.md')):
                    with open(path_str, 'r', encoding='utf-8', errors='ignore') as f:
                        texts.append(f.read())
                # PDF，通过 pdf_parser 提取文本（包括内置OCR能力）
                elif lower.endswith('.pdf'):
                    try:
                        pdf_result = await tool_registry.process_with_tool("pdf_parser", path_str)
                        if isinstance(pdf_result, dict) and pdf_result.get("text_content"):
                            texts.append(pdf_result["text_content"])
                    except Exception:
                        # 单个文件失败不影响整体流程
                        continue
                # 图片，通过 image_reader 进行 OCR
                elif lower.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')):
                    try:
                        img_result = await tool_registry.process_with_tool("image_reader", path_str)
                        if isinstance(img_result, dict) and img_result.get("text_content"):
                            texts.append(img_result["text_content"])
                    except Exception:
                        continue
            except Exception:
                continue
        return "\n\n".join(texts)

    async def _get_project_files(self, project_name: str, date: str) -> List[str]:
        try:
            metadata = self.metadata_manager.load_metadata(project_name, date)
            if not metadata:
                return []
            files = []
            for file_info in metadata.files:
                file_path = settings.BASE_DIR / file_info.stored_path
                if file_path.exists():
                    files.append(str(file_path))
            return files
        except Exception:
            return []

    def get_workflow_status(self, db: Session, wf_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态信息"""
        workflow = get_workflow_by_wf_id(db, wf_id)
        if not workflow:
            return None
        
        return {
            "wf_id": workflow.wf_id,
            "name": workflow.name,
            "status": workflow.status,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "finished_at": workflow.finished_at.isoformat() if workflow.finished_at else None,
            "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
            "llm_model": workflow.llm_model,
            "prompt_template": workflow.prompt_template,
            "error_message": workflow.error_message,
        }


workflow_engine = WorkflowEngine()
