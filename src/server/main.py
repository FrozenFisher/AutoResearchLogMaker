import sys
from pathlib import Path

# 确保可以找到 server 模块
# 将项目根目录的 src 目录添加到路径中
_project_root = Path(__file__).parent.parent.parent
_src_dir = _project_root / "src"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.config import settings, ensure_directories
from server.database import init_database
from server.routers.tool_router import router as tool_router
from server.routers.project_router import router as project_router
from server.routers.data_router import router as data_router
from server.routers.llm_router import router as llm_router

app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tool_router)
app.include_router(project_router)
app.include_router(data_router)
app.include_router(llm_router)


@app.on_event("startup")
async def on_startup():
    ensure_directories()
    init_database()


@app.get("/health")
async def health():
    return {"status": "ok"}
