@echo off
chcp 65001 >nul
title 批量 SonarQube 扫描

echo ===============================================
echo   批量 SonarQube 扫描工具
echo ===============================================
echo.

REM 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查 sonar-scanner
sonar-scanner --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未找到 sonar-scanner
    echo.
    echo 请安装 SonarScanner:
    echo   方式1: choco install sonarscanner-cli
    echo   方式2: 从官网下载 https://docs.sonarsource.com/sonarqube/latest/analyzing-source-code/scanners/sonarscanner/
    echo.
    pause
    exit /b 1
)

echo 使用方法:
echo   1. 扫描所有仓库:      python batch_sonar_scan.py
echo   2. 只列出仓库:        python batch_sonar_scan.py --list-only
echo   3. 扫描指定仓库:      python batch_sonar_scan.py -r repo1 repo2
echo   4. 跳过某些仓库:      python batch_sonar_scan.py -s repo1 repo2
echo   5. 指定组织:          python batch_sonar_scan.py -o MyOrg
echo.

REM 运行脚本
python batch_sonar_scan.py %*

echo.
pause











