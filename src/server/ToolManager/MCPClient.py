"""MCP Client 工具封装"""
from typing import Any, Dict, Optional
import json
import httpx
from .ToolRegistry import BaseTool


class MCPClient:
    """简化版 MCP 客户端，通过HTTP调用远端MCP Server工具接口"""

    def __init__(self, server_url: str, auth: Optional[Dict[str, Any]] = None, timeout: int = 60):
        self.server_url = server_url.rstrip('/')
        self.auth = auth or {}
        self.timeout = timeout

    async def call_tool(self, tool_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.server_url}/tools/{tool_name}"
        headers = {"Content-Type": "application/json"}
        if token := self.auth.get("bearer"):
            headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()


class MCPTool(BaseTool):
    """基于MCP的远端工具代理。config示例：
    {
      "name": "ext_summarizer",
      "type": "mcp",
      "config": {
        "server_url": "https://mcp.example.com",
        "auth": {"bearer": "TOKEN"},
        "remote_tool": "summarize",
        "timeout": 60
      }
    }
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            name=config.get("name", "mcp_tool"),
            description=config.get("description", "MCP external tool"),
            config=config
        )
        cfg = config.get("config", {})
        self.remote_tool = cfg.get("remote_tool")
        self.client = MCPClient(
            server_url=cfg.get("server_url", ""),
            auth=cfg.get("auth"),
            timeout=int(cfg.get("timeout", 60))
        )

    def validate_config(self) -> bool:
        cfg = self.config.get("config", {})
        return bool(cfg.get("server_url") and cfg.get("remote_tool"))

    async def process(self, input_data: Any) -> Any:
        payload = input_data if isinstance(input_data, dict) else {"input": input_data}
        return await self.client.call_tool(self.remote_tool, payload)
