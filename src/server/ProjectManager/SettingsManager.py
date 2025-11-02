"""设置管理器"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from server.config import get_project_settings_path
from server.models import ProjectSettings


class SettingsManager:
    """设置管理器"""
    
    def __init__(self):
        pass
    
    def load_settings(self, project_name: str) -> Optional[ProjectSettings]:
        """加载项目设置"""
        settings_path = get_project_settings_path(project_name)
        
        if not settings_path.exists():
            return None
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return ProjectSettings(**data)
        except (yaml.YAMLError, IOError, ValueError) as e:
            print(f"加载项目设置失败: {e}")
            return None
    
    def save_settings(self, project_name: str, settings: ProjectSettings) -> bool:
        """保存项目设置"""
        settings_path = get_project_settings_path(project_name)
        
        try:
            # 确保目录存在
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    settings.dict(), 
                    f, 
                    ensure_ascii=False, 
                    default_flow_style=False,
                    allow_unicode=True
                )
            
            return True
        except (IOError, yaml.YAMLError) as e:
            print(f"保存项目设置失败: {e}")
            return False
    
    def update_settings(
        self, 
        project_name: str, 
        **kwargs
    ) -> Tuple[bool, Optional[str]]:
        """更新项目设置"""
        try:
            # 加载现有设置
            current_settings = self.load_settings(project_name)
            if not current_settings:
                return False, "项目设置不存在"
            
            # 更新设置
            settings_dict = current_settings.dict()
            settings_dict.update(kwargs)
            
            # 创建新的设置对象
            updated_settings = ProjectSettings(**settings_dict)
            
            # 保存设置
            success = self.save_settings(project_name, updated_settings)
            if success:
                return True, "设置更新成功"
            else:
                return False, "设置保存失败"
                
        except Exception as e:
            return False, f"更新设置失败: {str(e)}"
    
    def get_default_prompt(self, project_name: str) -> Optional[str]:
        """获取默认提示模板"""
        settings = self.load_settings(project_name)
        return settings.default_prompt if settings else None
    
    def set_default_prompt(self, project_name: str, prompt: str) -> bool:
        """设置默认提示模板"""
        success, _ = self.update_settings(project_name, default_prompt=prompt)
        return success
    
    def get_required_tools(self, project_name: str) -> Dict[str, Any]:
        """获取必需工具配置"""
        settings = self.load_settings(project_name)
        return settings.required_tools if settings else {}
    
    def set_required_tools(self, project_name: str, tools: Dict[str, Any]) -> bool:
        """设置必需工具配置"""
        success, _ = self.update_settings(project_name, required_tools=tools)
        return success
    
    def add_default_tool(self, project_name: str, tool_name: str) -> bool:
        """添加默认工具"""
        settings = self.load_settings(project_name)
        if not settings:
            return False
        
        required_tools = settings.required_tools.copy()
        default_tools = required_tools.get("default_tools", [])
        
        if tool_name not in default_tools:
            default_tools.append(tool_name)
            required_tools["default_tools"] = default_tools
            return self.set_required_tools(project_name, required_tools)
        
        return True
    
    def remove_default_tool(self, project_name: str, tool_name: str) -> bool:
        """移除默认工具"""
        settings = self.load_settings(project_name)
        if not settings:
            return False
        
        required_tools = settings.required_tools.copy()
        default_tools = required_tools.get("default_tools", [])
        
        if tool_name in default_tools:
            default_tools.remove(tool_name)
            required_tools["default_tools"] = default_tools
            return self.set_required_tools(project_name, required_tools)
        
        return True
    
    def add_user_tool(self, project_name: str, tool_name: str) -> bool:
        """添加用户工具"""
        settings = self.load_settings(project_name)
        if not settings:
            return False
        
        required_tools = settings.required_tools.copy()
        user_tools = required_tools.get("user_tools", [])
        
        if tool_name not in user_tools:
            user_tools.append(tool_name)
            required_tools["user_tools"] = user_tools
            return self.set_required_tools(project_name, required_tools)
        
        return True
    
    def remove_user_tool(self, project_name: str, tool_name: str) -> bool:
        """移除用户工具"""
        settings = self.load_settings(project_name)
        if not settings:
            return False
        
        required_tools = settings.required_tools.copy()
        user_tools = required_tools.get("user_tools", [])
        
        if tool_name in user_tools:
            user_tools.remove(tool_name)
            required_tools["user_tools"] = user_tools
            return self.set_required_tools(project_name, required_tools)
        
        return True
    
    def create_default_settings(self, project_name: str) -> bool:
        """创建默认设置"""
        default_settings = ProjectSettings(
            default_prompt="请分析以下文件内容并生成研究总结",
            project_name=project_name,
            required_tools={
                "default_tools": ["pdf_parser", "image_reader"],
                "user_tools": []
            }
        )
        
        return self.save_settings(project_name, default_settings)
    
    def validate_settings(self, settings: ProjectSettings) -> Tuple[bool, Optional[str]]:
        """验证设置格式"""
        try:
            # 检查必需字段
            if not settings.default_prompt.strip():
                return False, "默认提示模板不能为空"
            
            if not settings.project_name.strip():
                return False, "项目名称不能为空"
            
            # 检查工具配置
            if not isinstance(settings.required_tools, dict):
                return False, "工具配置必须是字典格式"
            
            required_tools = settings.required_tools
            if "default_tools" not in required_tools:
                return False, "缺少默认工具配置"
            
            if "user_tools" not in required_tools:
                return False, "缺少用户工具配置"
            
            # 检查工具列表格式
            if not isinstance(required_tools["default_tools"], list):
                return False, "默认工具配置必须是列表格式"
            
            if not isinstance(required_tools["user_tools"], list):
                return False, "用户工具配置必须是列表格式"
            
            return True, None
            
        except Exception as e:
            return False, f"设置验证失败: {str(e)}"
    
    def get_settings_template(self) -> Dict[str, Any]:
        """获取设置模板"""
        return {
            "default_prompt": "请分析以下文件内容并生成研究总结",
            "project_name": "",
            "required_tools": {
                "default_tools": ["pdf_parser", "image_reader"],
                "user_tools": []
            }
        }
    
    def export_settings(self, project_name: str) -> Optional[Dict[str, Any]]:
        """导出项目设置"""
        settings = self.load_settings(project_name)
        return settings.dict() if settings else None
    
    def import_settings(self, project_name: str, settings_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """导入项目设置"""
        try:
            # 验证设置格式
            settings = ProjectSettings(**settings_data)
            is_valid, error_msg = self.validate_settings(settings)
            
            if not is_valid:
                return False, error_msg
            
            # 保存设置
            success = self.save_settings(project_name, settings)
            if success:
                return True, "设置导入成功"
            else:
                return False, "设置保存失败"
                
        except Exception as e:
            return False, f"导入设置失败: {str(e)}"
    
    def reset_to_default(self, project_name: str) -> bool:
        """重置为默认设置"""
        return self.create_default_settings(project_name)
