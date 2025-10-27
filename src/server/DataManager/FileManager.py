"""文件管理器"""
import os
import zlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import mimetypes
from config import settings, get_project_files_path
from models import FileInfo, FileSource, FileStatus
from .MetadataManager import MetadataManager


class FileManager:
    """文件管理器"""
    
    def __init__(self):
        self.metadata_manager = MetadataManager()
    
    def upload_file(
        self,
        project_name: str,
        date: str,
        file_content: bytes,
        filename: str,
        source: FileSource = FileSource.MANUAL_UPLOAD,
        tags: list = None,
        notes: str = None,
        replace_existing: bool = False
    ) -> Tuple[bool, Optional[str], Optional[FileInfo]]:
        """上传文件"""
        try:
            # 验证文件类型
            mime_type = self._get_mime_type(filename)
            if not self._is_allowed_file_type(mime_type):
                return False, f"不支持的文件类型: {mime_type}", None
            
            # 验证文件大小
            if len(file_content) > settings.MAX_FILE_SIZE:
                return False, f"文件大小超过限制: {settings.MAX_FILE_SIZE} bytes", None
            
            # 生成文件ID和存储路径
            file_id = self._generate_file_id(filename, file_content)
            stored_filename = self._generate_stored_filename(filename, file_id)
            stored_path = get_project_files_path(project_name, date) / stored_filename
            
            # 检查是否已存在
            if stored_path.exists() and not replace_existing:
                return False, "文件已存在，请使用更新接口或设置replace_existing=True", None
            
            # 确保目录存在
            stored_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存文件
            with open(stored_path, 'wb') as f:
                f.write(file_content)
            
            # 创建文件信息
            file_info = FileInfo(
                file_id=file_id,
                filename=filename,
                stored_path=str(stored_path.relative_to(settings.BASE_DIR)),
                original_name=filename,
                crc32=self._calculate_crc32(file_content),
                mime=mime_type,
                size_bytes=len(file_content),
                uploaded_at=datetime.now(),
                source=source,
                tags=tags or [],
                language=self._detect_language(filename),
                status={
                    "ocr": FileStatus.PENDING,
                    "parsed": FileStatus.PENDING
                },
                notes=notes
            )
            
            # 更新元数据
            success = self.metadata_manager.add_file_to_metadata(
                project_name, date, file_info, replace_existing
            )
            
            if success:
                return True, str(stored_path), file_info
            else:
                # 如果元数据更新失败，删除文件
                stored_path.unlink()
                return False, "元数据更新失败", None
                
        except Exception as e:
            return False, f"文件上传失败: {str(e)}", None
    
    def update_file(
        self,
        project_name: str,
        date: str,
        file_content: bytes,
        filename: str,
        source: FileSource = FileSource.MANUAL_UPLOAD,
        tags: list = None,
        notes: str = None
    ) -> Tuple[bool, Optional[str], Optional[FileInfo]]:
        """更新文件"""
        return self.upload_file(
            project_name, date, file_content, filename, 
            source, tags, notes, replace_existing=True
        )
    
    def get_file_info(self, project_name: str, date: str, file_id: str) -> Optional[FileInfo]:
        """获取文件信息"""
        metadata = self.metadata_manager.load_metadata(project_name, date)
        
        if not metadata:
            return None
        
        for file_info in metadata.files:
            if file_info.file_id == file_id:
                return file_info
        
        return None
    
    def get_file_content(self, project_name: str, date: str, file_id: str) -> Optional[bytes]:
        """获取文件内容"""
        file_info = self.get_file_info(project_name, date, file_id)
        
        if not file_info:
            return None
        
        file_path = settings.BASE_DIR / file_info.stored_path
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'rb') as f:
                return f.read()
        except IOError:
            return None
    
    def delete_file(self, project_name: str, date: str, file_id: str) -> bool:
        """删除文件"""
        file_info = self.get_file_info(project_name, date, file_id)
        
        if not file_info:
            return False
        
        # 从元数据中移除
        success = self.metadata_manager.remove_file_from_metadata(
            project_name, date, file_id, retire=True
        )
        
        if success:
            # 删除物理文件
            file_path = settings.BASE_DIR / file_info.stored_path
            if file_path.exists():
                try:
                    file_path.unlink()
                except OSError:
                    pass  # 忽略删除失败
        
        return success
    
    def list_files(self, project_name: str, date: str) -> list[FileInfo]:
        """列出文件"""
        metadata = self.metadata_manager.load_metadata(project_name, date)
        
        if not metadata:
            return []
        
        return metadata.files
    
    def get_files_by_type(self, project_name: str, date: str, mime_type: str) -> list[FileInfo]:
        """根据类型获取文件"""
        files = self.list_files(project_name, date)
        return [f for f in files if f.mime == mime_type]
    
    def get_files_by_source(self, project_name: str, date: str, source: FileSource) -> list[FileInfo]:
        """根据来源获取文件"""
        files = self.list_files(project_name, date)
        return [f for f in files if f.source == source]
    
    def update_file_status(
        self, 
        project_name: str, 
        date: str, 
        file_id: str, 
        status_type: str, 
        status: str
    ) -> bool:
        """更新文件处理状态"""
        file_info = self.get_file_info(project_name, date, file_id)
        
        if not file_info:
            return False
        
        file_info.status[status_type] = status
        
        return self.metadata_manager.update_file_in_metadata(
            project_name, date, file_id, file_info
        )
    
    def copy_file_to_output(
        self, 
        project_name: str, 
        date: str, 
        file_id: str, 
        output_filename: str
    ) -> Optional[str]:
        """复制文件到输出目录"""
        file_info = self.get_file_info(project_name, date, file_id)
        
        if not file_info:
            return None
        
        source_path = settings.BASE_DIR / file_info.stored_path
        output_dir = settings.BASE_DIR / "lib" / "server" / "usrdata" / project_name / "data" / date / "outputs"
        output_path = output_dir / output_filename
        
        try:
            # 确保输出目录存在
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, output_path)
            
            return str(output_path.relative_to(settings.BASE_DIR))
        except Exception as e:
            print(f"复制文件失败: {e}")
            return None
    
    def _generate_file_id(self, filename: str, content: bytes) -> str:
        """生成文件ID"""
        # 使用文件名和内容的CRC32生成唯一ID
        combined = f"{filename}_{len(content)}".encode('utf-8')
        crc32_value = zlib.crc32(combined) & 0xffffffff
        return f"f_{crc32_value:08x}"
    
    def _generate_stored_filename(self, original_filename: str, file_id: str) -> str:
        """生成存储文件名"""
        name, ext = os.path.splitext(original_filename)
        return f"{name}_{file_id}{ext}"
    
    def _calculate_crc32(self, content: bytes) -> str:
        """计算CRC32校验码"""
        crc32_value = zlib.crc32(content) & 0xffffffff
        return f"{crc32_value:08x}"
    
    def _get_mime_type(self, filename: str) -> str:
        """获取MIME类型"""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"
    
    def _is_allowed_file_type(self, mime_type: str) -> bool:
        """检查文件类型是否允许"""
        return mime_type in settings.ALLOWED_FILE_TYPES
    
    def _detect_language(self, filename: str) -> Optional[str]:
        """检测文件语言（简单实现）"""
        # 简单的语言检测，可以根据文件名或内容扩展
        if any(char in filename for char in "中文汉字"):
            return "zh"
        elif any(char in filename for char in "あいうえお"):
            return "ja"
        elif any(char in filename for char in "абвгде"):
            return "ru"
        else:
            return "en"
    
    def get_file_statistics(self, project_name: str, date: str) -> Dict[str, Any]:
        """获取文件统计信息"""
        files = self.list_files(project_name, date)
        
        stats = {
            "total_files": len(files),
            "total_size": sum(f.size_bytes or 0 for f in files),
            "by_type": {},
            "by_source": {},
            "by_status": {
                "ocr_pending": 0,
                "ocr_done": 0,
                "ocr_failed": 0,
                "parsed_pending": 0,
                "parsed_done": 0,
                "parsed_failed": 0
            }
        }
        
        for file_info in files:
            # 按类型统计
            mime_type = file_info.mime or "unknown"
            stats["by_type"][mime_type] = stats["by_type"].get(mime_type, 0) + 1
            
            # 按来源统计
            source = file_info.source.value
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # 按状态统计
            ocr_status = file_info.status.get("ocr", "pending")
            parsed_status = file_info.status.get("parsed", "pending")
            
            stats["by_status"][f"ocr_{ocr_status}"] += 1
            stats["by_status"][f"parsed_{parsed_status}"] += 1
        
        return stats
