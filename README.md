# RepoFlow 🚀

> 一个强大的自动化工具，用于简化项目从本地到 GitHub 发布的完整流程

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 核心功能

- ✅ **Git 全自动化** - 自动 commit、push，带重试机制
- ✅ **GitHub 仓库创建** - 一键创建并配置仓库
- ✅ **Secrets 自动设置** - 加密设置 Docker/PyPI/NPM Token
- ✅ **项目类型检测** - 智能识别 Python/Node.js/C# 等
- ✅ **敏感信息扫描** - 防止泄露 API Key、密码
- ✅ **本地立即部署** - Docker/PyPI 本地构建推送
- ✅ **PyPI 自动版本** - 根据 commit 自动递增版本号

---

## 📦 支持的发布目标

| 目标 | 语言要求 | 适用场景 | 本地发布 | 自动标签 | 每次Push构建 |
|------|---------|---------|---------|---------|------------|
| **Docker Hub** 🐳 | ✅ 任何语言 | 应用程序/服务 | ✅ | ✅ (main/sha) | ✅ |
| **PyPI** 📦 | ❌ 仅 Python | Python 包/库 | ✅ | ✅ (自动版本) | ✅ |
| **NPM** 📦 | ❌ 仅 Node.js | JS/TS 包/库 | 计划中 | ✅ (自动版本) | ✅ |

**说明：**
- **Docker**: 每次 push 自动构建，生成 `main`、`sha-xxx` 等标签
- **PyPI**: 根据 commit message 自动递增版本号并发布
- **NPM**: 根据 commit message 自动打标签并发布

---

## ⚡ 5分钟快速开始

### 1️⃣ 安装

**Windows:**
```powershell
.\install.ps1
```

**Linux/Mac:**
```bash
chmod +x install.sh && ./install.sh
```

**手动安装:**
```bash
pip install -r requirements.txt
```

### 2️⃣ 配置

```bash
python repoflow.py config
```

输入：
- **GitHub Token**: 访问 https://github.com/settings/tokens/new
  - 权限：`repo`, `workflow`, `write:packages`
- **默认组织名**: 如 `BACH-AI-Tools`
- **DockerHub 用户名**: (可选)

### 3️⃣ 发布项目

```bash
# 方式 1: 在项目目录中运行
cd /path/to/your/project
python /path/to/RepoFlow/repoflow.py init --repo your-project

# 方式 2: 指定项目路径（推荐！）
python repoflow.py init \
  --path /path/to/your/project \
  --repo your-project \
  --pipeline docker \
  --deploy-method both \
  --setup-secrets
```

**🎉 就这么简单！**

---

## 📚 完整命令参考

### 核心命令

```bash
# 检测项目类型
python repoflow.py detect --path /path/to/project

# 初始化发布（推荐带 --path）
python repoflow.py init \
  --path /path/to/project \
  --repo myapp

# 完整参数
python repoflow.py init \
  --path /path/to/project \
  --org BACH-AI-Tools \
  --repo myapp \
  --pipeline docker \
  --deploy-method both \
  --setup-secrets

# 扫描敏感信息
python repoflow.py scan --path /path/to/project

# 生成 Pipeline 配置
python repoflow.py pipeline --type docker --path /path/to/project
```

### 本地发布命令

```bash
# Docker 本地构建推送
python repoflow.py docker --image username/repo --tag v1.0.0

# PyPI 本地构建发布
python repoflow.py pypi --token pypi-xxx

# 仅构建不推送
python repoflow.py docker --image username/repo --build-only
python repoflow.py pypi --build-only
```

---

## 🎯 不同项目类型使用指南

### Python 项目（库/包）
```bash
python repoflow.py init --repo my-python-lib --pipeline pypi --setup-secrets
```
**自动版本管理：**
```bash
git commit -m "feat: add new API #minor"  # 1.0.0 → 1.1.0
git commit -m "fix: bug fix #patch"       # 1.0.0 → 1.0.1
git push  # 自动发布到 PyPI
```

