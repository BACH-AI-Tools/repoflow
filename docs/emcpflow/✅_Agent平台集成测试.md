# ✅ Agent 平台集成测试功能

## 🎯 功能概述

新增完整的 Agent 平台集成测试流程，自动创建 Agent、绑定 MCP、发布并生成测试链接。

## 🚀 完整流程

```
1. 发布 MCP 到 EMCP
   ↓
2. 点击 [🤖 Agent测试]
   ↓
3. 自动化流程:
   ├─ 登录 Agent 平台 (v5.kaleido.guru)
   ├─ 创建测试 Agent
   ├─ 查询 MCP 插件列表
   ├─ 确认 MCP 存在
   ├─ 绑定 MCP 到 Agent
   ├─ 发布 Agent
   ├─ 生成测试链接
   └─ 关闭 EMCP 模板（状态改为1）
   ↓
4. 访问链接测试 Agent
   ↓
5. ✅ 完成！
```

## 📋 测试步骤详解

### 步骤 1: 登录 Agent 平台

```
POST https://v5.kaleido.guru/api/authentication/verfiy_sms_validation_code_login?guest=true

Body:
{
  "prefix": "+86",
  "guest": true,
  "phone": "YOUR_PHONE_NUMBER",
  "validation_code": "11202507"  // 格式: MMyyyydd
}

Response:
{
  "session_key": "8e315ab6-xxx",
  "user_name": "用户名",
  "uid": 95
}
```

**验证码生成规则**: `MMyyyydd` 格式
- MM: 月份（如 11）
- yyyy: 年份（如 2025）
- dd: 日期两遍（如 0707）
- 例如: 2025-11-07 → `11202507`

### 步骤 2: 创建 Agent

```
POST https://v5.kaleido.guru/api/superAgent/create

Headers:
  Token: <session_key>

Body:
{
  "name": "巴赫数据分析服务器 测试",  // MCP名称 + "测试"
  "description": "利用LLM生成的描述",
  "logo": "",
  "super_agent_category_id": 261
}

Response:
{
  "err_code": 0,
  "body": {
    "super_agent_setting_id": 1231  // Agent ID
  }
}
```

### 步骤 3: 查询 MCP 插件列表

```
POST https://v5.kaleido.guru/api/plugin/query_plugin

Body:
{
  "current_page": 1,
  "isPublish": true,
  "page_size": 9999,
  "is_mcp_query": true  // 只查询 MCP 插件
}

Response:
{
  "err_code": 0,
  "body": [
    {
      "id": 100259,
      "name_for_model": "巴赫数据分析服务器",  // ⭐ 匹配 MCP 名称
      "description_for_model": "...",
      "api_url": "http://dataanalys.sitmcp.kaleido.guru/sse"
    },
    ...
  ]
}
```

**验证**: 检查 MCP 是否在列表中，不在则中止！

### 步骤 4: 绑定 MCP 到 Agent

```
POST https://v5.kaleido.guru/api/superAgent/update

Body:
{
  "super_agent_setting_id": "1231",
  "name": "巴赫数据分析服务器 测试",
  "description": "...",
  "plugin_ids": [100259],  // ⭐ 绑定 MCP 插件 ID
  "system_message": "你是一个AI助手",
  "llm_request": [...],  // DeepSeek 配置
  ...
}
```

### 步骤 5: 发布 Agent

```
POST https://v5.kaleido.guru/api/superAgent/publish/1231

Body:
{
  "description": "自动化测试发布",
  "upateAllAgentVersion": true
}

Response:
{
  "err_code": 0,
  "body": {
    "publish_id": 6297  // 发布 ID
  }
}
```

**访问链接**: `https://v5.kaleido.guru/chat?releaseId=6297`

### 步骤 6: 手动测试对话

**提示用户**: 访问链接，在对话中测试 MCP 工具是否可用

### 步骤 7: 关闭 EMCP 模板

```
PUT https://sit-emcp.kaleido.guru/api/Template/publish_mcp_template/{template_id}/1

// 1 = 关闭状态
```

