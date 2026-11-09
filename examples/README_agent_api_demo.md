# Agent 平台 API 调用示例

这是一个完整的、可独立运行的 Python 示例程序，演示如何调用 Agent 平台的所有测试接口。

## 📋 目录

- [快速开始](#快速开始)
- [接口列表](#接口列表)
- [使用说明](#使用说明)
- [代码示例](#代码示例)
- [常见问题](#常见问题)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置参数

编辑 `agent_platform_api_demo.py` 文件，修改以下参数：

```python
PHONE = "YOUR_PHONE_NUMBER"  # 你的手机号
MCP_NAME = "测试MCP"    # 要测试的 MCP 名称
```

### 3. 运行示例

```bash
# 方式 1: 运行完整测试流程（推荐）
python examples/agent_platform_api_demo.py

# 方式 2: 交互式选择模式
# 在 main() 函数中取消注释相应代码
```

## 📚 接口列表

示例代码包含以下 **9 个核心接口**：

### 1️⃣ 用户认证

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 1 | `/api/authentication/verfiy_sms_validation_code_login` | POST | 登录 Agent 平台 |

### 2️⃣ Agent 管理

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 2 | `/api/superAgent/create` | POST | 创建 Agent |
| 3 | `/api/plugin/query_plugin` | POST | 查询 MCP 插件列表 |
| 4 | `/api/superAgent/update` | POST | 更新 Agent（绑定 MCP） |
| 5 | `/api/superAgent/publish/{agent_id}` | POST | 发布 Agent |
| 6 | `/api/superAgent/skill_detail` | GET | 获取 Agent 技能 |

### 3️⃣ 会话管理

| 序号 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 7 | `/api/conversation/get_work_space_for_user` | GET | 获取工作区列表 |
| 8 | `/api/conversation/create_work_space` | POST | 创建工作区 |
| 9 | `/api/conversation/init` | POST | 创建会话 |

## 📖 使用说明

### 完整测试流程

示例代码演示了完整的 Agent 测试流程：

```
1. 登录 Agent 平台
   ↓
2. 创建测试 Agent
   ↓
3. 查询 MCP 插件
   ↓
4. 绑定 MCP 到 Agent
   ↓
5. 发布 Agent
   ↓
6. 获取 Agent 技能
   ↓
7. 获取/创建工作区
   ↓
8. 创建测试会话
   ↓
9. 输出测试结果
```

### 运行输出示例

```
======================================================================
  🚀 Agent 平台 API 完整测试流程演示
======================================================================

📋 配置信息:
   📱 手机号: YOUR_PHONE_NUMBER
   🔑 验证码: 12202501
   📦 MCP 名称: 测试MCP
   🤖 Agent 名称: 测试MCP 测试 Agent

----------------------------------------------------------------------
步骤 1/9: 登录 Agent 平台
----------------------------------------------------------------------

======================================================================
  接口 1: 登录 Agent 平台
======================================================================

📤 POST https://v5.kaleido.guru/api/authentication/verfiy_sms_validation_code_login?guest=true
📝 请求数据:
{
  "prefix": "+86",
  "guest": true,
  "phone": "YOUR_PHONE_NUMBER",
  "validation_code": "12202501"
}

📥 响应状态: 200
📋 响应数据:
{
  "err_code": 0,
  "body": {
    "session_key": "8e315ab6-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    "user_name": "测试用户",
    "uid": 95
  }
}

✅ 登录成功!
   👤 用户: 测试用户
   🆔 UID: 95
   🔑 Token: 8e315ab6-xxxx-xxxx-xxxx...

... (后续步骤输出)

======================================================================
  ✅ 完整流程执行成功!
======================================================================

📊 测试结果汇总:
   🤖 Agent ID: 1231
   📋 发布 ID: 6297
   🔗 Agent 链接: https://v5.kaleido.guru/chat?releaseId=6297
   💬 会话 ID: 394b4a42-d681-4cac-8b24-63806b51d8ee

💡 下一步:
   1. 访问 Agent 链接进行测试
   2. 在会话中发送测试消息
   3. 验证 MCP 工具是否正常调用
```

## 💻 代码示例

### 示例 1: 仅登录

```python
from agent_platform_api_demo import AgentPlatformDemo
from datetime import datetime

# 创建客户端
demo = AgentPlatformDemo()

# 登录
phone = "YOUR_PHONE_NUMBER"
validation_code = datetime.now().strftime("%m%Y%d")
user_info = demo.login(phone, validation_code)

print(f"Session Key: {demo.session_key}")
```

### 示例 2: 查询 MCP 插件

```python
# 接上一步，已登录

# 查询所有 MCP 插件
all_plugins = demo.query_plugins()

# 查询特定名称的 MCP
matched_plugins = demo.query_plugins(mcp_name="巴赫")
```

### 示例 3: 创建并发布 Agent

```python
# 接上一步，已登录

# 创建 Agent
agent_result = demo.create_agent(
    name="我的测试 Agent",
    description="这是一个测试 Agent"
)
agent_id = agent_result['super_agent_setting_id']

# 查询要绑定的 MCP
plugins = demo.query_plugins(mcp_name="测试MCP")
mcp_plugin_id = plugins[0]['id']

# 绑定 MCP
demo.update_agent(
    agent_id=agent_id,
    name="我的测试 Agent",
    description="这是一个测试 Agent",
    plugin_ids=[mcp_plugin_id]
)

# 发布 Agent
publish_result = demo.publish_agent(agent_id)
print(f"Agent 链接: {demo.base_url}/chat?releaseId={publish_result['publish_id']}")
```

### 示例 4: 创建测试会话

```python
# 接上一步，已有 agent_id

# 获取工作区
workspaces = demo.get_workspaces()
workspace_id = workspaces[0]['id']

# 创建会话
conversation_id = demo.create_conversation(
    agent_id=agent_id,
    workspace_id=workspace_id,
    conversation_name="测试会话"
)

print(f"会话 ID: {conversation_id}")
```

## 🔧 关键参数说明

### 验证码格式

验证码格式为 `MMyyyydd`，示例：

```python
# 2025年12月1日 → 12202501
validation_code = datetime.now().strftime("%m%Y%d")

# 解析：
# MM   = 12 (月份)
# yyyy = 2025 (年份)
# dd   = 01 (日期)
```

### Agent 分类 ID

默认分类 ID 为 `261`，如需使用其他分类，请查询平台获取。

### LLM 模型配置

默认使用 `deepseek-chat` 模型，配置如下：

```python
"llm_request": [
    {
        "type": 1,  # 类型 1
        "llm_model_name": "deepseek-chat",
        "llm_provider": 6,  # DeepSeek 提供商
        "llm_setting_name": "72e5c503-2c17-4167-863f-5b9e6b220332"
    },
    {
        "type": 2,  # 类型 2
        "llm_model_name": "deepseek-chat",
        "llm_provider": 6,
        "llm_setting_name": "72e5c503-2c17-4167-863f-5b9e6b220332"
    }
]
```

## ❓ 常见问题

### Q1: 登录失败，返回 502 Bad Gateway

**原因**：服务器繁忙或网络问题

**解决**：
1. 等待几秒后重试
2. 检查网络连接
3. 确认 `base_url` 是否正确

### Q2: 未找到 MCP 插件

**原因**：MCP 未发布到 Agent 平台

**解决**：
1. 确认 MCP 已成功发布到 EMCP 平台
2. 检查 MCP 名称是否正确（区分大小写）
3. 等待几分钟让平台同步数据

### Q3: 绑定 MCP 后发布失败

**原因**：插件配置不完整

**解决**：
1. 检查 `plugin_ids` 是否正确
2. 确认 MCP 插件状态为"已发布"
3. 查看错误信息中的详细原因

### Q4: Token 过期怎么办？

**原因**：Session Token 有效期限制

**解决**：
```python
# 重新登录获取新 Token
demo.login(phone, validation_code)
```

### Q5: 如何调试接口？

**方法**：
1. 查看详细的请求/响应日志
2. 使用浏览器开发者工具抓包对比
3. 检查返回的 `err_code` 和 `err_message`

## 🔗 相关链接

- Agent 平台：https://v5.kaleido.guru
- EMCP 平台：https://sit-emcp.kaleido.guru

## 📝 许可证

MIT License

---

**作者**: BACH Studio  
**日期**: 2025-12-01  
**版本**: 1.0.0
















