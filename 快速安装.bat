@echo off
chcp 65001 >nul
echo ========================================
echo 快速安装缺失依赖（跳过元数据准备）
echo ========================================
echo.

echo [1/3] 安装 PyMuPDF（跳过元数据）...
pip install --no-build-isolation --no-cache-dir pymupdf
if errorlevel 1 (
    echo 尝试使用镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-build-isolation pymupdf
)

echo.
echo [2/3] 安装 LangChain（跳过元数据）...
pip install --no-build-isolation --no-cache-dir langchain langchain-openai langgraph
if errorlevel 1 (
    echo 尝试使用镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-build-isolation langchain langchain-openai langgraph
)

echo.
echo [3/3] 清理配置文件...
if exist lib\server\usrdata\tools\usertool_xxx_config.json (
    del lib\server\usrdata\tools\usertool_xxx_config.json >nul 2>&1
)

echo.
echo ========================================
echo 安装完成！
echo ========================================
echo.
pause
