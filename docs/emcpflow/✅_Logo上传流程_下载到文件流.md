# ✅ Logo 上传流程 - 下载到文件流

## 📝 正确的上传流程

您提到的关键点：**生成的 logo 需要下载下来再提交文件流给接口** ✅

## 🔄 完整实现流程

### 步骤 1: 即梦 MCP 生成 Logo
```
即梦 MCP 生成
    ↓
返回图片 URL
例如: https://p9-aiop-sign.byteimg.com/tos-cn-i-vuqhorh59i/xxx.image
```

### 步骤 2: 下载图片到内存
```python
# logo_generator.py 第 316-320 行
response = requests.get(image_url, timeout=10)
response.raise_for_status()
image_data = response.content  # 二进制数据，存储在内存中
```

### 步骤 3: 构建文件流 (multipart/form-data)
```python
# logo_generator.py 第 340-343 行
files = {
    'file': (filename, image_data, 'image/png')
    #        --------  ----------  ------------
    #        文件名    二进制数据   MIME类型
}
```

### 步骤 4: 上传文件流到 EMCP
```python
# logo_generator.py 第 367 行
response = requests.post(
    upload_url,
    files=files,      # multipart/form-data 文件流
    headers=headers,  # 包含 token
    timeout=30
)
```

### 步骤 5: 解析响应，提取 fileUrl
```python
# logo_generator.py 第 367-370 行
data = response.json()
if data.get('err_code') == 0:
    file_url = data.get('body', {}).get('fileUrl')  # ✅ 正确提取
    return file_url
```

## 📊 完整的日志输出

现在一键发布时会看到详细的"下载 → 上传"过程：

```
🖼️ 开始生成Logo...
   🎨 使用即梦MCP生成Logo...
   📝 提示词: express Logo 设计:...
   
   🔌 连接即梦 MCP...
   ✅ 连接成功: de4ad82b-xxx
   🎨 使用工具: jimeng-v40-generate
   ⏳ 生成中...
   ✅ 即梦MCP生成成功!
   
   ⚠️ EMCP直接上传失败，尝试重新上传...
   📥 即梦URL: https://p9-aiop-sign.byteimg.com/tos-cn-i-vuqhorh59i...
   
   ⬇️ 下载图片: https://p9-aiop-sign.byteimg.com/tos-cn-i-vuqhorh59i...  ⭐ 步骤1
   ✅ 下载完成: 389,880 字节  ⭐ 二进制数据已在内存

======================================================================
📤 上传文件流到 EMCP  ⭐ 步骤2
   URL: https://sit-emcp.kaleido.guru/api/proxyStorage/NoAuth/upload_file
   文件名: logo.png
   大小: 389,880 字节  ⭐ 文件流大小
   Token: 9c665f60-b8e9-4ad8-b...
======================================================================

======================================================================
📥 响应: 200
{
  "err_code": 0,
  "body": {
    "fileUrl": "/api/proxyStorage/NoAuth/xxx.png"  ⭐ 步骤3: 提取 fileUrl
  }
}
======================================================================

✅ Logo 上传成功: /api/proxyStorage/NoAuth/xxx.png
✅ Logo已上传EMCP: /api/proxyStorage/NoAuth/xxx.png
```

## 🔧 技术实现细节

### 1. 下载图片 (内存中)

```python
# 从即梦 URL 下载
response = requests.get(image_url, timeout=10)
response.raise_for_status()

# 获取二进制数据 (不保存到磁盘)
image_data = response.content  # bytes 对象
```

**要点**:
- ✅ `response.content` 是二进制数据
- ✅ 数据在内存中，不写入磁盘
- ✅ 显示下载的字节数

### 2. 构建文件流

```python
# multipart/form-data 格式
files = {
    'file': (
        filename,      # 文件名 (如 'logo.png')
        image_data,    # 二进制数据 (bytes)
        'image/png'    # Content-Type
    )
}
```

**等价于 curl 中的**:
```bash
--data-raw $'------WebKitFormBoundary...\r\n
Content-Disposition: form-data; name="file"; filename="logo.png"\r\n
Content-Type: image/png\r\n\r\n
<二进制数据>\r\n
------WebKitFormBoundary...--\r\n'
```

### 3. 上传文件流

```python
# requests 会自动:
# 1. 设置 Content-Type: multipart/form-data
# 2. 生成 boundary
# 3. 编码文件数据
response = requests.post(
    url,
    files=files,        # 关键: files 参数
    headers=headers,    # token 等
    timeout=30
)
```

### 4. 解析响应

```python
data = response.json()
# {
#   "err_code": 0,
#   "body": {
#     "fileUrl": "/api/proxyStorage/NoAuth/xxx.png"  ✅
#   }
# }

file_url = data.get('body', {}).get('fileUrl')
```

## 📋 代码位置

### `logo_generator.py` - 主要实现

