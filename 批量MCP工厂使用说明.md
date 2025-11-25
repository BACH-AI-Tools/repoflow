# 🏭 批量 MCP 工厂使用说明

## 📋 简介

批量 MCP 工厂可以自动化处理多个 MCP 项目，执行完整的 **MCP 工厂发布流程**：

### 完整流程（12个步骤）

1. ✅ **扫描项目** - 检查敏感信息
2. ✅ **创建 GitHub 仓库** - 自动创建组织仓库
3. ✅ **生成 CI/CD Pipeline** - PyPI/NPM 自动发布
4. ✅ **推送代码** - 推送到 GitHub
5. ✅ **触发发布并等待完成** - 创建 Tag 触发 GitHub Actions，等待包发布
6. ✅ **获取包信息** - 从项目中提取包名、命令等
7. ✅ **AI 生成模板** - 生成多语言描述（或使用 README）
8. ✅ **生成 Logo** - 使用即梦 MCP 生成专业 Logo
9. ✅ **发布到 EMCP** - 创建或更新 EMCP 模板
10. ✅ **MCP 测试** - 测试所有 MCP 工具
11. ✅ **Agent 测试** - 创建 Agent 并绑定 MCP
12. ✅ **SignalR 对话测试** - 完整的对话测试

**环境变量 API_KEY 已预设为:** `c73d0eb842msh082900adbe7d22cp15a3e0jsn8156d94adb0d`

---

## 🚀 快速开始

### Windows 用户（推荐）

#### 方法 1：双击运行

```
双击 batch_mcp_factory.bat
输入你的 MCP 项目文件夹路径
确认继续
```

#### 方法 2：PowerShell

```powershell
.\batch_mcp_factory.ps1 -ProjectsDir "E:\mcp-projects"

# 只处理特定项目
.\batch_mcp_factory.ps1 -ProjectsDir "E:\mcp-projects" -Projects "1,3,5"
```

### Linux/Mac 用户

```bash
python batch_mcp_factory.py /path/to/mcp-projects

# 只处理特定项目
python batch_mcp_factory.py /path/to/mcp-projects --projects "1,3,5"
```

---

## 📖 详细使用说明

### 1. 准备工作

#### 确保已配置以下信息（在 `config.json` 中）

```json
{
  "github": {
    "token": "你的GitHub Token",
    "org_name": "你的组织名"
  },
  "pypi": {
    "token": "你的PyPI Token"
  },
  "npm": {
    "token": "你的NPM Token"
  },
  "emcp": {
    "phone_number": "你的EMCP手机号",
    "base_url": "https://sit-emcp.kaleido.guru"
  },
  "agent": {
    "phone_number": "你的Agent手机号",
    "base_url": "https://sit-agent.kaleido.guru"
  },
  "jimeng": {
    "enabled": true,
    "mcp_url": "即梦MCP地址",
    "emcp_key": "你的emcp-key",
    "emcp_usercode": "你的emcp-usercode"
  },
  "azure_openai": {
    "endpoint": "你的Azure OpenAI Endpoint",
    "api_key": "你的API Key",
    "deployment_name": "你的部署名称"
  }
}
```

#### 项目文件夹结构示例

```
E:\mcp-projects\
├── weather-mcp\
│   ├── src\
│   ├── setup.py 或 pyproject.toml
│   ├── requirements.txt
│   ├── README.md
│   └── mcp\
│       └── readme.md (可选，多语言描述)
│
├── translator-mcp\
│   ├── src\
│   ├── package.json
│   ├── README.md
│   └── mcp\
│       └── readme.md (可选)
│
└── database-mcp\
    └── ...
```

### 2. 运行批量处理

#### 交互模式（推荐新手）

```bash
# 双击 batch_mcp_factory.bat 或运行
python batch_mcp_factory.py
```

**提示：**

1. 输入 MCP 项目文件夹路径
2. 查看扫描到的项目列表
3. 选择处理所有项目或指定项目
4. 确认开始处理

#### 命令行模式（推荐高级用户）

```bash
# 处理所有项目
python batch_mcp_factory.py "E:\mcp-projects"

# 只处理项目 1, 3, 5
python batch_mcp_factory.py "E:\mcp-projects" --projects "1,3,5"
```

### 3. 处理过程

每个项目会依次执行 12 个步骤：

