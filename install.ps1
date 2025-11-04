# RepoFlow Windows 安装脚本

Write-Host "🚀 安装 RepoFlow..." -ForegroundColor Green

# 检查 Python 版本
$pythonVersion = python --version 2>&1
Write-Host "检测到 Python 版本: $pythonVersion" -ForegroundColor Cyan

# 询问是否创建虚拟环境
$createVenv = Read-Host "是否创建虚拟环境? (y/n)"
if ($createVenv -eq "y" -or $createVenv -eq "Y") {
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    Write-Host "✅ 虚拟环境已创建并激活" -ForegroundColor Green
}

# 安装依赖
Write-Host "📦 安装依赖包（使用清华镜像源）..." -ForegroundColor Yellow
python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 配置 RepoFlow
Write-Host ""
Write-Host "🔧 现在让我们配置 RepoFlow" -ForegroundColor Cyan
python repoflow.py config

Write-Host ""
Write-Host "✅ 安装完成!" -ForegroundColor Green
Write-Host ""
Write-Host "使用方法:" -ForegroundColor White
Write-Host "  python repoflow.py --help" -ForegroundColor Gray
Write-Host ""
Write-Host "快速开始:" -ForegroundColor White
Write-Host "  cd C:\path\to\your\project" -ForegroundColor Gray
Write-Host "  python $PWD\repoflow.py init --org BACH-AI-Tools --repo your-repo" -ForegroundColor Gray
Write-Host ""

