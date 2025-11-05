# RepoFlow 🚀

> 自动化项目发布工具 - 一键发布到 GitHub + 自动发布到 PyPI/NPM

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 核心功能

- 🎨 **可视化 GUI** - 极简界面，无需命令行
- 🔐 **安全检查** - 自动扫描敏感信息（API Key、密码等）
- 📦 **自动发布** - 支持 PyPI、NPM、Docker Hub
- 🏷️ **自动 Tag** - 自动创建版本 Tag 触发 GitHub Actions
- 🔄 **智能检测** - 自动识别项目类型和版本号

---

## 🚀 快速开始

### 方式 1：运行打包的 EXE（推荐，无需 Python）

**下载并运行：**
```
1. 下载 RepoFlow.exe
2. 双击运行
3. 完成！
```

### 方式 2：从源码运行（开发者）

#### 安装
```bash
git clone https://github.com/BACH-AI-Tools/RepoFlow.git
cd RepoFlow
pip install -r requirements.txt
```

#### 启动 GUI
**Windows:**
```powershell
.\run-repoflow-gui.bat
```

**Linux/Mac:**
```bash
./run-repoflow-gui.sh
```

#### 打包成 EXE
```powershell
# 方法 1: 运行打包脚本（推荐）
.\build-exe.bat

# 方法 2: 直接运行
python build_exe.py

# 生成的文件在
dist\RepoFlow.exe
```

### 3. 配置 GitHub Token

第一次使用时：
1. 点击 GUI 中的 **"🔗 获取新 Token"** 按钮
2. 在打开的页面点击 **"Generate token"**
3. 复制 token 并粘贴到 GUI 输入框
4. 点击 **"💾 保存"**

### 4. 发布项目

1. **选择项目文件夹** - 点击"浏览"选择你的项目
2. **自动检测** - GUI 会自动检测项目类型和版本号
3. **配置选项**:
   - ✅ 默认勾选 "立即发布到 PyPI/NPM"
   - 📌 版本号自动填充（可修改）
4. **点击发布** - 一键完成！

---

## 📦 包命名规范

RepoFlow 会自动为你的包添加统一前缀，避免命名冲突：

| 平台 | 包名格式 | 示例 |
|------|---------|------|
| **PyPI** | `bachai-{项目名}` | `bachai-data-analysis-mcp` |
| **NPM** | `@bachai/{项目名}` | `@bachai/file-search-mcp` |

**安装示例：**
```bash
# Python
pip install bachai-your-project

# Node.js
npm install @bachai/your-project
```

---

## 🔐 组织 Secrets 配置（一次性）

在 GitHub 组织设置中配置以下 Secrets（根据项目类型）：

访问：`https://github.com/organizations/你的组织/settings/secrets/actions`

| 项目类型 | 需要的 Secrets |
|---------|---------------|
| **Python** | `PYPI_TOKEN` |
| **Node.js** | `NPM_TOKEN` |
| **Docker** | `DOCKERHUB_USERNAME` + `DOCKERHUB_TOKEN` |

**配置一次，所有仓库通用！** ✨

### 如何获取 Token？

- **PyPI Token**: https://pypi.org/manage/account/token/
- **NPM Token**: https://www.npmjs.com/settings/你的用户名/tokens
- **DockerHub Token**: https://hub.docker.com/settings/security

---

## 🎯 工作流程

```
选择项目文件夹
    ↓
GUI 自动检测项目类型和版本号
    ↓
勾选"立即发布"（默认已勾选）
    ↓
点击"一键发布"
    ↓
✅ 扫描敏感信息
✅ 创建 GitHub 仓库
✅ 生成 CI/CD Pipeline
✅ 推送代码到 GitHub
✅ 自动创建并推送 Tag (v{版本号})
✅ 触发 GitHub Actions
✅ 自动发布到 PyPI/NPM
    ↓
完成！🎉
```

---

## 📋 安全检查

RepoFlow 会自动检查以下内容：

| 检查项 | 说明 | 不通过时 |
|--------|------|----------|
| ✅ **README.md** | 必须包含 README | 拒绝发布 |
| 🔍 **敏感信息** | API Key、密码、Token 等 | 拒绝发布 |
| 📦 **包名冲突** | 自动添加前缀 | 自动处理 |

---

