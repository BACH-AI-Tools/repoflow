@echo off
REM Secret Scanner 运行脚本
REM 用法: run-secret-scan.bat [目录路径]

echo ========================================
echo   RepoFlow Secret Scanner
echo ========================================

if "%1"=="" (
    python -m src.secret_scanner .
) else (
    python -m src.secret_scanner %*
)











