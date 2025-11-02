#!/bin/bash
# 安装脚本（Linux/Mac）

# 设置 Electron 镜像
export ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/

# 清理
echo "清理旧文件..."
rm -rf node_modules package-lock.json

# 安装依赖
echo "安装依赖..."
npm install

echo "安装完成！"
