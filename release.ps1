# RepoFlow 快速发布脚本
# 用于创建 tag 并触发自动构建

param(
    [Parameter(Mandatory=$true)]
    [string]$Version
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  RepoFlow 发布脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 验证版本号格式
if ($Version -notmatch '^\d+\.\d+\.\d+$') {
    Write-Host "❌ 错误: 版本号格式不正确" -ForegroundColor Red
    Write-Host "   应该是 x.y.z 格式（如 1.0.0）" -ForegroundColor Yellow
    exit 1
}

$tagName = "v$Version"

Write-Host "📌 版本号: $Version" -ForegroundColor Cyan
Write-Host "🏷️  Tag: $tagName" -ForegroundColor Cyan
Write-Host ""

# 检查 tag 是否已存在
try {
    git rev-parse $tagName 2>&1 | Out-Null
    Write-Host "❌ 错误: Tag '$tagName' 已经存在" -ForegroundColor Red
    Write-Host "请使用新的版本号或删除旧 tag" -ForegroundColor Yellow
    exit 1
} catch {
    # Tag 不存在，继续
}

# 显示即将发布的内容
Write-Host "准备发布..." -ForegroundColor Yellow
Write-Host ""
Write-Host "将会自动执行:" -ForegroundColor Cyan
Write-Host "  1. 创建 Git Tag: $tagName" -ForegroundColor White
Write-Host "  2. 推送到 GitHub" -ForegroundColor White
Write-Host "  3. 触发 GitHub Actions" -ForegroundColor White
Write-Host "  4. 自动构建 Windows/macOS/Linux 版本" -ForegroundColor White
Write-Host "  5. 创建 GitHub Release" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "确认发布? (y/n)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "[1/2] 创建 Tag..." -ForegroundColor Green
git tag -a $tagName -m "Release $tagName"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 创建 Tag 失败" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Tag 已创建" -ForegroundColor Green

Write-Host ""
Write-Host "[2/2] 推送到 GitHub..." -ForegroundColor Green
git push origin $tagName

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ 推送失败" -ForegroundColor Red
    exit 1
}

Write-Host "  ✓ Tag 已推送" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✅ 发布成功！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 GitHub Actions 正在自动构建..." -ForegroundColor Cyan
Write-Host ""
Write-Host "查看进度:" -ForegroundColor Yellow
Write-Host "  https://github.com/BACH-AI-Tools/RepoFlow/actions" -ForegroundColor Blue
Write-Host ""
Write-Host "构建完成后，可在此下载:" -ForegroundColor Yellow
Write-Host "  https://github.com/BACH-AI-Tools/RepoFlow/releases/tag/$tagName" -ForegroundColor Blue
Write-Host ""
Write-Host "💡 通常需要 5-10 分钟构建完成" -ForegroundColor Gray
Write-Host ""

