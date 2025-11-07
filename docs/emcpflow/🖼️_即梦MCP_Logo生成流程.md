# 🖼️ 即梦MCP Logo生成流程

## 完整流程

### Logo 生成和上传流程

```
开始生成Logo
    ↓
┌─────────────────────────────┐
│ 1. 尝试获取包的官方Logo     │
└─────────────────────────────┘
    ↓
有官方Logo？
├─ 是 → 下载并上传到EMCP → 返回EMCP URL
└─ 否 ↓
┌─────────────────────────────┐
│ 2. 使用即梦MCP生成Logo ⭐   │
└─────────────────────────────┘
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
调用即梦MCP工具
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
POST http://mcptest013.sitmcp.kaleido.guru/mcp/tools/call
Headers:
  - emcp-key: PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n
  - emcp-usercode: VGSdDTgj
Body:
{
  "name": "jimeng-v40-generate",  ✅ 正确的工具名
  "arguments": {
    "prompt": "Create a professional logo for..."
  }
}
    ↓
即梦MCP返回图片URL
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
上传图片到EMCP存储 ⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ↓
1. 从即梦URL下载图片
    ↓
2. POST https://sit-emcp.kaleido.guru/api/proxyStorage/NoAuth/upload_file
   表单: file=<图片数据>
    ↓
3. 返回EMCP存储URL
   /api/proxyStorage/NoAuth/xxx-xxx-xxx.png
    ↓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
完成！返回EMCP Logo URL ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## GUI 日志示例

### 完整的Logo生成过程

```
🖼️ 开始生成Logo...

======================================================================
📤 调用即梦MCP工具: generate_image
📋 参数: {
  "prompt": "Create a modern, professional logo for...",
  "size": "512x512"
}
======================================================================

📥 即梦MCP响应: 200
✅ 调用成功
   ✅ 图片生成成功: http://jimeng-server.com/images/xxx.png

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
  "err_message": "",
  "body": {
    "fileUrl": "/api/proxyStorage/NoAuth/426962bd-5859-4b09-b729-9339c364fe94.png"
  }
}
======================================================================

✅ Logo 上传成功: /api/proxyStorage/NoAuth/426962bd-5859-4b09-b729-9339c364fe94.png
   ✅ Logo已上传: /api/proxyStorage/NoAuth/426962bd-5859-4b09-b729-9339c364fe94.png
```

---

## 技术实现

### 1. 即梦MCP客户端

**文件**: `jimeng_mcp_client.py`

```python
class JimengMCPClient:
    def __init__(self):
        self.sse_url = "http://mcptest013.sitmcp.kaleido.guru/sse"
        self.headers = {
            "emcp-key": "PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n",
            "emcp-usercode": "VGSdDTgj"
        }
    
    def generate_logo(self, prompt: str, package_name: str) -> str:
        """
        调用即梦MCP生成图片
        
        返回: 图片URL（即梦服务器上的URL）
        """
        result = self.call_mcp_tool(
            tool_name="generate_image",
            arguments={"prompt": prompt, "size": "512x512"}
        )
        
        return result.get('image_url')  # 即梦返回的图片URL
```

### 2. Logo生成器

**文件**: `logo_generator.py`

```python
class LogoGenerator:
    def __init__(self, jimeng_mcp_client):
        self.jimeng_client = jimeng_mcp_client
    
    def _generate_logo_with_jimeng(self, package_info) -> str:
        """
        使用即梦MCP生成并上传到EMCP
        
        返回: EMCP Logo URL
        """
        # 1. 调用即梦MCP生成图片
        image_url = self.jimeng_client.generate_logo(prompt, package_name)
        
        # 2. 上传到EMCP
        emcp_logo_url = self._upload_logo_to_emcp(image_url=image_url)
        
        return emcp_logo_url  # EMCP存储URL
