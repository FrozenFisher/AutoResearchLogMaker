#!/bin/bash
# 启动开发环境（服务器 + 客户端）

echo "========================================"
echo "启动 AutoResearchLogMaker 开发环境"
echo "========================================"
echo ""

echo "[1/3] 检查 Python 环境..."
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python，请先安装 Python"
    exit 1
fi
python --version

echo "[2/3] 启动服务器..."
echo "服务器将在 http://localhost:8000 启动"
python run_server.py &
SERVER_PID=$!

echo "等待服务器启动..."
sleep 5

echo "[3/3] 检查服务器连接..."
cd src/client
node check-server.js
if [ $? -ne 0 ]; then
    echo ""
    echo "警告: 无法连接到服务器"
    echo "请检查服务器是否正常启动"
    echo ""
fi

echo ""
echo "[4/4] 启动客户端..."
npm run electron:dev

# 清理：客户端退出时停止服务器
trap "kill $SERVER_PID" EXIT
