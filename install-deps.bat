@echo off
echo ========================================
echo 安装 AutoResearchLogMaker 依赖
echo ========================================
echo.

echo [1/3] 安装核心依赖...
pip install fastapi uvicorn pydantic pydantic-settings python-multipart aiofiles sqlalchemy alembic pyyaml python-dotenv httpx pillow
if errorlevel 1 (
    echo 核心依赖安装失败
    pause
    exit /b 1
)

echo.
echo [2/3] 安装 LangChain...
pip install langchain langchain-openai langgraph
if errorlevel 1 (
    echo LangChain 安装失败，LLM 功能将不可用
)

echo.
echo [3/3] 安装 PyMuPDF（PDF 解析）...
pip install pymupdf
if errorlevel 1 (
    echo PyMuPDF 安装失败，PDF 解析功能将不可用
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
echo 可选：安装 OCR 功能（体积较大，下载较慢）
echo 运行: pip install paddlepaddle paddleocr
echo.
pause