### Python 项目（应用）
```bash
python repoflow.py init --repo my-flask-app --pipeline docker --deploy-method both
```

### Node.js 项目（库/包）
```bash
python repoflow.py init --repo my-js-lib --pipeline npm --setup-secrets
# 手动更新 package.json 版本，打 tag 发布
```

### C#/Java/Go 项目（应用）
```bash
python repoflow.py init --repo myapp --pipeline docker --deploy-method both
# 任何语言都可以用 Docker！
```

---

## 🔧 部署方式选择

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| **workflow** | GitHub Actions 自动化（默认） | 长期维护项目 |
| **local** | 本地立即构建推送 | 快速测试 |
| **both** | 两者都要（推荐！） | 完整 DevOps 体验 |

**示例：**
```bash
--deploy-method both  # 立即部署 + 持续集成
```

---

## 🎊 PyPI 自动版本管理

**Commit Message 规范：**

| 前缀 | 版本递增 | 示例 |
|------|---------|------|
| `feat: ... #minor` | 1.0.0 → **1.1**.0 | 新功能 |
| `fix: ... #patch` | 1.0.0 → 1.0.**1** | Bug修复 |
| `BREAKING: ... #major` | 1.0.0 → **2**.0.0 | 破坏性更改 |
| `docs: ... #none` | 不变 | 文档更新 |

**使用：**
```bash
git commit -m "feat: add user authentication #minor"
git push
# GitHub Actions 自动：递增版本 → 创建标签 → 发布到 PyPI
```

---

## 🔑 所需 Token

| Token | 用途 | 获取地址 |
|-------|------|---------|
| **GitHub Token** | 创建仓库、设置 Secrets | https://github.com/settings/tokens |
| **Docker Hub Token** | 推送镜像 | https://hub.docker.com/settings/security |
| **PyPI Token** | 发布 Python 包 | https://pypi.org/manage/account/token/ |
| **NPM Token** | 发布 Node.js 包 | https://www.npmjs.com/settings/tokens |

---

## 💡 常见场景

### 场景 1：发布 Python 库到 PyPI
```bash
# 在任何地方运行（指定项目路径）
python repoflow.py init \
  --path E:\code\my-awesome-lib \
  --repo awesome-lib \
  --pipeline pypi \
  --setup-secrets

# 后续开发（在项目目录中）
cd E:\code\my-awesome-lib
git commit -m "feat: add cool feature #minor"
git push  # 自动发布
```

### 场景 2：发布 Docker 应用（任何语言）
```bash
# 指定项目路径
python repoflow.py init \
  --path E:\code\my-app \
  --repo my-app \
  --pipeline docker \
  --deploy-method both \
  --setup-secrets

# 立即可用！镜像已推送到 Docker Hub
# 后续 push 也会自动构建
```

### 场景 3：发布 Node.js 包到 NPM
```bash
# 指定项目路径
python repoflow.py init \
  --path E:\code\my-js-package \
  --repo my-package \
  --pipeline npm \
  --setup-secrets

# 发布新版本（在项目目录中）
cd E:\code\my-js-package
git commit -m "feat: new feature #minor"
git push  # 自动打标签并发布
```

### 场景 4：多平台发布
```bash
# 指定项目路径
python repoflow.py init \
  --path E:\code\full-stack-project \
  --repo fullstack \
  --pipeline all \
  --deploy-method both \
  --setup-secrets
# 同时配置 Docker + PyPI + NPM
```

---

## 🚨 项目类型验证

RepoFlow 会自动验证 Pipeline 是否匹配：

**❌ 错误示例：**
```bash
# C# 项目选择 PyPI
python repoflow.py init --repo CSharpApp --pipeline pypi
```
**输出：**
```
❌ PyPI 只能发布 Python 包！
   当前项目不是 Python 项目
   建议：使用 --pipeline docker
```

