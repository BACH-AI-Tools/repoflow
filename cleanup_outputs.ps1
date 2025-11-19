#!/usr/bin/env pwsh
# 清理脚本 - 移动现有的 logo 和 HTML 报告到 outputs 目录

Write-Host "🧹 开始整理输出文件..." -ForegroundColor Cyan

# 创建输出目录
$logosDir = "outputs\logos"
$reportsDir = "outputs\reports"

Write-Host "📁 创建输出目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $logosDir | Out-Null
New-Item -ItemType Directory -Force -Path $reportsDir | Out-Null
Write-Host "   ✅ 已创建 $logosDir" -ForegroundColor Green
Write-Host "   ✅ 已创建 $reportsDir" -ForegroundColor Green

# 移动 logo 文件
Write-Host "`n📦 移动 logo 文件..." -ForegroundColor Yellow
$logoCount = 0
Get-ChildItem -Path "." -Filter "logo_*.png" -File | ForEach-Object {
    $dest = Join-Path $logosDir $_.Name
    if (Test-Path $dest) {
        Write-Host "   ⚠️  跳过（已存在）: $($_.Name)" -ForegroundColor DarkYellow
    } else {
        Move-Item -Path $_.FullName -Destination $dest
        Write-Host "   ✅ 移动: $($_.Name)" -ForegroundColor Green
        $logoCount++
    }
}
Write-Host "   📊 共移动 $logoCount 个 logo 文件" -ForegroundColor Cyan

# 移动 HTML 报告文件
Write-Host "`n📄 移动 HTML 报告..." -ForegroundColor Yellow
$reportCount = 0

# MCP 测试报告
Get-ChildItem -Path "." -Filter "mcp_test_report_*.html" -File | ForEach-Object {
    $dest = Join-Path $reportsDir $_.Name
    if (Test-Path $dest) {
        Write-Host "   ⚠️  跳过（已存在）: $($_.Name)" -ForegroundColor DarkYellow
    } else {
        Move-Item -Path $_.FullName -Destination $dest
        Write-Host "   ✅ 移动: $($_.Name)" -ForegroundColor Green
        $reportCount++
    }
}

# Agent 对话测试报告
Get-ChildItem -Path "." -Filter "agent_chat_test_*.html" -File | ForEach-Object {
    $dest = Join-Path $reportsDir $_.Name
    if (Test-Path $dest) {
        Write-Host "   ⚠️  跳过（已存在）: $($_.Name)" -ForegroundColor DarkYellow
    } else {
        Move-Item -Path $_.FullName -Destination $dest
        Write-Host "   ✅ 移动: $($_.Name)" -ForegroundColor Green
        $reportCount++
    }
}

Write-Host "   📊 共移动 $reportCount 个报告文件" -ForegroundColor Cyan

# 显示统计信息
Write-Host "`n✅ 整理完成！" -ForegroundColor Green
Write-Host "📁 输出目录结构:" -ForegroundColor Cyan
Write-Host "   outputs/" -ForegroundColor White
Write-Host "   ├── logos/    ($logoCount 个文件)" -ForegroundColor White
Write-Host "   └── reports/  ($reportCount 个文件)" -ForegroundColor White

Write-Host "`n💡 提示：outputs/ 目录已添加到 .gitignore，不会被提交到 Git" -ForegroundColor Yellow

