# RepoFlow 使用示例

## 场景 1: 发布 Python 项目到 PyPI

```bash
# 1. 配置 GitHub Token
python repoflow.py config

# 2. 在项目目录中运行完整流程
cd /path/to/your/python/project
python /path/to/repoflow.py init --org BACH-AI-Tools --repo my-awesome-package --pipeline pypi

# 3. 在 GitHub 仓库设置中添加 PyPI Token
# Settings -> Secrets and variables -> Actions -> New repository secret
# Name: PYPI_TOKEN
# Value: your_pypi_token

# 4. 创建版本标签并推送以触发发布
git tag v1.0.0
git push origin v1.0.0
```

## 场景 2: 发布 Docker 应用

```bash
# 1. 在项目目录中生成 Docker Pipeline
cd /path/to/your/docker/project
python /path/to/repoflow.py init --org BACH-AI-Tools --repo my-docker-app --pipeline docker

# 2. 在 GitHub 仓库设置中添加 DockerHub 凭证
# Secrets:
#   - DOCKERHUB_USERNAME: your_dockerhub_username
#   - DOCKERHUB_TOKEN: your_dockerhub_access_token

# 3. 推送代码，自动触发构建
git push origin main
```

## 场景 3: 发布 NPM 包

```bash
# 1. 初始化项目
cd /path/to/your/npm/package
python /path/to/repoflow.py init --org BACH-AI-Tools --repo my-npm-package --pipeline npm

# 2. 配置 NPM Token
# 在 GitHub 仓库设置中添加:
# Name: NPM_TOKEN
# Value: your_npm_token

# 3. 发布新版本
npm version patch  # 或 minor, major
git push origin main --tags
```

## 场景 4: 仅扫描敏感信息

```bash
# 在推送代码前检查敏感信息
cd /path/to/your/project
python /path/to/repoflow.py scan

# 如果发现敏感信息，添加到 .gitignore 或使用环境变量
```

## 场景 5: 分步执行

如果你想更多控制，可以分步执行：

```bash
# 步骤 1: 扫描敏感信息
python /path/to/repoflow.py scan

# 步骤 2: 创建 GitHub 仓库（手动或使用 GitHub CLI）
gh repo create BACH-AI-Tools/my-project --public

# 步骤 3: 生成 Pipeline 配置
python /path/to/repoflow.py pipeline --type docker

# 步骤 4: 手动推送
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/BACH-AI-Tools/my-project.git
git push -u origin main
```

## 配置多个项目类型的 Pipeline

```bash
# 生成所有类型的 Pipeline
python /path/to/repoflow.py init --org BACH-AI-Tools --repo multi-platform-app --pipeline all
```

## 高级配置

### 自定义 .repoflow/config.json

```json
{
  "github_token": "ghp_xxxxxxxxxxxx",
  "default_org": "BACH-AI-Tools",
  "dockerhub_username": "myusername",
  "npm_registry": "https://registry.npmjs.org",
  "auto_scan": true,
  "default_branch": "main",
  "private_repos": false
}
```

## 故障排除

### GitHub Token 权限

确保你的 GitHub Token 具有以下权限：
- `repo` (完整仓库访问)
- `workflow` (更新 GitHub Actions 工作流)
- `write:packages` (发布包)

### DockerHub Token

1. 登录 DockerHub
2. Account Settings -> Security -> New Access Token
3. 选择 Read, Write, Delete 权限

### NPM Token

```bash
npm login
npm token create
```

### PyPI Token

1. 登录 PyPI
2. Account settings -> API tokens -> Add API token
3. 选择 Scope: Entire account 或特定项目

