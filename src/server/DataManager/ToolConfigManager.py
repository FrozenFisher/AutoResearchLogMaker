"""工具配置管理器"""
import json
import os
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from config import settings


class ToolConfigManager:
    """工具配置管理器"""
    
    def __init__(self):
        self.static_dir = settings.STATIC_DIR
        self.tools_dir = settings.TOOLS_DIR
        self.default_config_path = self.static_dir / "default_tool_config.json"
        self.template_path = self.static_dir / "usertool_config_template.json"
    
    def get_default_tools(self) -> Dict[str, Any]:
        """获取默认工具配置"""
        if not self.default_config_path.exists():
            return {}
        
        try:
            with open(self.default_config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取默认工具配置失败: {e}")
            return {}
    
    def get_user_tools(self) -> Dict[str, Any]:
        """获取所有用户工具配置"""
        user_tools = {}
        
        if not self.tools_dir.exists():
            return user_tools
        
        for config_file in self.tools_dir.glob("usertool_*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    tool_config = json.load(f)
                    tool_name = config_file.stem.replace("usertool_", "")
                    user_tools[tool_name] = tool_config
            except (json.JSONDecodeError, IOError) as e:
                print(f"读取用户工具配置失败 {config_file}: {e}")
                continue
        
        return user_tools
    
    def get_all_tools(self) -> Dict[str, Any]:
        """获取所有工具配置（默认+用户）"""
        all_tools = {}
        
        # 添加默认工具
        default_tools = self.get_default_tools()
        if "default_tools" in default_tools:
            all_tools.update(default_tools["default_tools"])
        
        # 添加用户工具
        user_tools = self.get_user_tools()
        all_tools.update(user_tools)
        
        return all_tools
    
    def get_tool_config(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """获取指定工具的配置"""
        all_tools = self.get_all_tools()
        return all_tools.get(tool_name)
    
    def add_user_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> bool:
        """添加用户工具配置"""
        try:
            # 生成CRC32标识符
            tool_id = self._generate_tool_id(tool_name)
            config_filename = f"usertool_{tool_id}.json"
            config_path = self.tools_dir / config_filename
            
            # 确保目录存在
            self.tools_dir.mkdir(parents=True, exist_ok=True)
            
            # 写入配置文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(tool_config, f, ensure_ascii=False, indent=2)
            
            return True
        except (IOError, json.JSONEncodeError) as e:
            print(f"添加用户工具配置失败: {e}")
            return False
    
    def update_user_tool(self, tool_name: str, tool_config: Dict[str, Any]) -> bool:
        """更新用户工具配置"""
        # 查找对应的配置文件
        tool_file = None
        for config_file in self.tools_dir.glob("usertool_*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                    if existing_config.get("name") == tool_name:
                        tool_file = config_file
                        break
            except (json.JSONDecodeError, IOError):
                continue
        
        if not tool_file:
            return False
        
        try:
            with open(tool_file, 'w', encoding='utf-8') as f:
                json.dump(tool_config, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, json.JSONEncodeError) as e:
            print(f"更新用户工具配置失败: {e}")
            return False
    
    def delete_user_tool(self, tool_name: str) -> bool:
        """删除用户工具配置"""
        # 查找对应的配置文件
        tool_file = None
        for config_file in self.tools_dir.glob("usertool_*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                    if existing_config.get("name") == tool_name:
                        tool_file = config_file
                        break
            except (json.JSONDecodeError, IOError):
                continue
        
        if not tool_file:
            return False
        
        try:
            tool_file.unlink()
            return True
        except OSError as e:
            print(f"删除用户工具配置失败: {e}")
            return False
    
    def get_tool_template(self) -> Dict[str, Any]:
        """获取工具配置模板"""
        if not self.template_path.exists():
            return {
                "name": "",
                "description": "",
                "type": "custom",
                "config": {},
                "enabled": True
            }
        
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"读取工具配置模板失败: {e}")
            return {
                "name": "",
                "description": "",
                "type": "custom",
                "config": {},
                "enabled": True
            }
    
    def validate_tool_config(self, tool_config: Dict[str, Any]) -> bool:
        """验证工具配置格式"""
        required_fields = ["name", "description", "type", "config"]
        
        for field in required_fields:
            if field not in tool_config:
                return False
        
        # 检查名称是否已存在
        existing_tools = self.get_all_tools()
        if tool_config["name"] in existing_tools:
            return False
        
        return True
    
    def _generate_tool_id(self, tool_name: str) -> str:
        """生成工具ID（CRC32的8位十六进制）"""
        crc32_value = zlib.crc32(tool_name.encode('utf-8')) & 0xffffffff
        return f"{crc32_value:08x}"
    
    def list_tool_files(self) -> List[str]:
        """列出所有工具配置文件"""
        tool_files = []
        
        if not self.tools_dir.exists():
            return tool_files
        
        for config_file in self.tools_dir.glob("usertool_*.json"):
            tool_files.append(config_file.name)
        
        return sorted(tool_files)
