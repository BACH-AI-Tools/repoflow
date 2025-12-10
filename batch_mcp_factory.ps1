# 批量 MCP 工厂 PowerShell 脚本

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectsDir = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Projects = ""
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "🏭 批量 MCP 工厂" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 69) -ForegroundColor Cyan

# 设置环境变量
$env:API_KEY = "c73d0eb842msh082900adbe7d22cp15a3e0jsn8156d94adb0d"

# 如果没有提供项目目录，提示用户输入
if ([string]::IsNullOrEmpty($ProjectsDir)) {
    Write-Host ""
    $ProjectsDir = Read-Host "请输入 MCP 项目文件夹路径"
}

# 检查目录是否存在
if (-not (Test-Path $ProjectsDir)) {
    Write-Host "❌ 目录不存在: $ProjectsDir" -ForegroundColor Red
    exit 1
}

# 调用 Python 脚本
$pythonScript = Join-Path $PSScriptRoot "batch_mcp_factory.py"

if (-not (Test-Path $pythonScript)) {
    Write-Host "❌ 找不到 Python 脚本: $pythonScript" -ForegroundColor Red
    exit 1
}

# 构建参数
$args = @($ProjectsDir)

if (-not [string]::IsNullOrEmpty($Projects)) {
    $args += "--projects"
    $args += $Projects
}

# 运行 Python 脚本
Write-Host ""
Write-Host "▶️ 启动批量 MCP 工厂..." -ForegroundColor Yellow
Write-Host ""

python $args

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 处理过程中出现错误" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "✅ 处理完成！" -ForegroundColor Green

