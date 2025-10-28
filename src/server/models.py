"""Pydantic数据模型定义"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


class WorkflowStatus(str, Enum):
    """工作流状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class FileSource(str, Enum):
    """文件来源枚举"""
    MANUAL_UPLOAD = "manual_upload"
    CLIPBOARD = "clipboard"
    SCREENSHOT = "screenshot"
    CRAWLER = "crawler"


class FileStatus(str, Enum):
    """文件处理状态枚举"""
    PENDING = "pending"
    DONE = "done"
    FAILED = "failed"


# 基础响应模型
class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = Field(default=0, description="状态码，0表示成功")
    status: str = Field(default="ok", description="状态描述")
    message: str = Field(default="", description="消息")
    data: Optional[Any] = Field(default=None, description="数据")


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    code: int = Field(default=1, description="错误码")
    status: str = Field(default="error", description="错误状态")


# 文件相关模型
class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str = Field(description="文件ID")
    filename: str = Field(description="文件名")
    stored_path: str = Field(description="存储路径")
    original_name: Optional[str] = Field(default=None, description="原始文件名")
    crc32: Optional[str] = Field(default=None, description="CRC32校验码")
    mime: Optional[str] = Field(default=None, description="MIME类型")
    size_bytes: Optional[int] = Field(default=None, description="文件大小（字节）")
    uploaded_at: datetime = Field(description="上传时间")
    source: FileSource = Field(default=FileSource.MANUAL_UPLOAD, description="文件来源")
    tags: List[str] = Field(default_factory=list, description="标签")
    language: Optional[str] = Field(default=None, description="语言")
    status: Dict[str, str] = Field(default_factory=dict, description="处理状态")
    notes: Optional[str] = Field(default=None, description="备注")


class AuthorInfo(BaseModel):
    """作者信息模型"""
    user_id: str = Field(description="用户ID")
    display_name: str = Field(description="显示名称")


class WorkflowInfo(BaseModel):
    """工作流信息模型"""
    wf_id: str = Field(description="工作流ID")
    name: str = Field(description="工作流名称")
    started_at: Optional[datetime] = Field(default=None, description="开始时间")
    finished_at: Optional[datetime] = Field(default=None, description="结束时间")
    status: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="状态")
    outputs: List[str] = Field(default_factory=list, description="输出文件路径")
    llm_model: Optional[str] = Field(default=None, description="LLM模型")
    prompt_template: Optional[str] = Field(default=None, description="提示模板")


class SummaryInfo(BaseModel):
    """总结信息模型"""
    auto_summary: Optional[str] = Field(default=None, description="自动总结文件路径")
    user_notes: Optional[str] = Field(default=None, description="用户备注")


class GitInfo(BaseModel):
    """Git信息模型"""
    commit_hash: Optional[str] = Field(default=None, description="提交哈希")
    repo: Optional[str] = Field(default=None, description="仓库地址")


class Permissions(BaseModel):
    """权限信息模型"""
    read: List[str] = Field(default_factory=list, description="读取权限")
    write: List[str] = Field(default_factory=list, description="写入权限")


class RecordMetadata(BaseModel):
    """记录元数据模型"""
    record_id: str = Field(description="记录ID")
    project: str = Field(description="项目名称")
    date: str = Field(description="日期")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")
    author: AuthorInfo = Field(description="作者信息")
    files: List[FileInfo] = Field(default_factory=list, description="文件列表")
    summary: SummaryInfo = Field(default_factory=SummaryInfo, description="总结信息")
    workflows: List[WorkflowInfo] = Field(default_factory=list, description="工作流列表")
    tags: List[str] = Field(default_factory=list, description="标签")
    related_git: Optional[GitInfo] = Field(default=None, description="Git信息")
    permissions: Permissions = Field(default_factory=Permissions, description="权限")
    notes_general: Optional[str] = Field(default=None, description="通用备注")


# 项目相关模型
class ProjectInfo(BaseModel):
    """项目信息模型"""
    name: str = Field(description="项目名称")
    display_name: str = Field(description="显示名称")
    description: Optional[str] = Field(default=None, description="描述")
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class ProjectSettings(BaseModel):
    """项目设置模型"""
    default_prompt: str = Field(description="默认提示模板")
    project_name: str = Field(description="项目名称")
    required_tools: Dict[str, Any] = Field(description="必需工具配置")


