# AutoResearchLogMaker 依赖安装脚本（PowerShell）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装 AutoResearchLogMaker 依赖" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 pip
Write-Host "[检查] 验证 pip 是否可用..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version
    Write-Host "✅ pip 已安装: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ pip 未找到，请先安装 Python 和 pip" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 安装核心依赖
Write-Host "[1/4] 安装核心依赖..." -ForegroundColor Yellow
pip install fastapi uvicorn pydantic pydantic-settings python-multipart aiofiles sqlalchemy alembic pyyaml python-dotenv httpx pillow
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 核心依赖安装失败" -ForegroundColor Red
    exit 1
}
Write-Host "✅ 核心依赖安装成功" -ForegroundColor Green

Write-Host ""

# 安装 LangChain
Write-Host "[2/4] 安装 LangChain（LLM 功能）..." -ForegroundColor Yellow
pip install langchain langchain-openai langgraph
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  LangChain 安装失败，LLM 功能将不可用" -ForegroundColor Yellow
} else {
    Write-Host "✅ LangChain 安装成功" -ForegroundColor Green
}

Write-Host ""

# 安装 PyMuPDF
Write-Host "[3/4] 安装 PyMuPDF（PDF 解析）..." -ForegroundColor Yellow
pip install pymupdf
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  PyMuPDF 安装失败，PDF 解析功能将不可用" -ForegroundColor Yellow
} else {
    Write-Host "✅ PyMuPDF 安装成功" -ForegroundColor Green
}

Write-Host ""

# 修复 usertool_xxx_config.json
Write-Host "[4/4] 修复配置文件..." -ForegroundColor Yellow
$toolConfigPath = "lib\server\usrdata\tools\usertool_xxx_config.json"
if (Test-Path $toolConfigPath) {
    $content = Get-Content $toolConfigPath -Raw
    if ([string]::IsNullOrWhiteSpace($content)) {
        Write-Host "删除空的模板文件..." -ForegroundColor Yellow
        Remove-Item $toolConfigPath -Force
        Write-Host "✅ 已删除空的配置文件" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "[验证] 验证安装..." -ForegroundColor Yellow
try {
    python -c "import fastapi, uvicorn, sqlalchemy; print('✓ 核心依赖正常')" 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "✓ 核心依赖正常" -ForegroundColor Green } else { Write-Host "✗ 核心依赖验证失败" -ForegroundColor Red }
} catch {
    Write-Host "✗ 核心依赖验证失败" -ForegroundColor Red
}

try {
    python -c "import fitz; print('✓ PyMuPDF 正常')" 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "✓ PyMuPDF 正常" -ForegroundColor Green } else { Write-Host "✗ PyMuPDF 未安装" -ForegroundColor Yellow }
} catch {
    Write-Host "✗ PyMuPDF 未安装" -ForegroundColor Yellow
}

try {
    python -c "from langchain_openai import ChatOpenAI; print('✓ LangChain 正常')" 2>$null
    if ($LASTEXITCODE -eq 0) { Write-Host "✓ LangChain 正常" -ForegroundColor Green } else { Write-Host "✗ LangChain 未安装" -ForegroundColor Yellow }
} catch {
    Write-Host "✗ LangChain 未安装" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "可选：安装 OCR 功能（体积较大，下载较慢）" -ForegroundColor Yellow
Write-Host "运行: pip install paddlepaddle paddleocr" -ForegroundColor Gray
Write-Host ""
Write-Host "启动服务器: python run_server.py" -ForegroundColor Cyan
Write-Host ""

pause
