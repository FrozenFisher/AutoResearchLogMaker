import os
import sys
from pathlib import Path
import uvicorn


def get_bool(env_name: str, default: bool) -> bool:
    val = os.getenv(env_name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def main():
    # 添加项目根目录到 Python 路径
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    try:
        from src.server.config import settings
    except Exception as e:
        # 兜底默认
        print(f"警告: 无法加载配置 ({e})，使用默认配置")
        class _S:
            API_HOST = "0.0.0.0"
            API_PORT = 8000
        settings = _S()

    host = os.getenv("API_HOST", getattr(settings, "API_HOST", "0.0.0.0"))
    port = int(os.getenv("API_PORT", getattr(settings, "API_PORT", 8000)))
    
    # Windows 下的 reload 模式有兼容性问题，建议禁用
    # 如果需要热重载，可以设置为 True，但需要确保 PYTHONPATH 正确
    is_windows = os.name == 'nt'
    reload_enabled = get_bool("API_RELOAD", not is_windows)
    
    if reload_enabled and is_windows:
        print("警告: Windows 下 reload 模式可能有问题，建议禁用 (设置 API_RELOAD=0)")

    # 设置环境变量确保子进程能找到模块
    os.environ["PYTHONPATH"] = str(project_root)
    
    # 如果在 Windows 下使用 reload，需要直接导入 app 而不是字符串
    if reload_enabled and is_windows:
        # Windows 下使用直接导入方式避免模块查找问题
        from src.server.main import app
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload_enabled,
            reload_dirs=[str(project_root / "src")],
            log_level=os.getenv("API_LOG_LEVEL", "info"),
            workers=1,  # Windows 下只使用单 worker
        )
    else:
        # Linux/Mac 或禁用 reload 时使用字符串方式
        uvicorn.run(
            "src.server.main:app",
            host=host,
            port=port,
            reload=reload_enabled,
            log_level=os.getenv("API_LOG_LEVEL", "info"),
            workers=int(os.getenv("API_WORKERS", "1")),
            env_file=".env" if Path(".env").exists() else None,
        )


if __name__ == "__main__":
    main()
