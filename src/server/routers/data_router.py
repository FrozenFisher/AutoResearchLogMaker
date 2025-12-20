from fastapi import APIRouter, UploadFile, File, Form, Depends, Response
from typing import Any, Dict, Optional, List

from server.DataManager.FileManager import FileManager
from server.DataManager.MetadataManager import MetadataManager
from server.ProjectManager.ProjectManager import ProjectManager
from server.models import BaseResponse, FileSource

router = APIRouter(prefix="/project/{project}/data", tags=["data"])

file_manager = FileManager()
metadata_manager = MetadataManager()
project_manager = ProjectManager()


@router.post("/{date}/upload_files", response_model=BaseResponse)
async def upload_files(
    project: str,
    date: str,
    file: UploadFile = File(...),
    source: str = Form("manual_upload"),
    tags: str = Form(""),
    notes: str = Form("")
) -> Dict[str, Any]:
    content = await file.read()
    tag_list = [t for t in tags.split(',') if t.strip()] if tags else []
    ok, msg, info = file_manager.upload_file(project, date, content, file.filename, FileSource(source), tag_list, notes, False)
    if not ok:
        return {"code": 1, "status": "error", "message": msg or "upload failed", "data": None}
    return {"code": 0, "status": "ok", "message": "uploaded", "data": info.dict()}


@router.post("/{date}/update_files", response_model=BaseResponse)
async def update_files(
    project: str,
    date: str,
    file: UploadFile = File(...),
    source: str = Form("manual_upload"),
    tags: str = Form(""),
    notes: str = Form("")
) -> Dict[str, Any]:
    content = await file.read()
    tag_list = [t for t in tags.split(',') if t.strip()] if tags else []
    ok, msg, info = file_manager.update_file(project, date, content, file.filename, FileSource(source), tag_list, notes)
    if not ok:
        return {"code": 2, "status": "error", "message": msg or "update failed", "data": None}
    return {"code": 0, "status": "ok", "message": "updated", "data": info.dict()}


@router.get("/{date}/metadata", response_model=BaseResponse)
async def get_metadata(project: str, date: str) -> Dict[str, Any]:
    md = metadata_manager.load_metadata(project, date)
    if not md:
        return {"code": 3, "status": "error", "message": "metadata not found", "data": None}
    return {"code": 0, "status": "ok", "message": "", "data": md.dict()}


@router.get("/dates", response_model=BaseResponse)
async def get_project_dates(project: str) -> Dict[str, Any]:
    """获取项目下所有已有记录的日期列表（按时间倒序）"""
    dates: List[str] = project_manager.get_project_dates(project)
    return {"code": 0, "status": "ok", "message": "", "data": dates}


@router.get("/{date}/preview")
async def preview_file(
    project: str,
    date: str,
    filename: str,
) -> Response:
    """
    文件预览接口

    入参：
    - project: 项目名称（路径参数）
    - date: 日期（路径参数）
    - filename: 文件名（查询参数）
    """
    ok, msg, content, mime_type = file_manager.get_file_content_by_name(
        project, date, filename
    )
    if not ok or content is None:
        # 返回简单的文本错误信息，前端会以消息提示为主
        return Response(
          content=(msg or "file not found"),
          media_type="text/plain",
          status_code=404,
        )

    return Response(content=content, media_type=mime_type or "application/octet-stream")
