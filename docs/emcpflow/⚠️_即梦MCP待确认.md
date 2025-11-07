# ⚠️ 即梦MCP调用方式待确认

## 当前问题

**错误信息**: `Cannot POST /sse`

说明SSE端点不支持POST请求。

---

## 已尝试的方法

### 方法1: POST到/sse（失败）

```python
requests.post(
    "http://mcptest013.sitmcp.kaleido.guru/sse",
    json=mcp_message,
    stream=True
)
```

**结果**: 404 - Cannot POST /sse ❌

### 方法2: POST到/mcp/tools/call（失败）

```python
requests.post(
    "http://mcptest013.sitmcp.kaleido.guru/mcp/tools/call",
    json=payload
)
```

**结果**: 404 - Cannot POST /mcp/tools/call ❌

---

## 需要确认

### 问题1: 如何建立SSE连接？

**可能的方式**：
- GET /sse （建立连接，接收事件）
- 但如何发送工具调用请求？

### 问题2: 如何调用工具？

**可能的方式**：
- 通过查询参数？
- 通过另一个HTTP端点？
- 通过WebSocket？
- 通过某种特殊的SSE协议？

### 问题3: MCP消息格式

**标准 JSON-RPC 格式**：
```json
{
  "jsonrpc": "2.0",
  "id": "uuid",
  "method": "tools/call",
  "params": {
    "name": "jimeng-v40-generate",
    "arguments": {
      "prompt": "..."
    }
  }
}
```

**问题**: 这个消息应该通过什么方式发送？

---

## 临时方案

### 当前实现

**已禁用即梦MCP**，使用默认Logo：

```python
# 在 ai_generator.py 中
logo_url = logo_generator.get_or_generate_logo(
    ...,
    use_jimeng=False  # 暂时禁用
)
```

**效果**：
- ✅ 使用默认Logo：`/api/proxyStorage/NoAuth/default-mcp-logo.png`
- ✅ 或使用包的官方Logo（如果有）
- ✅ 发布流程正常工作

---

## 需要的信息

为了正确实现即梦MCP调用，需要：

1. **正确的调用示例** - curl 命令或代码示例
2. **工具列表** - 如何获取可用工具列表
3. **响应格式** - 图片URL在响应的哪个字段
4. **文档链接** - 即梦MCP的API文档

---

## 建议

### 方案A: 暂时使用默认Logo（当前）

**优点**：
- ✅ 立即可用
- ✅ 稳定可靠
- ✅ 发布流程完整

**缺点**：
- ❌ Logo不是个性化的

### 方案B: 等待正确调用方式

**需要**：
- 即梦MCP的正确调用示例
- 或者直接在Cursor/Claude中测试即梦MCP

---

## 当前状态

**功能状态**：
- ✅ 所有其他功能正常
- ✅ LLM生成三语言
- ✅ 401自动登录
- ✅ 400 AI修复
- ✅ 完整日志
- ⚠️ 即梦MCP Logo生成待确认

**用户体验**：
- 可以正常发布
- Logo使用默认的
- 可以后续在EMCP平台手动更新Logo

---

## 测试即梦MCP

如果您能提供正确的调用方式，我立即集成！

**需要的信息**：
1. curl 命令示例
2. 或者在您的环境中成功调用的代码
3. 工具的完整名称和参数格式
4. 响应的完整JSON结构

---

**暂时禁用即梦MCP，使用默认Logo** ⚠️  
**其他所有功能正常工作** ✅  
**等待正确调用方式** 🔍

