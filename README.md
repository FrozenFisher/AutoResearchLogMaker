# AutoResearchLogMaker

自动化研究日志生成工具，支持AI驱动的文件解析和总结功能。

## 功能特性

- 📄 **多格式文件支持**：PDF、图片、Excel、文本文件
- 🤖 **AI驱动总结**：基于LangChain和LangGraph的智能工作流
- 📊 **项目管理**：按日期组织研究文件和日志
- 🔧 **工具系统**：支持PDF解析、OCR、Excel读取、MCP外部工具
- 🔄 **版本控制**：文件更新历史追踪
- 🎨 **图形界面**：Electron + Vue 3 客户端

## 技术栈

### 后端
- **FastAPI**: Web框架和RESTful API
- **LangChain + LangGraph**: LLM工作流编排
- **PyMuPDF**: PDF解析
- **PaddleOCR**: 图片OCR（可选）
- **SQLite**: 项目和workflow状态存储
- **JSON/YAML**: 用户可读的数据文件

### 前端
- **Electron**: 桌面应用框架
- **Vue 3**: 前端框架
- **TypeScript**: 类型安全
- **Element Plus**: UI组件库

## 快速开始

### 环境要求

- Python >= 3.11, < 3.12
- Node.js >= 18.0.0（用于客户端）
- pip 或 PDM（Python包管理器）

### 安装依赖

#### 方法 1：使用安装脚本（推荐）

**Windows:**
```bash
install-deps.bat
```

**Linux/macOS:**
```bash
chmod +x install-deps.sh
./install-deps.sh
```

#### 方法 2：使用 PDM

```bash
pdm install
```

#### 方法 3：手动安装

```bash
# 核心依赖
pip install fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy alembic \
    pyyaml python-dotenv httpx pillow

# LangChain（LLM功能）
pip install langchain langchain-openai langgraph

# PDF解析
pip install pymupdf

# OCR功能（可选，体积较大）
pip install paddlepaddle paddleocr
```

#### 使用国内镜像（如果下载慢）

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy alembic \
    langchain langchain-openai langgraph \
    pymupdf pillow pyyaml python-dotenv httpx
```

### 启动服务器

#### 方法 1：使用启动脚本

```bash
python run_server.py
```

#### 方法 2：使用 PDM

```bash
pdm run server
```

#### 方法 3：直接使用 uvicorn

```bash
uvicorn src.server.main:app --host 0.0.0.0 --port 8000
```

服务器启动后，访问 http://localhost:8000/health 验证运行状态。

### 启动客户端

#### 开发模式

**Windows:**
```bash
start-dev.bat
```

**Linux/macOS:**
```bash
chmod +x start-dev.sh
./start-dev.sh
```

#### 手动启动

```bash
cd src/client
npm install
npm run electron:dev
```

## 项目结构

```
AutoResearchLogMaker/
├── src/
│   ├── server/              # 后端服务
│   │   ├── main.py          # FastAPI应用入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # SQLite数据库
│   │   ├── models.py        # Pydantic数据模型
│   │   ├── DataManager/     # 数据管理模块
│   │   ├── ProjectManager/  # 项目管理模块
│   │   ├── ToolManager/     # 工具管理模块
│   │   ├── WorkflowManager/ # 工作流管理模块
│   │   ├── LLMManager/      # LLM管理模块
│   │   └── routers/         # API路由
│   └── client/              # 前端客户端
│       ├── electron/        # Electron主进程
│       └── src/             # Vue应用
├── lib/
│   └── server/
│       ├── static/          # 静态模板文件
│       └── usrdata/         # 用户数据目录
├── docs/                    # 文档目录
│   └── archive/             # 历史开发文档
├── install-deps.bat        # Windows安装脚本
├── install-deps.sh         # Linux/macOS安装脚本
├── run_server.py           # 服务器启动脚本
├── start-dev.bat           # Windows开发环境启动
├── start-dev.sh            # Linux/macOS开发环境启动
└── pyproject.toml          # 项目配置和依赖
```

## 配置说明

### 环境变量

创建 `.env` 文件（可选）：

```env
# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=0  # Windows下建议设为0

