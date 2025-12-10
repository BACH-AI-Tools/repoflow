# GitHub 安全设置指南

## 🔐 推荐的安全配置

RepoFlow 创建的仓库会自动配置以下安全功能：

### 1. 漏洞警报（Vulnerability Alerts）

**所有仓库自动启用** ✅ 🆓

检测依赖包中的已知漏洞，并自动创建 Dependabot 警报。

### 2. Secret Scanning（密钥扫描）

| 仓库类型 | 状态 | 说明 |
|---------|------|------|
| **公开仓库** | 🆓 免费 | 自动启用，无需配置 |
| **私有仓库** | 💰 付费 | 需要 GitHub Advanced Security |

检测提交中的敏感信息（API Keys、Tokens、密码等）。

### 3. Push Protection（推送保护）

| 仓库类型 | 状态 | 说明 |
|---------|------|------|
| **公开仓库** | 🆓 免费 | 基于 Secret Scanning |
| **私有仓库** | 💰 付费 | 需要 GitHub Advanced Security |

阻止包含敏感信息的提交被推送到 GitHub。

---

## 🎯 两种配置方式

### 方案 1：仓库级别配置（推荐）🆓

**适用于：公开仓库**

1. 访问仓库设置：
   ```
   https://github.com/你的组织/你的仓库/settings/security_analysis
   ```

2. 启用以下功能：

#### ✅ Dependency graph（免费）
- 自动分析项目依赖

#### ✅ Dependabot alerts（免费）
- 漏洞警报

#### ✅ Dependabot security updates（免费）
- 自动创建 PR 修复漏洞

#### ✅ Secret scanning（公开仓库免费）
- 扫描所有提交中的敏感信息
- 检测已知的 Token 模式
- 支持 200+ 种密钥类型

#### ✅ Push protection（公开仓库免费）
- **最重要**：阻止包含敏感信息的推送
- 实时检测
- 提示用户删除敏感信息

**优点：**
- ✅ 完全免费
- ✅ 立即可用
- ✅ 无需组织权限

---

### 方案 2：组织级别配置（私有仓库）💰

**适用于：私有仓库**

需要 GitHub Advanced Security（付费功能）

1. 访问组织设置：
   ```
   https://github.com/organizations/你的组织名/settings/security_analysis
   ```

2. 启用 GitHub Advanced Security

3. 为所有（或指定）仓库启用安全功能

**优点：**
- ✅ 适用于私有仓库
- ✅ 统一管理
- ✅ 批量配置

**缺点：**
- ❌ 需要付费

---

## 🛡️ 工作原理

### 推送保护流程

```
开发者提交代码
     ↓
git push
     ↓
GitHub 扫描提交内容
     ↓
发现敏感信息？
     ├─ 是 → ❌ 阻止推送
     │        └─ 提示用户删除
     └─ 否 → ✅ 允许推送
```

### 检测的敏感信息类型

| 类型 | 示例 |
|------|------|
| **GitHub Token** | `ghp_xxxxxxxxxxxx` |
| **AWS Access Key** | `AKIA...` |
| **Azure Secret** | `xxx` |
| **Google API Key** | `AIza...` |
| **Stripe API Key** | `sk_live_...` |
| **数据库密码** | `password=xxx` |
| **私钥** | `-----BEGIN PRIVATE KEY-----` |
| **JWT Token** | `eyJ...` |

**支持 200+ 种密钥模式！**

---

## 📋 配置检查清单

### 对于公开仓库（推荐）🆓

仓库管理员：

- [ ] 访问仓库设置 → Security & analysis
- [ ] 启用 Dependency graph ✅
- [ ] 启用 Dependabot alerts ✅
- [ ] 启用 Dependabot security updates ✅
- [ ] 启用 Secret scanning ✅（免费）
- [ ] 启用 Push protection ✅（免费）
- [ ] 配置分支保护规则
- [ ] 禁止强制推送（force push）

**一切都是免费的！** 🎉