## 🛠️ 命令行使用（高级）

### 基础命令

```bash
# 配置
python repoflow.py config

# 自动检测并发布
python repoflow.py init --repo 仓库名 --pipeline auto

# 指定 Pipeline 发布
python repoflow.py init --repo 仓库名 --pipeline pypi
```

### 示例

```bash
# 发布 Python 项目到 PyPI
python repoflow.py init --repo my-python-package --pipeline pypi

# 发布 Node.js 项目到 NPM
python repoflow.py init --repo my-node-package --pipeline npm

# 发布 Docker 镜像
python repoflow.py init --repo my-app --pipeline docker
```

更多命令：
```bash
python repoflow.py --help
```

---

## 📁 项目结构

```
RepoFlow/
├── repoflow_gui.py         # GUI 主程序
├── repoflow.py             # CLI 主程序
├── src/                    # 核心模块
│   ├── github_manager.py   # GitHub API
│   ├── git_manager.py      # Git 操作
│   ├── pipeline_generator.py # CI/CD 生成
│   ├── secret_scanner.py   # 敏感信息扫描
│   └── ...
├── requirements.txt        # Python 依赖
└── README.md              # 本文档
```

---

## 🎓 使用技巧

### 1. 版本号管理

遵循[语义化版本](https://semver.org/lang/zh-CN/)规范：

- `1.0.0` - 首次发布
- `1.0.1` - Bug 修复
- `1.1.0` - 新功能（兼容）
- `2.0.0` - 重大更新（不兼容）

### 2. Tag 已存在怎么办？

如果 Tag 已存在，GUI 会提示你：

**方案 1：修改版本号**（推荐）
```
1.0.0 → 1.0.1
```

**方案 2：删除旧 Tag**
```bash
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

### 3. 发布失败排查

1. **检查 Secrets** - 确保在组织中配置了正确的 Token
2. **检查包名** - PyPI/NPM 上包名必须唯一
3. **查看 Actions** - 访问 GitHub Actions 查看详细日志

---

## ❓ 常见问题

### Q: 推送时弹出多次 Git 认证窗口？

A: 这是正常的，一次认证用于推送代码，一次用于推送 Tag。

### Q: 如何更新已发布的包？

A: 修改版本号，然后重新发布即可：
```
1.0.0 → 1.0.1
```

### Q: 支持哪些项目类型？

A: 
- ✅ Python (PyPI)
- ✅ Node.js (NPM)
- ✅ Docker
- ✅ C# / .NET (NuGet) - 开发中

### Q: 可以发布到私有仓库吗？

A: 可以！勾选"创建为私有仓库"选项即可。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🔗 相关链接

- [GitHub Actions 文档](https://docs.github.com/actions)
- [PyPI 发布指南](https://packaging.python.org/tutorials/packaging-projects/)
- [NPM 发布指南](https://docs.npmjs.com/packages-and-modules/contributing-packages-to-the-registry)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

---

---

## 📦 打包成可执行文件

### 快速打包

**Windows:**
```powershell
# 双击运行
build-exe.bat

# 或使用 PowerShell
.\build-exe.ps1
```

**macOS/Linux:**
```bash
# 运行构建脚本
./build-exe.sh
```

**生成的文件：**
- Windows: `dist/RepoFlow.exe` (~20 MB)
- macOS: `dist/RepoFlow` (~25 MB)
- Linux: `dist/RepoFlow` (~25 MB)

**特点：**
- ✅ 独立可执行文件
- ✅ 无需 Python 环境
- ✅ 包含所有依赖

### 自动构建（GitHub Actions）

每次推送 tag 时自动构建三个平台的版本：

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

GitHub Actions 会自动：
1. ✅ 构建 Windows/macOS/Linux 版本
2. ✅ 创建 GitHub Release
3. ✅ 上传所有平台的可执行文件

**下载地址：**
```
https://github.com/BACH-AI-Tools/RepoFlow/releases
```

### 分发给用户

只需要把对应平台的文件给用户：

**Windows:**
- 发送 `RepoFlow.exe`
- 用户双击运行

**macOS/Linux:**
- 发送 `RepoFlow`
- 用户运行：
  ```bash
  chmod +x RepoFlow
  ./RepoFlow
  ```

**就这么简单！** 🎉

---

**Made with ❤️ by BACH Studio**
