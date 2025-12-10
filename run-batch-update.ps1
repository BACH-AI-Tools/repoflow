# EMCP 模板批量更新工具
# PowerShell 脚本

$Host.UI.RawUI.WindowTitle = "EMCP 模板批量更新"

Write-Host "========================================"
Write-Host "   EMCP 模板批量更新工具"
Write-Host "========================================"
Write-Host ""
Write-Host "更新内容: 分类 + 名称 + 简介 + 描述 + Logo" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
try {
    python --version | Out-Null
} catch {
    Write-Host "[错误] 未找到 Python，请先安装 Python" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "[1] 预览模式 (dry-run) - 只查看，不实际更新"
Write-Host "[2] 更新前 3 个模板 (测试)"
Write-Host "[3] 更新所有模板 (含 Logo)"
Write-Host "[4] 更新所有模板 (不含 Logo)"
Write-Host "[5] 自定义数量更新"
Write-Host ""

$choice = Read-Host "请选择操作 (1-5)"

switch ($choice) {
    "1" {
        Write-Host ""
        Write-Host "正在预览..." -ForegroundColor Cyan
        python batch_update_emcp.py --dry-run
    }
    "2" {
        Write-Host ""
        Write-Host "正在更新前 3 个模板..." -ForegroundColor Cyan
        python batch_update_emcp.py --limit 3
    }
    "3" {
        Write-Host ""
        Write-Host "警告：将更新所有模板（含重新生成 Logo）！" -ForegroundColor Yellow
        $confirm = Read-Host "确认继续？(y/n)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            python batch_update_emcp.py
        } else {
            Write-Host "已取消" -ForegroundColor Gray
        }
    }
    "4" {
        Write-Host ""
        Write-Host "警告：将更新所有模板（不重新生成 Logo）！" -ForegroundColor Yellow
        $confirm = Read-Host "确认继续？(y/n)"
        if ($confirm -eq "y" -or $confirm -eq "Y") {
            python batch_update_emcp.py --no-logo
        } else {
            Write-Host "已取消" -ForegroundColor Gray
        }
    }
    "5" {
        $num = Read-Host "请输入要更新的数量"
        $logo = Read-Host "是否重新生成Logo？(y/n)"
        Write-Host ""
        if ($logo -eq "y" -or $logo -eq "Y") {
            Write-Host "正在更新前 $num 个模板（含 Logo）..." -ForegroundColor Cyan
            python batch_update_emcp.py --limit $num
        } else {
            Write-Host "正在更新前 $num 个模板（不含 Logo）..." -ForegroundColor Cyan
            python batch_update_emcp.py --limit $num --no-logo
        }
    }
    default {
        Write-Host "无效选择" -ForegroundColor Red
    }
}

Write-Host ""
Read-Host "按回车键退出"



