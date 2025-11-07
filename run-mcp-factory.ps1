# MCP工厂启动脚本

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🏭 MCP工厂" -ForegroundColor Green
Write-Host "  流程化MCP发布平台" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

python mcp_factory_gui.py

Read-Host "按回车键退出"

