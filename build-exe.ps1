# RepoFlow 快速打包脚本 (PowerShell)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RepoFlow 打包工具" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否安装了 PyInstaller
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw
    }
} catch {
    Write-Host "[警告] PyInstaller 未安装，正在安装..." -ForegroundColor Yellow
    pip install pyinstaller
    Write-Host ""
}

# 运行打包脚本
Write-Host "[步骤 1/2] 开始打包..." -ForegroundColor Green
python build.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] 打包失败" -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "[步骤 2/2] 测试运行..." -ForegroundColor Green
Write-Host ""

# 询问是否立即运行
$runNow = Read-Host "是否立即运行 RepoFlow.exe? (y/n)"
if ($runNow -eq "y" -or $runNow -eq "Y") {
    Start-Process "dist\RepoFlow.exe"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  打包完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  可执行文件: dist\RepoFlow.exe" -ForegroundColor Cyan
Write-Host "  双击即可运行" -ForegroundColor Cyan
Write-Host ""

