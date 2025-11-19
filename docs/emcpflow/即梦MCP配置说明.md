# 即梦 MCP 配置说明

## ⚠️ 重要提示

即梦 MCP 的 `emcp-key` 和 `emcp-usercode` 是**个人认证凭证**，需要您自己申请和配置，**切勿使用文档中的示例值**！

## 📋 配置步骤

### 1. 申请即梦 MCP 凭证

请联系即梦团队获取您的专属凭证：
- `emcp-key`: 您的 API 密钥
- `emcp-usercode`: 您的用户代码

### 2. 配置到项目中

打开项目根目录的 `config.json` 文件（如果没有，请复制 `config_template.json` 并重命名为 `config.json`）：

```json
{
  "jimeng": {
    "enabled": true,
    "mcp_url": "http://mcptest013.sitmcp.kaleido.guru/sse",
    "emcp_key": "YOUR_EMCP_KEY_HERE",
    "emcp_usercode": "YOUR_EMCP_USERCODE_HERE",
    "_note": "即梦 MCP Logo 生成配置，需要自己申请 emcp-key 和 emcp-usercode"
  }
}
```

将 `YOUR_EMCP_KEY_HERE` 和 `YOUR_EMCP_USERCODE_HERE` 替换为您申请到的真实凭证。

### 3. 验证配置

运行测试脚本验证配置是否正确：

```bash
python tests/test_jimeng_mcp_v2.py
```

如果配置正确，应该能成功连接到即梦 MCP 服务器并生成图片。

## 🔒 安全注意事项

1. **切勿提交凭证到 Git**
   - `config.json` 已经在 `.gitignore` 中，不会被提交
   - 确保不要将凭证硬编码到代码中

2. **保护您的凭证**
   - 不要在公开场合分享您的 `emcp-key` 和 `emcp-usercode`
   - 如果凭证泄露，请立即联系即梦团队重置

3. **团队协作**
   - 每个团队成员应使用自己的凭证
   - 或者使用团队共享的凭证（需要妥善保管）

## 📖 文档中的示例

文档中出现的以下值**仅为示例**，不能直接使用：

```json
"emcp-key": "PI1EQcsELJ7uPJnL3VNS89UaNIgRkL8n",  // ❌ 示例值，请替换
"emcp-usercode": "VGSdDTgj"  // ❌ 示例值，请替换
```

## ❓ 常见问题

### Q: 我没有即梦 MCP 凭证，还能使用这个工具吗？

A: 可以，但 Logo 自动生成功能将被禁用。您需要：
1. 在 `config.json` 中设置 `"jimeng": {"enabled": false}`
2. 或者手动提供 Logo URL

### Q: 如何申请即梦 MCP 凭证？

A: 请联系即梦团队或 EMCP 平台管理员获取申请流程。

### Q: 凭证有使用限制吗？

A: 具体限制取决于您的账号类型，请咨询即梦团队了解详情。

## 📞 联系支持

如有配置问题，请联系：
- 即梦团队：获取凭证和使用支持
- RepoFlow 开发者：代码和集成相关问题

