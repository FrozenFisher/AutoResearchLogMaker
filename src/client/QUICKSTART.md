# 快速开始

## 1. 安装依赖

```bash
cd src/client
npm install
```

## 2. 配置环境变量

复制 `.env.example` 为 `.env`（可选，默认使用 `http://localhost:8000`）：

```bash
cp .env.example .env
```

## 3. 启动服务器

确保服务器已启动（在项目根目录）：

```bash
python run_server.py
```

## 4. 启动客户端

### 开发模式

```bash
npm run electron:dev
```

这将同时启动：
- Vite 开发服务器（http://localhost:5173）
- Electron 应用窗口

### 仅前端开发

```bash
npm run dev
```

然后在浏览器访问 http://localhost:5173

## 5. 构建生产版本

```bash
# 构建
npm run build

# 打包为可执行文件
npm run dist
```

## 功能说明

### 已实现功能

- ✅ 文件管理：按日期上传和管理文件
- ✅ 工作流管理：创建、启动和监控工作流
- ✅ 工具配置：查看和配置工具
- ✅ 结果查看：查看研究总结

### 注意事项

1. **项目名称**：默认使用 `default_project`，可在 `src/stores/project.ts` 中修改
2. **服务器地址**：默认 `http://localhost:8000`，可在 `.env` 文件中配置
3. **文件上传**：支持 PDF、图片、Excel 文件，单个文件不超过 50MB

## 故障排查

### 无法连接到服务器

- 确保服务器已启动（运行 `python run_server.py`）
- 检查服务器端口是否为 8000
- 检查 `.env` 文件中的 `VITE_API_BASE` 配置

### Electron 窗口无法打开

- 检查是否已安装所有依赖：`npm install`
- 查看控制台错误信息
- 确保端口 5173 未被占用
