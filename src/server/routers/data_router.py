from fastapi import APIRouter, UploadFile, File, Form, Depends
from typing import Any, Dict
from server.DataManager.FileManager import FileManager
from server.DataManager.MetadataManager import MetadataManager
from server.models import BaseResponse, FileSource

router = APIRouter(prefix="/project/{project}/data", tags=["data"])

file_manager = FileManager()
metadata_manager = MetadataManager()


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
