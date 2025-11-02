@echo off
REM 安装脚本（Windows）

REM 设置 Electron 镜像
set ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/

REM 清理
echo 清理旧文件...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del /f package-lock.json

REM 安装依赖
echo 安装依赖...
npm install

echo 安装完成！
pause
