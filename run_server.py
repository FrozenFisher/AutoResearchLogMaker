import os
import uvicorn


def get_bool(env_name: str, default: bool) -> bool:
    val = os.getenv(env_name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def main():
    try:
        from src.server.config import settings
    except Exception:
        # 兜底默认
        class _S:
            API_HOST = "0.0.0.0"
            API_PORT = 8000
        settings = _S()

    host = os.getenv("API_HOST", getattr(settings, "API_HOST", "0.0.0.0"))
    port = int(os.getenv("API_PORT", getattr(settings, "API_PORT", 8000)))
    reload_enabled = get_bool("API_RELOAD", True)

    uvicorn.run(
        "src.server.main:app",
        host=host,
        port=port,
        reload=reload_enabled,
        log_level=os.getenv("API_LOG_LEVEL", "info"),
        workers=int(os.getenv("API_WORKERS", "1")),
    )


if __name__ == "__main__":
    main()
