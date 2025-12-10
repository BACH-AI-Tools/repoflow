@echo off
echo ========================================
echo   MCP工厂 Web界面
echo ========================================
echo.

:: 检查Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到Python，请先安装Python 3.10+
    pause
    exit /b 1
)

:: 进入目录
cd /d "%~dp0"

:: 检查依赖
echo [1/3] 检查依赖...
pip show flask >nul 2>nul
if %errorlevel% neq 0 (
    echo [2/3] 安装依赖...
    pip install -r requirements.txt -q
) else (
    echo [2/3] 依赖已安装
)

:: 启动服务器
echo [3/3] 启动Web服务器...
echo.
echo  访问地址: http://localhost:5000
echo  按 Ctrl+C 停止服务器
echo.
python app.py

pause

