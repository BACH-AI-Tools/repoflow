# Logo 功能说明

## 📌 概述

EMCPFlow 提供了多种 Logo 获取和生成方案，满足不同需求。

---

## 🎨 Logo 方案

### 方案 1: 使用默认 Logo（推荐）

**特点**：
- ✅ 无需配置
- ✅ 立即可用
- ✅ 零成本

**Logo URL**：
```
/api/proxyStorage/NoAuth/default-mcp-logo.png
```

**适用场景**：
- 快速发布
- 不在意 Logo 个性化
- 测试环境

---

### 方案 2: 使用包官方 Logo

**特点**：
- ✅ 来自包的官方资源
- ✅ 自动识别
- ✅ 专业可靠

**支持来源**：
- PyPI 包的 project_urls
- NPM 包的 repository
- Docker Hub 的官方图标

**实现**：
系统会自动尝试从包信息中提取 logo，如果找不到则使用默认 logo。

**适用场景**：
- 包有官方 logo
- 希望保持品牌一致性

---

### 方案 3: 使用 DALL-E 生成（高级功能）

**特点**：
- 🎨 AI 自动生成
- 🎨 个性化设计
- 💰 需要成本

**要求**：
1. Azure OpenAI 资源
2. 部署 DALL-E 模型（dall-e-3 或 dall-e-2）
3. 配置额外的部署名称

**配置**：
```json
{
  "azure_openai": {
    "azure_endpoint": "https://your-resource.openai.azure.com/",
    "api_key": "your-api-key",
    "deployment_name": "gpt-4o",
    "dalle_deployment": "dall-e-3"
  }
}
```

**成本**：
- DALL-E 3: 约 $0.04/张图片
- DALL-E 2: 约 $0.018/张图片

**注意事项**：
- ⚠️ 生成的图片需要上传到 EMCP 存储
- ⚠️ 需要额外的 API 配额
- ⚠️ 生成时间较长（10-30秒）

**适用场景**：
- 需要独特的 logo
- 预算充足
- 不赶时间

---

### 方案 4: 手动指定 Logo URL

**特点**：
- ✅ 完全自定义
- ✅ 使用自己的图片
- ✅ 灵活可控

**方法**：

#### 方法 A: 修改配置文件
```json
{
  "default_logo_url": "https://your-cdn.com/your-logo.png"
}
```

#### 方法 B: 在代码中指定
```python
# 在 ai_generator.py 或 emcp_manager.py 中修改默认值
self.default_logo = "https://your-logo-url.png"
```

**适用场景**：
- 已有公司/项目 logo
- 需要统一品牌形象
- 对 logo 有特殊要求

---

## 🔧 当前实现

### 自动 Logo 获取流程

```
输入包信息
    ↓
1. 尝试从包信息获取官方 logo
    ├─ PyPI: project_urls['Logo']
    ├─ NPM: repository.logo
    └─ Docker: Docker Hub logo
    ↓
2. 如果找不到，且启用了 AI 生成
    └─ 使用 DALL-E 生成
    ↓
3. 否则使用默认 logo
    └─ /api/proxyStorage/NoAuth/default-mcp-logo.png
```

### 代码位置

- `logo_generator.py` - Logo 生成器
- `ai_generator.py` - AI 集成
- `emcp_manager.py` - 默认配置

---

## 💡 推荐方案

### 一般用户（推荐）

**方案 1: 使用默认 Logo**

原因：
- ✅ 最简单
- ✅ 无需配置
- ✅ 零成本
- ✅ 立即可用

### 企业用户

**方案 4: 手动指定 Logo**

原因：
- ✅ 统一品牌形象
- ✅ 使用公司 logo
- ✅ 完全可控

### 高级用户

**方案 3: DALL-E 生成**

原因：
- 🎨 个性化设计
- 🎨 AI 自动生成
- 🎨 独一无二

---

## 📝 使用示例

### 示例 1: 使用默认 Logo（无需配置）

```python
# 运行程序
python emcpflow_simple_gui.py

# 输入包名
requests

# 点击发布
# Logo 自动使用: /api/proxyStorage/NoAuth/default-mcp-logo.png
```

### 示例 2: 启用 Logo 自动获取

```python
# logo_generator.py 会自动尝试从包信息获取
# 如果包有官方 logo，会自动使用
# 否则使用默认 logo
```

### 示例 3: 启用 DALL-E 生成（需要配置）

```python
# 1. 配置 DALL-E 部署
# config.json:
{
  "azure_openai": {
    "dalle_deployment": "dall-e-3"
  }
}

# 2. 在代码中启用
ai_generator = AITemplateGenerator(
    azure_endpoint=endpoint,
    api_key=key,
    enable_logo_generation=True  # 启用 Logo 生成
)
```

---

## ⚙️ 配置选项

### 在 ConfigManager 中添加 Logo 配置

```python
# config_manager.py

def save_logo_config(self, default_logo_url: str = None, enable_dalle: bool = False):
    """保存 Logo 配置"""
    self._config['logo'] = {
        'default_url': default_logo_url or '/api/proxyStorage/NoAuth/default-mcp-logo.png',
        'enable_dalle': enable_dalle,
    }
    self.save_config(self._config)
```

---

## 🎯 未来计划

### 计划功能

- [ ] 从 GitHub 自动获取项目 logo
- [ ] 简单文字 logo 生成（使用 PIL）
- [ ] Logo 缓存机制
- [ ] 批量生成 logo
- [ ] Logo 预览功能

---

## ❓ 常见问题

### Q1: 必须配置 Logo 吗？

**A**: 不必须。系统会自动使用默认 logo，无需配置。

### Q2: DALL-E 生成 Logo 需要额外费用吗？

**A**: 是的。DALL-E API 调用需要付费，具体费用见 Azure OpenAI 定价。

### Q3: 可以使用自己的 Logo 吗？

**A**: 可以。上传到公开可访问的 CDN，然后在配置中指定 URL 即可。

### Q4: Logo 必须是什么格式？

**A**: 推荐 PNG 格式，512x512 像素，支持透明背景。

### Q5: Logo 生成失败怎么办？

**A**: 系统会自动降级到默认 logo，不会影响发布流程。

---

## 🔗 相关资源

- **Azure OpenAI 定价**: https://azure.microsoft.com/pricing/details/cognitive-services/openai-service/
- **DALL-E 文档**: https://platform.openai.com/docs/guides/images
- **Logo 设计指南**: https://www.canva.com/learn/logo-design/

---

**总结**：对于大多数用户，使用默认 Logo 即可满足需求。如有特殊要求，可以选择手动指定或 AI 生成。


