@echo off
chcp 65001 >nul 2>&1
title RepoFlow GUI
echo 启动 RepoFlow GUI...
python repoflow_gui.py
if errorlevel 1 (
    echo.
    echo 启动失败，请检查是否已安装依赖：
    echo pip install -r requirements.txt
    pause
)

