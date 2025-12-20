from fastapi import APIRouter
from typing import Any, Dict

from server.DataManager.ToolConfigManager import ToolConfigManager
from server.models import BaseResponse, ErrorResponse

router = APIRouter(prefix="/tool", tags=["tool"])

tool_manager = ToolConfigManager()


@router.get("/tool_list", response_model=BaseResponse)
async def tool_list() -> Dict[str, Any]:
    """获取所有工具配置（默认 + 用户）"""
    all_tools = tool_manager.get_all_tools()
    return {"code": 0, "status": "ok", "message": "", "data": all_tools}


@router.get("/defaults", response_model=BaseResponse)
async def default_tools() -> Dict[str, Any]:
    """获取默认工具配置"""
    defaults = tool_manager.get_default_tools()
    return {"code": 0, "status": "ok", "message": "", "data": defaults}


@router.get("/templates", response_model=BaseResponse)
async def tool_templates() -> Dict[str, Any]:
    """获取按工具类型划分的工具模板与字段说明"""
    templates = tool_manager.get_tool_templates()
    return {"code": 0, "status": "ok", "message": "", "data": templates}


@router.get("/{user_tool}", response_model=BaseResponse)
async def get_user_tool(user_tool: str) -> Dict[str, Any]:
    cfg = tool_manager.get_tool_config(user_tool)
    if cfg is None:
        return {"code": 1, "status": "error", "message": "tool not found", "data": None}
    return {"code": 0, "status": "ok", "message": "", "data": cfg}


@router.post("/{user_tool}/add", response_model=BaseResponse)
async def add_user_tool(user_tool: str, body: Dict[str, Any]) -> Dict[str, Any]:
    # 校验基本字段
    ok = tool_manager.validate_tool_config(body)
    if not ok:
        return {"code": 2, "status": "error", "message": "invalid tool config", "data": None}
    success = tool_manager.add_user_tool(user_tool, body)
    if not success:
        return {"code": 3, "status": "error", "message": "failed to add user tool", "data": None}
    return {"code": 0, "status": "ok", "message": "added", "data": body}


@router.post("/{user_tool}/edit", response_model=BaseResponse)
async def edit_user_tool(user_tool: str, body: Dict[str, Any]) -> Dict[str, Any]:
    success = tool_manager.update_user_tool(user_tool, body)
    if not success:
        return {"code": 4, "status": "error", "message": "failed to update user tool", "data": None}
    return {"code": 0, "status": "ok", "message": "updated", "data": body}
