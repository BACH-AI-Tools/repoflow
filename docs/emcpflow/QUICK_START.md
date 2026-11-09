# EMCPFlow 快速开始 🚀

## 📦 安装

```bash
cd E:\code\EMCPFlow
pip install -r requirements.txt
```

## 🚀 运行

### Windows
```bash
run.bat
```

或者
```bash
python emcpflow_gui.py
```

## 📋 使用步骤

### 1. 登录 EMCP

- 手机号：`YOUR_PHONE_NUMBER`
- 验证码：`11202505`
- 点击"登录"

### 2. 选择 MCP 项目

点击"浏览"选择你的 MCP 项目文件夹，例如：
- `E:\code\test_mcp_publish\data-analysis-mcp` (PyPI)
- `E:\code\test_mcp_publish\file-search-mcp` (NPM)

### 3. 自动填充

EMCPFlow 会自动：
- 检测项目类型
- 读取包名
- 生成启动命令
- 填充模板信息

### 4. 发布

检查信息无误后，点击"发布到 EMCP"

## 🎯 示例

### 发布 PyPI 包

```
项目路径: E:\code\test_mcp_publish\data-analysis-mcp
类型: PyPI (自动检测)
包名: bachai-data-analysis-mcp
命令: python -m bachai_data_analysis_mcp
路由: /data-analysis
```

### 发布 NPM 包

```
项目路径: E:\code\test_mcp_publish\file-search-mcp
类型: NPM (自动检测)
包名: @bachai/file-search-mcp
命令: @bachai/file-search-mcp
路由: /file-search
```

## 📦 打包成 EXE

```bash
build.bat
```

生成的文件：`dist\EMCPFlow.exe`

## ✅ 完成

发布成功后，访问：
```
https://sit-emcp.kaleido.guru
```

查看你发布的 MCP！



