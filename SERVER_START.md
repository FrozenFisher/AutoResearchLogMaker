# 服务器启动指南

## 问题说明

Windows 下使用 uvicorn 的 reload 模式时，多进程会导致模块导入路径问题。

## 解决方案

### 方案 1：使用简化启动脚本（推荐）

```bash
# Windows
python run_server_simple.py

# 或使用批处理文件
run_server_fixed.bat
```

这个脚本：
- ✅ 自动设置 PYTHONPATH
- ✅ 禁用 reload 模式（避免多进程问题）
- ✅ 直接导入 app 对象

### 方案 2：禁用 reload 模式

设置环境变量后使用原脚本：

```bash
# Windows PowerShell
$env:API_RELOAD="0"
python run_server.py

# Windows CMD
set API_RELOAD=0
python run_server.py
```

### 方案 3：修复后的原脚本（自动检测）

`run_server.py` 已更新，会自动：
- 在 Windows 下默认禁用 reload
- 设置正确的 PYTHONPATH
- 如果启用 reload，会使用直接导入方式

## 验证服务器运行

服务器启动后，访问：
- http://localhost:8000/health

应该返回：
```json
{"status":"ok"}
```

## 故障排查

### 错误: ModuleNotFoundError: No module named 'server'

**原因**: Python 无法找到 `server` 模块

**解决**:
1. 确保在项目根目录运行脚本
2. 使用 `run_server_simple.py`（自动设置路径）
3. 或手动设置 PYTHONPATH：
   ```bash
   # Windows
   set PYTHONPATH=%CD%
   python run_server.py
   
   # Linux/Mac
   export PYTHONPATH=$PWD
   python run_server.py
   ```

### 错误: 多进程相关错误（Windows）

**原因**: Windows 下的 multiprocessing 和 uvicorn reload 不兼容

**解决**: 禁用 reload 模式（方案 1 或 2）

### 错误: 端口已被占用

**解决**:
```bash
# Windows 查找占用端口的进程
netstat -ano | findstr :8000

# 终止进程（替换 PID）
taskkill /PID <PID> /F

# 或修改端口
set API_PORT=8001
python run_server_simple.py
```

## 开发模式建议

### 开发时（需要热重载）

如果确实需要热重载，可以：
1. 使用 Linux/Mac（reload 模式正常工作）
2. 或在 Windows 下手动重启服务器（不使用 reload）

### 生产环境

生产环境不应使用 reload 模式，应该：
```bash
# 禁用 reload
set API_RELOAD=0
python run_server.py
```
