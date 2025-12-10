@echo off
chcp 65001 >nul
echo ========================================
echo   EMCP 模板批量更新工具
echo ========================================
echo.
echo 更新内容: 分类 + 名称 + 简介 + 描述 + Logo
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

echo [1] 预览模式 (dry-run) - 只查看，不实际更新
echo [2] 更新前 3 个模板 (测试)
echo [3] 更新所有模板 (含 Logo)
echo [4] 更新所有模板 (不含 Logo)
echo [5] 自定义数量更新
echo.
set /p choice="请选择操作 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 正在预览...
    python batch_update_emcp.py --dry-run
) else if "%choice%"=="2" (
    echo.
    echo 正在更新前 3 个模板...
    python batch_update_emcp.py --limit 3
) else if "%choice%"=="3" (
    echo.
    echo 警告：将更新所有模板（含重新生成 Logo）！
    set /p confirm="确认继续？(y/n): "
    if /i "%confirm%"=="y" (
        python batch_update_emcp.py
    ) else (
        echo 已取消
    )
) else if "%choice%"=="4" (
    echo.
    echo 警告：将更新所有模板（不重新生成 Logo）！
    set /p confirm="确认继续？(y/n): "
    if /i "%confirm%"=="y" (
        python batch_update_emcp.py --no-logo
    ) else (
        echo 已取消
    )
) else if "%choice%"=="5" (
    set /p num="请输入要更新的数量: "
    set /p logo="是否重新生成Logo？(y/n): "
    echo.
    if /i "%logo%"=="y" (
        echo 正在更新前 %num% 个模板（含 Logo）...
        python batch_update_emcp.py --limit %num%
    ) else (
        echo 正在更新前 %num% 个模板（不含 Logo）...
        python batch_update_emcp.py --limit %num% --no-logo
    )
) else (
    echo 无效选择
)

echo.
pause



