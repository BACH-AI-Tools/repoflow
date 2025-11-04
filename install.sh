#!/bin/bash
# RepoFlow 快速安装脚本

echo "🚀 安装 RepoFlow..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "检测到 Python 版本: $python_version"

# 创建虚拟环境（可选）
read -p "是否创建虚拟环境? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ 虚拟环境已创建并激活"
fi

# 安装依赖
echo "📦 安装依赖包（使用清华镜像源）..."
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 配置 RepoFlow
echo ""
echo "🔧 现在让我们配置 RepoFlow"
python3 repoflow.py config

echo ""
echo "✅ 安装完成!"
echo ""
echo "使用方法:"
echo "  python3 repoflow.py --help"
echo ""
echo "快速开始:"
echo "  cd /path/to/your/project"
echo "  python3 $(pwd)/repoflow.py init --org BACH-AI-Tools --repo your-repo"
echo ""

