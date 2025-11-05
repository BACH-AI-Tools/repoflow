@echo off
REM RepoFlow 快速打包脚本 (Windows)

echo ========================================
echo   RepoFlow 打包工具
echo ========================================
echo.

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [警告] PyInstaller 未安装，正在安装...
    pip install pyinstaller
    echo.
)

REM 运行打包脚本
echo [步骤 1/2] 开始打包...
python build_exe.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败
    pause
    exit /b 1
)

echo.
echo [步骤 2/2] 测试运行...
echo.

REM 询问是否立即运行
set /p run_now="是否立即运行 RepoFlow.exe? (y/n): "
if /i "%run_now%"=="y" (
    start dist\RepoFlow.exe
)

echo.
echo ========================================
echo   打包完成！
echo ========================================
echo.
echo   可执行文件: dist\RepoFlow.exe
echo   双击即可运行
echo.

pause

