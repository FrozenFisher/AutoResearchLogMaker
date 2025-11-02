# LangChain 安装指南

## 项目依赖配置

项目已经在 `pyproject.toml` 中配置了以下 LangChain 相关依赖：
- `langchain>=0.1.0`
- `langchain-openai>=0.0.2`
- `langgraph>=0.0.20`

## 安装方式

### 方式 1：使用 PDM（推荐）

如果项目使用 PDM 管理依赖：

```bash
# 安装所有依赖（包括 langchain）
pdm install

# 或只安装项目依赖（不包括开发依赖）
pdm install --prod
```

### 方式 2：使用 pip

```bash
# 安装所有依赖
pip install -e .

# 或直接安装 langchain 相关包
pip install langchain>=0.1.0 langchain-openai>=0.0.2 langgraph>=0.0.20

# 如果需要从 requirements.txt 安装
pip install -r requirements.txt  # 如果有这个文件
```

### 方式 3：单独安装 LangChain

如果只需要安装 LangChain 及其相关包：

```bash
# 基础 LangChain
pip install langchain

# OpenAI 集成
pip install langchain-openai

# LangGraph（工作流编排）
pip install langgraph

# 或者一次性安装
pip install langchain langchain-openai langgraph
```

## 验证安装

安装完成后，验证是否成功：

```bash
python -c "from langchain_openai import ChatOpenAI; print('LangChain 安装成功')"
```

或者在 Python 中：

```python
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage
    from langchain_core.prompts import ChatPromptTemplate
    print("✅ LangChain 安装成功")
except ImportError as e:
    print(f"❌ LangChain 安装失败: {e}")
```

## 系统要求

- **Python 版本**: >= 3.11, < 3.12（根据 pyproject.toml）
- **操作系统**: Windows / Linux / macOS

## 常见问题

### 1. 版本冲突

如果遇到版本冲突，可以：

```bash
# 升级 pip
pip install --upgrade pip

# 使用兼容版本
pip install langchain==0.1.0 langchain-openai==0.0.2 langgraph==0.0.20
```

### 2. 网络问题（中国）

如果下载慢，可以使用国内镜像：

```bash
# 使用清华镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple langchain langchain-openai langgraph

# 或使用阿里镜像
pip install -i https://mirrors.aliyun.com/pypi/simple/ langchain langchain-openai langgraph
```

### 3. 权限问题（Windows）

如果在 Windows 上遇到权限错误：

```bash
# 使用用户安装
pip install --user langchain langchain-openai langgraph

# 或以管理员身份运行 PowerShell
```

## 完整依赖安装

如果要安装项目的所有依赖（不仅仅是 LangChain）：

```bash
# 方式 1: 使用 pip（如果有 requirements.txt）
pip install -r requirements.txt

# 方式 2: 手动安装（从 pyproject.toml）
pip install fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy alembic \
    langchain langchain-openai langgraph \
    pymupdf paddlepaddle paddleocr pillow pyyaml \
    python-dotenv httpx
```

## 开发环境设置

如果使用虚拟环境（推荐）：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -e .
# 或
pdm install
```

## 检查服务器中的 LangChain

服务器启动时会自动检测 LangChain 是否可用：

- 如果已安装：LLM 功能可用
- 如果未安装：会显示 "LangChain未安装，LLM功能将不可用"，但服务器仍可运行

查看 `src/server/LLMManager/LLMService.py` 中的检测逻辑。
