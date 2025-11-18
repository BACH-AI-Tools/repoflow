# 🏭 MCP工厂

> **一键自动化MCP发布平台** - 从本地项目到完整测试报告，3分钟搞定

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## 🎯 核心功能

### 🏭 一键生产线
选择项目文件夹 → 点击开始 → 3分钟后完成

### ✨ 自动完成
- ✅ **智能检测** - 读取完整 README.md，检测项目信息和环境变量
- ✅ **环境变量配置** - 自动检测并弹窗让用户填写配置说明
- ✅ **GitHub发布** - 创建仓库、推送代码
- ✅ **PyPI/NPM发布** - 自动触发CI/CD（PyPI 和 NPM 都支持完整 README）
- ✅ **即梦 Logo** - 基于完整 README 描述生成专业 Logo
- ✅ **EMCP注册** - 发布到EMCP平台（包含环境变量配置）
- ✅ **MCP测试** - 测试所有工具
- ✅ **Agent测试** - 创建Agent并测试
- ✅ **对话测试** - SignalR自动化对话测试
- ✅ **生成报告** - HTML报告 + CDN链接

### 🎨 流程可视化
- 📊 树状步骤展示
- 🎯 实时进度更新
- 📋 详细日志输出
- ⚠️ 智能错误处理

---

## 🚀 快速开始

### 📦 安装依赖

```bash
# 克隆项目
git clone https://github.com/BACH-AI-Tools/RepoFlow.git
cd RepoFlow

# 安装依赖
pip install -r requirements.txt
```

### 🎨 启动 GUI

**🍎 Apple 风格界面（推荐，优雅简洁）：**
```powershell
.\run-mcp-factory.bat
```

三个界面对比：

| 界面 | 视觉风格 | 特点 | 适用场景 |
|-----|---------|------|---------|
| **Apple 风格界面** 🍎⭐ | 浅色主题 + Apple 设计语言<br>简洁优雅<br>留白设计 | • 🎨 Apple 设计语言<br>• 浅色系配色 (#F5F5F7)<br>• 系统蓝强调色 (#007AFF)<br>• SF Pro 字体<br>• 白色卡片设计<br>• 干净的交互效果<br>• 完整的流程追踪 | 🔥 **强烈推荐**<br>追求简洁优雅<br>MCP 完整流程 |
| **Ultra 界面** | 深色主题 + 荧光色<br>Glassmorphism 毛玻璃<br>发光动画效果 | • 2024设计趋势<br>• 荧光青/粉色系<br>• 发光按钮<br>• 流畅动画 | 追求炫酷视觉体验<br>（仅基础功能） |
| **现代化界面** | Material Design 3<br>浅色/紫色系 | • 简洁美观<br>• 圆角卡片<br>• 悬停效果 | 基础发布功能 |

---

### 首次使用配置

1. **点击 ⚙️ 设置**
2. **配置必要信息**：
   - GitHub Token
   - EMCP账号（手机号，验证码自动生成）
   - Azure OpenAI（可选）
3. **保存配置**

### 日常使用

1. 选择项目文件夹（自动检测信息）
2. 点击"🏭 开始生产"
3. 等待3-5分钟
4. 完成！

---

## 📦 打包成 EXE
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

## 🔐 安全保护

### GitHub 原生安全功能（推荐）✨

RepoFlow 创建的仓库会自动配置 GitHub 安全功能：

| 功能 | 说明 | 公开仓库 | 私有仓库 |
|------|------|---------|---------|
| ✅ **Vulnerability Alerts** | 依赖漏洞警报 | 🆓 自动启用 | 🆓 自动启用 |
| ✅ **Secret Scanning** | 检测敏感信息 | 🆓 免费 | 💰 需 Advanced Security |
| ✅ **Push Protection** | 阻止敏感推送 | 🆓 免费 | 💰 需 Advanced Security |
| ✅ **Branch Protection** | 分支保护规则 | 🆓 自动配置 | 🆓 自动配置 |

**推荐：发布到公开仓库，免费享受所有安全功能！** 🎁

### 本地检查

| 检查项 | 说明 | 不通过时 |
|--------|------|----------|
| ✅ **README.md** | 必须包含 README | 拒绝发布 |
| 📦 **包名冲突** | 自动添加前缀 | 自动处理 |

### 为什么使用 GitHub 原生保护？

| 对比项 | 本地扫描 | GitHub Push Protection |
|--------|---------|----------------------|
| **准确性** | ❌ 误报较多 | ✅ 高精度（GitHub 维护）|
| **覆盖率** | ❌ 有限模式 | ✅ 200+ 种密钥类型 |
| **实时性** | ❌ 可绕过 | ✅ 强制执行 |
| **维护** | ❌ 需要自己更新 | ✅ GitHub 自动更新 |

**推荐配置：** 在组织中启用 GitHub Advanced Security，详见 [安全设置指南](docs/GitHub安全设置指南.md)

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

## 📁 核心文件

```
MCP工厂/
├── mcp_factory_gui.py ⭐          # 主程序
├── settings_window.py            # 设置窗口
├── repoflow.py                   # CLI版本
├── run-mcp-factory.bat          # 启动脚本
├── src/                          # 核心模块
│   ├── workflow_executor.py     # 工作流执行器
│   ├── unified_config_manager.py # 配置管理
│   ├── github_manager.py        # GitHub管理
│   ├── git_manager.py           # Git操作
│   ├── emcp_manager.py          # EMCP管理
│   ├── mcp_tester.py            # MCP测试
│   ├── agent_tester.py          # Agent测试
│   ├── signalr_chat_tester.py   # 对话测试
│   └── ... 更多模块
├── requirements.txt             # 依赖
└── README.md                    # 本文档
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

## 📚 配置

- 配置文件模板: `config_template.json`
- 配置文件位置: `~/.repoflow/config.json`
- 技术文档: `docs/emcpflow/`

---

## 🔗 相关平台

### RepoFlow
- [GitHub](https://github.com)
- [PyPI](https://pypi.org)
- [NPM](https://www.npmjs.com)
- [Docker Hub](https://hub.docker.com)

### EMCPFlow
- [EMCP 平台（测试）](https://sit-emcp.kaleido.guru)
- [EMCP 平台（正式）](https://emcp.kaleido.guru)
- [Agent 平台](https://v5.kaleido.guru)
- [即梦 AI](https://jimeng.jianying.com/)

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境设置
```bash
# 克隆项目
git clone https://github.com/BACH-AI-Tools/RepoFlow.git
cd RepoFlow

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements.txt
```

### 代码结构
- `src/` - 核心模块（请保持模块化和可测试性）
- `tests/` - 测试文件（请为新功能添加测试）
- `docs/` - 文档（请更新相关文档）

---

## 🎉 更新日志

### v3.0.0 - MCP工厂（2025-11-07）
- ✅ 完整的自动化流程（GitHub → EMCP → 测试）
- ✅ 流程化步骤展示
- ✅ 详细日志输出
- ✅ 真实执行所有功能

---

**Made with ❤️ by BACH Studio (巴赫工作室)**