## 📊 日志输出示例

```
======================================================================
🤖 开始 Agent 平台集成测试
======================================================================

📋 步骤 1/7: 登录 Agent 平台...
   📤 POST https://v5.kaleido.guru/api/authentication/...
   📱 手机号: YOUR_PHONE_NUMBER
   🔑 验证码: 11202507
   📥 响应: 200
   ✅ 登录成功
   👤 用户: 富国AI脑
   🆔 UID: 95
   🔑 Token: 8e315ab6-d708-450a...

📋 步骤 2/7: 创建测试 Agent...
   🤖 使用 LLM 生成 Agent 描述...
   ✅ LLM 生成描述: 集成了巴赫数据分析服务器的AI Agent...
   📤 POST https://v5.kaleido.guru/api/superAgent/create
   📝 名称: 巴赫数据分析服务器 测试
   📥 响应: 200
   ✅ Agent 已创建
   🆔 Agent ID: 1231

📋 步骤 3/7: 查询 MCP 插件...
   📤 POST https://v5.kaleido.guru/api/plugin/query_plugin
   📥 响应: 200
   ✅ 找到 32 个 MCP 插件
   ✅ 找到匹配的 MCP: 巴赫数据分析服务器
      ID: 100259
      UUID: 4b52770b-xxx

📋 步骤 4/7: 绑定 MCP 到 Agent...
   📤 POST https://v5.kaleido.guru/api/superAgent/update
   🔗 绑定插件: [100259]
   📥 响应: 200
   ✅ Agent 已更新

📋 步骤 5/7: 发布 Agent...
   📤 POST https://v5.kaleido.guru/api/superAgent/publish/1231
   📥 响应: 200
   ✅ Agent 已发布
   🆔 发布ID: 6297
   🔗 访问链接: https://v5.kaleido.guru/chat?releaseId=6297

📋 步骤 6/7: 测试 Agent 对话...
   💡 请手动访问链接测试: https://v5.kaleido.guru/chat?releaseId=6297
   💡 确认 Agent 能够正常调用 MCP 工具

📋 步骤 7/7: 关闭 EMCP 模板...
   📤 PUT https://sit-emcp.kaleido.guru/api/Template/publish_mcp_template/xxx/1
   📝 修改为: 关闭状态(1)
   📥 响应: 200
   ✅ EMCP 模板已关闭（状态改为1）

======================================================================
✅ Agent 集成测试完成！
======================================================================

🔗 Agent 访问链接: https://v5.kaleido.guru/chat?releaseId=6297
💡 请访问链接测试 Agent 是否能正常使用 MCP 工具
```

## 🎨 GUI 界面

### 按钮布局

```
┌──────────────────────────────────────────────┐
│  输入包地址:                                  │
│  ┌────────────────────────────────────────┐  │
│  │  bachai-data-analysis-mcp              │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────┐ ┌──────┐ ┌──────────┐ ┌──────────┐│
│  │🚀一键发布│ │⚙️设置│ │🧪MCP测试 │ │🤖Agent测试││ ⭐
│  └────────┘ └──────┘ └──────────┘ └──────────┘│
└──────────────────────────────────────────────┘
```

### 测试对话框

```
┌─────────────────────────────────────┐
│  确认 Agent 测试                     │
├─────────────────────────────────────┤
│  即将进行 Agent 平台集成测试:        │
│                                     │
│  MCP 名称: 巴赫数据分析服务器        │
│  模板 ID: 4b52770b-xxx              │
│                                     │
│  测试流程:                           │
│  1. 登录 Agent 平台                 │
│  2. 创建测试 Agent                  │
│  3. 查询 MCP 插件                   │
│  4. 绑定 MCP 到 Agent               │
│  5. 发布 Agent                      │
│  6. 生成测试链接                    │
│  7. 关闭 EMCP 模板                  │
│                                     │
│  是否继续？                          │
│                                     │
│      [是(Y)]    [否(N)]             │
└─────────────────────────────────────┘
```

## 📁 新增文件

**agent_tester.py** (约 350 行)

