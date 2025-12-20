"""工具配置管理器"""
import json
import os
import zlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from server.config import settings


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
    
    def get_tool_templates(self) -> Dict[str, Any]:
        """获取按工具类型划分的配置模板与字段说明

        返回结构示例：
        {
            "pdf_parser": {
                "type": "pdf_parser",
                "label": "PDF解析",
                "description": "...",
                "fields": [
                    {
                        "name": "extract_images",
                        "label": "提取图片",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "是否从 PDF 中提取图片内容"
                    },
                    ...
                ]
            },
            ...
        }
        """
        return {
            "pdf_parser": {
                "type": "pdf_parser",
                "label": "PDF解析",
                "description": "解析 PDF 文件并提取文本/图片/表格内容。",
                "fields": [
                    {
                        "name": "extract_images",
                        "label": "提取图片",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "是否从 PDF 中提取图片内容。",
                    },
                    {
                        "name": "extract_tables",
                        "label": "提取表格",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "是否尝试识别并提取表格数据。",
                    },
                    {
                        "name": "max_pages",
                        "label": "最大页数",
                        "type": "number",
                        "required": False,
                        "default": 100,
                        "help": "限制解析的最大页数，避免超大文档耗时过长。",
                    },
                    {
                        "name": "language",
                        "label": "语言",
                        "type": "string",
                        "required": False,
                        "default": "zh",
                        "help": "主要语言，用于优化解析效果，例如 zh / en。",
                    },
                ],
            },
            "image_reader": {
                "type": "image_reader",
                "label": "图片OCR",
                "description": "对图片进行文字识别（OCR）。",
                "fields": [
                    {
                        "name": "language",
                        "label": "语言",
                        "type": "string",
                        "required": False,
                        "default": "ch",
                        "help": "OCR 语言，例如 ch（中文）、en（英文）。",
                    },
                    {
                        "name": "use_gpu",
                        "label": "使用GPU",
                        "type": "boolean",
                        "required": False,
                        "default": False,
                        "help": "是否启用 GPU 加速（需要本机环境支持）。",
                    },
                    {
                        "name": "enable_detection",
                        "label": "启用检测",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "是否启用文本区域检测。",
                    },
                    {
                        "name": "enable_recognition",
                        "label": "启用识别",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "是否启用文字内容识别。",
                    },
                ],
            },
            "text_processor": {
                "type": "text_processor",
                "label": "文本处理",
                "description": "对原始文本进行清理、分段等预处理。",
                "fields": [
                    {
                        "name": "remove_extra_spaces",
                        "label": "移除多余空格",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "是否自动合并多余的空格和空行。",
                    },
                    {
                        "name": "remove_special_chars",
                        "label": "移除特殊字符",
                        "type": "boolean",
                        "required": False,
                        "default": False,
                        "help": "是否移除不可见控制字符等特殊符号。",
                    },
                    {
                        "name": "min_text_length",
                        "label": "最小文本长度",
                        "type": "number",
                        "required": False,
                        "default": 10,
                        "help": "过滤掉长度小于该值的短文本片段。",
                    },
                    {
                        "name": "max_text_length",
                        "label": "最大文本长度",
                        "type": "number",
                        "required": False,
                        "default": 10000,
                        "help": "单段文本的最大长度，超过会被截断或分段。",
                    },
                ],
            },
            "excel_reader": {
                "type": "excel_reader",
                "label": "Excel读取",
                "description": "读取 Excel 表格并转换为结构化数据。",
                "fields": [
                    {
                        "name": "sheet",
                        "label": "工作表名称/索引",
                        "type": "string",
                        "required": False,
                        "default": "",
                        "help": "要读取的工作表名称，留空则读取第一个。",
                    },
                    {
                        "name": "header",
                        "label": "包含表头",
                        "type": "boolean",
                        "required": False,
                        "default": True,
                        "help": "第一行是否作为表头使用。",
                    },
                    {
                        "name": "max_rows",
                        "label": "最大行数",
                        "type": "number",
                        "required": False,
                        "default": 5000,
                        "help": "限制读取的最大行数，避免超大表格引发性能问题。",
                    },
                ],
            },
            "mcp": {
                "type": "mcp",
                "label": "MCP 工具",
                "description": "通过 MCP 客户端调用外部工具服务。",
                "fields": [
                    {
                        "name": "server_url",
                        "label": "服务器地址",
                        "type": "string",
                        "required": True,
                        "default": "",
                        "help": "MCP 服务端地址，例如 http://localhost:9000。",
                    },
                    {
                        "name": "api_key",
                        "label": "API Key",
                        "type": "string",
                        "required": False,
                        "default": "",
                        "help": "访问 MCP 服务所需的凭证（如有）。",
                    },
                ],
            },
            "custom": {
                "type": "custom",
                "label": "自定义工具",
                "description": "完全自定义配置的工具，通常需要在代码中手动接入。",
                "fields": [
                    {
                        "name": "config",
                        "label": "自定义配置",
                        "type": "object",
                        "required": False,
                        "default": {},
                        "help": "任意 JSON 配置，具体含义由自定义工具代码决定。",
                    }
                ],
            },
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
