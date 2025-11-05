#!/bin/bash
# RepoFlow 打包脚本 (macOS/Linux)

echo "========================================"
echo "  RepoFlow 打包工具"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.7+"
    exit 1
fi

# 检查是否安装了 PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "[警告] PyInstaller 未安装，正在安装..."
    pip3 install pyinstaller
    echo ""
fi

# 运行打包脚本
echo "[步骤 1/2] 开始打包..."
python3 build.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 打包失败"
    exit 1
fi

echo ""
echo "[步骤 2/2] 设置执行权限..."
chmod +x dist/RepoFlow

echo ""
echo "========================================"
echo "  ✅ 打包完成！"
echo "========================================"
echo ""
echo "  可执行文件: dist/RepoFlow"
echo ""
echo "  运行方式:"
echo "    ./dist/RepoFlow"
echo ""

# 询问是否立即运行
read -p "是否立即运行? (y/n): " run_now
if [[ $run_now =~ ^[Yy]$ ]]; then
    ./dist/RepoFlow &
    echo "已在后台启动"
fi

echo ""
echo "完成！"

