# 快速安装指南（解决卡顿问题）

## 问题：安装卡在 "Preparing metadata (pyproject.toml)"

这是因为 pip 在解析项目依赖时较慢。使用以下方法可以快速解决：

## 方法 1：跳过元数据准备（最快）

### 使用脚本：
```cmd
快速安装.bat
```

### 手动执行：
```cmd
# 安装 PyMuPDF
pip install --no-build-isolation --no-cache-dir pymupdf

# 安装 LangChain
pip install --no-build-isolation --no-cache-dir langchain langchain-openai langgraph
```

## 方法 2：使用镜像源（推荐）

```cmd
# 设置镜像源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

# 然后安装
pip install pymupdf langchain langchain-openai langgraph
```

## 方法 3：单独安装（最稳定）

不通过 pyproject.toml，直接安装需要的包：

```cmd
# 只安装缺失的关键包
pip install pymupdf
pip install langchain
pip install langchain-openai
pip install langgraph
```

## 方法 4：跳过有问题的依赖

如果只需要让服务器运行，可以先跳过可选依赖：

```cmd
# 最小安装（只装必需的）
pip install fastapi uvicorn pydantic sqlalchemy

# PDF 解析（如果需要）
pip install pymupdf

# LLM 功能（如果需要）
pip install langchain langchain-openai langgraph
```

## 推荐步骤

1. **停止当前安装**：按 `Ctrl+C` 取消

2. **使用快速安装脚本**：
   ```cmd
   快速安装.bat
   ```

3. **或手动快速安装**：
   ```cmd
   pip install --no-build-isolation pymupdf langchain langchain-openai langgraph
   ```

## 验证

安装完成后验证：

```cmd
python -c "import fitz; print('✅ PyMuPDF 安装成功')"
python -c "from langchain_openai import ChatOpenAI; print('✅ LangChain 安装成功')"
```

## 如果仍然很慢

使用预编译的 wheel 包：

```cmd
pip install --only-binary :all: pymupdf langchain langchain-openai langgraph
```

## 临时禁用功能

如果暂时不需要某些功能，可以：
- 跳过 PyMuPDF：PDF 解析功能不可用，但服务器可以运行
- 跳过 LangChain：LLM 功能不可用，但服务器可以运行

服务器会自动检测并优雅降级。