# 工具相关模型
class ToolConfig(BaseModel):
    """工具配置模型"""
    name: str = Field(description="工具名称")
    description: str = Field(description="工具描述")
    type: str = Field(description="工具类型")
    config: Dict[str, Any] = Field(description="工具配置")
    enabled: bool = Field(default=True, description="是否启用")


class ToolListResponse(BaseResponse):
    """工具列表响应模型"""
    data: List[ToolConfig] = Field(description="工具列表")


class ToolResponse(BaseResponse):
    """工具响应模型"""
    data: ToolConfig = Field(description="工具配置")


# 工作流图配置 Schema
class WorkflowNode(BaseModel):
    id: str
    type: str  # tool | llm | branch | merge | start | end
    name: Optional[str] = None
    tool_name: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    input_map: Dict[str, str] = Field(default_factory=dict)  # from context keys
    output_key: str = Field(default="result")


class WorkflowEdge(BaseModel):
    source: str
    target: str
    condition: Optional[str] = None  # e.g. "result.success == true"


class WorkflowGraphConfig(BaseModel):
    name: str
    llm_model: Optional[str] = None
    prompt_template: Optional[str] = None
    nodes: List[WorkflowNode]
    edges: List[WorkflowEdge]

    @validator("nodes")
    def unique_node_ids(cls, v):
        ids = [n.id for n in v]
        if len(ids) != len(set(ids)):
            raise ValueError("节点ID必须唯一")
        return v

    @validator("edges")
    def edge_refs_exist(cls, v, values):
        node_ids = set(n.id for n in values.get("nodes", []))
        for e in v:
            if e.source not in node_ids or e.target not in node_ids:
                raise ValueError(f"边引用了不存在的节点: {e.source}->{e.target}")
        return v


class WorkflowConfigUpload(BaseModel):
    name: str
    graph: WorkflowGraphConfig


class WorkflowTemplateResponse(BaseModel):
    template: WorkflowGraphConfig


class WorkflowListResponse(BaseResponse):
    data: List[WorkflowInfo] = Field(description="工作流列表")


class WorkflowStatusResponse(BaseResponse):
    data: WorkflowInfo = Field(description="工作流信息")


class StartWorkflowRequest(BaseModel):
    workflow_name: str = Field(description="工作流名称")
    files: List[str] = Field(default_factory=list, description="文件列表")
    custom_prompt: Optional[str] = Field(default=None, description="自定义提示")


class StartWorkflowResponse(BaseResponse):
    data: str = Field(description="工作流ID")


# 文件上传相关模型
class FileUploadRequest(BaseModel):
    filename: str = Field(description="文件名")
    source: FileSource = Field(default=FileSource.MANUAL_UPLOAD, description="文件来源")
    tags: List[str] = Field(default_factory=list, description="标签")
    notes: Optional[str] = Field(default=None, description="备注")


class FileUploadResponse(BaseResponse):
    data: str = Field(description="文件路径")


class FileUpdateRequest(BaseModel):
    filename: str = Field(description="文件名")
    source: FileSource = Field(default=FileSource.MANUAL_UPLOAD, description="文件来源")
    tags: List[str] = Field(default_factory=list, description="标签")
    notes: Optional[str] = Field(default=None, description="备注")
    replace_existing: bool = Field(default=False, description="是否替换现有文件")


class MetadataResponse(BaseResponse):
    data: RecordMetadata = Field(description="记录元数据")


# 验证器
@validator('date')
def validate_date(cls, v):
    """验证日期格式"""
    try:
        datetime.strptime(v, '%Y-%m-%d')
        return v
    except ValueError:
        raise ValueError('日期格式必须为 YYYY-MM-DD')


@validator('record_id')
def validate_record_id(cls, v):
    """验证记录ID格式"""
    if not v or len(v) < 10:
        raise ValueError('记录ID不能为空且长度至少10位')
    return v