**核心类**:
- `AgentPlatformClient` - Agent 平台 API 客户端
- `AgentTester` - Agent 测试器
- `AgentTesterLogger` - 日志记录器

**核心方法**:
- `login()` - 登录 Agent 平台
- `create_agent()` - 创建 Agent
- `query_plugins()` - 查询 MCP 插件
- `update_agent()` - 绑定 MCP
- `publish_agent()` - 发布 Agent
- `_close_emcp_template()` - 关闭 EMCP 模板

## 🔑 关键技术点

### 1. Agent 平台认证

```python
headers = {
    'Token': session_key,  // ⭐ Agent 平台使用大写 Token
    'Content-Type': 'application/json;charset=UTF-8'
}
```

**注意**: 
- Agent 平台: 大写 `Token`
- EMCP 平台: 小写 `token`

### 2. 验证码生成

```python
validation_code = datetime.now().strftime("%m%Y%d%d")
# 11202507 = 11(月) + 2025(年) + 07(日) + 07(日)
```

### 3. MCP 插件查找

```python
# 在插件列表中查找匹配的 MCP
matched = [p for p in plugins if mcp_name.lower() in p.get('name_for_model', '').lower()]

if not matched:
    raise Exception("未找到 MCP 插件，请确认已发布到 EMCP！")
```

**关键**: 如果 MCP 不在列表中，中止后续操作！

### 4. 模板状态

| 状态 | 说明 |
|------|------|
| 1 | 关闭 |
| 2 | 发布状态 (Dummy) |
| 3 | 测试状态 |

## 💡 使用 LLM 生成 Agent 描述

```python
prompt = f"""
基于以下 MCP 服务信息，生成一个简洁专业的 Agent 描述（50-100字）：

MCP 名称：{mcp_name}
MCP 描述：{mcp_description}

要求：
1. 说明这是一个集成了该 MCP 的 AI Agent
2. 突出 MCP 的核心功能
3. 语言简洁专业
"""

response = ai_generator.client.chat.completions.create(
    model=ai_generator.deployment_name,  # ⭐ 使用正确的 deployment
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
)
```

## 🎯 与 MCP 测试的区别

### MCP 测试 🧪

**目的**: 测试 MCP 服务本身

**流程**:
```
创建Pod → 测试工具 → HTML报告 → 恢复状态
```

**结果**: 工具可用性报告

### Agent 测试 🤖

**目的**: 测试 Agent + MCP 集成

**流程**:
```
创建Agent → 绑定MCP → 发布 → 生成链接 → 关闭模板
```

**结果**: Agent 对话测试链接

## 📊 测试报告结构

```python
{
  "template_id": "xxx",
  "mcp_name": "巴赫数据分析服务器",
  "test_time": "2025-11-06T17:00:00",
  "steps": [
    {"step": 1, "name": "登录Agent平台", "success": True},
    {"step": 2, "name": "创建Agent", "success": True},
    {"step": 3, "name": "查询MCP插件", "success": True},
    {"step": 4, "name": "绑定MCP", "success": True},
    {"step": 5, "name": "发布Agent", "success": True},
    {"step": 6, "name": "测试对话", "success": True, "manual": True},
    {"step": 7, "name": "关闭EMCP模板", "success": True}
  ],
  "agent_id": 1231,
  "publish_id": 6297,
  "mcp_plugin_id": 100259,
  "agent_url": "https://v5.kaleido.guru/chat?releaseId=6297",
  "success": True
}
```

## 🔄 完整的端到端流程

```
┌──────────────────┐
│  发布包到 EMCP    │
└────────┬─────────┘
         │
    ┌────▼────────────┐
    │  🧪 MCP 测试    │ (可选)
    │  测试工具可用性  │
    └────────────────┘
         │
    ┌────▼────────────┐
    │  🤖 Agent 测试  │
    │  ├─ 登录 Agent  │
    │  ├─ 创建 Agent  │
    │  ├─ 绑定 MCP    │
    │  ├─ 发布 Agent  │
    │  └─ 关闭模板    │
    └────────────────┘
         │
    ┌────▼────────────┐
    │  访问链接测试    │
    │  验证集成效果    │
    └─────────────────┘
```

