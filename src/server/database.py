"""数据库连接和模型定义"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.sql import func
from server.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


class Project(Base):
    """项目表"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # 关系
    workflows = relationship("Workflow", back_populates="project")


class Workflow(Base):
    """工作流表"""
    __tablename__ = "workflows"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    wf_id = Column(String(50), unique=True, index=True, nullable=False)  # 如: wf_20251012_170200
    name = Column(String(200), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, success, failed
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    llm_model = Column(String(100))
    prompt_template = Column(String(100))
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关系
    project = relationship("Project", back_populates="workflows")


class FileRecord(Base):
    """文件记录表（用于快速索引）"""
    __tablename__ = "file_records"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_id = Column(String(50), index=True, nullable=False)  # 如: f_ab12
    filename = Column(String(500), nullable=False)
    stored_path = Column(String(1000), nullable=False)
    original_name = Column(String(500))
    crc32 = Column(String(8))
    mime_type = Column(String(100))
    size_bytes = Column(Integer)
    uploaded_at = Column(DateTime, default=func.now())
    source = Column(String(50))  # manual_upload, clipboard, screenshot, crawler
    tags = Column(Text)  # JSON字符串
    language = Column(String(10))
    status_ocr = Column(String(20), default="pending")  # pending, done, failed
    status_parsed = Column(String(20), default="pending")  # pending, done, failed
    embedding_id = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    retired_at = Column(DateTime)
    
    # 关系
    project = relationship("Project")


def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)


def get_project_by_name(db: Session, project_name: str) -> Optional[Project]:
    """根据项目名获取项目"""
    return db.query(Project).filter(Project.name == project_name, Project.is_active == True).first()


def create_project(db: Session, name: str, display_name: str, description: str = None) -> Project:
    """创建新项目"""
    project = Project(
        name=name,
        display_name=display_name,
        description=description
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def get_workflow_by_wf_id(db: Session, wf_id: str) -> Optional[Workflow]:
    """根据工作流ID获取工作流"""
    return db.query(Workflow).filter(Workflow.wf_id == wf_id).first()


def create_workflow(
    db: Session, 
    project_id: int, 
    wf_id: str, 
    name: str,
    llm_model: str = None,
    prompt_template: str = None
) -> Workflow:
    """创建新工作流"""
    workflow = Workflow(
        project_id=project_id,
        wf_id=wf_id,
        name=name,
        llm_model=llm_model,
        prompt_template=prompt_template
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return workflow


def update_workflow_status(
    db: Session, 
    wf_id: str, 
    status: str, 
    error_message: str = None
) -> Optional[Workflow]:
    """更新工作流状态"""
    workflow = get_workflow_by_wf_id(db, wf_id)
    if workflow:
        workflow.status = status
        if status == "running":
            workflow.started_at = datetime.now()
        elif status in ["success", "failed"]:
            workflow.finished_at = datetime.now()
        if error_message:
            workflow.error_message = error_message
        db.commit()
        db.refresh(workflow)
    return workflow


def get_project_files(db: Session, project_id: int, date: str = None) -> List[FileRecord]:
    """获取项目文件列表"""
    query = db.query(FileRecord).filter(
        FileRecord.project_id == project_id,
        FileRecord.is_active == True
    )
    if date:
        query = query.filter(FileRecord.uploaded_at.like(f"{date}%"))
    return query.all()


def create_file_record(
    db: Session,
    project_id: int,
    file_id: str,
    filename: str,
    stored_path: str,
    original_name: str = None,
    crc32: str = None,
    mime_type: str = None,
    size_bytes: int = None,
    source: str = "manual_upload",
    tags: List[str] = None,
    language: str = None,
    notes: str = None
) -> FileRecord:
    """创建文件记录"""
    import json
    
    file_record = FileRecord(
        project_id=project_id,
        file_id=file_id,
        filename=filename,
        stored_path=stored_path,
        original_name=original_name,
        crc32=crc32,
        mime_type=mime_type,
        size_bytes=size_bytes,
        source=source,
        tags=json.dumps(tags) if tags else None,
        language=language,
        notes=notes
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)
    return file_record


def retire_file_record(db: Session, file_id: str) -> Optional[FileRecord]:
    """标记文件记录为已废弃"""
    file_record = db.query(FileRecord).filter(FileRecord.file_id == file_id).first()
    if file_record:
        file_record.is_active = False
        file_record.retired_at = datetime.now()
        db.commit()
        db.refresh(file_record)
    return file_record
