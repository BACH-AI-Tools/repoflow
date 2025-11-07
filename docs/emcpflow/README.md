# EMCPFlow 🌐

> MCP 一键发布到 EMCP 平台 - 只需输入包地址，自动完成所有操作

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 新版特性

### 🎯 极简操作流程

**只需一个包地址，自动完成所有操作！**

1. ✅ **输入包地址** - PyPI/NPM/Docker Hub URL 或包名
2. ✅ **自动检测** - 自动识别包类型和获取包信息  
3. ✅ **AI生成** - 使用 Azure OpenAI 自动生成模板描述
4. ✅ **一键发布** - 自动发布到 EMCP 平台

### 🚀 核心功能

- 🎨 **极简 GUI** - 只有一个输入框，操作超简单
- 🔐 **自动登录** - 配置一次凭据，后续自动登录
- 🤖 **LLM 驱动** - Azure OpenAI (gpt-4o) 完全自动生成所有内容
- 🌍 **三语言支持** - LLM 直接生成中文简体/繁体/英文（准确度 99%）
- 🎯 **智能分类** - 从 API 获取真实分类，LLM 智能选择
- 📦 **多平台支持** - 支持 NPM (npx)、PyPI (uvx)、Deno、Docker
- 🌐 **API 驱动** - 动态获取分类、来源等配置（零硬编码）
- 🖼️ **Logo 上传** - 支持图片上传到 EMCP，可生成文字 Logo
- 🔄 **智能更新** - 自动判断创建或更新（避免重复）
- 🛠️ **AI 自动修复** - API 错误时，LLM 自动分析并修复参数，自动重试（最多3次）⭐

---

## 🚀 快速开始

### 方式一：直接运行（推荐）

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行简化版（推荐）
python emcpflow_simple_gui.py

# 3. 点击 [设置] 配置（仅首次）
#    - EMCP 手机号和验证码
#    - Azure OpenAI 配置（已提供）

# 4. 输入包地址，点击 [一键发布]
```

### 方式二：下载运行（无需 Python）

```
1. 下载 EMCPFlow.exe
2. 双击运行
3. 点击 [设置] 配置凭据（仅首次）
4. 输入包地址
5. 点击 [一键发布]
```

---

## ⚙️ 初始配置

### 1️⃣ 配置 EMCP 登录凭据（必需）

点击 `[设置]` 按钮，填写：

- **手机号**: 您的 EMCP 账号手机号
- **验证码**: 固定验证码（如 `11202505`）

配置后，工具会自动登录，无需每次手动输入。

### 2️⃣ 配置 Azure OpenAI（可选，推荐）

点击 `[设置]` 按钮，填写：

- **Endpoint**: 如 `https://jinderu.openai.azure.com`
- **API Key**: 您的 Azure OpenAI API Key
- **Deployment**: 部署名称（如 `gpt-4o`）

配置后，将使用 AI 自动生成更专业、吸引人的模板描述。

> 💡 **不配置 Azure OpenAI 也能使用**，将使用基础生成器自动生成模板信息。

### 3️⃣ 重要限制和特性

#### 路由前缀限制
- ⚠️ **路由前缀不能超过 10 个字符**
- 系统会自动截断并优化
- 例如：`data-analysis` → `data-analy`

#### 多语言支持（LLM 驱动）
- ✅ **LLM 直接生成三种语言**（简体、繁体、英文）
- ✅ 繁体中文由 LLM 生成（准确度 99%，不使用字典转换）
- ✅ 完整支持：中文简体 / 中文繁体 / 英文
- ✅ 专业翻译质量，符合各地用词习惯

#### 包类型支持
- ✅ **NPM** - package_type=1 (npx)
- ✅ **PyPI** - package_type=2 (uvx) - 使用现代化 uvx 工具
- ✅ **Deno** - package_type=3 (deno)
- ✅ **Docker** - package_type=4 (container)
- 📖 详见 [包类型说明.md](包类型说明.md)

#### Logo 功能
- ✅ 默认使用 EMCP 平台提供的默认 logo
- ✅ 系统会尝试从包信息中获取官方 logo
- ✅ 支持生成简单文字 logo 并自动上传
- ✅ 实现了图片上传到 EMCP 功能
- ⚙️ 可选：配置 DALL-E 生成个性化 logo（需要额外配置）
- 📖 详见 [LOGO_说明.md](LOGO_说明.md)

---

## 📖 使用说明

### 支持的输入格式

#### PyPI 包
```
# URL 格式
https://pypi.org/project/requests

# 或直接输入包名
requests
```

