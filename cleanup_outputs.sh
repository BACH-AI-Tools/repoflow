#!/bin/bash
# 清理脚本 - 移动现有的 logo 和 HTML 报告到 outputs 目录

echo "🧹 开始整理输出文件..."

# 创建输出目录
logos_dir="outputs/logos"
reports_dir="outputs/reports"

echo "📁 创建输出目录..."
mkdir -p "$logos_dir"
mkdir -p "$reports_dir"
echo "   ✅ 已创建 $logos_dir"
echo "   ✅ 已创建 $reports_dir"

# 移动 logo 文件
echo ""
echo "📦 移动 logo 文件..."
logo_count=0
for file in logo_*.png; do
    if [ -f "$file" ]; then
        dest="$logos_dir/$file"
        if [ -f "$dest" ]; then
            echo "   ⚠️  跳过（已存在）: $file"
        else
            mv "$file" "$dest"
            echo "   ✅ 移动: $file"
            ((logo_count++))
        fi
    fi
done
echo "   📊 共移动 $logo_count 个 logo 文件"

# 移动 HTML 报告文件
echo ""
echo "📄 移动 HTML 报告..."
report_count=0

# MCP 测试报告
for file in mcp_test_report_*.html; do
    if [ -f "$file" ]; then
        dest="$reports_dir/$file"
        if [ -f "$dest" ]; then
            echo "   ⚠️  跳过（已存在）: $file"
        else
            mv "$file" "$dest"
            echo "   ✅ 移动: $file"
            ((report_count++))
        fi
    fi
done

# Agent 对话测试报告
for file in agent_chat_test_*.html; do
    if [ -f "$file" ]; then
        dest="$reports_dir/$file"
        if [ -f "$dest" ]; then
            echo "   ⚠️  跳过（已存在）: $file"
        else
            mv "$file" "$dest"
            echo "   ✅ 移动: $file"
            ((report_count++))
        fi
    fi
done

echo "   📊 共移动 $report_count 个报告文件"

# 显示统计信息
echo ""
echo "✅ 整理完成！"
echo "📁 输出目录结构:"
echo "   outputs/"
echo "   ├── logos/    ($logo_count 个文件)"
echo "   └── reports/  ($report_count 个文件)"

echo ""
echo "💡 提示：outputs/ 目录已添加到 .gitignore，不会被提交到 Git"

