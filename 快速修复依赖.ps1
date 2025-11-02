# 快速修复：安装缺失的依赖

Write-Host "正在安装缺失的依赖..." -ForegroundColor Yellow

# 安装 PyMuPDF
Write-Host "安装 PyMuPDF..." -ForegroundColor Cyan
pip install pymupdf

# 安装 LangChain
Write-Host "安装 LangChain..." -ForegroundColor Cyan
pip install langchain langchain-openai langgraph

# 删除空的配置文件
$toolFile = "lib\server\usrdata\tools\usertool_xxx_config.json"
if (Test-Path $toolFile) {
    $content = Get-Content $toolFile -Raw
    if ([string]::IsNullOrWhiteSpace($content)) {
        Remove-Item $toolFile -Force
        Write-Host "已删除空的配置文件" -ForegroundColor Green
    }
}

Write-Host "完成！请重启服务器。" -ForegroundColor Green
