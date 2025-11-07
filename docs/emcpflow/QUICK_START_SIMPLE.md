# EMCPFlow 快速开始指南 🚀

## 5分钟上手

### 第一步：安装依赖

```bash
pip install -r requirements.txt
```

### 第二步：运行程序

```bash
python emcpflow_simple_gui.py
```

### 第三步：配置（仅首次）

点击 `[设置]` 按钮，填写：

#### EMCP 登录凭据（必需）
- **手机号**: 您的 EMCP 账号
- **验证码**: 固定验证码

#### Azure OpenAI（可选）
- **Endpoint**: `https://your-resource.openai.azure.com/`
- **API Key**: 您的 API Key
- **Deployment**: `gpt-4`

点击 `[保存]`

### 第四步：发布包

1. 在输入框中输入包地址，例如：
   ```
   https://pypi.org/project/requests
   ```
   或直接输入包名：
   ```
   requests
   ```

2. 点击 `[🚀 一键发布]`

3. 等待处理完成（通常 10-30 秒）

4. 看到 "🎉 发布完成！" 即成功

---

## 支持的输入示例

### PyPI 包
```
https://pypi.org/project/requests
requests
numpy
pandas
```

### NPM 包
```
https://www.npmjs.com/package/express
express
@vue/cli
react
```

### Docker 镜像
```
https://hub.docker.com/r/nginx/nginx
nginx/nginx
mysql/mysql-server
username/my-image
```

---

## 常见问题

### ❓ 提示 "未登录 EMCP 平台"？

**解决**: 点击 `[设置]`，填写手机号和验证码，保存后会自动登录。

### ❓ 提示 "无法识别的包"？

**解决**: 
1. 检查包名是否正确
2. 尝试使用完整的 URL
3. 确认包在对应平台上存在

### ❓ 不想配置 Azure OpenAI？

**没问题！** 不配置 AI 也能使用，会使用基础生成器自动生成模板信息。

### ❓ 想要更好的模板描述？

**配置 Azure OpenAI！** AI 生成的描述更专业、更吸引人。

---

## 配置文件位置

```
Windows: C:\Users\<用户名>\.emcpflow\config.json
Linux/Mac: ~/.emcpflow/config.json
```

可以手动编辑此文件：

```json
{
  "emcp_credentials": {
    "phone_number": "17610785055",
    "validation_code": "11202505"
  },
  "azure_openai": {
    "azure_endpoint": "https://your-resource.openai.azure.com/",
    "api_key": "your-api-key",
    "deployment_name": "gpt-4",
    "api_version": "2024-02-15-preview"
  }
}
```

---

## 测试示例

### 快速测试 - 发布 requests 包

```bash
# 1. 运行程序
python emcpflow_simple_gui.py

# 2. 在输入框中输入
requests

# 3. 点击 [一键发布]
```

预期结果：
```
📦 步骤 1/4: 获取包信息...
   ✅ 类型: PYPI
   ✅ 包名: requests
   ✅ 版本: 2.31.0

🤖 步骤 2/4: 生成模板信息...
   ✅ 名称: Requests
   ✅ 简介: Python HTTP for Humans.
   ✅ 命令: python -m requests

📝 步骤 3/4: 构建发布数据...
   ✅ 模板数据已构建

🌐 步骤 4/4: 发布到 EMCP 平台...
   ✅ 发布成功！

🎉 发布完成！
```

---

## 进阶使用

### 批量发布

可以多次使用，每次输入不同的包名：

```
第一次: requests
第二次: flask  
第三次: express
```

### 查看日志

所有操作日志都显示在界面下方的日志区域，可以：
- 查看详细处理过程
- 诊断错误原因
- 复制日志信息

---

**🎉 恭喜！您已掌握 EMCPFlow 的使用方法**

有问题？查看 [README.md](README.md) 获取更多信息。


