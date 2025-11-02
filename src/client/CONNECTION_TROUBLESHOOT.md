# 服务器连接问题排查指南

## 快速检查

### 1. 检查服务器是否运行

在项目根目录运行：

```bash
# 启动服务器
python run_server.py
```

应该看到类似输出：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. 测试服务器连接

在浏览器中访问：http://localhost:8000/health

应该看到：
```json
{"status":"ok"}
```

或者在客户端目录运行检查脚本：

```bash
# 使用 Node.js 检查
node check-server.js

# 或使用 curl
curl http://localhost:8000/health
```

## 常见问题及解决方案

### 问题 1: 服务器未启动

**症状**: 客户端显示"无法连接到服务器"

**解决**:
1. 打开终端，进入项目根目录
2. 运行: `python run_server.py`
3. 确保看到服务器启动信息
4. 保持这个终端窗口打开

### 问题 2: 端口冲突

**症状**: 服务器启动失败，提示端口被占用

**解决**:
```bash
# Windows 检查端口占用
netstat -ano | findstr :8000

# 停止占用端口的进程（替换 PID）
taskkill /PID <PID> /F

# 或修改服务器端口（在 .env 文件中）
API_PORT=8001
```

然后更新客户端的 `.env` 文件：
```env
VITE_API_BASE=http://localhost:8001
```

### 问题 3: 防火墙阻止

**症状**: 服务器已启动，但客户端无法连接

**解决**:
- Windows: 在防火墙设置中允许 Python 和 Node.js 通过防火墙
- 或者临时禁用防火墙测试

### 问题 4: API_BASE 配置错误

**症状**: 连接错误的地址

**解决**:
检查 `src/client/.env` 文件：
```env
VITE_API_BASE=http://localhost:8000
```

确保：
- 协议正确（http 或 https）
- 主机名正确（localhost 或实际 IP）
- 端口号匹配服务器配置（默认 8000）

### 问题 5: CORS 错误（浏览器控制台）

**症状**: 浏览器控制台显示 CORS 相关错误

**解决**:
服务器已配置 CORS 中间件，允许所有来源。如果仍有问题，检查：
- 服务器 `src/server/main.py` 中的 CORS 配置
- 确保 `allow_origins=["*"]` 存在

### 问题 6: 网络超时

**症状**: 请求超时

**解决**:
1. 检查网络连接
2. 检查服务器响应速度
3. 增加客户端超时时间（在 `src/client/src/api/index.ts` 中修改 timeout）

## 诊断步骤

### 步骤 1: 确认服务器运行

```bash
# 检查进程
# Windows PowerShell
Get-Process python | Where-Object {$_.CommandLine -like "*run_server*"}

# Linux/Mac
ps aux | grep run_server
```

### 步骤 2: 测试端口连通性

```bash
# Windows
Test-NetConnection localhost -Port 8000

# Linux/Mac
nc -zv localhost 8000

# 或使用 telnet
telnet localhost 8000
```

### 步骤 3: 检查服务器日志

查看服务器终端输出，确认：
- 服务器已启动
- 没有错误信息
- 能够处理请求

### 步骤 4: 检查客户端配置

1. 打开浏览器开发者工具（F12）
2. 查看 Network 标签
3. 查看 Console 标签中的错误信息
4. 检查请求 URL 是否正确

## 开发环境建议

### 同时启动服务器和客户端

创建启动脚本 `start-all.bat`（Windows）或 `start-all.sh`（Linux/Mac）：

**Windows (start-all.bat)**:
```batch
@echo off
echo 启动服务器...
start cmd /k "cd /d %~dp0 && python run_server.py"
timeout /t 3
echo 启动客户端...
cd src\client
npm run electron:dev
```

**Linux/Mac (start-all.sh)**:
```bash
#!/bin/bash
echo "启动服务器..."
python run_server.py &
sleep 3
echo "启动客户端..."
cd src/client
npm run electron:dev
```

## 检查清单

- [ ] 服务器进程正在运行
- [ ] 端口 8000 可以访问
- [ ] 浏览器可以访问 http://localhost:8000/health
- [ ] `.env` 文件配置正确
- [ ] 防火墙未阻止连接
- [ ] 没有端口冲突
- [ ] 网络连接正常

## 获取帮助

如果以上方法都无法解决问题，请提供：
1. 服务器启动日志
2. 客户端错误信息（浏览器控制台）
3. 操作系统版本
4. Python 和 Node.js 版本
