@echo off
REM RepoFlow 启动脚本 (Windows CMD)
REM 确保使用正确的 Python 3.13 环境

set PYTHON="C:\Users\ZH\AppData\Local\Programs\Python\Python313\python.exe"
set SCRIPT=%~dp0repoflow.py

%PYTHON% %SCRIPT% %*