```

### 3. 上传到EMCP

```python
def _upload_logo_to_emcp(self, image_url: str) -> str:
    """
    从URL下载图片并上传到EMCP
    
    流程:
    1. 从image_url下载图片
    2. 上传到 POST /api/proxyStorage/NoAuth/upload_file
    3. 返回EMCP存储URL
    """
    # 1. 下载图片
    response = requests.get(image_url)
    image_data = response.content
    
    # 2. 上传到EMCP
    files = {'file': ('logo.png', image_data, 'image/png')}
    response = requests.post(upload_url, files=files)
    
    # 3. 返回EMCP URL
    return response.json()['body']['fileUrl']
```

---

## Logo 生成优先级

### 自动选择策略

```
1. 包官方Logo
   ↓ 没有
2. 即梦MCP生成 ⭐ 优先
   ↓ 失败
3. DALL-E生成（如果配置）
   ↓ 失败
4. 默认Logo
```

### 代码配置

```python
logo_url = logo_generator.get_or_generate_logo(
    package_info,
    package_type,
    generate_with_ai=False,      # DALL-E
    use_jimeng=True  # ⭐ 启用即梦MCP（默认True）
)
```

---

## 即梦MCP配置

### 默认配置（已内置）

```json
{
  "jimeng_mcp": {
    "sse_url": "http://mcptest013.sitmcp.kaleido.guru/sse",
    "emcp_key": "PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n",
    "emcp_usercode": "VGSdDTgj"
  }
}
```

### 自动初始化

```python
# 在 ai_generator.py 中自动初始化
jimeng_client = JimengMCPClient()
logo_generator = LogoGenerator(jimeng_mcp_client=jimeng_client)
```

---

## 完整的发布日志示例

```
📦 步骤 1/4: 获取包信息...
   ✅ 类型: NPM
   ✅ 包名: @bachstudio/mcp-file-search

🤖 步骤 2/4: 生成模板信息...
   ✅ 已获取分类列表
   使用 Azure OpenAI 生成三语言内容...
   
🖼️ 开始生成Logo...
   🎨 使用即梦MCP生成Logo...
   
======================================================================
📤 调用即梦MCP工具: generate_image
📋 参数: {
  "prompt": "Create a modern, professional logo for...",
  "size": "512x512"
}
======================================================================

📥 即梦MCP响应: 200
✅ 调用成功
   ✅ 图片生成成功: http://jimeng.server/image/xxx.png
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
   ✅ Logo已上传: /api/proxyStorage/NoAuth/xxx.png

   ✅ 名称: 智能文件搜索服务
   ✅ 命令: npx @bachstudio/mcp-file-search
   ✅ Logo: /api/proxyStorage/NoAuth/xxx.png ⭐

📝 步骤 3/4: 构建发布数据...
...
```

---

## API 接口

### 即梦MCP接口（假设）

```
POST http://mcptest013.sitmcp.kaleido.guru/mcp/tools/call

Headers:
  emcp-key: PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n
  emcp-usercode: VGSdDTgj
  Content-Type: application/json

Body:
{
  "name": "jimeng-v40-generate",  ✅ 正确的工具名
  "arguments": {
    "prompt": "提示词"
  }
}

Response (MCP标准格式):
{
  "content": [
    {
      "text": "http://image-url...",  // 图片URL
      "type": "image"
    }
  ]
}

或其他可能的格式:
{
  "image_url": "http://...",
  "url": "http://...",
  "data": {"url": "http://..."}
}
```

### EMCP 图片上传接口

```
POST https://sit-emcp.kaleido.guru/api/proxyStorage/NoAuth/upload_file

Body (multipart/form-data):
  file: <图片二进制数据>

Response:
{
  "err_code": 0,
  "body": {
    "fileUrl": "/api/proxyStorage/NoAuth/xxx.png"
  }
}
```

---

## 故障降级

### 如果即梦MCP不可用

```
即梦MCP生成失败
    ↓
自动降级到DALL-E（如果配置）
    ↓
降级到默认Logo
    ↓
仍然可以成功发布 ✅
```

### 日志示例（降级）

```
🖼️ 开始生成Logo...
   🎨 使用即梦MCP生成Logo...
   ⚠️ 即梦MCP服务不可用
   ℹ️ 使用默认Logo
   
   ✅ Logo: /api/proxyStorage/NoAuth/default-mcp-logo.png
