@echo off
chcp 65001 >nul
echo.
echo ╔══════════════════════════════════════════════════════════════════╗
echo ║           批量配置 SonarQube 扫描                                  ║
echo ║   一键完成：组织 Secrets + GitHub Actions Workflow                  ║
echo ╚══════════════════════════════════════════════════════════════════╝
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

echo 请选择操作模式:
echo.
echo   1. 预览模式（查看将要进行的操作，不实际执行）
echo   2. 执行配置（设置组织 Secrets + 添加 Workflow 到所有仓库）
echo   3. 只列出仓库
echo   4. 退出
echo.
set /p choice="请输入选项 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🔍 预览模式...
    python batch_setup_sonar.py --dry-run
) else if "%choice%"=="2" (
    echo.
    echo ⚠️  即将配置 100 个仓库，确认继续？
    set /p confirm="输入 Y 确认: "
    if /i "%confirm%"=="Y" (
        echo.
        echo 🚀 开始配置...
        python batch_setup_sonar.py
    ) else (
        echo 已取消
    )
) else if "%choice%"=="3" (
    echo.
    echo 📋 仓库列表...
    python batch_setup_sonar.py --list-only
) else if "%choice%"=="4" (
    exit /b 0
) else (
    echo 无效选项
)

echo.
pause











