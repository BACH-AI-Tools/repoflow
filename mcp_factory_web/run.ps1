# MCP工厂 Web界面 - PowerShell启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   MCP工厂 Web界面" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 进入脚本目录
Set-Location $PSScriptRoot

# 检查Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[✓] Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[✗] 未找到Python，请先安装Python 3.10+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查依赖
Write-Host "[1/3] 检查依赖..." -ForegroundColor Yellow

$flaskInstalled = pip show flask 2>$null
if (-not $flaskInstalled) {
    Write-Host "[2/3] 安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt -q
} else {
    Write-Host "[2/3] 依赖已安装" -ForegroundColor Green
}

# 启动服务器
Write-Host "[3/3] 启动Web服务器..." -ForegroundColor Yellow
Write-Host ""
Write-Host "  访问地址: " -NoNewline
Write-Host "http://localhost:5000" -ForegroundColor Cyan
Write-Host "  按 Ctrl+C 停止服务器"
Write-Host ""

python app.py