#### NPM 包
```
# URL 格式
https://www.npmjs.com/package/express

# 或直接输入包名
express
@scope/package-name
```

#### Docker 镜像
```
# URL 格式
https://hub.docker.com/r/nginx/nginx

# 或直接输入镜像名
nginx/nginx
username/image
```

### 发布流程

```
输入包地址 → 点击 [一键发布]
       ↓
步骤 1: 从包管理平台获取包信息
       ↓
步骤 2: AI 自动生成模板描述
       ↓
步骤 3: 构建 EMCP 模板数据
       ↓
步骤 4: 发布到 EMCP 平台
       ↓
    完成！🎉
```

---

## 🎯 使用示例

### 示例 1: 发布 PyPI 包

```
输入: https://pypi.org/project/requests
结果: 
  - 类型: PyPI
  - 包名: requests
  - 命令: python -m requests
  - 自动生成专业描述
  - 一键发布到 EMCP
```

### 示例 2: 发布 NPM 包

```
输入: express
结果:
  - 类型: NPM
  - 包名: express
  - 命令: express
  - 自动生成专业描述
  - 一键发布到 EMCP
```

### 示例 3: 发布 Docker 镜像

```
输入: nginx/nginx
结果:
  - 类型: Docker
  - 镜像: nginx/nginx
  - 自动生成专业描述
  - 一键发布到 EMCP
```

---

## 📂 项目结构

```
EMCPFlow/
├── emcpflow_simple_gui.py    # 简化版 GUI（推荐使用）
├── emcpflow_gui.py            # 完整版 GUI
├── emcp_manager.py            # EMCP 平台管理
├── package_fetcher.py         # 包信息获取器（新）
├── ai_generator.py            # AI 模板生成器（新）
├── config_manager.py          # 配置管理器
├── project_detector.py        # 本地项目检测器
├── requirements.txt           # 依赖列表
└── README.md                  # 说明文档
```

---

## 🔗 EMCP 平台

- **测试环境**: https://sit-emcp.kaleido.guru
- **正式环境**: https://emcp.kaleido.guru

---

## 🛠️ 技术栈

- **GUI**: Tkinter
- **HTTP**: Requests
- **AI**: Azure OpenAI (可选)
- **API**: PyPI / NPM / Docker Hub

---

## 📝 配置文件位置

配置文件存储在用户目录：

```
Windows: C:\Users\<用户名>\.emcpflow\config.json
Linux/Mac: ~/.emcpflow/config.json
```

包含：
- EMCP 登录凭据
- Azure OpenAI 配置
- 登录 Session

---

## ❓ 常见问题

### Q: 首次使用需要配置什么？

A: 只需在 `[设置]` 中配置 EMCP 手机号和验证码即可。Azure OpenAI 是可选的。

### Q: 不配置 Azure OpenAI 能用吗？

A: 可以！不配置 AI 时，会使用基础生成器自动从包信息生成模板，只是描述可能不如 AI 生成的专业。

### Q: 支持哪些包管理平台？

A: 支持 PyPI、NPM、Docker Hub。可以输入完整 URL 或直接输入包名。

### Q: 发布失败怎么办？

A: 检查日志输出，常见原因：
- 未登录（配置 EMCP 凭据）
- 包名不存在
- 网络连接问题
- 包已发布过

---

## 🎨 新旧版本对比

| 功能 | 旧版本 | 新版本 |
|-----|-------|--------|
| **输入方式** | 选择本地文件夹 | 输入包地址 |
| **登录方式** | 每次手动登录 | 配置后自动登录 |
| **模板生成** | 手动填写 | AI 自动生成 |
| **包信息** | 从本地提取 | 从官方源获取 |
| **操作步骤** | 5+ 步骤 | 1 步搞定 |

---

## 📚 更多文档

### 核心程序
- `emcpflow_simple_gui.py` - 简化版主程序（推荐）
- `emcpflow_gui.py` - 完整版程序（适合本地项目）

### 核心模块
- `package_fetcher.py` - 包信息获取器源码
- `ai_generator.py` - AI 生成器源码
- `logo_generator.py` - Logo 生成器源码

### 文档
- [QUICK_START_SIMPLE.md](QUICK_START_SIMPLE.md) - 快速开始指南
- [使用说明.md](使用说明.md) - 详细使用说明
- [LOGO_说明.md](LOGO_说明.md) - Logo 功能说明
- [CHANGELOG.md](CHANGELOG.md) - 更新日志
- [CONFIG_EXAMPLE.json](CONFIG_EXAMPLE.json) - 配置示例

---

**Made with ❤️ by BACH Studio**