**✅ 正确示例：**
```bash
# C# 项目选择 Docker
python repoflow.py init --repo CSharpApp --pipeline docker
```
**输出：**
```
✅ 任何项目都可以使用 Docker！
```

---

## 🔧 高级功能

### 自动检测项目类型
```bash
python repoflow.py detect
```

### 本地 Docker 构建
```bash
# 仅构建
python repoflow.py docker --image username/repo --build-only

# 构建并推送
python repoflow.py docker --image username/repo --tag v1.0.0
```

### 本地 PyPI 发布
```bash
# 构建并上传
python repoflow.py pypi --token pypi-xxx

# 仅构建
python repoflow.py pypi --build-only
```

---

## 🛠️ 技术栈

- **Python 3.7+**
- **依赖**: Click, Rich, PyGithub, GitPython, PyNaCl
- **Git** - 版本控制
- **Docker** (可选) - 本地构建

---

## 📖 完整文档

- **英文文档**: [README_EN.md](README_EN.md)
- **详细教程**: [GET_STARTED.md](GET_STARTED.md)

---

## 🆘 常见问题

### Q: 如何获取 GitHub Token?
访问 https://github.com/settings/tokens/new，勾选 `repo`, `workflow`, `write:packages` 权限。

### Q: 支持哪些项目类型？
- ✅ Python → PyPI + Docker
- ✅ Node.js → NPM + Docker  
- ✅ C#/Java/Go/Rust/任何语言 → Docker

### Q: 如何修复网络连接问题？
```bash
# 方法 1: 配置代理
git config --global http.proxy http://127.0.0.1:7890

# 方法 2: 使用 SSH（推荐）
ssh-keygen -t rsa -b 4096
# 添加公钥到 https://github.com/settings/keys
```

### Q: 虚拟环境创建失败？
```bash
# 删除旧的 venv
Remove-Item -Recurse -Force .\venv

# 重新创建
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 🎯 最佳实践

1. ✅ 使用虚拟环境隔离依赖
2. ✅ 运行前先 `repoflow scan` 检查敏感信息
3. ✅ 使用 `--deploy-method both` 获得最佳体验
4. ✅ PyPI 项目遵循 Commit Message 规范
5. ✅ 定期更新 Token

---

## 📝 示例项目

```bash
# 克隆示例
git clone https://github.com/BACH-AI-Tools/testrepoflow
cd testrepoflow

# 查看已配置的 workflows
ls .github/workflows/
# docker-publish.yml  # Docker 自动构建
# pypi-publish.yml    # PyPI 自动发布（含自动版本）
# npm-publish.yml     # NPM 自动发布
```

---

## 💻 快速启动脚本

项目包含便捷启动脚本：

**Windows:**
```powershell
.\run-repoflow.ps1 init --repo myapp --pipeline docker
```

**Linux/Mac:**
```bash
./run-repoflow.sh init --repo myapp --pipeline docker
```

---

## 🌟 特色功能

### 1. 完全自动化的 PyPI 发布
```bash
git commit -m "feat: awesome feature #minor"
git push
# 自动：版本递增 → 打标签 → 发布到 PyPI
```

### 2. 灵活的部署方式
```bash
--deploy-method both
# 立即本地部署 + GitHub Actions 持续集成
```

### 3. 智能项目检测
```bash
python repoflow.py detect
# 自动识别项目类型并推荐合适的 Pipeline
```

### 4. 一键设置 Secrets
```bash
--setup-secrets
# 自动加密设置所有必要的 GitHub Secrets
```

---

## 📄 许可证

MIT License - 完全开源免费

---

## 🔗 相关链接

- **GitHub**: https://github.com/BACH-AI-Tools/RepoFlow
- **问题反馈**: https://github.com/BACH-AI-Tools/RepoFlow/issues

---

**让发布变得简单！** ✨ **享受自动化的便利！** 🎊
