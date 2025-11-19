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
            # 检测项目类型
            from src.project_detector import ProjectDetector
            detector = ProjectDetector(project_path)
            info = detector.get_project_info()
            detected_types = info['detected_types']
            
            # 检查是否有 .csproj 文件
            has_csproj = any(project_path.glob('*.csproj'))
            
            # 根据项目类型生成不同的 Dockerfile
            if 'dotnet' in detected_types or has_csproj:
                # 获取 .csproj 文件名作为项目名
                csproj_files = list(project_path.glob('*.csproj'))
                if csproj_files:
                    project_name = csproj_files[0].stem
                else:
                    project_name = project_path.name
                
                # C# / .NET Dockerfile
                dockerfile_content = f"""# 多阶段构建 - .NET 应用
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# 复制项目文件
COPY *.csproj ./
RUN dotnet restore

# 复制所有代码并构建
COPY . .
RUN dotnet publish -c Release -o /app/publish

# 运行时镜像
FROM mcr.microsoft.com/dotnet/runtime:8.0
WORKDIR /app
COPY --from=build /app/publish .

# 设置入口点
ENTRYPOINT ["dotnet", "{project_name}.dll"]
"""
            elif 'nodejs' in detected_types:
                # Node.js Dockerfile
                dockerfile_content = """# 多阶段构建 - Node.js 应用
FROM node:18-alpine AS builder
WORKDIR /app

# 复制依赖文件
COPY package*.json ./
RUN npm ci

# 复制代码并构建
COPY . .
RUN npm run build || true

# 生产镜像
FROM node:18-alpine
WORKDIR /app

# 复制依赖和构建产物
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./

# 运行应用
EXPOSE 3000
CMD ["node", "dist/index.js"]
"""
            else:
                # Python Dockerfile (默认)
                dockerfile_content = """# 多阶段构建 - Python 应用
FROM python:3.11-slim AS builder
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
CMD ["python", "main.py"]
"""
            
            dockerfile.write_text(dockerfile_content, encoding='utf-8')
        
        # 创建 .dockerignore
        dockerignore = project_path / '.dockerignore'
        if not dockerignore.exists():
            dockerignore_content = """# Git
.git
.gitignore
.gitattributes

# Build artifacts
bin/
obj/
dist/
build/
*.egg-info/

# Dependencies
node_modules/
__pycache__/
*.pyc
*.pyo
*.pyd
venv/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Documentation
*.md
README*

# OS
.DS_Store
Thumbs.db
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
        
        # 检查并更新 package.json
        if package_json.exists():
            # 读取现有的 package.json
            import json
            try:
                with open(package_json, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # 不再自动添加 @bachai/ 作用域，保持用户原有的包名
                current_name = package_data.get('name', '')
                print(f"📝 保持原包名: {current_name}")
                
            except Exception as e:
                print(f"⚠️ 读取 package.json 失败: {e}")
        else:
            # 创建新的 package.json（带 @bachai/ 作用域）
            package_name = f"@bachai/{project_path.name.lower()}"
            package_data = {
                "name": package_name,
                "version": "1.0.0",
                "description": "",
                "main": "index.js",
                "scripts": {
                    "test": "echo \"No tests specified\" && exit 0",
                    "build": "echo \"No build step\""
                },
                "keywords": [],
                "author": "BACH Studio",
                "license": "MIT"
            }
            package_json.write_text(json.dumps(package_data, indent=2, ensure_ascii=False), encoding='utf-8')
            print(f"📝 创建 package.json: {package_name}")
    
    def _generate_pypi_pipeline(self, project_path: Path):
        """生成 PyPI Pipeline (GitHub Actions)"""
        workflow_dir = project_path / '.github' / 'workflows'
        workflow_dir.mkdir(parents=True, exist_ok=True)
        
        workflow_content = """name: Build and Publish to PyPI

on:
  push:
    tags:
      - 'v*'  # 在创建 v* tag 时触发
    branches:
      - main
      - master
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
        # 只在 tag 推送或手动触发时发布
        if: startsWith(github.ref, 'refs/tags/v') || github.event_name == 'workflow_dispatch'
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
      
      - name: Build completed
        if: "!startsWith(github.ref, 'refs/tags/v') && github.event_name != 'workflow_dispatch'"
        run: echo "✅ 构建完成！要发布到 PyPI，请创建 v* tag 或手动触发 workflow"
"""
        
        workflow_file = workflow_dir / 'pypi-publish.yml'
        workflow_file.write_text(workflow_content, encoding='utf-8')
        
        # 生成 setup.py（如果不存在）
        setup_py = project_path / 'setup.py'
        if not setup_py.exists():
            # 使用原始项目名作为包名，不自动添加前缀
            package_name = project_path.name.lower()
            setup_content = f'''"""Setup script for {project_path.name}"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="{package_name}",
    version="1.0.0",
    author="BACH Studio",
    author_email="contact@bachstudio.com",
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
            # 使用原始项目名作为包名，不自动添加前缀
            package_name = project_path.name.lower()
            toml_content = f'''[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{package_name}"
version = "1.0.0"
description = "A short description"
readme = "README.md"
requires-python = ">=3.7"
license = {{text = "MIT"}}
authors = [
    {{name = "BACH Studio", email = "contact@bachstudio.com"}}
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

