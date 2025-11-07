# ✅ Logo 上传 - 自动重登录重试

## 🎯 用户反馈

> "我发现上传图片401后，你竟然不进行登录获取最新token，直接跳过了"

**问题**：当上传图片遇到 401 Unauthorized（token 过期）时，代码直接失败，没有尝试重新登录。

## ✅ 解决方案

### 新增功能：401 自动重登录重试

当检测到 401 错误时：
1. ⚠️ **检测 401** - Token 可能已过期
2. 🔄 **自动重新登录** - 获取新的 token
3. 🔄 **重试上传** - 使用新 token 重新上传
4. ✅ **成功或降级** - 成功则返回 URL，失败则使用默认 logo

## 🔧 技术实现

### 修改的文件

**`logo_generator.py`** - `_upload_logo_to_emcp()` 方法

### 核心逻辑

```python
def _upload_logo_to_emcp(
    self,
    image_url: str = None,
    image_path: str = None,
    base_url: str = "https://sit-emcp.kaleido.guru",
    _retry_count: int = 0  # ⭐ 新增：避免无限循环
) -> str:
    # ... 下载图片，构建文件流 ...
    
    # 上传文件流
    response = requests.post(upload_url, files=files, headers=headers, timeout=30)
    
    # ⭐ 检查 401 错误（token 过期）
    if response.status_code == 401 and _retry_count == 0:
        LogoLogger.log(f"\n⚠️ 收到 401 Unauthorized - Token 可能已过期")
        
        # ⭐ 尝试重新登录
        if self.emcp_manager:
            LogoLogger.log(f"🔄 尝试重新登录 EMCP...")
            
            # 1. 加载登录凭据
            from config_manager import ConfigManager
            config_mgr = ConfigManager()
            creds = config_mgr.load_emcp_credentials()
            
            if creds:
                # 2. 重新登录
                login_result = self.emcp_manager.login(
                    creds['phone_number'],
                    creds['validation_code']
                )
                
                if login_result:
                    LogoLogger.log(f"✅ 重新登录成功，获得新 token")
                    LogoLogger.log(f"🔄 重试上传...")
                    
                    # 3. ⭐ 重试上传（_retry_count=1 避免无限循环）
                    return self._upload_logo_to_emcp(
                        image_url=image_url,
                        image_path=image_path,
                        base_url=base_url,
                        _retry_count=1  # ⭐ 只重试一次
                    )
    
    # 正常处理响应...
```

## 📊 完整流程

### 正常情况（Token 有效）

```
1. 下载图片
   ↓
2. 上传到 EMCP (带 token)
   ↓
3. 收到 200 响应
   ↓
4. 提取 fileUrl
   ↓
5. ✅ 返回 EMCP URL
```

### Token 过期情况（401 错误）

```
1. 下载图片
   ↓
2. 上传到 EMCP (带旧 token)
   ↓
3. ⚠️ 收到 401 Unauthorized
   ↓
4. 🔄 检测到 401 错误
   ↓
5. 🔄 重新登录 EMCP
   ├─ 加载登录凭据
   ├─ 调用 login() 方法
   └─ 获得新的 session_key
   ↓
6. 🔄 重试上传 (带新 token)
   ↓
7. 收到 200 响应
   ↓
8. 提取 fileUrl
   ↓
9. ✅ 返回 EMCP URL
```

### 重新登录失败

```
1-4. (同上)
   ↓
5. 🔄 尝试重新登录
   ↓
6. ❌ 登录失败
   ↓
7. 使用默认 Logo
   ↓
8. 返回 /api/proxyStorage/NoAuth/default-mcp-logo.png
```

## 📋 详细日志输出

### 场景 1: 第一次上传成功

```
⬇️ 下载图片: https://p3-aiop-sign.byteimg.com/...
✅ 下载完成: 161,797 字节

======================================================================
📤 上传文件流到 EMCP
   URL: https://sit-emcp.kaleido.guru/api/proxyStorage/NoAuth/upload_file
   Token: ca47253b-c2a1-4629-b...
======================================================================

======================================================================
📥 响应: 200
{
  "err_code": 0,
  "body": {
    "fileUrl": "/api/proxyStorage/NoAuth/xxx.png"
  }
}
======================================================================

✅ Logo 上传成功: /api/proxyStorage/NoAuth/xxx.png
```

### 场景 2: Token 过期，自动重登录成功 ⭐

```
⬇️ 下载图片: https://p3-aiop-sign.byteimg.com/...
✅ 下载完成: 161,797 字节

======================================================================
📤 上传文件流到 EMCP
   Token: ca47253b-c2a1-4629-b... (旧token)
======================================================================

⚠️ 收到 401 Unauthorized - Token 可能已过期  ⭐
🔄 尝试重新登录 EMCP...  ⭐

======================================================================
📤 HTTP 请求: POST https://sit-emcp.kaleido.guru/api/Login/login
======================================================================

======================================================================
📥 HTTP 响应: 200
   SessionKey: f8d92bc1-3e45-4d28-a...  (新token)
======================================================================

✅ 重新登录成功，获得新 token  ⭐
🔄 重试上传...  ⭐

⬇️ 下载图片: https://p3-aiop-sign.byteimg.com/...
✅ 下载完成: 161,797 字节

======================================================================
📤 上传文件流到 EMCP
   Token: f8d92bc1-3e45-4d28-a... (新token)  ⭐
======================================================================

======================================================================
📥 响应: 200
{
  "err_code": 0,
  "body": {
    "fileUrl": "/api/proxyStorage/NoAuth/xxx.png"
  }
}
======================================================================

✅ Logo 上传成功: /api/proxyStorage/NoAuth/xxx.png  ✅
```

