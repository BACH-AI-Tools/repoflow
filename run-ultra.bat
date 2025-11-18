@echo off
chcp 65001 >nul 2>&1
title RepoFlow Ultra
echo 启动 RepoFlow Ultra 现代化界面...
python repoflow_ultra.py
if errorlevel 1 (
    echo.
    echo 启动失败，请检查依赖安装
    pause
)


