from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from server.database import get_db, SessionLocal, get_project_by_name
from server.WorkflowManager.WorkflowStorage import WorkflowStorage
from server.WorkflowManager.WorkflowEngine import workflow_engine
from server.ProjectManager.ProjectManager import ProjectManager
from server.models import BaseResponse, WorkflowGraphConfig, ProjectInfo

router = APIRouter(prefix="/project", tags=["project"])

storage = WorkflowStorage()
project_manager = ProjectManager()


@router.get("/projects", response_model=BaseResponse)
async def list_projects(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """列出所有项目，并标记当前项目"""
    projects = project_manager.list_projects(db)
    current_name = project_manager.get_current_project_name()

    # 校验当前项目是否仍然存在且为激活状态
    if current_name:
        current_proj = project_manager.get_project(db, current_name)
        if not current_proj or not current_proj.is_active:
            current_name = None

    # 如果当前项目无效且仍有其他项目，则自动选择第一个项目
    if not current_name and projects:
        current_name = projects[0].name
        project_manager.set_current_project_name(current_name)
    data = {
        "projects": [
            {
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
                "is_active": p.is_active,
                "is_current": p.name == current_name,
            }
            for p in projects
        ],
        "current_project": current_name,
    }
    return {"code": 0, "status": "ok", "message": "", "data": data}


@router.post("/projects", response_model=BaseResponse)
async def create_project(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """创建新项目"""
    name: Optional[str] = body.get("name")
    display_name: Optional[str] = body.get("display_name") or name
    description: Optional[str] = body.get("description")

    if not name:
        return {
            "code": 1,
            "status": "error",
            "message": "项目名称不能为空",
            "data": None,
        }

    ok, msg, project = project_manager.create_project(
        db,
        name=name,
        display_name=display_name or name,
        description=description,
    )
    if not ok or not project:
        return {
            "code": 2,
            "status": "error",
            "message": msg or "创建项目失败",
            "data": None,
        }

    # 如果当前还没有选择项目，则默认将新建项目设为当前项目
    if not project_manager.get_current_project_name():
        project_manager.set_current_project_name(project.name)

    info = ProjectInfo(
        name=project.name,
        display_name=project.display_name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
    return {
        "code": 0,
        "status": "ok",
        "message": "项目创建成功",
        "data": info.dict(),
    }


@router.get("/projects/current", response_model=BaseResponse)
async def get_current_project(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取当前项目详情，如果未设置则尝试使用第一个激活项目"""
    current_name = project_manager.get_current_project_name()

    if not current_name:
        # 尝试自动选择第一个激活项目
        projects = project_manager.list_projects(db)
        if projects:
            current = projects[0]
            project_manager.set_current_project_name(current.name)
            current_name = current.name
        else:
            return {
                "code": 1,
                "status": "error",
                "message": "尚未创建任何项目",
                "data": None,
            }

    project = project_manager.get_project(db, current_name)
    if not project:
        return {
            "code": 2,
            "status": "error",
            "message": "当前项目不存在，请重新选择",
            "data": None,
        }

    info = ProjectInfo(
        name=project.name,
        display_name=project.display_name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
    return {
        "code": 0,
        "status": "ok",
        "message": "",
        "data": info.dict(),
    }


@router.post("/projects/switch", response_model=BaseResponse)
async def switch_project(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """切换当前项目"""
    name: Optional[str] = body.get("name")
    if not name:
        return {
            "code": 1,
            "status": "error",
            "message": "项目名称不能为空",
            "data": None,
        }

    proj = get_project_by_name(db, name)
    if not proj:
        return {
            "code": 2,
            "status": "error",
            "message": "项目不存在",
            "data": None,
        }

    project_manager.set_current_project_name(name)

    return {
        "code": 0,
        "status": "ok",
        "message": "切换项目成功",
        "data": {"name": name},
    }


@router.delete("/projects/{name}", response_model=BaseResponse)
async def delete_project(
    name: str,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """删除项目（硬删除，删除所有数据）"""
    if not name:
        return {
            "code": 1,
            "status": "error",
            "message": "项目名称不能为空",
            "data": None,
        }

    # 检查是否是当前项目
    current_name = project_manager.get_current_project_name()
    if current_name == name:
        # 如果删除的是当前项目，需要先切换到其他项目
        projects = project_manager.list_projects(db)
        other_projects = [p for p in projects if p.name != name]
        if other_projects:
            # 切换到第一个其他项目
            project_manager.set_current_project_name(other_projects[0].name)
        else:
            # 没有其他项目，清空当前项目
            project_manager.set_current_project_name("")

    # 执行硬删除
    ok, msg = project_manager.hard_delete_project(db, name)
    if not ok:
        return {
            "code": 2,
            "status": "error",
            "message": msg or "删除项目失败",
            "data": None,
        }

    return {
        "code": 0,
        "status": "ok",
        "message": "项目删除成功",
        "data": {"name": name},
    }


@router.get("/{project}/workflow_list", response_model=BaseResponse)
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
            "created_at": w.created_at,
        }
        for w in executions
    ]
    return {"code": 0, "status": "ok", "message": "", "data": data}


@router.get("/{project}/workflow_template", response_model=BaseResponse)
async def workflow_template(project: str) -> Dict[str, Any]:
    tpl = storage.load_template()
    if not tpl:
        return {"code": 1, "status": "error", "message": "template not found", "data": None}
    return {"code": 0, "status": "ok", "message": "", "data": tpl.dict()}


@router.post("/{project}/create_workflow_from_template", response_model=BaseResponse)
async def create_workflow_from_template(project: str, body: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    date = body.get("date")
    name = body.get("name", "workflow")
    overrides = body.get("overrides", {})
    if not date:
        return {"code": 2, "status": "error", "message": "date is required", "data": None}
    ok, err, wf_id = storage.create_from_template(project, date, name, overrides)
    if not ok:
        return {"code": 3, "status": "error", "message": err or "create from template failed", "data": None}
    
    # 创建数据库记录
    proj = get_project_by_name(db, project)
    if proj:
        # 从保存的配置文件中获取llm_model和prompt_template
        config = storage.load_workflow_config(project, date, wf_id)
        llm_model = None
        prompt_template = None
        if config:
            llm_model = config.get("llm_model")
            prompt_template = config.get("prompt_template")
        
        storage.create_workflow_execution(db, proj.id, wf_id, name, llm_model, prompt_template)
    
    return {"code": 0, "status": "ok", "message": "created", "data": {"wf_id": wf_id}}


@router.post("/{project}/upload_workflow", response_model=BaseResponse)
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


@router.post("/{project}/start_workflow", response_model=BaseResponse)
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


@router.get("/{project}/workflow_status/{wf_id}", response_model=BaseResponse)
async def workflow_status(project: str, wf_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    info = workflow_engine.get_workflow_status(db, wf_id)
    if not info:
        return {"code": 5, "status": "error", "message": "workflow not found", "data": None}
    return {"code": 0, "status": "ok", "message": "", "data": info}


@router.get("/{project}/workflow_detail/{wf_id}", response_model=BaseResponse)
async def workflow_detail(project: str, wf_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    获取工作流执行详情：
    - status: 数据库中的状态信息（包含 error_message 等）
    - output: 工作流输出（包含 summary 等）
    """
    status_info = workflow_engine.get_workflow_status(db, wf_id)
    output = storage.get_workflow_output_by_wf_id(project, wf_id)

    if not status_info and not output:
        return {"code": 5, "status": "error", "message": "workflow not found", "data": None}

    data = {
        "status": status_info,
        "output": output,
    }
    return {"code": 0, "status": "ok", "message": "", "data": data}
