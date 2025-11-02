"""
简化的服务器启动脚本（推荐用于 Windows）
禁用 reload 模式以避免多进程问题
"""
import os
import sys
from pathlib import Path

# 确保项目根目录和 src 目录都在 Python 路径中
project_root = Path(__file__).parent.absolute()
src_dir = project_root / "src"

# 添加到 sys.path
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置环境变量
os.environ["PYTHONPATH"] = os.pathsep.join([str(src_dir), str(project_root)])

# 现在可以安全导入（使用 server 前缀，因为 src 已在路径中）
from server.main import app
import uvicorn

if __name__ == "__main__":
    # 获取配置
    try:
        from server.config import settings
        host = os.getenv("API_HOST", settings.API_HOST)
        port = int(os.getenv("API_PORT", settings.API_PORT))
    except Exception as e:
        print(f"警告: 无法加载配置 ({e})，使用默认配置")
        host = "0.0.0.0"
        port = 8000
    
    print(f"启动服务器: http://{host}:{port}")
    print("按 CTRL+C 停止服务器")
    
    # 禁用 reload 模式以避免 Windows 下的多进程问题
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,  # Windows 下禁用 reload
        log_level="info",
    )
