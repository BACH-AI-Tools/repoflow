"""CI/CD Pipeline 生成器"""

from pathlib import Path
import json


class PipelineGenerator:
    """生成不同类型的 CI/CD Pipeline 配置"""
    
    def generate(self, pipeline_type: str, project_path: Path):
        """
        生成指定类型的 Pipeline
        
        Args:
            pipeline_type: Pipeline 类型 (docker, npm, pypi)
            project_path: 项目路径
        """
        generators = {
            'docker': self._generate_docker_pipeline,
            'npm': self._generate_npm_pipeline,
            'pypi': self._generate_pypi_pipeline,
        }
        
        if pipeline_type not in generators:
            raise ValueError(f"不支持的 Pipeline 类型: {pipeline_type}")
        
        generators[pipeline_type](project_path)
    
    def _generate_docker_pipeline(self, project_path: Path):
        """生成 Docker Pipeline (GitHub Actions)"""
        workflow_dir = project_path / '.github' / 'workflows'
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = """name: Build and Push Docker Image

on:
  push:
    branches: [ main, master ]
    tags:
      - 'v*'
  pull_request:
    branches: [ main, master ]

env:
  REGISTRY: docker.io
  IMAGE_NAME: ${{ secrets.DOCKERHUB_USERNAME }}/${{ github.event.repository.name }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Docker Hub
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
"""
        
        workflow_file = workflow_dir / 'docker-publish.yml'
        workflow_file.write_text(workflow_content, encoding='utf-8')
        
        # 生成示例 Dockerfile（如果不存在）
        dockerfile = project_path / 'Dockerfile'
        if not dockerfile.exists():
            dockerfile_content = """# 多阶段构建示例
FROM python:3.11-slim as builder

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 生产镜像
FROM python:3.11-slim

WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# 复制应用代码
COPY . .

# 运行应用
CMD ["python", "app.py"]
"""
            dockerfile.write_text(dockerfile_content, encoding='utf-8')
        
        # 创建 .dockerignore
        dockerignore = project_path / '.dockerignore'
        if not dockerignore.exists():
            dockerignore_content = """__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
venv
.git
.gitignore
.dockerignore
*.md
.vscode
.idea
"""
            dockerignore.write_text(dockerignore_content, encoding='utf-8')
    
    def _generate_npm_pipeline(self, project_path: Path):
        """生成 NPM Pipeline (GitHub Actions)"""
        workflow_dir = project_path / '.github' / 'workflows'
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = """name: Build and Publish to NPM

on:
  push:
    tags:
      - 'v*'  # 只在创建 v* tag 时触发
  workflow_dispatch:  # 允许手动触发

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          registry-url: 'https://registry.npmjs.org'

      - name: Install dependencies
        run: npm ci
        continue-on-error: true

      - name: Run tests
        run: npm test
        continue-on-error: true

      - name: Build
        run: npm run build
        continue-on-error: true

      - name: Publish to NPM
        run: npm publish --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
"""
        
        workflow_file = workflow_dir / 'npm-publish.yml'
        workflow_file.write_text(workflow_content, encoding='utf-8')
        
        # 检查 package.json 是否存在，如果不存在则创建示例
        package_json = project_path / 'package.json'
        if not package_json.exists():
            package_data = {
                "name": project_path.name.lower(),
                "version": "1.0.0",
                "description": "",
                "main": "index.js",
                "scripts": {
                    "test": "echo \"Error: no test specified\" && exit 0",
                    "build": "echo \"No build step\""
                },
                "keywords": [],
                "author": "",
                "license": "MIT"
            }
            package_json.write_text(json.dumps(package_data, indent=2), encoding='utf-8')
    
    def _generate_pypi_pipeline(self, project_path: Path):
        """生成 PyPI Pipeline (GitHub Actions)"""
        workflow_dir = project_path / '.github' / 'workflows'
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = """name: Build and Publish to PyPI

on:
  push:
    tags:
      - 'v*'  # 只在创建 v* tag 时触发
  workflow_dispatch:  # 允许手动触发

jobs:
  build-and-publish:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine

      - name: Build package
        run: python -m build

      - name: Check package
        run: twine check dist/*

      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
"""
        
        workflow_file = workflow_dir / 'pypi-publish.yml'
        workflow_file.write_text(workflow_content, encoding='utf-8')
        
        # 生成 setup.py（如果不存在）
        setup_py = project_path / 'setup.py'
        if not setup_py.exists():
            setup_content = f'''"""Setup script for {project_path.name}"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{project_path.name.lower()}",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A short description",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BACH-AI-Tools/{project_path.name}",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        # 添加你的依赖
    ],
)
'''
            setup_py.write_text(setup_content, encoding='utf-8')
        
        # 生成 pyproject.toml（现代 Python 打包）
        pyproject_toml = project_path / 'pyproject.toml'
        if not pyproject_toml.exists():
            toml_content = f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{project_path.name.lower()}"
version = "1.0.0"
description = "A short description"
readme = "README.md"
requires-python = ">=3.7"
license = {{text = "MIT"}}
authors = [
    {{name = "Your Name", email = "your.email@example.com"}}
]
keywords = []
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[project.urls]
Homepage = "https://github.com/BACH-AI-Tools/{project_path.name}"
'''
            pyproject_toml.write_text(toml_content, encoding='utf-8')

