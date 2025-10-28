from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.config import settings, ensure_directories
from server.database import init_database
from server.routers.tool_router import router as tool_router
from server.routers.project_router import router as project_router
from server.routers.data_router import router as data_router

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


@app.on_event("startup")
async def on_startup():
    ensure_directories()
    init_database()


@app.get("/health")
async def health():
    return {"status": "ok"}
