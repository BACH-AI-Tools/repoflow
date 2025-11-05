#!/bin/bash
# RepoFlow 快速发布脚本 (macOS/Linux)

# 检查参数
if [ $# -eq 0 ]; then
    echo "❌ 错误: 请提供版本号"
    echo "用法: ./release.sh 1.0.0"
    exit 1
fi

VERSION=$1

echo "========================================"
echo "  RepoFlow 发布脚本"
echo "========================================"
echo ""

# 验证版本号格式
if [[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ 错误: 版本号格式不正确"
    echo "   应该是 x.y.z 格式（如 1.0.0）"
    exit 1
fi

TAG_NAME="v${VERSION}"

echo "📌 版本号: $VERSION"
echo "🏷️  Tag: $TAG_NAME"
echo ""

# 检查 tag 是否已存在
if git rev-parse "$TAG_NAME" >/dev/null 2>&1; then
    echo "❌ 错误: Tag '$TAG_NAME' 已经存在"
    echo "请使用新的版本号或删除旧 tag"
    exit 1
fi

# 显示即将发布的内容
echo "准备发布..."
echo ""
echo "将会自动执行:"
echo "  1. 创建 Git Tag: $TAG_NAME"
echo "  2. 推送到 GitHub"
echo "  3. 触发 GitHub Actions"
echo "  4. 自动构建 Windows/macOS/Linux 版本"
echo "  5. 创建 GitHub Release"
echo ""

read -p "确认发布? (y/n): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

echo ""
echo "[1/2] 创建 Tag..."
git tag -a "$TAG_NAME" -m "Release $TAG_NAME"

if [ $? -ne 0 ]; then
    echo "❌ 创建 Tag 失败"
    exit 1
fi

echo "  ✓ Tag 已创建"

echo ""
echo "[2/2] 推送到 GitHub..."
git push origin "$TAG_NAME"

if [ $? -ne 0 ]; then
    echo "❌ 推送失败"
    exit 1
fi

echo "  ✓ Tag 已推送"

echo ""
echo "========================================"
echo "  ✅ 发布成功！"
echo "========================================"
echo ""
echo "🚀 GitHub Actions 正在自动构建..."
echo ""
echo "查看进度:"
echo "  https://github.com/BACH-AI-Tools/RepoFlow/actions"
echo ""
echo "构建完成后，可在此下载:"
echo "  https://github.com/BACH-AI-Tools/RepoFlow/releases/tag/$TAG_NAME"
echo ""
echo "💡 通常需要 5-10 分钟构建完成"
echo ""

