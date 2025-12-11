# 批量配置 SonarQube 扫描
# 一键完成：组织 Secrets + GitHub Actions Workflow

param(
    [switch]$DryRun,
    [switch]$ListOnly,
    [switch]$SkipSecrets,
    [string[]]$Repos,
    [string[]]$Skip
)

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║           批量配置 SonarQube 扫描                                  ║" -ForegroundColor Cyan
Write-Host "║   一键完成：组织 Secrets + GitHub Actions Workflow                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# 构建参数
$args = @()

if ($DryRun) {
    $args += "--dry-run"
}

if ($ListOnly) {
    $args += "--list-only"
}

if ($SkipSecrets) {
    $args += "--skip-secrets"
}

if ($Repos) {
    $args += "-r"
    $args += $Repos
}

if ($Skip) {
    $args += "-s"
    $args += $Skip
}

# 如果没有参数，显示交互菜单
if ($args.Count -eq 0) {
    Write-Host "请选择操作模式:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  1. 预览模式（查看将要进行的操作，不实际执行）"
    Write-Host "  2. 执行配置（设置组织 Secrets + 添加 Workflow）"
    Write-Host "  3. 只列出仓库"
    Write-Host "  4. 退出"
    Write-Host ""
    $choice = Read-Host "请输入选项 (1-4)"
    
    switch ($choice) {
        "1" {
            Write-Host ""
            Write-Host "🔍 预览模式..." -ForegroundColor Green
            python batch_setup_sonar.py --dry-run
        }
        "2" {
            Write-Host ""
            Write-Host "⚠️  即将配置所有仓库" -ForegroundColor Yellow
            $confirm = Read-Host "确认继续？(Y/N)"
            if ($confirm -eq "Y" -or $confirm -eq "y") {
                Write-Host ""
                Write-Host "🚀 开始配置..." -ForegroundColor Green
                python batch_setup_sonar.py
            } else {
                Write-Host "已取消" -ForegroundColor Yellow
            }
        }
        "3" {
            Write-Host ""
            Write-Host "📋 仓库列表..." -ForegroundColor Green
            python batch_setup_sonar.py --list-only
        }
        "4" {
            exit 0
        }
        default {
            Write-Host "无效选项" -ForegroundColor Red
        }
    }
} else {
    # 使用命令行参数
    python batch_setup_sonar.py @args
}

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")











