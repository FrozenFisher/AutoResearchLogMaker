"""配置管理模块"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础路径配置
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    LIB_DIR: Path = BASE_DIR / "lib"
    SERVER_DIR: Path = LIB_DIR / "server"
    STATIC_DIR: Path = SERVER_DIR / "static"
    USRDATA_DIR: Path = SERVER_DIR / "usrdata"
    TOOLS_DIR: Path = USRDATA_DIR / "tools"
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./lib/server/database.db"
    
    # API配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_TITLE: str = "AutoResearchLogMaker API"
    API_VERSION: str = "0.1.0"
    
    # LLM配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    DEFAULT_LLM_MODEL: str = "gpt-3.5-turbo"
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: list[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/bmp",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # OCR配置
    OCR_LANGUAGE: str = "ch"  # 中文
    OCR_USE_GPU: bool = False
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def get_project_path(project_name: str) -> Path:
    """获取项目根路径"""
    return settings.USRDATA_DIR / project_name


def get_project_files_path(project_name: str, date: str) -> Path:
    """获取项目文件路径"""
    return get_project_path(project_name) / "files" / date


def get_project_data_path(project_name: str, date: str) -> Path:
    """获取项目数据路径"""
    return get_project_path(project_name) / "data" / date


def get_project_settings_path(project_name: str) -> Path:
    """获取项目设置文件路径"""
    return get_project_path(project_name) / "settings.yaml"


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        settings.STATIC_DIR,
        settings.USRDATA_DIR,
        settings.TOOLS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
