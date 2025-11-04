#!/usr/bin/env pwsh
# PowerShell 启动脚本

Write-Host "启动 RepoFlow GUI..." -ForegroundColor Cyan

try {
    python repoflow_gui.py
} catch {
    Write-Host ""
    Write-Host "启动失败，请检查是否已安装依赖：" -ForegroundColor Red
    Write-Host "pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "按任意键继续"
}

