#!/bin/bash
# Linux/Mac 启动脚本

echo "启动 RepoFlow GUI..."

python3 repoflow_gui.py

if [ $? -ne 0 ]; then
    echo ""
    echo "启动失败，请检查是否已安装依赖："
    echo "pip3 install -r requirements.txt"
    read -p "按任意键继续..."
fi

