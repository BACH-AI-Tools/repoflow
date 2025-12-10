@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ======================================================================
echo 🏭 批量 MCP 工厂
echo ======================================================================

REM 检查是否安装了 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未安装 Python
    echo 请先安装 Python 3.8 或更高版本
    pause
    exit /b 1
)

REM 设置环境变量
set "API_KEY=c73d0eb842msh082900adbe7d22cp15a3e0jsn8156d94adb0d"

REM 如果没有参数，进入交互模式
if "%~1"=="" (
    python "%~dp0batch_mcp_factory.py"
) else (
    python "%~dp0batch_mcp_factory.py" %*
)

if errorlevel 1 (
    echo.
    echo ❌ 处理失败
    pause
    exit /b 1
)

echo.
echo ✅ 处理完成！
pause

