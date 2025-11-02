@echo off
chcp 65001 >nul
echo ========================================
echo 修复依赖问题
echo ========================================
echo.

echo [修复 1/3] 安装 PyMuPDF（跳过元数据准备）...
pip install --no-build-isolation --no-cache-dir pymupdf
if errorlevel 1 (
    echo 尝试使用镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-build-isolation pymupdf
)

echo.
echo [修复 2/3] 安装 LangChain（跳过元数据准备）...
pip install --no-build-isolation --no-cache-dir langchain langchain-openai langgraph
if errorlevel 1 (
    echo 尝试使用镜像源...
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-build-isolation langchain langchain-openai langgraph
)

echo.
echo [修复 3/3] 清理配置文件...
if exist lib\server\usrdata\tools\usertool_xxx_config.json (
    echo 删除空的模板文件...
    del lib\server\usrdata\tools\usertool_xxx_config.json
)

echo.
echo ========================================
echo 修复完成！
echo ========================================
echo.
echo 验证安装：
echo   python -c "import fitz; print('✅ PyMuPDF OK')"
echo   python -c "from langchain_openai import ChatOpenAI; print('✅ LangChain OK')"
echo.
echo 请重新启动服务器验证。
echo.
pause
