@echo off
REM 修复的服务器启动脚本（Windows）
REM 设置 PYTHONPATH 并启动服务器

echo 设置 Python 路径...
set PYTHONPATH=%CD%

echo 启动服务器...
python run_server_simple.py

pause
