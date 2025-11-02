from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Any, Dict
from datetime import datetime
from server.database import get_db, SessionLocal
from sqlalchemy.orm import Session
from server.WorkflowManager.WorkflowStorage import WorkflowStorage
from server.WorkflowManager.WorkflowEngine import workflow_engine
from server.database import get_project_by_name
from server.models import BaseResponse, WorkflowGraphConfig

router = APIRouter(prefix="/project/{project}", tags=["project"])

storage = WorkflowStorage()


@router.get("/workflow_list", response_model=BaseResponse)
async def workflow_list(project: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    proj = get_project_by_name(db, project)
    if not proj:
        return {"code": 1, "status": "error", "message": "project not found", "data": []}
    executions = storage.list_workflow_executions(db, proj.id)
    data = [
        {
            "wf_id": w.wf_id,
            "name": w.name,
            "status": w.status,
            "started_at": w.started_at,
            "finished_at": w.finished_at,
        }
        for w in executions
    ]
    return {"code": 0, "status": "ok", "message": "", "data": data}


@router.get("/workflow_template", response_model=BaseResponse)
async def workflow_template(project: str) -> Dict[str, Any]:
    tpl = storage.load_template()
    if not tpl:
        return {"code": 1, "status": "error", "message": "template not found", "data": None}
    return {"code": 0, "status": "ok", "message": "", "data": tpl.dict()}


@router.post("/create_workflow_from_template", response_model=BaseResponse)
async def create_workflow_from_template(project: str, body: Dict[str, Any]) -> Dict[str, Any]:
    date = body.get("date")
    name = body.get("name", "workflow")
    overrides = body.get("overrides", {})
    if not date:
        return {"code": 2, "status": "error", "message": "date is required", "data": None}
    ok, err, wf_id = storage.create_from_template(project, date, name, overrides)
    if not ok:
        return {"code": 3, "status": "error", "message": err or "create from template failed", "data": None}
    return {"code": 0, "status": "ok", "message": "created", "data": {"wf_id": wf_id}}


@router.post("/upload_workflow", response_model=BaseResponse)
async def upload_workflow(project: str, body: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    date = body.get("date")
    wf_id = body.get("wf_id")
    config = body.get("config") or body.get("graph") or body
    if not date or not wf_id:
        return {"code": 4, "status": "error", "message": "date and wf_id are required", "data": None}
    try:
        WorkflowGraphConfig(**config)
    except Exception as e:
        return {"code": 5, "status": "error", "message": f"schema invalid: {e}", "data": None}
    ok, err = storage.save_workflow_config(project, date, wf_id, config)
    if not ok:
        return {"code": 6, "status": "error", "message": err or "save failed", "data": None}
    proj = get_project_by_name(db, project)
    if proj:
        storage.create_workflow_execution(db, proj.id, wf_id, config.get("name", wf_id), config.get("llm_model"), config.get("prompt_template"))
    return {"code": 0, "status": "ok", "message": "uploaded", "data": {"wf_id": wf_id}}


@router.post("/start_workflow", response_model=BaseResponse)
async def start_workflow(project: str, body: Dict[str, Any], background: BackgroundTasks, db: Session = Depends(get_db)) -> Dict[str, Any]:
    wf_id = body.get("wf_id")
    date = body.get("date")
    files = body.get("files", [])
    custom_prompt = body.get("custom_prompt")
    if not wf_id or not date:
        return {"code": 4, "status": "error", "message": "wf_id and date are required", "data": None}

    def _run():
        from server.database import SessionLocal
        with SessionLocal() as s:
            import asyncio
            asyncio.run(workflow_engine.execute_workflow(s, project, date, wf_id, files, custom_prompt))

    background.add_task(_run)
    return {"code": 0, "status": "ok", "message": "started", "data": {"wf_id": wf_id, "date": date}}


@router.get("/workflow_status/{wf_id}", response_model=BaseResponse)
async def workflow_status(project: str, wf_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    info = workflow_engine.get_workflow_status(db, wf_id)
    if not info:
        return {"code": 5, "status": "error", "message": "workflow not found", "data": None}
    return {"code": 0, "status": "ok", "message": "", "data": info}
