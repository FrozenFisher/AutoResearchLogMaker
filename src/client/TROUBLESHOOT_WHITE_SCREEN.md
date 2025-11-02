# 白屏问题排查指南

## 问题症状

Electron 窗口打开但显示空白（白屏），没有任何内容。

## 常见原因

### 1. Vite 开发服务器未启动

**症状**: 窗口空白，开发者工具显示网络错误

**解决**:
```bash
# 确保在 src/client 目录下运行
cd src/client

# 启动 Vite 开发服务器
npm run dev
```

应该看到：
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

### 2. 端口冲突

**症状**: Vite 启动失败，提示端口被占用

**解决**:
```bash
# Windows 检查端口占用
netstat -ano | findstr :5173

# 终止占用进程（替换 PID）
taskkill /PID <PID> /F

# 或修改端口（在 vite.config.ts 中）
server: {
  port: 5174,
}
```

### 3. 依赖未安装

**症状**: 控制台显示模块未找到错误

**解决**:
```bash
cd src/client
npm install
```

### 4. 打开开发者工具查看错误

**方法**:
1. 在 Electron 窗口中按 `F12` 或 `Ctrl+Shift+I`
2. 查看 Console 标签中的错误信息
3. 查看 Network 标签确认资源是否加载成功

### 5. 检查启动顺序

正确的启动顺序：

**方法 1：使用 npm 脚本（推荐）**
```bash
cd src/client
npm run electron:dev
```
这会自动启动 Vite 和 Electron。

**方法 2：手动启动（分两个终端）**

终端 1：
```bash
cd src/client
npm run dev
```

终端 2（等待终端 1 启动完成后）：
```bash
cd src/client
electron .
```

## 调试步骤

### 步骤 1: 检查 Vite 服务器

在浏览器中访问：http://localhost:5173

如果能看到 Vue 应用，说明 Vite 正常，问题在 Electron。

### 步骤 2: 检查 Electron 控制台

在 Electron 窗口中打开开发者工具（F12），查看：
- Console 标签：是否有 JavaScript 错误
- Network 标签：资源是否加载成功
- Sources 标签：源码是否正确加载

### 步骤 3: 检查控制台输出

在启动 Electron 的终端中，查看：
- 是否有 "Vite 服务器已就绪" 消息
- 是否有错误信息

### 步骤 4: 简化测试

创建一个简单的测试页面：

```html
<!-- test.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Test</title>
</head>
<body>
    <h1>Electron 正常工作</h1>
</body>
</html>
```

修改 `main.js` 临时加载这个文件：
```javascript
mainWindow.loadFile('test.html');
```

如果能显示，说明 Electron 正常，问题在 Vue 应用。

## 快速修复

如果以上都不行，尝试：

1. **清除缓存并重新安装**:
```bash
cd src/client
rm -rf node_modules package-lock.json
npm install
```

2. **重建 Electron**:
```bash
npm run build:main
```

3. **检查 Node.js 版本**:
```bash
node --version
# 应该 >= 16.x
```

4. **使用最新版本的依赖**:
```bash
npm update
```

## 常见错误信息

### "Failed to load resource: net::ERR_CONNECTION_REFUSED"
- Vite 服务器未启动
- 运行 `npm run dev`

### "Cannot find module 'vue'"
- 依赖未安装
- 运行 `npm install`

### "Uncaught SyntaxError"
- 代码语法错误
- 查看具体错误位置并修复

### "router is not defined"
- 路由配置问题
- 检查 `router.ts` 文件

## 验证修复

修复后，应该看到：
- ✅ Electron 窗口显示完整的应用界面
- ✅ 顶部有 "AutoResearchLogMaker" 标题
- ✅ 左侧有导航菜单
- ✅ 主内容区域显示当前页面
