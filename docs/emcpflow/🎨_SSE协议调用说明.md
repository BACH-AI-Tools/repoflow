# 🎨 即梦MCP SSE协议调用说明

## SSE协议调用流程

### 完整实现

```python
# 1. 构建MCP JSON-RPC消息
mcp_message = {
    "jsonrpc": "2.0",
    "id": "uuid-xxx-xxx",
    "method": "tools/call",
    "params": {
        "name": "jimeng-v40-generate",
        "arguments": {
            "prompt": "Create a logo..."
        }
    }
}

# 2. 发送POST请求到SSE端点
POST http://mcptest013.sitmcp.kaleido.guru/sse
Headers:
  - emcp-key: PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n
  - emcp-usercode: VGSdDTgj
  - Accept: text/event-stream
  - Cache-Control: no-cache
Body: mcp_message (JSON)

# 3. 保持stream连接，解析SSE事件流
data: {"jsonrpc":"2.0","id":"uuid-xxx-xxx","result":{"content":[...]}}

# 4. 提取图片URL
result.content[0].text  // 或其他字段
```

---

## 代码实现

### 核心方法

**文件**: `jimeng_mcp_client.py`

```python
def _send_sse_request(self, mcp_message: dict, timeout: int):
    """发送SSE请求并解析响应"""
    
    # 1. POST到SSE端点
    with requests.post(
        self.sse_url,
        headers=self.headers,
        json=mcp_message,
        stream=True,  # ✅ 保持连接
        timeout=timeout
    ) as response:
        
        # 2. 解析SSE事件流
        buffer = ""
        for line in response.iter_lines():
            decoded_line = line.decode('utf-8')
            
            # 3. 处理SSE协议
            if decoded_line.startswith('data: '):
                buffer += decoded_line[6:]
            elif decoded_line.strip() == '':
                # 消息结束
                if buffer:
                    event_data = json.loads(buffer)
                    
                    # 4. 检查是否是我们的响应
                    if event_data.get('id') == mcp_message['id']:
                        return event_data.get('result')
                    
                    buffer = ""
```

---

## GUI 日志示例

### 成功调用

```
======================================================================
📤 通过SSE调用即梦MCP工具: jimeng-v40-generate
📋 SSE URL: http://mcptest013.sitmcp.kaleido.guru/sse
📋 参数: {"prompt": "Create a logo..."}
======================================================================

📤 MCP消息: {
  "jsonrpc": "2.0",
  "id": "12345-uuid",
  "method": "tools/call",
  "params": {
    "name": "jimeng-v40-generate",
    "arguments": {
      "prompt": "..."
    }
  }
}

📥 SSE连接状态: 200
✅ SSE连接已建立，等待响应...

📨 收到事件: {
  "jsonrpc": "2.0",
  "id": "12345-uuid",
  "result": {
    "content": [
      {
        "type": "image",
        "text": "http://image-server.com/xxx.png"
      }
    ]
  }
}

✅ 获得工具响应
✅ 工具调用成功
   📋 即梦MCP返回数据: {...}
   ✅ 图片生成成功: http://image-server.com/xxx.png
```

### 然后上传到EMCP

```
   ✅ 即梦MCP生成成功
   📤 上传到EMCP存储...

======================================================================
📤 POST https://sit-emcp.kaleido.guru/api/proxyStorage/NoAuth/upload_file
📦 上传文件: logo.png
======================================================================

======================================================================
📥 响应: 200
📋 {
  "err_code": 0,
  "body": {
    "fileUrl": "/api/proxyStorage/NoAuth/xxx.png"
  }
}
======================================================================

✅ Logo 上传成功: /api/proxyStorage/NoAuth/xxx.png
```

---

## 技术要点

### 1. SSE协议

**SSE (Server-Sent Events)**：
- 服务器向客户端推送事件
- 使用 `text/event-stream` 格式
- 保持长连接
- 适合实时数据推送

**格式**：
```
data: {"message": "..."}

data: {"another": "message"}

```

### 2. MCP JSON-RPC协议

**标准格式**：
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "method": "tools/call",
  "params": {
    "name": "tool-name",
    "arguments": {...}
  }
}
```

**响应格式**：
```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "result": {
    "content": [
      {
        "type": "image",
        "text": "http://image-url"
      }
    ]
  }
}
```

### 3. 图片URL提取

**支持多种格式**：
```python
# MCP标准格式
result['content'][0]['text']

# 或其他可能的字段
result['image_url']
result['url']
result['data']['url']
```

---

## 配置

### 即梦MCP配置

```json
{
  "sse_url": "http://mcptest013.sitmcp.kaleido.guru/sse",
  "emcp_key": "PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n",
  "emcp_usercode": "VGSdDTgj",
  "tool_name": "jimeng-v40-generate"  ✅
}
```

**已内置到代码中，无需额外配置！**

---

## 调试

### 如果仍然失败

**查看GUI日志**：
1. SSE连接状态
2. 发送的MCP消息
3. 收到的SSE事件
4. 提取的图片URL

**可能的问题**：
- SSE连接超时（默认120秒）
- 图片生成时间过长
- 响应格式不匹配
- 网络问题

**解决方法**：
- 增加timeout时间
- 查看实际响应格式
- 调整URL提取逻辑
- 检查即梦MCP服务状态

---

## 测试

### 运行测试脚本

```bash
python test_jimeng_mcp.py
```

**预期输出**：
```
测试即梦MCP Logo生成（SSE协议）
======================================

配置:
  SSE URL: http://mcptest013.sitmcp.kaleido.guru/sse
  工具名: jimeng-v40-generate
  
调用即梦MCP...
📥 SSE连接状态: 200
✅ SSE连接已建立，等待响应...
📨 收到事件: {...}
✅ 图片生成成功: http://...

✅ 测试成功！
```

### 在GUI中测试

```bash
python emcpflow_simple_gui.py

# 输入包名
requests

# 点击 [一键发布]

# 查看日志中的即梦MCP调用过程
```

---

## ✅ 更新内容

### 修改的文件

1. **jimeng_mcp_client.py**
   - ✅ 改为SSE协议调用
   - ✅ 实现 `_send_sse_request()` 方法
   - ✅ 使用正确的工具名 `jimeng-v40-generate`
   - ✅ 解析SSE事件流
   - ✅ 支持MCP JSON-RPC协议
   - ✅ 增加超时时间到120秒

2. **test_jimeng_mcp.py**
   - ✅ 更新测试脚本
   - ✅ 添加详细说明

---

## 完整流程

```
调用 jimeng_client.generate_logo()
    ↓
构建 MCP JSON-RPC 消息
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "jimeng-v40-generate",
    "arguments": {"prompt": "..."}
  }
}
    ↓
POST 到 SSE 端点（stream=True）
    ↓
解析 SSE 事件流
data: {...}
    ↓
提取图片 URL
    ↓
下载图片
    ↓
上传到 EMCP
POST /api/proxyStorage/NoAuth/upload_file
    ↓
返回 EMCP Logo URL
/api/proxyStorage/NoAuth/xxx.png
    ↓
用于模板 ✅
```

---

**SSE客户端已完整实现！** ✅  
**使用正确工具名：jimeng-v40-generate** ✅  
**所有日志输出到GUI** 📋  
**立即可以测试！** 🚀

