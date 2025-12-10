# MCP工厂 (MCP Factory)

**一站式MCP服务器生产与发布平台**

将第三方API自动转换为MCP服务器，并批量发布到各大平台。

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## ✨ 功能特性

### 🔍 API爬取转换
- **RapidAPI** - 自动爬取RapidAPI平台的API，生成MCP服务器
- **百度API** - 自动化购买和提取百度API平台的免费API
- **OpenAPI/Swagger** - 支持任意OpenAPI 3.0+/Swagger 2.0规范转换

### 🚀 MCP发布流水线
- **GitHub** - 发布到GitHub组织，自动添加CI/CD工作流
- **PyPI/NPM** - 发布到官方包源，支持TestPyPI测试
- **EMCP** - 发布到EMCP平台，自动生成Logo和测试

### 🌐 第三方平台发布
- **LobeHub** - 批量提交到LobeHub MCP市场
- **mcp.so** - 批量提交到mcp.so平台
- 更多平台持续支持中...

### 📊 统一管理
- **配置中心** - 所有配置集中管理
- **实时日志** - 所有操作实时日志展示
- **批量处理** - 支持批量爬取、批量发布

---

## 🚀 快速开始

### 方式一：Web界面（推荐）

```bash
cd mcp_factory_web
pip install -r requirements.txt
python app.py
```

然后访问 http://localhost:5000

### 方式二：命令行

```bash
# 安装依赖
pip install -e .

# 批量发布MCP
python batch_publish_folder.py --input ./mcps --org BACH-AI-Tools
```

---

## 📁 项目结构

```
repoflow/
├── mcp_factory_web/          # 🌐 Web界面（主入口）
│   ├── app.py                # Flask应用
│   ├── modules/              # 功能模块
│   │   ├── api_crawler.py    # API爬取
│   │   ├── mcp_publisher.py  # MCP发布
│   │   ├── platform_publisher.py  # 平台发布
│   │   ├── config.py         # 配置管理
│   │   └── logger.py         # 日志管理
│   ├── templates/            # HTML模板
│   └── static/               # CSS/JS静态文件
│
├── src/                      # 核心模块
│   ├── github_manager.py     # GitHub操作
│   ├── pypi_manager.py       # PyPI发布
│   ├── emcp_manager.py       # EMCP管理
│   ├── mcp_tester.py         # MCP测试
│   └── ...
│
├── batch_publish_folder.py   # 批量发布脚本
├── batch_mcp_factory.py      # 批量MCP工厂
└── templates/                # CI/CD模板
```

---

## ⚙️ 配置说明

所有配置集中在 `mcp_factory_web/config.json`，也可通过Web界面的配置中心修改。

### 主要配置项

| 配置路径 | 说明 | 默认值 |
|---------|------|--------|
| `github.org_name` | GitHub组织名 | BACH-AI-Tools |
| `github.add_workflows` | 添加CI/CD | true |
| `pypi.use_test_pypi` | 使用TestPyPI | true |
| `emcp.generate_logo` | 生成Logo | true |
| `crawler.rapidapi.use_selenium` | 使用Selenium | false |
| `mcp.default_transport` | 传输协议 | stdio |

---

## 📖 使用指南

### API爬取转换

1. 访问 **API爬取** 页面
2. 输入 RapidAPI URL 或上传 OpenAPI 文件
3. 点击 **开始爬取** 或 **转换为MCP**
4. 在 **已生成MCP** 列表中查看结果

### MCP发布

1. 访问 **MCP发布** 页面
2. 选择要发布的项目
3. 配置发布目标（GitHub/PyPI/EMCP）
4. 点击 **开始发布**
5. 在日志中查看详细进度

### 第三方平台发布

1. 访问 **平台发布** 页面
2. 选择目标平台（LobeHub/mcp.so）
3. 选择要提交的项目
4. 点击 **开始提交**

---

## 🔧 环境要求

- Python 3.10+
- Node.js 18+ (可选，用于TypeScript项目)
- Git
- GitHub CLI (`gh`) (可选，用于自动创建仓库)

### 安装依赖

```bash
# Web界面依赖
pip install flask flask-cors playwright

# 完整依赖
pip install -r requirements.txt

# 安装Playwright浏览器（用于自动化）
playwright install chromium
```

---

## 🤝 相关项目

- [APItoMCP](https://github.com/BACH-AI-Tools/api-to-mcp) - API转MCP核心库
- [FastMCP](https://fastmcp.wiki) - MCP框架

---

## 📝 许可证

MIT License

---

## 📮 联系方式

如有问题或建议，欢迎提交 Issue。

---

**Made with ❤️ by MCP Factory Team**