```
项目 [1/5]: weather-mcp
======================================================================
▶️ 步骤 1/12: 扫描项目
✅ 未发现敏感信息

▶️ 步骤 2/12: 创建 GitHub 仓库
✅ 仓库创建成功
🔗 仓库地址: https://github.com/BACH-AI-Tools/weather-mcp

▶️ 步骤 3/12: 生成 CI/CD Pipeline
✅ Pipeline 文件已生成

▶️ 步骤 4/12: 推送代码到 GitHub
✅ 代码推送成功

▶️ 步骤 5/12: 触发发布并等待完成
✅ 标签推送成功
⏳ 等待包发布到仓库...
✅ 包已成功发布！

▶️ 步骤 6/12: 获取包信息
📦 包名: weather-mcp
✅ 步骤完成

▶️ 步骤 7/12: AI 生成模板
✅ AI 生成完成
  中文: 天气查询 MCP 服务器
  繁体: 天氣查詢 MCP 伺服器
  英文: Weather Query MCP Server

▶️ 步骤 8/12: 生成 Logo
🎨 使用即梦 MCP 生成 Logo...
✅ Logo 生成成功！

▶️ 步骤 9/12: 发布到 EMCP
✅ CREATE 成功！
🆔 模板ID: xxx

▶️ 步骤 10/12: MCP 测试
✅ MCP 测试完成
  总工具数: 3
  通过: 3
  失败: 0
  成功率: 100.0%

▶️ 步骤 11/12: Agent 测试
✅ Agent 创建和发布完成

▶️ 步骤 12/12: SignalR 对话测试
✅ SignalR 对话测试完成

======================================================================
✅ 项目处理完成: weather-mcp
======================================================================
📦 包名: weather-mcp
🔗 GitHub: https://github.com/BACH-AI-Tools/weather-mcp
🆔 模板ID: xxx
⏱️ 耗时: 245.3 秒
✅ 完成步骤: 12/12
======================================================================

⏸️ 休息 5 秒后处理下一个项目...
```

### 4. 处理完成后

#### 查看总结

```
======================================================================
📊 批量处理总结
======================================================================

总项目数: 5
  ✅ 成功: 5
  ❌ 失败: 0
  📈 成功率: 100.0%
  ⏱️ 总耗时: 1234.5 秒 (20.6 分钟)
  ⚡ 平均耗时: 246.9 秒/项目

✅ 成功的项目:

  • weather-mcp
    包名: weather-mcp
    GitHub: https://github.com/BACH-AI-Tools/weather-mcp
    模板ID: xxx
    耗时: 245.3秒
    完成: 12/12 步骤

  • translator-mcp
    包名: translator-mcp
    GitHub: https://github.com/BACH-AI-Tools/translator-mcp
    模板ID: yyy
    耗时: 258.1秒
    完成: 12/12 步骤

  ... (其他项目)

💾 结果已保存: outputs/batch_results/batch_result_20250125_143025.json
======================================================================
```

#### 查看结果文件

结果会保存到 `outputs/batch_results/batch_result_YYYYMMDD_HHMMSS.json`

```json
[
  {
    "project_name": "weather-mcp",
    "success": true,
    "start_time": "2025-01-25T14:30:25",
    "end_time": "2025-01-25T14:34:30",
    "duration": 245.3,
    "steps_completed": [
      "扫描项目",
      "创建 GitHub 仓库",
      "生成 Pipeline",
      "推送代码",
      "触发发布",
      "获取包信息",
      "AI 生成模板",
      "生成 Logo",
      "发布到 EMCP",
      "MCP 测试",
      "Agent 测试",
      "SignalR 对话测试"
    ],
    "package_name": "weather-mcp",
    "github_url": "https://github.com/BACH-AI-Tools/weather-mcp",
    "template_id": "xxx",
    "logo_url": "https://...",
    "agent_id": "yyy",
    "errors": []
  }
]
```

---

## 🎯 使用场景

### 场景 1：昨天创建了 10 个 MCP 项目，今天一键发布

```
1. 双击 batch_mcp_factory.bat
2. 输入项目文件夹路径
3. 确认处理所有项目
4. 喝杯咖啡 ☕，等待约 30-40 分钟（10个项目）
5. 查看总结报告
6. 完成！✅
```

**结果：**
- 10 个项目全部发布到 GitHub
- 10 个包全部发布到 PyPI/NPM
- 10 个模板全部发布到 EMCP
- 10 个项目全部测试完成
- 自动生成测试报告

### 场景 2：只处理某几个项目

```bash
# 只处理项目 2, 4, 6
python batch_mcp_factory.py "E:\mcp-projects" --projects "2,4,6"
```

### 场景 3：失败后重新处理

如果某个项目失败，可以：

1. 查看错误信息
2. 修复问题
3. 重新运行，只处理失败的项目

```bash
# 假设项目 3 失败了
python batch_mcp_factory.py "E:\mcp-projects" --projects "3"
```

---

## ⚙️ 高级配置

### 1. 跳过某些步骤

如果某些项目不需要测试，可以修改 `batch_mcp_factory.py`：

```python
# 注释掉不需要的步骤
# executor.step_test_mcp()
# executor.step_test_agent()
# executor.step_test_chat()
```

### 2. 调整等待时间

修改 `batch_mcp_factory.py` 中的休息时间：

```python
# 项目之间休息时间（避免 API 限流）
time.sleep(5)  # 改为 10 或更长
```