---

### 对于私有仓库 💰

组织管理员：

- [ ] 购买 GitHub Advanced Security
- [ ] 访问组织安全设置
- [ ] 启用 GitHub Advanced Security
- [ ] 为仓库启用 Secret scanning
- [ ] 为仓库启用 Push protection
- [ ] 配置自定义 secret 模式（可选）

仓库管理员：

- [ ] 确认继承组织安全设置
- [ ] 配置分支保护规则
- [ ] 启用 Required reviews（可选）
- [ ] 禁止强制推送（force push）

---

### 所有开发者

- [ ] 了解推送保护机制
- [ ] 不在代码中硬编码敏感信息
- [ ] 使用环境变量或密钥管理系统
- [ ] 使用 `.gitignore` 排除敏感文件

---

## 🚫 被阻止时怎么办？

### 场景 1：推送被阻止

```bash
$ git push
remote: error: Secret scanning found the following secrets:
remote: 
remote: - GitHub Personal Access Token (ghp_xxxx...)
remote:   Found in: config.py:15
remote: 
remote: Push blocked. Please remove the secret and try again.
```

**解决方法：**

1. 删除敏感信息
2. 提交修改
3. 重新推送

```bash
# 1. 编辑文件删除敏感信息
vim config.py

# 2. 提交
git add config.py
git commit -m "remove sensitive data"

# 3. 重新推送
git push
```

### 场景 2：已经推送了敏感信息

**立即行动：**

1. **撤销密钥** - 立即在服务提供商处撤销泄露的密钥
2. **删除历史** - 使用 `git filter-branch` 或 BFG Repo-Cleaner
3. **强制推送** - 清理后强制推送

```bash
# 使用 BFG Repo-Cleaner（推荐）
bfg --replace-text passwords.txt

# 或使用 git filter-branch
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch config/secrets.py' \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push --force --all
git push --force --tags
```

---

## 💡 最佳实践

### 1. 使用环境变量

```python
import os

# ❌ 错误
API_KEY = "sk_live_xxxxxxxxxxxxx"

# ✅ 正确
API_KEY = os.getenv("API_KEY")
```

### 2. 使用 .env 文件（不提交）

```bash
# .env
API_KEY=your_api_key_here
DATABASE_URL=postgres://user:pass@host/db
```

```python
# .gitignore
.env
.env.local
*.key
*.pem
```

### 3. 使用密钥管理服务

- **AWS Secrets Manager**
- **Azure Key Vault**
- **HashiCorp Vault**
- **GitHub Secrets**（CI/CD）

### 4. 代码审查

- 在 PR 中检查敏感信息
- 使用自动化工具辅助检查

---

## 🔗 相关链接

- [GitHub Secret Scanning 文档](https://docs.github.com/en/code-security/secret-scanning)
- [Push Protection 文档](https://docs.github.com/en/code-security/secret-scanning/push-protection-for-repositories-and-organizations)
- [Dependabot 文档](https://docs.github.com/en/code-security/dependabot)
- [分支保护规则](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)

---

## ✅ 启用后的好处

1. **自动保护** - 无需手动检查
2. **实时阻止** - 推送时立即检测
3. **全面覆盖** - 支持 200+ 种密钥类型
4. **历史扫描** - 扫描所有历史提交
5. **通知机制** - 发现问题立即通知
6. **完全免费** - 🆓 公开仓库完全免费！

---

## 💡 最佳选择

### 推荐方案

| 场景 | 推荐方案 | 费用 |
|------|---------|------|
| **开源项目** | 公开仓库 + 仓库级配置 | 🆓 免费 |
| **内部项目** | 私有仓库 + 组织级配置 | 💰 付费 |
| **混合场景** | 开源用公开，敏感用私有 | 部分免费 |

**推荐：尽可能使用公开仓库，享受免费的完整安全保护！** 🎁

---

**快速开始：创建公开仓库，立即启用所有安全功能！** 🛡️

