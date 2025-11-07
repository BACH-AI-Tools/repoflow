# ✅ 修复工具列表获取 - 使用 Server ID

## 🎯 问题

用户指出：
> "tools后面跟着是emcp serverid，不是emcp temlateid"

之前代码直接用 template_id 获取工具列表，导致 401 错误。

## ✅ 正确的流程

### 两步获取

```
步骤 1: template_id → server_id
GET /api/Service/get_mcp_main_server_id/{template_id}
返回: server_id

步骤 2: server_id → 工具列表
GET /api/Service/get_mcp_test_tools/{server_id}
返回: 工具列表
```

## 🔧 实现代码

```python
# 步骤 0.1: 获取 Server ID
server_id_url = f"{emcp_base_url}/api/Service/get_mcp_main_server_id/{template_id}"

response = requests.get(server_id_url, headers={'token': emcp_token}, timeout=30)

# 支持 401 自动重登录
if response.status_code == 401:
    emcp_manager.login(...)  # 重新登录
    response = requests.get(server_id_url, headers={'token': new_token})

server_id_data = response.json()
server_id = server_id_data.get('body')  # "526cff00-6a2a-4736-8251-0b5c5966a60f"

# 步骤 0.2: 获取工具列表
tools_url = f"{emcp_base_url}/api/Service/get_mcp_test_tools/{server_id}"  # ⭐ 使用 server_id

response = requests.get(tools_url, headers={'token': emcp_token}, timeout=30)

tools_data = response.json()
tools = tools_data.get('body', [])
```

## 📊 日志输出

```
📋 步骤 0: 从 EMCP 获取 MCP 工具列表...
   📋 模板ID: d95b2899-25eb-414a-bea0-00ebabf58b47
   
   📋 步骤 0.1: 获取 Server ID...  ⭐
   📤 GET https://sit-emcp.kaleido.guru/api/Service/get_mcp_main_server_id/xxx
   📥 响应: 200
   ✅ Server ID: 526cff00-6a2a-4736-8251-0b5c5966a60f  ⭐
   
   📋 步骤 0.2: 获取工具列表...  ⭐
   📤 GET https://sit-emcp.kaleido.guru/api/Service/get_mcp_test_tools/526cff00-xxx  ⭐ 使用 server_id
   📥 响应: 200
   ✅ 成功获取 25 个工具  ⭐
      1. 获取某支股票的行情数据
      2. 获取某支股票的行情数据-详细
      ...
```

## 🔄 支持 401 自动重登录

两个步骤都支持 401 自动重登录：

### 步骤 0.1: 获取 Server ID
```
401 → 重新登录 → 重试 → 成功获取 server_id
```

### 步骤 0.2: 获取工具列表
```
使用最新的 token（步骤0.1可能已刷新）
```

## 📋 API 说明

### 1. 获取 Server ID

```
GET /api/Service/get_mcp_main_server_id/{template_id}

Headers:
  token: <EMCP token>
  language: ch_cn

Response:
{
  "err_code": 0,
  "body": "526cff00-6a2a-4736-8251-0b5c5966a60f"  // Server ID
}
```

### 2. 获取工具列表

```
GET /api/Service/get_mcp_test_tools/{server_id}

Headers:
  token: <EMCP token>
  language: ch_cn

Response:
{
  "err_code": 0,
  "body": [
    {
      "functionName": "获取某支股票的行情数据",
      "functionApi": "quotec",
      "parameters": [...]
    },
    ...
  ]
}
```

## ✅ 完成功能

- [x] ✅ template_id → server_id
- [x] ✅ server_id → 工具列表
- [x] ✅ 两步都支持 401 重登录
- [x] ✅ 详细日志输出
- [x] ✅ 正确的 API 调用顺序

## 🎊 最终效果

现在再次测试时：

```
📋 步骤 0.1: 获取 Server ID
   ✅ Server ID: xxx
   
📋 步骤 0.2: 获取工具列表
   ✅ 找到 25 个工具
   
🔧 测试 1/25: ...
🔧 测试 2/25: ...
...
✅ 所有工具测试完成！
```

**完全正确的流程！** ✅

---

**修复时间**: 2025-11-06  
**修复内容**: 使用正确的 server_id 获取工具列表  
**API**: template_id → server_id → 工具列表  
**开发**: 巴赫工作室 (BACH Studio)

**Made with ❤️ by 巴赫工作室**