### 场景 3: Token 过期，重新登录也失败

```
⚠️ 收到 401 Unauthorized - Token 可能已过期
🔄 尝试重新登录 EMCP...

======================================================================
📤 HTTP 请求: POST https://sit-emcp.kaleido.guru/api/Login/login
======================================================================

======================================================================
📥 HTTP 响应: 400
   错误: 验证码错误
======================================================================

❌ 重新登录失败
❌ Token 过期且重新登录失败，使用默认 logo

返回值: "/api/proxyStorage/NoAuth/default-mcp-logo.png"
```

## 🎯 关键特性

### 1. 智能检测
```python
if response.status_code == 401 and _retry_count == 0:
```
- ✅ 只在首次遇到 401 时重试
- ✅ 避免无限循环（_retry_count 限制）

### 2. 自动重新登录
```python
login_result = self.emcp_manager.login(
    creds['phone_number'],
    creds['validation_code']
)
```
- ✅ 使用保存的凭据
- ✅ 自动获取新 token
- ✅ 更新 session_key

### 3. 递归重试
```python
return self._upload_logo_to_emcp(
    image_url=image_url,
    image_path=image_path,
    base_url=base_url,
    _retry_count=1  # 避免无限循环
)
```
- ✅ 使用新 token 重试
- ✅ _retry_count=1 防止再次重试
- ✅ 保持原始参数

### 4. 优雅降级
```python
# 重新登录失败
return self.default_logo
```
- ✅ 不阻断发布流程
- ✅ 使用默认 logo
- ✅ 保存本地备份

## 🔒 安全措施

### 防止无限循环
```python
_retry_count: int = 0  # 参数
```

**第一次上传**：
- `_retry_count = 0`
- 遇到 401 → 重新登录 → 重试

**重试上传**：
- `_retry_count = 1`
- 遇到 401 → 不再重试，使用默认 logo

### 异常处理
```python
try:
    # 重新登录逻辑
except Exception as login_error:
    LogoLogger.log(f"❌ 重新登录异常: {login_error}")
```
- ✅ 捕获登录异常
- ✅ 记录错误日志
- ✅ 返回默认 logo

## 💡 优势

### 1. 用户体验
- ✅ **无感知** - 自动处理 token 过期
- ✅ **高成功率** - token 过期不影响发布
- ✅ **透明** - 详细日志显示过程

### 2. 健壮性
- ✅ **自动恢复** - token 过期自动刷新
- ✅ **避免死循环** - 只重试一次
- ✅ **优雅降级** - 失败时使用默认 logo

### 3. 维护性
- ✅ **清晰逻辑** - 代码易于理解
- ✅ **详细日志** - 便于调试
- ✅ **可扩展** - 易于添加其他重试策略

## 🧪 测试场景

### 测试 1: Token 有效
1. 正常登录
2. 上传图片
3. ✅ 直接成功

### 测试 2: Token 过期
1. 手动让 token 过期（或等待）
2. 上传图片
3. ⚠️ 收到 401
4. 🔄 自动重新登录
5. 🔄 重试上传
6. ✅ 成功

### 测试 3: 登录凭据失效
1. Token 过期
2. 上传图片
3. ⚠️ 收到 401
4. 🔄 尝试重新登录
5. ❌ 登录失败（验证码过期）
6. 使用默认 logo

## 📊 对比

### 修复前 ❌

```
上传 → 401 → ❌ 直接失败 → 使用默认 logo
```

**问题**：
- Token 过期就失败
- 不尝试恢复
- 浪费已生成的 logo

### 修复后 ✅

```
上传 → 401 → 🔄 重新登录 → 🔄 重试 → ✅ 成功
```

**优势**：
- 自动恢复
- 提高成功率
- 用户无感知

## ✅ 总结

### 核心改进

1. **401 检测** - 识别 token 过期
2. **自动重登录** - 获取新 token
3. **智能重试** - 使用新 token 重新上传
4. **防止循环** - 最多重试一次
5. **优雅降级** - 失败时使用默认 logo

### 适用场景

- ✅ Token 过期
- ✅ 长时间未使用
- ✅ Session 失效
- ✅ 多个并发请求

### 用户价值

- 🎯 **更高成功率** - token 过期不再失败
- 🚀 **无缝体验** - 自动处理，用户无感知
- 📊 **透明可控** - 详细日志显示全过程

---

**实现时间**: 2025-11-06  
**核心功能**: 401 自动重登录重试  
**影响范围**: Logo 上传功能  
**开发**: 巴赫工作室 (BACH Studio)

**Made with ❤️ by 巴赫工作室**

