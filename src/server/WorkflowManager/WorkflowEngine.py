"""工作流引擎"""
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from config import settings
from database import get_project_by_name, get_workflow_by_wf_id, update_workflow_status
from models import WorkflowStatus, FileInfo
from .WorkflowStorage import WorkflowStorage
from ..ToolManager.ToolRegistry import tool_registry
from ..DataManager.MetadataManager import MetadataManager


class WorkflowState:
    """工作流状态"""
    
    def __init__(self):
        self.messages = []
        self.files = []
        self.processed_files = []
        self.text_content = ""
        self.summary = ""
        self.error_message = ""
        self.current_step = ""
        self.metadata = {}


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflow_storage = WorkflowStorage()
        self.metadata_manager = MetadataManager()
        self.graph = None
        self._build_workflow_graph()
    
    def _build_workflow_graph(self):
        """构建工作流图"""
        # 创建状态图
        workflow = StateGraph(WorkflowState)
        
        # 添加节点
        workflow.add_node("file_processing", self._process_files)
        workflow.add_node("text_extraction", self._extract_text)
        workflow.add_node("content_analysis", self._analyze_content)
        workflow.add_node("summary_generation", self._generate_summary)
        workflow.add_node("error_handling", self._handle_error)
        
        # 添加边
        workflow.add_edge("file_processing", "text_extraction")
        workflow.add_edge("text_extraction", "content_analysis")
        workflow.add_edge("content_analysis", "summary_generation")
        workflow.add_edge("summary_generation", END)
        
        # 错误处理边
        workflow.add_edge("file_processing", "error_handling")
        workflow.add_edge("text_extraction", "error_handling")
        workflow.add_edge("content_analysis", "error_handling")
        workflow.add_edge("summary_generation", "error_handling")
        workflow.add_edge("error_handling", END)
        
        # 编译图
        self.graph = workflow.compile()
    
    async def execute_workflow(
        self, 
        db: Session, 
        project_name: str, 
        date: str, 
        wf_id: str,
        files: List[str] = None,
        custom_prompt: str = None
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """执行工作流"""
        try:
            # 更新工作流状态为运行中
            update_workflow_status(db, wf_id, WorkflowStatus.RUNNING.value)
            
            # 获取工作流配置
            workflow_config = self.workflow_storage.load_workflow_config(project_name, wf_id)
            if not workflow_config:
                raise ValueError(f"工作流配置不存在: {wf_id}")
            
            # 获取文件列表
            if not files:
                files = await self._get_project_files(project_name, date)
            
            # 创建初始状态
            initial_state = WorkflowState()
            initial_state.files = files
            initial_state.metadata = {
                "project_name": project_name,
                "date": date,
                "wf_id": wf_id,
                "custom_prompt": custom_prompt,
                "workflow_config": workflow_config
            }
            
            # 执行工作流
            result = await self.graph.ainvoke(initial_state)
            
            # 保存输出
            output_data = {
                "summary": result.summary,
                "processed_files": result.processed_files,
                "text_content": result.text_content,
                "metadata": result.metadata,
                "execution_time": datetime.now().isoformat()
            }
            
            success, output_path = self.workflow_storage.save_workflow_output(
                project_name, date, wf_id, output_data
            )
            
            if success:
                # 更新工作流状态为成功
                update_workflow_status(db, wf_id, WorkflowStatus.SUCCESS.value)
                
                # 更新元数据
                await self._update_metadata_with_workflow_result(
                    project_name, date, wf_id, result
                )
                
                return True, "工作流执行成功", output_data
            else:
                # 更新工作流状态为失败
                update_workflow_status(db, wf_id, WorkflowStatus.FAILED.value, "输出保存失败")
                return False, "输出保存失败", None
                
        except Exception as e:
            # 更新工作流状态为失败
            update_workflow_status(db, wf_id, WorkflowStatus.FAILED.value, str(e))
            return False, f"工作流执行失败: {str(e)}", None
    
    async def _process_files(self, state: WorkflowState) -> WorkflowState:
        """处理文件节点"""
        try:
            state.current_step = "file_processing"
            processed_files = []
            
            for file_path in state.files:
                try:
                    # 根据文件类型选择处理工具
                    file_ext = file_path.split('.')[-1].lower()
                    
                    if file_ext == 'pdf':
                        tool = tool_registry.get_tool("pdf_parser")
                    elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
                        tool = tool_registry.get_tool("image_reader")
                    else:
                        # 默认使用文本处理工具
                        tool = tool_registry.get_tool("text_processor")
                    
                    if tool:
                        result = await tool.process(file_path)
                        processed_files.append({
                            "file_path": file_path,
                            "tool_used": tool.name,
                            "result": result
                        })
                    else:
                        processed_files.append({
                            "file_path": file_path,
                            "tool_used": "none",
                            "result": {"error": "No suitable tool found"}
                        })
                        
                except Exception as e:
                    processed_files.append({
                        "file_path": file_path,
                        "tool_used": "error",
                        "result": {"error": str(e)}
                    })
            
            state.processed_files = processed_files
            return state
            
        except Exception as e:
            state.error_message = f"文件处理失败: {str(e)}"
            return state
    
    async def _extract_text(self, state: WorkflowState) -> WorkflowState:
        """提取文本节点"""
        try:
            state.current_step = "text_extraction"
            text_content = ""
            
            for processed_file in state.processed_files:
                result = processed_file.get("result", {})
                
                # 从不同工具的结果中提取文本
                if "text_content" in result:
                    text_content += result["text_content"] + "\n"
                elif "cleaned_text" in result:
                    text_content += result["cleaned_text"] + "\n"
                elif "text" in result:
                    text_content += result["text"] + "\n"
            
            state.text_content = text_content.strip()
            return state
            
        except Exception as e:
            state.error_message = f"文本提取失败: {str(e)}"
            return state
    
    async def _analyze_content(self, state: WorkflowState) -> WorkflowState:
        """内容分析节点"""
        try:
            state.current_step = "content_analysis"
            
            # 使用文本处理工具分析内容
            text_tool = tool_registry.get_tool("text_processor")
            if text_tool and state.text_content:
                analysis_result = await text_tool.process(state.text_content)
                state.metadata["content_analysis"] = analysis_result
            
            return state
            
        except Exception as e:
            state.error_message = f"内容分析失败: {str(e)}"
            return state
    
    async def _generate_summary(self, state: WorkflowState) -> WorkflowState:
        """生成总结节点"""
        try:
            state.current_step = "summary_generation"
            
            # 这里应该调用LLM服务生成总结
            # 暂时使用简单的文本摘要
            if state.text_content:
                # 简单的文本摘要（取前500字符）
                summary = state.text_content[:500]
                if len(state.text_content) > 500:
                    summary += "..."
                
                state.summary = summary
            else:
                state.summary = "没有可总结的内容"
            
            return state
            
        except Exception as e:
            state.error_message = f"总结生成失败: {str(e)}"
            return state
    
    async def _handle_error(self, state: WorkflowState) -> WorkflowState:
        """错误处理节点"""
        state.current_step = "error_handling"
        state.summary = f"工作流执行失败: {state.error_message}"
        return state
    
    async def _get_project_files(self, project_name: str, date: str) -> List[str]:
        """获取项目文件列表"""
        try:
            metadata = self.metadata_manager.load_metadata(project_name, date)
            if not metadata:
                return []
            
            files = []
            for file_info in metadata.files:
                # 构建完整文件路径
                file_path = settings.BASE_DIR / file_info.stored_path
                if file_path.exists():
                    files.append(str(file_path))
            
            return files
            
        except Exception as e:
            print(f"获取项目文件失败: {e}")
            return []
    
    async def _update_metadata_with_workflow_result(
        self, 
        project_name: str, 
        date: str, 
        wf_id: str, 
        result: WorkflowState
    ):
        """更新元数据中的工作流结果"""
        try:
            from models import WorkflowInfo, SummaryInfo
            
            # 创建工作流信息
            workflow_info = WorkflowInfo(
                wf_id=wf_id,
                name=f"工作流_{wf_id}",
                started_at=datetime.now(),
                finished_at=datetime.now(),
                status=WorkflowStatus.SUCCESS,
                outputs=[],  # 这里可以添加输出文件路径
                llm_model=result.metadata.get("workflow_config", {}).get("llm_model"),
                prompt_template=result.metadata.get("workflow_config", {}).get("prompt_template")
            )
            
            # 更新工作流信息
            self.metadata_manager.add_workflow_to_metadata(
                project_name, date, workflow_info
            )
            
            # 更新总结信息
            summary_info = SummaryInfo(
                auto_summary=result.summary,
                user_notes=None
            )
            
            self.metadata_manager.update_summary_in_metadata(
                project_name, date, summary_info
            )
            
        except Exception as e:
            print(f"更新元数据失败: {e}")
    
    def get_workflow_status(self, db: Session, wf_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        workflow = get_workflow_by_wf_id(db, wf_id)
        
        if not workflow:
            return None
        
        return {
            "wf_id": workflow.wf_id,
            "name": workflow.name,
            "status": workflow.status,
            "started_at": workflow.started_at,
            "finished_at": workflow.finished_at,
            "error_message": workflow.error_message,
            "llm_model": workflow.llm_model,
            "prompt_template": workflow.prompt_template
        }
    
    def cancel_workflow(self, db: Session, wf_id: str) -> bool:
        """取消工作流"""
        try:
            workflow = get_workflow_by_wf_id(db, wf_id)
            if not workflow:
                return False
            
            if workflow.status in ["pending", "running"]:
                update_workflow_status(db, wf_id, WorkflowStatus.FAILED.value, "用户取消")
                return True
            
            return False
            
        except Exception as e:
            print(f"取消工作流失败: {e}")
            return False
    
    def get_workflow_execution_history(self, db: Session, project_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取工作流执行历史"""
        try:
            workflows = db.query(Workflow).filter(
                Workflow.project_id == project_id
            ).order_by(Workflow.created_at.desc()).limit(limit).all()
            
            history = []
            for workflow in workflows:
                history.append({
                    "wf_id": workflow.wf_id,
                    "name": workflow.name,
                    "status": workflow.status,
                    "started_at": workflow.started_at,
                    "finished_at": workflow.finished_at,
                    "created_at": workflow.created_at,
                    "error_message": workflow.error_message
                })
            
            return history
            
        except Exception as e:
            print(f"获取工作流执行历史失败: {e}")
            return []


# 全局工作流引擎实例
workflow_engine = WorkflowEngine()
