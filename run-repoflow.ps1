# RepoFlow 启动脚本
# 确保使用正确的 Python 3.13 环境

$python = "C:\Users\ZH\AppData\Local\Programs\Python\Python313\python.exe"
$script = Join-Path $PSScriptRoot "repoflow.py"

# 检查 Python 是否存在
if (-not (Test-Path $python)) {
    Write-Host "❌ 错误: Python 3.13 未找到!" -ForegroundColor Red
    Write-Host "路径: $python" -ForegroundColor Yellow
    exit 1
}

# 检查脚本是否存在
if (-not (Test-Path $script)) {
    Write-Host "❌ 错误: repoflow.py 未找到!" -ForegroundColor Red
    exit 1
}

# 运行 RepoFlow
& $python $script $args