## ⚠️ 重要检查

### MCP 必须在插件列表中

```python
plugins = query_plugins(mcp_name)

if not plugins or len(plugins) == 0:
    raise Exception("未找到 MCP 插件！请确认 MCP 已成功发布到 EMCP 平台！")
    // ⭐ 中止后续操作
```

**原因**: 如果 MCP 不存在，后续绑定会失败

## 🎯 测试完成对话框

```
┌─────────────────────────────────────────┐
│  ✅ Agent 集成测试完成！                 │
│                                         │
│  Agent ID: 1231                         │
│  发布 ID: 6297                          │
│  MCP 插件 ID: 100259                    │
│                                         │
│  🔗 Agent 访问链接:                     │
│  https://v5.kaleido.guru/chat?          │
│  releaseId=6297                         │
│                                         │
│  💡 请访问链接测试 Agent 是否能           │
│  正常使用 MCP 工具                       │
│                                         │
│              [确定]                      │
└─────────────────────────────────────────┘
```

## 🔧 技术实现

### API 调用封装

```python
class AgentPlatformClient:
    def __init__(self, base_url="https://v5.kaleido.guru"):
        self.base_url = base_url
        self.session_key = None
    
    def _get_headers(self):
        return {
            'Token': self.session_key,  # 大写
            'Content-Type': 'application/json;charset=UTF-8'
        }
    
    def login(self, phone, validation_code):
        # 登录逻辑
    
    def create_agent(self, name, description):
        # 创建逻辑
    
    def query_plugins(self, mcp_name):
        # 查询逻辑
    
    def update_agent(self, agent_id, plugin_ids):
        # 更新逻辑
    
    def publish_agent(self, agent_id):
        # 发布逻辑
```

### LLM 集成

```python
def _generate_agent_info(self, mcp_name, mcp_description):
    # 使用 LLM 生成专业的 Agent 描述
    
    if self.ai_generator:
        # 使用 LLM 生成
        response = self.ai_generator.client.chat.completions.create(
            model=self.ai_generator.deployment_name,  # ⭐
            messages=[...]
        )
        return agent_name, llm_description
    else:
        # 降级方案
        return agent_name, simple_description
```

## 📈 用户价值

### 自动化程度

**手动流程** ❌:
```
1. 登录 Agent 平台
2. 创建 Agent
3. 配置 Agent
4. 查找 MCP
5. 绑定 MCP
6. 填写配置
7. 发布 Agent
8. 获取链接
9. 关闭 EMCP 模板

总耗时: 10-15 分钟
```

**自动化流程** ✅:
```
1. 点击 [🤖 Agent测试]
2. 确认
3. 等待完成 (30-60秒)
4. 获得测试链接

总耗时: 1 分钟
```

**节省时间**: **90%+**

### 错误预防

- ✅ 自动检查 MCP 是否存在
- ✅ 不存在则中止操作
- ✅ 避免无效的 Agent 创建

## ✅ 完成清单

- [x] ✅ 创建 `agent_tester.py` 模块
- [x] ✅ 实现 Agent 平台登录
- [x] ✅ 实现 Agent 创建
- [x] ✅ 实现 MCP 插件查询和验证
- [x] ✅ 实现 MCP 绑定
- [x] ✅ 实现 Agent 发布
- [x] ✅ 实现 EMCP 模板关闭
- [x] ✅ LLM 生成 Agent 描述
- [x] ✅ GUI 添加 Agent 测试按钮
- [x] ✅ 保存 MCP 名称和描述
- [x] ✅ 详细日志输出
- [x] ✅ 错误处理

---

**实现时间**: 2025-11-06  
**功能**: Agent 平台集成测试  
**平台**: [v5.kaleido.guru](https://v5.kaleido.guru/)  
**开发**: 巴赫工作室 (BACH Studio)

**Made with ❤️ by 巴赫工作室**

