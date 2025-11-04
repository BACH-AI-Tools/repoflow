# RepoFlow Makefile

.PHONY: help install dev-install test lint format clean run

help:  ## 显示帮助信息
	@echo "RepoFlow - 可用命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## 安装依赖
	pip install -r requirements.txt

dev-install:  ## 安装开发依赖
	pip install -r requirements.txt
	pip install black flake8 pytest mypy pre-commit

test:  ## 运行测试
	pytest tests/ -v

lint:  ## 运行代码检查
	flake8 src/ repoflow.py --max-line-length=100
	mypy src/ repoflow.py --ignore-missing-imports

format:  ## 格式化代码
	black src/ repoflow.py tests/ --line-length=100

clean:  ## 清理临时文件
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .mypy_cache/

run:  ## 运行 RepoFlow
	python repoflow.py --help

build:  ## 构建分发包
	python -m build

upload-test:  ## 上传到 TestPyPI
	python -m twine upload --repository testpypi dist/*

upload:  ## 上传到 PyPI
	python -m twine upload dist/*

.DEFAULT_GOAL := help

