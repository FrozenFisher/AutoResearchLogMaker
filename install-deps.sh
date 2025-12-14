#!/bin/bash
# AutoResearchLogMaker 依赖安装脚本
# 用于生产环境部署

set -e  # 遇到错误立即退出

echo "========================================"
echo "安装 AutoResearchLogMaker 依赖"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python 3.11"
    exit 1
fi

# 检查 pip 是否安装
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "错误: 未找到 pip，请先安装 pip"
    exit 1
fi

# 确定使用的命令
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python)
PIP_CMD=$(command -v pip3 2>/dev/null || command -v pip)

echo "[1/4] 安装核心依赖..."
$PIP_CMD install fastapi uvicorn pydantic pydantic-settings python-multipart aiofiles sqlalchemy alembic pyyaml python-dotenv httpx pillow
if [ $? -ne 0 ]; then
    echo "错误: 核心依赖安装失败"
    exit 1
fi

echo ""
echo "[2/4] 安装 LangChain（LLM功能）..."
$PIP_CMD install langchain langchain-openai langgraph || echo "警告: LangChain 安装失败，LLM 功能将不可用"

echo ""
echo "[3/4] 安装 PyMuPDF（PDF 解析）..."
$PIP_CMD install pymupdf || echo "警告: PyMuPDF 安装失败，PDF 解析功能将不可用"

echo ""
echo "[4/4] 验证安装..."
$PYTHON_CMD -c "import fastapi, uvicorn, sqlalchemy; print('✓ 核心依赖正常')" 2>/dev/null || echo "✗ 核心依赖验证失败"
$PYTHON_CMD -c "import fitz; print('✓ PyMuPDF 正常')" 2>/dev/null || echo "✗ PyMuPDF 未安装"
$PYTHON_CMD -c "from langchain_openai import ChatOpenAI; print('✓ LangChain 正常')" 2>/dev/null || echo "✗ LangChain 未安装"

echo ""
echo "========================================"
echo "安装完成！"
echo "========================================"
echo ""
echo "可选：安装 OCR 功能（体积较大，下载较慢）"
echo "运行: $PIP_CMD install paddlepaddle paddleocr"
echo ""
echo "启动服务器: $PYTHON_CMD run_server.py"
echo ""