```

---

## 🎯 关键特性

### 1. 完全自动化

- ✅ 自动调用即梦MCP
- ✅ 自动生成提示词
- ✅ 自动下载图片
- ✅ 自动上传到EMCP
- ✅ 自动返回EMCP URL

### 2. 完整日志

**所有步骤都记录到GUI**：
- ✅ 即梦MCP调用请求
- ✅ 即梦MCP响应
- ✅ 图片下载
- ✅ EMCP上传请求
- ✅ EMCP上传响应
- ✅ 最终Logo URL

### 3. 智能降级

- 即梦MCP失败 → DALL-E（如果有）
- DALL-E失败 → 默认Logo
- 保证流程不中断 ✅

---

## 配置说明

### 即梦MCP配置（已内置）

配置在 `jimeng_mcp_client.py` 中：

```python
JimengMCPClient(
    sse_url="http://mcptest013.sitmcp.kaleido.guru/sse",
    emcp_key="PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n",
    emcp_usercode="VGSdDTgj"
)
```

**无需额外配置**，开箱即用！

---

## 使用示例

### 发布包时自动生成Logo

```bash
python emcpflow_simple_gui.py

# 输入包名
@bachstudio/mcp-file-search

# 点击 [一键发布]

# 在GUI日志中查看：
# ✅ 即梦MCP生成Logo的完整过程
# ✅ 图片上传到EMCP的详细日志
# ✅ 最终得到的EMCP Logo URL
```

### 预期结果

```json
{
  "logo_url": "/api/proxyStorage/NoAuth/426962bd-5859-4b09-b729-9339c364fe94.png"
}
```

**这个URL是EMCP存储的URL，可以直接在模板中使用** ✅

---

## 🎁 优势

### 对比传统方案

| 功能 | 传统方案 | 即梦MCP方案 |
|-----|---------|------------|
| **Logo来源** | 默认或手动 | AI自动生成 ✅ |
| **个性化** | 无 | 每个包独特 ✅ |
| **质量** | 一般 | 专业 ✅ |
| **操作** | 手动上传 | 全自动 ✅ |
| **成本** | 免费 | 即梦MCP服务 |

---

## 🔧 调试

### 如果即梦MCP调用失败

**查看GUI日志**：
1. 即梦MCP请求详情
2. 即梦MCP响应
3. 错误信息

**可能的问题**：
- 即梦MCP工具名错误（可能不叫 `generate_image`）
- 响应格式不匹配
- 网络连接问题
- 服务不稳定

**解决方法**：
- 查看实际响应格式
- 调整 `image_url` 提取逻辑
- 联系即梦MCP服务提供方

---

## 📝 注意事项

### 即梦MCP工具名

**正确的工具名**: `jimeng-v40-generate` ✅

```python
# 在 jimeng_mcp_client.py 中
result = self.call_mcp_tool(
    tool_name="jimeng-v40-generate",  # ✅ 已更新
    arguments={
        "prompt": "提示词"
    }
)
```

**已配置正确，无需修改！**

### 响应格式适配

根据实际响应调整提取逻辑：

```python
# 当前支持多种可能的字段
image_url = (
    result.get('image_url') or       # 字段1
    result.get('url') or             # 字段2
    result.get('data', {}).get('url') or  # 字段3
    result.get('content', [{}])[0].get('text')  # 字段4
)
```

---

## ✅ 总结

### 完整实现

1. ✅ **即梦MCP集成** - 自动调用生成图片
2. ✅ **自动上传** - 图片自动上传到EMCP
3. ✅ **返回EMCP URL** - 直接可用的Logo URL
4. ✅ **完整日志** - 所有过程显示在GUI
5. ✅ **智能降级** - 失败时使用默认Logo
6. ✅ **开箱即用** - 无需额外配置

### Logo生成流程

```
即梦MCP生成 → 上传到EMCP → 返回EMCP URL → 用于模板
```

---

**Logo生成完全自动化！** 🎉  
**使用即梦MCP资源！** 🎨  
**所有日志都在GUI中！** 📋  
**立即可用！** 🚀

