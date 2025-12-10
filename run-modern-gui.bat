@echo off
chcp 65001 >nul 2>&1
title RepoFlow - 现代化 GUI
echo 启动 RepoFlow 现代化界面...
python modern_gui.py
if errorlevel 1 (
    echo.
    echo 启动失败，请检查依赖
    pause
)