### 3. 自定义包名前缀

如果你想给所有包添加统一前缀，可以在项目的 `setup.py` 或 `package.json` 中设置。

---

## 📊 性能预估

### 单个项目处理时间

| 步骤 | 平均耗时 | 说明 |
|------|----------|------|
| 1-4: 代码处理和推送 | 30-60秒 | 取决于项目大小 |
| 5: 等待包发布 | 120-180秒 | GitHub Actions 构建时间 |
| 6-9: EMCP 发布 | 30-60秒 | 包含 AI 生成和 Logo |
| 10-12: 测试 | 60-120秒 | 取决于工具数量 |
| **总计** | **240-420秒** | **4-7分钟/项目** |

### 批量处理时间预估

| 项目数 | 预计时间 |
|--------|----------|
| 5个 | 20-35分钟 |
| 10个 | 40-70分钟 |
| 20个 | 80-140分钟 |

**💡 提示：** 可以在处理过程中去做其他事情，脚本会自动完成所有步骤。

---

## ❓ 常见问题

### Q1: 某个项目失败了怎么办？

**A:** 脚本会继续处理其他项目。查看错误信息，修复后单独重新处理该项目：

```bash
python batch_mcp_factory.py "E:\mcp-projects" --projects "3"
```

### Q2: 可以中断处理吗？

**A:** 可以按 `Ctrl+C` 中断。已处理的项目结果会保存。

### Q3: GitHub Actions 构建失败怎么办？

**A:** 脚本会检测到并停止该项目的后续流程。你需要：

1. 检查 GitHub Actions 日志
2. 修复构建问题
3. 重新运行该项目

### Q4: 可以批量更新已发布的项目吗？

**A:** 可以！如果项目已在 GitHub 和 EMCP 上，脚本会：
- 更新 GitHub 仓库
- 创建新版本
- 更新 EMCP 模板

### Q5: API 配额不够用怎么办？

**A:** 调整休息时间：

```python
# 在 batch_mcp_factory.py 中
time.sleep(10)  # 从 5 秒改为 10 秒或更长
```

### Q6: 如何批量处理不同文件夹的项目？

**A:** 分别运行多次：

```bash
python batch_mcp_factory.py "E:\mcp-projects-1"
python batch_mcp_factory.py "E:\mcp-projects-2"
python batch_mcp_factory.py "E:\mcp-projects-3"
```

---

## 🔧 故障排除

### 问题 1: 找不到项目

**症状：** 显示"没有找到任何 MCP 项目"

**解决：**
- 检查路径是否正确
- 确保项目有 `setup.py`/`pyproject.toml` 或 `package.json`

### 问题 2: GitHub 推送失败

**症状：** 步骤 4 推送代码失败

**解决：**
- 检查 GitHub Token 是否有效
- 检查是否有推送权限

### 问题 3: 包发布超时

**症状：** 步骤 5 等待超时

**解决：**
- 检查 GitHub Actions 是否运行
- 检查构建日志是否有错误
- 手动等待构建完成后重新运行

### 问题 4: EMCP 登录失败

**症状：** 步骤 9 发布失败

**解决：**
- 检查手机号和验证码配置
- 确认今天的验证码（自动生成）
- 检查网络连接

---

## 📝 最佳实践

### 1. 批量处理前的准备

- ✅ 检查所有项目的 README 文件是否完整
- ✅ 确保所有项目都有正确的版本号
- ✅ 测试单个项目的发布流程
- ✅ 确认配置文件正确

### 2. 分批处理

如果项目很多，建议分批处理：

```bash
# 第一批：1-5
python batch_mcp_factory.py "E:\mcp-projects" --projects "1,2,3,4,5"

# 第二批：6-10
python batch_mcp_factory.py "E:\mcp-projects" --projects "6,7,8,9,10"
```

### 3. 保存处理记录

处理结果会自动保存到 `outputs/batch_results/`，建议：
- 定期备份结果文件
- 用于追踪发布历史

### 4. 监控处理进度

可以开另一个终端查看 GitHub Actions：

```bash
# 查看所有 workflow runs
gh run list --repo BACH-AI-Tools/weather-mcp
```

---

## 🎉 总结

批量 MCP 工厂可以：

- ✅ 自动化处理多个 MCP 项目
- ✅ 执行完整的 12 步发布流程
- ✅ 自动生成 Logo 和多语言描述
- ✅ 自动运行完整测试
- ✅ 生成详细的处理报告
- ✅ 节省大量时间和精力

**从手动处理 1-2 小时/项目 → 自动处理 4-7 分钟/项目** ⚡

---

## 📚 相关文档

- `mcp_factory_gui.py` - MCP 工厂 GUI 版本
- `src/workflow_executor.py` - 工作流执行器
- `config_template.json` - 配置文件模板

---

**祝你批量发布愉快！** 🚀🎉

