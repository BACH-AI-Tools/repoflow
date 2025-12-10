@echo off
REM 清理缓存并启动 RepoFlow Ultimate
echo 正在清理 Python 缓存...
if exist __pycache__ rd /s /q __pycache__
if exist src\__pycache__ rd /s /q src\__pycache__

echo 启动 RepoFlow Ultimate...
python -B repoflow_ultimate.py

pause





