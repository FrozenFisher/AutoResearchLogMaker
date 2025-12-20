"""项目管理器"""
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from server.config import settings, get_project_path, get_project_settings_path
from server.database import get_project_by_name, create_project, Project
from server.models import ProjectInfo, ProjectSettings


class ProjectManager:
    """项目管理器"""
    
    def __init__(self):
        # 当前项目配置文件，存放在全局 usrdata 目录下
        self._current_project_file = settings.USRDATA_DIR / "current_project.txt"
    
    def create_project(
        self, 
        db: Session, 
        name: str, 
        display_name: str, 
        description: str = None,
        default_prompt: str = "请分析以下文件内容并生成研究总结",
        required_tools: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str], Optional[Project]]:
        """创建新项目"""
        try:
            # 检查项目名是否已存在
            existing_project = get_project_by_name(db, name)
            if existing_project:
                return False, f"项目 '{name}' 已存在", None
            
            # 验证项目名
            if not self._is_valid_project_name(name):
                return False, "项目名只能包含字母、数字、下划线和连字符", None
            
            # 创建数据库记录
            project = create_project(db, name, display_name, description)
            
            # 创建目录结构
            success = self._create_project_directories(name)
            if not success:
                # 如果目录创建失败，删除数据库记录
                db.delete(project)
                db.commit()
                return False, "项目目录创建失败", None
            
            # 创建默认设置文件
            settings_success = self._create_default_settings(
                name, default_prompt, required_tools
            )
            if not settings_success:
                # 如果设置文件创建失败，删除数据库记录和目录
                db.delete(project)
                db.commit()
                shutil.rmtree(get_project_path(name), ignore_errors=True)
                return False, "项目设置文件创建失败", None
            
            return True, "项目创建成功", project
            
        except Exception as e:
            return False, f"创建项目失败: {str(e)}", None
    
    def get_project(self, db: Session, name: str) -> Optional[Project]:
        """获取项目"""
        return get_project_by_name(db, name)
    
    def list_projects(self, db: Session) -> List[Project]:
        """列出所有项目"""
        return db.query(Project).filter(Project.is_active == True).all()
    
    def update_project(
        self, 
        db: Session, 
        name: str, 
        display_name: str = None, 
        description: str = None
    ) -> Tuple[bool, Optional[str]]:
        """更新项目信息"""
        try:
            project = get_project_by_name(db, name)
            if not project:
                return False, f"项目 '{name}' 不存在"
            
            if display_name:
                project.display_name = display_name
            if description is not None:
                project.description = description
            
            project.updated_at = datetime.now()
            db.commit()
            
            return True, "项目更新成功"
            
        except Exception as e:
            return False, f"更新项目失败: {str(e)}"
    
    def delete_project(self, db: Session, name: str) -> Tuple[bool, Optional[str]]:
        """删除项目（软删除）"""
        try:
            project = get_project_by_name(db, name)
            if not project:
                return False, f"项目 '{name}' 不存在"
            
            # 软删除：标记为非活跃
            project.is_active = False
            project.updated_at = datetime.now()
            db.commit()
            
            return True, "项目删除成功"
            
        except Exception as e:
            return False, f"删除项目失败: {str(e)}"
    
    def hard_delete_project(self, db: Session, name: str) -> Tuple[bool, Optional[str]]:
        """硬删除项目（删除所有数据）"""
        try:
            project = get_project_by_name(db, name)
            if not project:
                return False, f"项目 '{name}' 不存在"
            
            # 删除数据库记录
            db.delete(project)
            db.commit()
            
            # 删除目录结构
            project_path = get_project_path(name)
            if project_path.exists():
                shutil.rmtree(project_path)
            
            return True, "项目完全删除成功"
            
        except Exception as e:
            return False, f"硬删除项目失败: {str(e)}"
    
    def get_project_info(self, db: Session, name: str) -> Optional[ProjectInfo]:
        """获取项目信息"""
        project = get_project_by_name(db, name)
        if not project:
            return None
        
        return ProjectInfo(
            name=project.name,
            display_name=project.display_name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at
        )
    
    def get_project_statistics(self, db: Session, name: str) -> Dict[str, Any]:
        """获取项目统计信息"""
        project = get_project_by_name(db, name)
        if not project:
            return {}
        
        project_path = get_project_path(name)
        
        stats = {
            "project_name": name,
            "created_at": project.created_at,
            "updated_at": project.updated_at,
            "total_workflows": len(project.workflows),
            "active_workflows": len([w for w in project.workflows if w.status == "running"]),
            "completed_workflows": len([w for w in project.workflows if w.status == "success"]),
            "failed_workflows": len([w for w in project.workflows if w.status == "failed"]),
            "total_dates": 0,
            "total_files": 0,
            "total_size": 0
        }
        
        # 统计文件和日期
        files_dir = project_path / "files"
        if files_dir.exists():
            dates = [d for d in files_dir.iterdir() if d.is_dir()]
            stats["total_dates"] = len(dates)
            
            for date_dir in dates:
                metadata_file = date_dir / "record_meta.json"
                if metadata_file.exists():
                    try:
                        import json
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            files = metadata.get("files", [])
                            stats["total_files"] += len(files)
                            stats["total_size"] += sum(f.get("size_bytes", 0) for f in files)
                    except (json.JSONDecodeError, IOError):
                        continue
        
        return stats
    
    def backup_project(self, name: str, backup_path: str) -> Tuple[bool, Optional[str]]:
        """备份项目"""
        try:
            project_path = get_project_path(name)
            if not project_path.exists():
                return False, f"项目 '{name}' 不存在"
            
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建备份目录名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{name}_backup_{timestamp}"
            backup_project_path = backup_dir / backup_name
            
            # 复制项目目录
            shutil.copytree(project_path, backup_project_path)
            
            return True, str(backup_project_path)
            
        except Exception as e:
            return False, f"备份项目失败: {str(e)}"
    
    def restore_project(self, backup_path: str, new_name: str = None) -> Tuple[bool, Optional[str]]:
        """恢复项目"""
        try:
            backup_dir = Path(backup_path)
            if not backup_dir.exists():
                return False, "备份目录不存在"
            
            # 查找最新的备份
            backup_dirs = [d for d in backup_dir.iterdir() if d.is_dir() and d.name.startswith("_backup_")]
            if not backup_dirs:
                return False, "未找到有效的备份"
            
            latest_backup = max(backup_dirs, key=lambda x: x.stat().st_mtime)
            
            # 确定项目名
            if new_name:
                project_name = new_name
            else:
                project_name = latest_backup.name.split("_backup_")[0]
            
            # 检查项目名是否已存在
            project_path = get_project_path(project_name)
            if project_path.exists():
                return False, f"项目 '{project_name}' 已存在"
            
            # 恢复项目目录
            shutil.copytree(latest_backup, project_path)
            
            return True, f"项目 '{project_name}' 恢复成功"
            
        except Exception as e:
            return False, f"恢复项目失败: {str(e)}"
    
    def _create_project_directories(self, name: str) -> bool:
        """创建项目目录结构"""
        try:
            project_path = get_project_path(name)
            
            # 创建主要目录
            directories = [
                project_path,
                project_path / "files",
                project_path / "data",
                project_path / "data" / "outputs",
                project_path / "data" / "workflows"
            ]
            
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"创建项目目录失败: {e}")
            return False
    
    def _create_default_settings(
        self, 
        name: str, 
        default_prompt: str, 
        required_tools: Dict[str, Any] = None
    ) -> bool:
        """创建默认设置文件"""
        try:
            settings_path = get_project_settings_path(name)
            
            if required_tools is None:
                required_tools = {
                    "default_tools": ["pdf_parser", "image_reader"],
                    "user_tools": []
                }
            
            settings_data = {
                "default_prompt": default_prompt,
                "project_name": name,
                "required_tools": required_tools
            }
            
            import yaml
            with open(settings_path, 'w', encoding='utf-8') as f:
                yaml.dump(settings_data, f, default_flow_style=False)
            
            return True
            
        except Exception as e:
            print(f"创建默认设置文件失败: {e}")
            return False
    
    def _is_valid_project_name(self, name: str) -> bool:
        """验证项目名是否有效"""
        if not name or len(name) < 2:
            return False
        
        # 只允许字母、数字、下划线和连字符
        import re
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))
    
    def get_project_dates(self, name: str) -> List[str]:
        """获取项目的所有日期"""
        project_path = get_project_path(name)
        files_dir = project_path / "files"
        
        if not files_dir.exists():
            return []
        
        dates = []
        for date_dir in files_dir.iterdir():
            if date_dir.is_dir():
                dates.append(date_dir.name)
        
        return sorted(dates, reverse=True)  # 最新的在前

    def get_current_project_name(self) -> Optional[str]:
        """获取当前项目名称"""
        try:
            if not self._current_project_file.exists():
                return None
            content = self._current_project_file.read_text(encoding="utf-8").strip()
            return content or None
        except Exception as e:
            print(f"读取当前项目失败: {e}")
            return None

    def set_current_project_name(self, name: str) -> bool:
        """设置当前项目名称"""
        try:
            # 确保目录存在
            self._current_project_file.parent.mkdir(parents=True, exist_ok=True)
            self._current_project_file.write_text(name, encoding="utf-8")
            return True
        except Exception as e:
            print(f"保存当前项目失败: {e}")
            return False