# LLM配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，用于自定义API端点

# 日志级别
API_LOG_LEVEL=info
```

### 项目设置

项目设置文件位于 `lib/server/usrdata/{project_name}/settings.yaml`：

```yaml
project_name: "my_research_project"
default_prompt: "### 默认Prompt模板"
required_tools:
  default_tools:
    - pdf_parser
    - image_reader
  user_tools: []
```

## API接口

### 健康检查
- `GET /health` - 检查服务状态

### 工具管理
- `GET /tool/tool_list` - 获取所有工具列表
- `GET /tool/{user_tool}` - 获取指定工具配置
- `POST /tool/{user_tool}/add` - 添加新工具
- `POST /tool/{user_tool}/edit` - 编辑工具配置

### 项目管理
- `GET /project/{project}/workflow_template` - 获取工作流模板
- `POST /project/{project}/create_workflow_from_template` - 从模板创建工作流
- `POST /project/{project}/upload_workflow` - 上传工作流配置
- `POST /project/{project}/start_workflow` - 启动工作流
- `GET /project/{project}/workflow_status/{wf_id}` - 查询工作流状态

### 数据管理
- `POST /project/{project}/data/{date}/upload_files` - 上传文件
- `POST /project/{project}/data/{date}/update_files` - 更新文件
- `GET /project/{project}/data/{date}/metadata` - 获取元数据

## 常见问题

### 安装问题

**Q: PyMuPDF 安装失败**
```bash
pip install --upgrade pip
pip install pymupdf
```

**Q: LangChain 版本冲突**
```bash
pip install langchain==0.1.0 langchain-openai==0.0.2 langgraph==0.0.20
```

**Q: 安装卡在 "Preparing metadata"**
```bash
# 使用镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install --no-build-isolation pymupdf langchain langchain-openai langgraph
```

### 启动问题

**Q: ModuleNotFoundError: No module named 'server'**
- 确保在项目根目录运行脚本
- 检查 PYTHONPATH 是否正确设置

**Q: Windows 下 reload 模式问题**
- 设置环境变量 `API_RELOAD=0`
- 或使用 `run_server.py`（已自动处理）

**Q: 端口已被占用**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/macOS
lsof -ti:8000 | xargs kill
```

### 功能问题

**Q: OCR 功能不可用**
- OCR功能是可选的，需要安装 `paddlepaddle` 和 `paddleocr`
- 如果不需要OCR，可以跳过安装

**Q: LLM 功能不可用**
- 检查是否安装了 `langchain`、`langchain-openai`、`langgraph`
- 检查 `OPENAI_API_KEY` 环境变量是否设置

## 开发指南

### 最小安装（仅核心功能）

如果只需要基本功能，可以只安装：

```bash
pip install fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy \
    langchain langchain-openai langgraph \
    pymupdf pillow pyyaml python-dotenv httpx
```

跳过：
- `alembic`（数据库迁移，可选）
- `paddlepaddle` 和 `paddleocr`（OCR功能，可选，体积较大）

### 验证安装

```bash
# 测试 PyMuPDF
python -c "import fitz; print('✅ PyMuPDF 安装成功')"

# 测试 LangChain
python -c "from langchain_openai import ChatOpenAI; print('✅ LangChain 安装成功')"

# 测试核心模块
python -c "import fastapi, uvicorn, sqlalchemy; print('✅ 核心依赖安装成功')"
```

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关文档

历史开发文档已移至 `docs/archive/` 目录：
- `plan.md` - 服务器实现计划
- `plan_client.md` - 客户端实现计划
- `design.md` - 设计文档
- `q2.md` - 需求分析
