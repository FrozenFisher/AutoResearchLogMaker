"""工具注册表"""
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
from .DataManager.ToolConfigManager import ToolConfigManager


class BaseTool(ABC):
    """工具基类"""
    
    def __init__(self, name: str, description: str, config: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """处理输入数据"""
        pass
    
    def validate_config(self) -> bool:
        """验证工具配置"""
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "enabled": self.enabled
        }


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_config_manager = ToolConfigManager()
        self._load_default_tools()
        self._load_user_tools()
    
    def register_tool(self, tool: BaseTool) -> bool:
        """注册工具"""
        try:
            if not tool.validate_config():
                print(f"工具 '{tool.name}' 配置验证失败")
                return False
            
            self.tools[tool.name] = tool
            print(f"工具 '{tool.name}' 注册成功")
            return True
            
        except Exception as e:
            print(f"注册工具 '{tool.name}' 失败: {e}")
            return False
    
    def unregister_tool(self, tool_name: str) -> bool:
        """注销工具"""
        if tool_name in self.tools:
            del self.tools[tool_name]
            print(f"工具 '{tool_name}' 注销成功")
            return True
        return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """获取工具"""
        return self.tools.get(tool_name)
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """列出所有工具"""
        return [tool.get_info() for tool in self.tools.values()]
    
    def list_enabled_tools(self) -> List[Dict[str, Any]]:
        """列出启用的工具"""
        return [tool.get_info() for tool in self.tools.values() if tool.enabled]
    
    def enable_tool(self, tool_name: str) -> bool:
        """启用工具"""
        tool = self.get_tool(tool_name)
        if tool:
            tool.enabled = True
            return True
        return False
    
    def disable_tool(self, tool_name: str) -> bool:
        """禁用工具"""
        tool = self.get_tool(tool_name)
        if tool:
            tool.enabled = False
            return True
        return False
    
    async def process_with_tool(self, tool_name: str, input_data: Any) -> Any:
        """使用指定工具处理数据"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"工具 '{tool_name}' 不存在")
        
        if not tool.enabled:
            raise ValueError(f"工具 '{tool_name}' 已禁用")
        
        return await tool.process(input_data)
    
    def get_tools_by_type(self, tool_type: str) -> List[BaseTool]:
        """根据类型获取工具"""
        return [tool for tool in self.tools.values() 
                if tool.config.get("type") == tool_type]
    
    def _load_default_tools(self):
        """加载默认工具"""
        try:
            # 注册PDF解析工具
            from .PDFParser import PDFParserTool
            pdf_tool = PDFParserTool()
            self.register_tool(pdf_tool)
            
            # 注册图片读取工具
            from .ImageReader import ImageReaderTool
            image_tool = ImageReaderTool()
            self.register_tool(image_tool)
            
            # 注册文本处理工具
            from .TextProcessor import TextProcessorTool
            text_tool = TextProcessorTool()
            self.register_tool(text_tool)
            
        except ImportError as e:
            print(f"加载默认工具失败: {e}")
    
    def _load_user_tools(self):
        """加载用户工具"""
        try:
            user_tools = self.tool_config_manager.get_user_tools()
            
            for tool_name, tool_config in user_tools.items():
                if tool_config.get("enabled", True):
                    # 根据工具类型创建相应的工具实例
                    tool_type = tool_config.get("type", "custom")
                    
                    if tool_type == "pdf_parser":
                        from .PDFParser import PDFParserTool
                        tool = PDFParserTool(tool_config)
                    elif tool_type == "image_reader":
                        from .ImageReader import ImageReaderTool
                        tool = ImageReaderTool(tool_config)
                    elif tool_type == "text_processor":
                        from .TextProcessor import TextProcessorTool
                        tool = TextProcessorTool(tool_config)
                    else:
                        # 自定义工具
                        tool = CustomTool(tool_name, tool_config)
                    
                    self.register_tool(tool)
                    
        except Exception as e:
            print(f"加载用户工具失败: {e}")
    
    def reload_tools(self):
        """重新加载所有工具"""
        self.tools.clear()
        self._load_default_tools()
        self._load_user_tools()
    
    def get_tool_statistics(self) -> Dict[str, Any]:
        """获取工具统计信息"""
        total_tools = len(self.tools)
        enabled_tools = len([t for t in self.tools.values() if t.enabled])
        
        tool_types = {}
        for tool in self.tools.values():
            tool_type = tool.config.get("type", "unknown")
            tool_types[tool_type] = tool_types.get(tool_type, 0) + 1
        
        return {
            "total_tools": total_tools,
            "enabled_tools": enabled_tools,
            "disabled_tools": total_tools - enabled_tools,
            "tool_types": tool_types
        }


class CustomTool(BaseTool):
    """自定义工具"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(
            name=name,
            description=config.get("description", ""),
            config=config
        )
        self.process_func = config.get("process_func")
    
    async def process(self, input_data: Any) -> Any:
        """处理输入数据"""
        if self.process_func and callable(self.process_func):
            return await self.process_func(input_data)
        else:
            raise NotImplementedError(f"工具 '{self.name}' 未实现处理函数")
    
    def validate_config(self) -> bool:
        """验证工具配置"""
        required_fields = ["description", "type"]
        return all(field in self.config for field in required_fields)


# 全局工具注册表实例
tool_registry = ToolRegistry()
