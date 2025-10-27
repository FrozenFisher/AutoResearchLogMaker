"""工作流存储管理器"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from config import get_project_data_path, settings
from database import get_workflow_by_wf_id, create_workflow, update_workflow_status, Workflow
from models import WorkflowInfo, WorkflowStatus


class WorkflowStorage:
    """工作流存储管理器"""
    
    def __init__(self):
        pass
    
    def get_workflow_path(self, project_name: str, wf_id: str) -> Path:
        """获取工作流文件路径"""
        return get_project_data_path(project_name, "workflows") / f"workflow_{wf_id}.json"
    
    def save_workflow_config(
        self, 
        project_name: str, 
        wf_id: str, 
        workflow_config: Dict[str, Any]
    ) -> bool:
        """保存工作流配置"""
        try:
            workflow_path = self.get_workflow_path(project_name, wf_id)
            
            # 确保目录存在
            workflow_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 添加元数据
            config_with_meta = {
                "wf_id": wf_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "config": workflow_config
            }
            
            with open(workflow_path, 'w', encoding='utf-8') as f:
                json.dump(config_with_meta, f, ensure_ascii=False, indent=2)
            
            return True
            
        except (IOError, json.JSONEncodeError) as e:
            print(f"保存工作流配置失败: {e}")
            return False
    
    def load_workflow_config(self, project_name: str, wf_id: str) -> Optional[Dict[str, Any]]:
        """加载工作流配置"""
        workflow_path = self.get_workflow_path(project_name, wf_id)
        
        if not workflow_path.exists():
            return None
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("config")
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载工作流配置失败: {e}")
            return None
    
    def list_workflow_configs(self, project_name: str) -> List[Dict[str, Any]]:
        """列出所有工作流配置"""
        workflows_dir = get_project_data_path(project_name, "workflows")
        
        if not workflows_dir.exists():
            return []
        
        workflow_configs = []
        
        for config_file in workflows_dir.glob("workflow_*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    config_info = {
                        "wf_id": data.get("wf_id"),
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                        "config": data.get("config", {})
                    }
                    
                    workflow_configs.append(config_info)
                    
            except (json.JSONDecodeError, IOError) as e:
                print(f"读取工作流配置失败 {config_file}: {e}")
                continue
        
        # 按创建时间排序
        workflow_configs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return workflow_configs
    
    def delete_workflow_config(self, project_name: str, wf_id: str) -> bool:
        """删除工作流配置"""
        try:
            workflow_path = self.get_workflow_path(project_name, wf_id)
            
            if workflow_path.exists():
                workflow_path.unlink()
                return True
            
            return False
            
        except OSError as e:
            print(f"删除工作流配置失败: {e}")
            return False
    
    def create_workflow_execution(
        self, 
        db: Session, 
        project_id: int, 
        wf_id: str, 
        name: str,
        llm_model: str = None,
        prompt_template: str = None
    ) -> Tuple[bool, Optional[str], Optional[Workflow]]:
        """创建工作流执行记录"""
        try:
            # 检查工作流ID是否已存在
            existing_workflow = get_workflow_by_wf_id(db, wf_id)
            if existing_workflow:
                return False, f"工作流 '{wf_id}' 已存在", None
            
            # 创建数据库记录
            workflow = create_workflow(
                db, project_id, wf_id, name, llm_model, prompt_template
            )
            
            return True, "工作流执行记录创建成功", workflow
            
        except Exception as e:
            return False, f"创建工作流执行记录失败: {str(e)}", None
    
    def update_workflow_execution_status(
        self, 
        db: Session, 
        wf_id: str, 
        status: WorkflowStatus,
        error_message: str = None
    ) -> Tuple[bool, Optional[str]]:
        """更新工作流执行状态"""
        try:
            workflow = update_workflow_status(db, wf_id, status.value, error_message)
            
            if workflow:
                return True, "工作流状态更新成功"
            else:
                return False, f"工作流 '{wf_id}' 不存在"
                
        except Exception as e:
            return False, f"更新工作流状态失败: {str(e)}"
    
    def get_workflow_execution(self, db: Session, wf_id: str) -> Optional[Workflow]:
        """获取工作流执行记录"""
        return get_workflow_by_wf_id(db, wf_id)
    
    def list_workflow_executions(self, db: Session, project_id: int) -> List[Workflow]:
        """列出项目的工作流执行记录"""
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
    
    def save_workflow_output(
        self, 
        project_name: str, 
        date: str, 
        wf_id: str, 
        output_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """保存工作流输出"""
        try:
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"output_{timestamp}.json"
            
            # 输出目录
            output_dir = get_project_data_path(project_name, date) / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / output_filename
            
            # 添加元数据
            output_with_meta = {
                "wf_id": wf_id,
                "created_at": datetime.now().isoformat(),
                "output": output_data
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_with_meta, f, ensure_ascii=False, indent=2)
            
            return True, str(output_path.relative_to(settings.BASE_DIR))
            
        except (IOError, json.JSONEncodeError) as e:
            return False, f"保存工作流输出失败: {str(e)}"
    
    def load_workflow_output(self, project_name: str, date: str, output_filename: str) -> Optional[Dict[str, Any]]:
        """加载工作流输出"""
        try:
            output_path = get_project_data_path(project_name, date) / "outputs" / output_filename
            
            if not output_path.exists():
                return None
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("output")
                
        except (json.JSONDecodeError, IOError) as e:
            print(f"加载工作流输出失败: {e}")
            return None
    
    def list_workflow_outputs(self, project_name: str, date: str) -> List[Dict[str, Any]]:
        """列出工作流输出"""
        outputs_dir = get_project_data_path(project_name, date) / "outputs"
        
        if not outputs_dir.exists():
            return []
        
        outputs = []
        
        for output_file in outputs_dir.glob("output_*.json"):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    output_info = {
                        "filename": output_file.name,
                        "wf_id": data.get("wf_id"),
                        "created_at": data.get("created_at"),
                        "output": data.get("output", {})
                    }
                    
                    outputs.append(output_info)
                    
            except (json.JSONDecodeError, IOError) as e:
                print(f"读取工作流输出失败 {output_file}: {e}")
                continue
        
        # 按创建时间排序
        outputs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return outputs
    
    def get_workflow_statistics(self, db: Session, project_id: int) -> Dict[str, Any]:
        """获取工作流统计信息"""
        workflows = self.list_workflow_executions(db, project_id)
        
        stats = {
            "total_workflows": len(workflows),
            "by_status": {
                "pending": 0,
                "running": 0,
                "success": 0,
                "failed": 0
            },
            "by_model": {},
            "avg_execution_time": 0
        }
        
        total_execution_time = 0
        completed_count = 0
        
        for workflow in workflows:
            # 按状态统计
            status = workflow.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # 按模型统计
            model = workflow.llm_model or "unknown"
            stats["by_model"][model] = stats["by_model"].get(model, 0) + 1
            
            # 计算执行时间
            if workflow.started_at and workflow.finished_at:
                execution_time = (workflow.finished_at - workflow.started_at).total_seconds()
                total_execution_time += execution_time
                completed_count += 1
        
        # 计算平均执行时间
        if completed_count > 0:
            stats["avg_execution_time"] = total_execution_time / completed_count
        
        return stats
    
    def cleanup_old_workflows(self, db: Session, days_old: int = 30) -> int:
        """清理旧的工作流记录"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            # 删除旧的工作流记录
            old_workflows = db.query(Workflow).filter(
                Workflow.created_at < cutoff_date,
                Workflow.status.in_(["success", "failed"])
            ).all()
            
            count = len(old_workflows)
            
            for workflow in old_workflows:
                db.delete(workflow)
            
            db.commit()
            
            return count
            
        except Exception as e:
            print(f"清理旧工作流失败: {e}")
            return 0
