# 完整依赖安装指南

## 问题诊断

从服务器启动日志看到以下问题：

1. ❌ `No module named 'fitz'` - PyMuPDF 未安装
2. ⚠️ `LangChain未安装` - LangChain 相关包未安装
3. ⚠️ `usertool_xxx_config.json` 读取失败 - 模板文件问题（不影响运行）

## 快速安装所有依赖

### 方法 1：使用 pip（推荐）

在项目根目录运行：

```bash
# 安装所有必需依赖
pip install fastapi>=0.104.0 uvicorn[standard]>=0.24.0 \
    pydantic>=2.5.0 pydantic-settings>=2.1.0 \
    python-multipart>=0.0.6 aiofiles>=23.2.1 \
    sqlalchemy>=2.0.23 alembic>=1.13.0 \
    langchain>=0.1.0 langchain-openai>=0.0.2 langgraph>=0.0.20 \
    pymupdf>=1.23.8 paddlepaddle>=2.5.2 paddleocr>=2.7.0 \
    pillow>=10.1.0 pyyaml>=6.0.1 python-dotenv>=1.0.0 httpx>=0.25.2
```

### 方法 2：使用 PDM

```bash
pdm install
```

### 方法 3：分步安装（如果遇到问题）

#### 步骤 1：安装核心依赖
```bash
pip install fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy alembic
```

#### 步骤 2：安装 LangChain（LLM 功能）
```bash
pip install langchain langchain-openai langgraph
```

#### 步骤 3：安装 PyMuPDF（PDF 解析）
```bash
pip install pymupdf
```

#### 步骤 4：安装 OCR 相关（可选）
```bash
# PaddleOCR（中文 OCR，体积较大）
pip install paddlepaddle paddleocr

# 或跳过 OCR，如果需要时再安装
```

#### 步骤 5：安装其他依赖
```bash
pip install pillow pyyaml python-dotenv httpx
```

## 验证安装

```bash
# 测试 PyMuPDF
python -c "import fitz; print('✅ PyMuPDF 安装成功')"

# 测试 LangChain
python -c "from langchain_openai import ChatOpenAI; print('✅ LangChain 安装成功')"

# 测试其他核心模块
python -c "import fastapi, uvicorn, sqlalchemy; print('✅ 核心依赖安装成功')"
```

## 使用国内镜像（如果下载慢）

```bash
# 使用清华镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy alembic \
    langchain langchain-openai langgraph \
    pymupdf pillow pyyaml python-dotenv httpx

# PaddleOCR 体积较大，可以稍后安装
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple \
    paddlepaddle paddleocr
```

## 最小安装（核心功能）

如果只需要基本功能，可以只安装：

```bash
pip install fastapi uvicorn pydantic pydantic-settings \
    python-multipart aiofiles sqlalchemy \
    langchain langchain-openai langgraph \
    pymupdf pillow pyyaml python-dotenv httpx
```

跳过：
- `alembic`（数据库迁移，可选）
- `paddlepaddle` 和 `paddleocr`（OCR 功能，可选，体积较大）

## 解决 usertool_xxx_config.json 问题

这个文件是模板文件，如果损坏或为空，可以删除：

```bash
# 删除模板文件（会在需要时重新创建）
rm lib/server/usrdata/tools/usertool_xxx_config.json

# Windows:
del lib\server\usrdata\tools\usertool_xxx_config.json
```

或者检查文件内容，如果是空的或格式错误，可以清空它。

## 安装后的检查清单

启动服务器后，检查以下内容：

- ✅ 没有 `No module named 'fitz'` 错误
- ✅ 没有 `LangChain未安装` 提示（如果已安装）
- ⚠️ `usertool_xxx_config.json` 警告可以忽略（不影响功能）

## 常见问题

### Q: PyMuPDF 安装失败

```bash
# 尝试单独安装
pip install --upgrade pip
pip install pymupdf

# 或者使用预编译版本
pip install pymupdf --only-binary=all
```

### Q: PaddleOCR 安装失败或太慢

OCR 功能是可选的，可以：
- 先跳过，需要时再安装
- 使用其他 OCR 方案
- 或只处理文本/PDF，不处理图片

### Q: LangChain 版本冲突

```bash
# 使用指定版本
pip install langchain==0.1.0 langchain-openai==0.0.2 langgraph==0.0.20
```

## 一键安装脚本

创建 `install-deps.bat`（Windows）：

```batch
@echo off
echo 安装项目依赖...
pip install fastapi uvicorn pydantic pydantic-settings python-multipart aiofiles sqlalchemy alembic langchain langchain-openai langgraph pymupdf pillow pyyaml python-dotenv httpx
echo.
echo 可选：安装 OCR 功能（体积较大）
echo pip install paddlepaddle paddleocr
pause
```

运行：
```bash
install-deps.bat
```
