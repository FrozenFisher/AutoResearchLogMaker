@echo off
REM AutoResearchLogMaker 依赖安装脚本
REM 用于生产环境部署

echo ========================================
echo 安装 AutoResearchLogMaker 依赖
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.11
    pause
    exit /b 1
)

REM 检查 pip 是否安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 pip，请先安装 pip
    pause
    exit /b 1
)

echo [1/4] 安装核心依赖...
pip install fastapi uvicorn pydantic pydantic-settings python-multipart aiofiles sqlalchemy alembic pyyaml python-dotenv httpx pillow
if errorlevel 1 (
    echo 错误: 核心依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/4] 安装 LangChain（LLM功能）...
pip install langchain langchain-openai langgraph
if errorlevel 1 (
    echo 警告: LangChain 安装失败，LLM 功能将不可用
)

echo.
echo [3/4] 安装 PyMuPDF（PDF 解析）...
pip install pymupdf
if errorlevel 1 (
    echo 警告: PyMuPDF 安装失败，PDF 解析功能将不可用
)

echo.
echo [4/4] 验证安装...
python -c "import fastapi, uvicorn, sqlalchemy; print('✓ 核心依赖正常')" 2>nul || echo "✗ 核心依赖验证失败"
python -c "import fitz; print('✓ PyMuPDF 正常')" 2>nul || echo "✗ PyMuPDF 未安装"
python -c "from langchain_openai import ChatOpenAI; print('✓ LangChain 正常')" 2>nul || echo "✗ LangChain 未安装"

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 可选：安装 OCR 功能（体积较大，下载较慢）
echo 运行: pip install paddlepaddle paddleocr
echo.
echo 启动服务器: python run_server.py
echo.
pause
