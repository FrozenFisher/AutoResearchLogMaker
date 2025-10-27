"""元数据管理器"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import get_project_files_path, get_project_data_path, settings
from models import RecordMetadata, FileInfo, AuthorInfo, SummaryInfo, WorkflowInfo, GitInfo, Permissions


class MetadataManager:
    """元数据管理器"""
    
    def __init__(self):
        pass
    
    def get_metadata_path(self, project_name: str, date: str) -> Path:
        """获取元数据文件路径"""
        return get_project_files_path(project_name, date) / "record_meta.json"
    
    def load_metadata(self, project_name: str, date: str) -> Optional[RecordMetadata]:
        """加载元数据"""
        metadata_path = self.get_metadata_path(project_name, date)
        
        if not metadata_path.exists():
            return None
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return RecordMetadata(**data)
        except (json.JSONDecodeError, IOError, ValueError) as e:
            print(f"加载元数据失败: {e}")
            return None
    
    def save_metadata(self, project_name: str, date: str, metadata: RecordMetadata) -> bool:
        """保存元数据"""
        metadata_path = self.get_metadata_path(project_name, date)
        
        try:
            # 确保目录存在
            metadata_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 更新修改时间
            metadata.updated_at = datetime.now()
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata.dict(), f, ensure_ascii=False, indent=2, default=str)
            
            return True
        except (IOError, json.JSONEncodeError) as e:
            print(f"保存元数据失败: {e}")
            return False
    
    def create_metadata(
        self, 
        project_name: str, 
        date: str, 
        author: AuthorInfo,
        record_id: Optional[str] = None
    ) -> RecordMetadata:
        """创建新的元数据"""
        if not record_id:
            record_id = self._generate_record_id(date)
        
        metadata = RecordMetadata(
            record_id=record_id,
            project=project_name,
            date=date,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            author=author,
            files=[],
            summary=SummaryInfo(),
            workflows=[],
            tags=[],
            permissions=Permissions(read=[author.user_id], write=[author.user_id])
        )
        
        return metadata
    
    def add_file_to_metadata(
        self, 
        project_name: str, 
        date: str, 
        file_info: FileInfo,
        replace_existing: bool = False
    ) -> bool:
        """添加文件到元数据"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            # 创建新的元数据
            author = AuthorInfo(user_id="system", display_name="System")
            metadata = self.create_metadata(project_name, date, author)
        
        if replace_existing:
            # 标记同名文件为已废弃
            for i, existing_file in enumerate(metadata.files):
                if existing_file.filename == file_info.filename:
                    metadata.files[i] = file_info
                    break
            else:
                metadata.files.append(file_info)
        else:
            # 添加新文件
            metadata.files.append(file_info)
        
        return self.save_metadata(project_name, date, metadata)
    
    def update_file_in_metadata(
        self, 
        project_name: str, 
        date: str, 
        file_id: str, 
        file_info: FileInfo
    ) -> bool:
        """更新元数据中的文件信息"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return False
        
        for i, existing_file in enumerate(metadata.files):
            if existing_file.file_id == file_id:
                metadata.files[i] = file_info
                break
        else:
            return False
        
        return self.save_metadata(project_name, date, metadata)
    
    def remove_file_from_metadata(
        self, 
        project_name: str, 
        date: str, 
        file_id: str,
        retire: bool = True
    ) -> bool:
        """从元数据中移除文件"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return False
        
        if retire:
            # 标记为已废弃
            for file_info in metadata.files:
                if file_info.file_id == file_id:
                    file_info.status["retired"] = "true"
                    file_info.status["retired_at"] = datetime.now().isoformat()
                    break
        else:
            # 完全移除
            metadata.files = [f for f in metadata.files if f.file_id != file_id]
        
        return self.save_metadata(project_name, date, metadata)
    
    def add_workflow_to_metadata(
        self, 
        project_name: str, 
        date: str, 
        workflow_info: WorkflowInfo
    ) -> bool:
        """添加工作流到元数据"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            author = AuthorInfo(user_id="system", display_name="System")
            metadata = self.create_metadata(project_name, date, author)
        
        metadata.workflows.append(workflow_info)
        return self.save_metadata(project_name, date, metadata)
    
    def update_workflow_in_metadata(
        self, 
        project_name: str, 
        date: str, 
        wf_id: str, 
        workflow_info: WorkflowInfo
    ) -> bool:
        """更新元数据中的工作流信息"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return False
        
        for i, existing_workflow in enumerate(metadata.workflows):
            if existing_workflow.wf_id == wf_id:
                metadata.workflows[i] = workflow_info
                break
        else:
            return False
        
        return self.save_metadata(project_name, date, metadata)
    
    def update_summary_in_metadata(
        self, 
        project_name: str, 
        date: str, 
        summary: SummaryInfo
    ) -> bool:
        """更新元数据中的总结信息"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return False
        
        metadata.summary = summary
        return self.save_metadata(project_name, date, metadata)
    
    def add_tags_to_metadata(
        self, 
        project_name: str, 
        date: str, 
        tags: List[str]
    ) -> bool:
        """添加标签到元数据"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return False
        
        for tag in tags:
            if tag not in metadata.tags:
                metadata.tags.append(tag)
        
        return self.save_metadata(project_name, date, metadata)
    
    def get_files_by_tags(
        self, 
        project_name: str, 
        date: str, 
        tags: List[str]
    ) -> List[FileInfo]:
        """根据标签获取文件"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return []
        
        matching_files = []
        for file_info in metadata.files:
            if any(tag in file_info.tags for tag in tags):
                matching_files.append(file_info)
        
        return matching_files
    
    def get_workflows_by_status(
        self, 
        project_name: str, 
        date: str, 
        status: str
    ) -> List[WorkflowInfo]:
        """根据状态获取工作流"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return []
        
        return [wf for wf in metadata.workflows if wf.status == status]
    
    def get_metadata_summary(self, project_name: str, date: str) -> Dict[str, Any]:
        """获取元数据摘要"""
        metadata = self.load_metadata(project_name, date)
        
        if not metadata:
            return {}
        
        return {
            "record_id": metadata.record_id,
            "project": metadata.project,
            "date": metadata.date,
            "created_at": metadata.created_at,
            "updated_at": metadata.updated_at,
            "file_count": len(metadata.files),
            "workflow_count": len(metadata.workflows),
            "tags": metadata.tags,
            "summary_available": metadata.summary.auto_summary is not None
        }
    
    def _generate_record_id(self, date: str) -> str:
        """生成记录ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import random
        random_suffix = f"{random.randint(1000, 9999):04x}"
        return f"{timestamp}_{random_suffix}"
    
    def list_project_dates(self, project_name: str) -> List[str]:
        """列出项目的所有日期"""
        project_path = Path(settings.USRDATA_DIR) / project_name / "files"
        
        if not project_path.exists():
            return []
        
        dates = []
        for date_dir in project_path.iterdir():
            if date_dir.is_dir() and (date_dir / "record_meta.json").exists():
                dates.append(date_dir.name)
        
        return sorted(dates, reverse=True)  # 最新的在前