```python
def _upload_logo_to_emcp(self, image_url=None, image_path=None, base_url=...):
    # 第 314-335 行: 下载图片
    if image_url:
        LogoLogger.log(f"   ⬇️ 下载图片: {image_url[:60]}...")
        response = requests.get(image_url, timeout=10)
        image_data = response.content
        LogoLogger.log(f"   ✅ 下载完成: {len(image_data):,} 字节")
    
    # 第 337-343 行: 构建文件流
    files = {
        'file': (filename, image_data, 'image/png')
    }
    
    # 第 345-367 行: 添加 token 并上传
    headers = {'token': self.emcp_manager.session_key, ...}
    response = requests.post(upload_url, files=files, headers=headers, ...)
    
    # 第 367-370 行: 提取 fileUrl
    data = response.json()
    file_url = data.get('body', {}).get('fileUrl')
```

### `jimeng_logo_generator.py` - 独立工具

```python
def _upload_to_emcp(self, image_url, base_url):
    # 第 425-431 行: 下载图片
    print(f"   ⬇️ 下载图片: {image_url[:60]}...")
    response = requests.get(image_url, timeout=30)
    image_data = response.content
    print(f"   ✅ 下载完成: {len(image_data):,} 字节")
    
    # 第 436-439 行: 构建文件流
    files = {'file': ('logo.png', image_data, 'image/png')}
    
    # 第 441-447 行: 上传
    print(f"   📤 上传文件流到 EMCP...")
    response = requests.post(upload_url, files=files, ...)
    
    # 第 453-456 行: 提取 fileUrl
    logo_url = data.get('body', {}).get('fileUrl')
```

## 🎯 关键改进

### 1. 明确的日志
- ✅ 显示下载步骤和字节数
- ✅ 显示上传文件流信息
- ✅ 显示 fileUrl 提取结果

### 2. 完整的流程
```
即梦URL → [下载] → 二进制数据 → [构建文件流] → [上传] → fileUrl
```

### 3. 内存处理
- ✅ 不需要保存到临时文件
- ✅ 直接在内存中处理
- ✅ 效率更高

## 🔍 与 curl 对比

### curl 命令
```bash
curl 'https://sit-emcp.kaleido.guru/api/proxyStorage/NoAuth/upload_file' \
  -H 'token: 9c665f60-b8e9-4ad8-baf9-698625fdc1ee' \
  --data-raw $'------WebKitFormBoundary...\r\n
Content-Disposition: form-data; name="file"; filename="logo.png"\r\n
Content-Type: image/png\r\n\r\n
<二进制数据>\r\n
------WebKitFormBoundary...--\r\n'
```

### Python 等价代码
```python
# 下载
image_data = requests.get(image_url).content

# 构建文件流
files = {'file': ('logo.png', image_data, 'image/png')}

# 上传 (requests 自动处理 multipart/form-data)
response = requests.post(
    upload_url,
    files=files,
    headers={'token': token}
)
```

**优势**:
- ✅ 自动处理 boundary
- ✅ 自动设置 Content-Type
- ✅ 代码更简洁

## 📊 数据流转图

```
┌─────────────────┐
│  即梦 MCP 生成  │
└────────┬────────┘
         │ 返回 URL
         ↓
┌─────────────────────────────┐
│  步骤 1: 下载图片到内存      │
│  image_data = response.content │  ⭐ 二进制数据
└────────┬────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  步骤 2: 构建文件流          │
│  files = {                   │
│    'file': (name, data, type)│  ⭐ multipart/form-data
│  }                           │
└────────┬────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  步骤 3: POST 上传           │
│  headers = {'token': ...}    │  ⭐ 带认证
│  requests.post(files=files)  │
└────────┬────────────────────┘
         │
         ↓
┌─────────────────────────────┐
│  步骤 4: 解析响应            │
│  fileUrl = body.fileUrl      │  ⭐ 正确提取
└─────────────────────────────┘
```

## ✅ 验证清单

- [x] ✅ 从 URL 下载图片
- [x] ✅ 获取二进制数据 (response.content)
- [x] ✅ 构建 multipart/form-data 文件流
- [x] ✅ 添加 token header
- [x] ✅ 上传文件流
- [x] ✅ 解析 body.fileUrl
- [x] ✅ 详细的日志输出
- [x] ✅ 显示下载/上传字节数

## 🧪 测试验证

### 运行测试
```bash
python emcpflow_simple_gui.py
```

### 观察日志
应该看到：
```
⬇️ 下载图片: https://...  ✅ 下载步骤
✅ 下载完成: 389,880 字节  ✅ 二进制数据大小

📤 上传文件流到 EMCP     ✅ 上传步骤
   大小: 389,880 字节      ✅ 文件流大小

📥 响应: 200
   fileUrl: /api/proxyStorage/NoAuth/xxx.png  ✅ 正确提取
```

---

**总结**: 代码已正确实现"下载 → 文件流 → 上传"的完整流程，现在日志更详细，清楚显示每个步骤！✅

**更新时间**: 2025-11-06  
**开发**: 巴赫工作室 (BACH Studio)

**Made with ❤️ by 巴赫工作室**

