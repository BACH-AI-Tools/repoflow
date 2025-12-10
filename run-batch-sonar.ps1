# 批量 SonarQube 扫描脚本
# 用法: .\run-batch-sonar.ps1 [参数]

param(
    [string]$Org,           # GitHub 组织名
    [string[]]$Repos,       # 只扫描这些仓库
    [string[]]$Skip,        # 跳过这些仓库
    [switch]$ListOnly,      # 只列出仓库
    [switch]$NoCleanup      # 不清理临时文件
)

$Host.UI.RawUI.WindowTitle = "批量 SonarQube 扫描"

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "  批量 SonarQube 扫描工具" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    $null = python --version 2>&1
} catch {
    Write-Host "[错误] 未找到 Python，请先安装 Python" -ForegroundColor Red
    exit 1
}

# 检查 sonar-scanner
try {
    $null = sonar-scanner --version 2>&1
} catch {
    Write-Host "[警告] 未找到 sonar-scanner" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请安装 SonarScanner:" -ForegroundColor Yellow
    Write-Host "  方式1: choco install sonarscanner-cli"
    Write-Host "  方式2: 从官网下载 https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/"
    Write-Host ""
    exit 1
}

# 构建参数
$args = @()

if ($Org) {
    $args += "--org", $Org
}

if ($Repos) {
    $args += "--repos"
    $args += $Repos
}

if ($Skip) {
    $args += "--skip"
    $args += $Skip
}

if ($ListOnly) {
    $args += "--list-only"
}

if ($NoCleanup) {
    $args += "--no-cleanup"
}

# 显示帮助
if ($args.Count -eq 0) {
    Write-Host "使用方法:" -ForegroundColor Green
    Write-Host "  扫描所有仓库:      .\run-batch-sonar.ps1"
    Write-Host "  只列出仓库:        .\run-batch-sonar.ps1 -ListOnly"
    Write-Host "  扫描指定仓库:      .\run-batch-sonar.ps1 -Repos repo1,repo2"
    Write-Host "  跳过某些仓库:      .\run-batch-sonar.ps1 -Skip repo1,repo2"
    Write-Host "  指定组织:          .\run-batch-sonar.ps1 -Org MyOrg"
    Write-Host ""
}

# 运行 Python 脚本
python batch_sonar_scan.py @args

Write-Host ""
Write-Host "按任意键退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")








