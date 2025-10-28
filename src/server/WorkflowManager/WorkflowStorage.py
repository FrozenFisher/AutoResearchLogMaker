"""工作流存储管理器"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from config import get_project_data_path, settings
from database import get_workflow_by_wf_id, create_workflow, update_workflow_status, Workflow
from models import WorkflowInfo, WorkflowStatus, WorkflowGraphConfig


class WorkflowStorage:
    """工作流存储管理器"""
    
    def __init__(self):
        self.default_template_path = settings.STATIC_DIR / "default_workflow.json"
    
    def get_workflow_dir(self, project_name: str, date: str) -> Path:
        return get_project_data_path(project_name, date) / "workflows"

    def get_workflow_path(self, project_name: str, date: str, wf_id: str) -> Path:
        return self.get_workflow_dir(project_name, date) / f"{wf_id}.json"

    def load_template(self) -> Optional[WorkflowGraphConfig]:
        if not self.default_template_path.exists():
            return None
        with open(self.default_template_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return WorkflowGraphConfig(**data)

    def save_workflow_config(self, project_name: str, date: str, wf_id: str, workflow_config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            # 校验schema
            WorkflowGraphConfig(**workflow_config)
            workflow_path = self.get_workflow_path(project_name, date, wf_id)
            workflow_path.parent.mkdir(parents=True, exist_ok=True)
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(workflow_config, f, ensure_ascii=False, indent=2)
            return True, None
        except Exception as e:
            return False, str(e)

    def create_from_template(self, project_name: str, date: str, name: str, overrides: Dict[str, Any] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        template = self.load_template()
        if not template:
            return False, "template not found", None
        base = template.dict()
        base["name"] = name or base.get("name")
        if overrides:
            # 只覆盖允许字段
            for key in ["nodes", "edges", "llm_model", "prompt_template"]:
                if key in overrides:
                    base[key] = overrides[key]
        # 生成wf_id
        ts = datetime.now().strftime("wf_%Y%m%d_%H%M%S")
        ok, err = self.save_workflow_config(project_name, date, ts, base)
        if not ok:
            return False, err, None
        return True, None, ts

    def load_workflow_config(self, project_name: str, date: str, wf_id: str) -> Optional[Dict[str, Any]]:
        workflow_path = self.get_workflow_path(project_name, date, wf_id)
        if not workflow_path.exists():
            return None
        with open(workflow_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_workflow_configs(self, project_name: str, date: str) -> List[Dict[str, Any]]:
        workflows_dir = self.get_workflow_dir(project_name, date)
        if not workflows_dir.exists():
            return []
        items = []
        for p in workflows_dir.glob("*.json"):
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items.append({"wf_id": p.stem, "name": data.get("name"), "created_at": p.stat().st_mtime})
            except Exception:
                continue
        return items

    def delete_workflow_config(self, project_name: str, wf_id: str) -> bool:
        """删除工作流配置"""
        try:
            workflow_path = self.get_workflow_path(project_name, date, wf_id)
            
            if workflow_path.exists():
                workflow_path.unlink()
                return True
            
            return False
            
        except OSError as e:
            print(f"删除工作流配置失败: {e}")
            return False

    def create_workflow_execution(self, db: Session, project_id: int, wf_id: str, name: str, llm_model: str = None, prompt_template: str = None) -> Tuple[bool, Optional[str], Optional[Workflow]]:
        try:
            existing_workflow = get_workflow_by_wf_id(db, wf_id)
            if existing_workflow:
                return False, f"工作流 '{wf_id}' 已存在", None
            workflow = create_workflow(db, project_id, wf_id, name, llm_model, prompt_template)
            return True, "工作流执行记录创建成功", workflow
        except Exception as e:
            return False, f"创建工作流执行记录失败: {str(e)}", None

    def update_workflow_execution_status(self, db: Session, wf_id: str, status: WorkflowStatus, error_message: str = None) -> Tuple[bool, Optional[str]]:
        try:
            workflow = update_workflow_status(db, wf_id, status.value, error_message)
            if workflow:
                return True, "工作流状态更新成功"
            else:
                return False, f"工作流 '{wf_id}' 不存在"
        except Exception as e:
            return False, f"更新工作流状态失败: {str(e)}"

    def get_workflow_execution(self, db: Session, wf_id: str) -> Optional[Workflow]:
        return get_workflow_by_wf_id(db, wf_id)

    def list_workflow_executions(self, db: Session, project_id: int) -> List[Workflow]:
        return db.query(Workflow).filter(Workflow.project_id == project_id).all()

    def get_workflow_execution_info(self, db: Session, wf_id: str) -> Optional[WorkflowInfo]:
        """获取工作流执行信息"""
        workflow = get_workflow_by_wf_id(db, wf_id)
        
        if not workflow:
            return None
        
        return WorkflowInfo(
            wf_id=workflow.wf_id,
            name=workflow.name,
            started_at=workflow.started_at,
            finished_at=workflow.finished_at,
            status=WorkflowStatus(workflow.status),
            outputs=[],  # 这里可以从元数据中获取
            llm_model=workflow.llm_model,
            prompt_template=workflow.prompt_template
        )
    
    def save_workflow_output(self, project_name: str, date: str, wf_id: str, output_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"output_{timestamp}.json"
            output_dir = get_project_data_path(project_name, date) / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / output_filename
            output_with_meta = {"wf_id": wf_id, "created_at": datetime.now().isoformat(), "output": output_data}
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_with_meta, f, ensure_ascii=False, indent=2)
            return True, str(output_path.relative_to(settings.BASE_DIR))
        except Exception as e:
            return False, f"保存工作流输出失败: {str(e)}"

    def load_workflow_output(self, project_name: str, date: str, output_filename: str) -> Optional[Dict[str, Any]]:
        try:
            output_path = get_project_data_path(project_name, date) / "outputs" / output_filename
            if not output_path.exists():
                return None
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("output")
        except Exception:
            return None

    def list_workflow_outputs(self, project_name: str, date: str) -> List[Dict[str, Any]]:
        outputs_dir = get_project_data_path(project_name, date) / "outputs"
        if not outputs_dir.exists():
            return []
        outputs = []
        for output_file in outputs_dir.glob("output_*.json"):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    outputs.append({"filename": output_file.name, "wf_id": data.get("wf_id"), "created_at": data.get("created_at"), "output": data.get("output", {})})
            except Exception:
                continue
        outputs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return outputs

    def get_workflow_statistics(self, db: Session, project_id: int) -> Dict[str, Any]:
        workflows = self.list_workflow_executions(db, project_id)
        stats = {"total_workflows": len(workflows), "by_status": {"pending": 0, "running": 0, "success": 0, "failed": 0}, "by_model": {}, "avg_execution_time": 0}
        total_execution_time = 0
        completed_count = 0
        for workflow in workflows:
            status = workflow.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            model = workflow.llm_model or "unknown"
            stats["by_model"][model] = stats["by_model"].get(model, 0) + 1
            if workflow.started_at and workflow.finished_at:
                execution_time = (workflow.finished_at - workflow.started_at).total_seconds()
                total_execution_time += execution_time
                completed_count += 1
        if completed_count > 0:
            stats["avg_execution_time"] = total_execution_time / completed_count
        return stats

    def cleanup_old_workflows(self, db: Session, days_old: int = 30) -> int:
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            old_workflows = db.query(Workflow).filter(Workflow.created_at < cutoff_date, Workflow.status.in_(["success", "failed"]))
            count = old_workflows.count()
            for workflow in old_workflows:
                db.delete(workflow)
            db.commit()
            return count
        except Exception:
            return 0
