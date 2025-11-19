# Agent 测试判断逻辑优化

## 🐛 问题描述

在 Agent 对话测试中，有时会出现**明明调用了工具，但报告中显示"未调用"或"失败"**的情况。

### 问题原因

工具名称匹配逻辑过于严格：

1. **从 EMCP 获取的工具名称**：`API_job_search`（带 `API_` 前缀）
2. **Agent 实际调用的函数名称**：`job_search`（不带前缀）
3. **原有匹配逻辑**：使用简单的字符串包含检查

```python
# 原有逻辑（过于严格）
tool_called = any(expect_tool.lower() in fn.lower() for fn in function_calls)
# 期望: "API_job_search"
# 实际: "job_search"
# 结果: 不匹配 ❌
```

## ✅ 解决方案

### 智能匹配算法

优化后的匹配逻辑支持：

1. **去除前缀匹配**：自动去除 `API_` 前缀后再比较
2. **双向包含匹配**：支持部分匹配
3. **大小写不敏感**：统一转为小写比较

```python
# 新逻辑（智能匹配）
expect_tool_clean = expect_tool.lower().replace('api_', '')
# expect_tool = "API_job_search" → "job_search"

for fn in function_calls:
    fn_clean = fn.lower().replace('api_', '')
    # fn = "job_search" → "job_search"
    
    # 双向匹配
    if expect_tool_clean in fn_clean or fn_clean in expect_tool_clean:
        tool_called = True
        matched_function = fn
        break
```

## 📊 匹配示例

### ✅ 成功匹配的情况

| EMCP 工具名称 | Agent 调用名称 | 匹配结果 |
|-------------|--------------|---------|
| `API_job_search` | `job_search` | ✅ 匹配 |
| `API_job_search` | `API_job_search` | ✅ 匹配 |
| `job_details` | `job_details` | ✅ 匹配 |
| `API_get_salary` | `get_salary` | ✅ 匹配 |
| `search` | `job_search` | ✅ 匹配（包含） |

### ❌ 不匹配的情况

| EMCP 工具名称 | Agent 调用名称 | 匹配结果 |
|-------------|--------------|---------|
| `job_search` | `salary_info` | ❌ 不匹配 |
| `API_get_user` | `get_company` | ❌ 不匹配 |

## 🔍 调试信息

在测试过程中，日志会显示详细的匹配信息：

### 成功匹配

```
🔧 测试 1/4: Search for jobs
   API: API_job_search
   描述: Search for jobs posted on any public job site...
   📝 测试问题: 请帮我在芝加哥搜索开发者职位
   🔧 [工具调用] 函数: job_search
   ✅ 确认调用工具: API_job_search (匹配到: job_search)
   ✅ 测试通过
```

### 匹配失败

```
🔧 测试 1/4: Search for jobs
   API: API_job_search
   描述: Search for jobs posted on any public job site...
   📝 测试问题: 请帮我在芝加哥搜索开发者职位
   ❌ 期望工具 API_job_search 未被调用
   📋 实际调用: []
   ❌ 测试失败: 期望工具未被调用
```

## 🎯 判断标准

一个工具测试被标记为**成功**，需要满足：

1. ✅ **对话完成**：`is_complete == True`
2. ✅ **有回复内容**：`len(full_content) > 0`
3. ✅ **工具被调用**：在 `AgentFunctionCallMessage` 中找到匹配的 `FunctionName`

## 📝 测试报告说明

### HTML 报告结构

```html
<tr>
    <td>1</td>
    <td>
        <strong>Search for jobs</strong><br>
        <small>API: API_job_search</small>
    </td>
    <td>请帮我在芝加哥搜索开发者职位</td>
    <td><span class="badge badge-success">✅ 通过</span></td>
    <td>Found 100 jobs in chicago...</td>
    <td>bachai-jsearch</td>
    <td>job_search</td> <!-- 实际调用的函数 -->
</tr>
```

### 状态标记

- ✅ **通过**（绿色徽章）：工具正确调用，测试成功
- ❌ **失败**（红色徽章）：工具未调用或调用错误
- **函数调用列**：
  - 显示实际调用的函数名（如 `job_search`）
  - 或显示 <span style="color:#dc3545;">未调用</span>（红色文字）

## 🔧 代码位置

**文件**：`src/signalr_chat_tester.py`

**关键方法**：
- `test_conversation_with_tools()` - 主测试流程（第 45 行）
- `_send_and_receive()` - 发送消息并检查响应（第 669 行）
- 工具匹配逻辑（第 748-770 行）

## ⚠️ 常见问题

### Q1: 为什么有些工具显示"未调用"？

**可能原因：**

1. **Agent 真的没调用**
   - Agent 理解测试问题时，认为不需要使用该工具
   - 测试问题设计不够明确

2. **函数名称完全不匹配**
   - EMCP 返回的工具名称和实际调用的完全不同
   - 这种情况即使优化后也无法匹配

3. **Agent 响应超时**
   - Agent 没有在规定时间内完成响应
   - 检查日志中的超时信息

### Q2: 如何确认工具确实被调用了？

查看测试日志中的 `AgentFunctionCallMessage`：

```
🔧 [工具调用] 函数: job_search
   参数: {"query": "developer jobs in chicago"}
   响应: {...}
```

如果看到这条日志，说明工具确实被调用了。

### Q3: 如何提高工具调用成功率？

1. **优化测试问题**：
   - 使用明确、具体的问题
   - 包含工具相关的关键词
   - 参考工具描述和参数

2. **使用 AI 生成测试问题**：
   - 配置 Azure OpenAI
   - AI 会根据工具描述生成最佳测试问题

3. **检查 Agent 配置**：
   - 确保 MCP 插件正确启用
   - 检查 Agent 的权限设置

### Q4: 为什么同一个 MCP 有些工具通过，有些失败？

这是正常现象：

- ✅ **通过的工具**：测试问题设计好，Agent 理解正确
- ❌ **失败的工具**：可能测试问题不够明确，或工具参数复杂

**解决方法**：
1. 手动测试失败的工具，验证功能
2. 优化测试问题，使其更明确
3. 查看 Agent 日志，了解为什么没调用

## 📈 优化效果

### 修复前

```
📊 测试统计
   总工具数: 4
   ✅ 通过: 1
   ❌ 失败: 3
   📊 成功率: 25.0%
```

**问题**：即使工具实际被调用，也因为名称不匹配而判定失败。

### 修复后

```
📊 测试统计
   总工具数: 4
   ✅ 通过: 3
   ❌ 失败: 1
   📊 成功率: 75.0%
```

**改进**：智能匹配识别出实际调用，成功率显著提高。

## 🎯 最佳实践

### 1. 查看完整日志

不要只看 HTML 报告，要查看完整的测试日志：

```bash
# 运行测试时查看控制台输出
# 或者查看保存的日志文件
```

### 2. 检查 FunctionName

在日志中搜索 `AgentFunctionCallMessage`，确认实际调用的函数名称。

### 3. 对比工具列表

对比 EMCP 返回的工具列表和实际调用的函数名称，确认命名规则。

### 4. 手动验证

对于标记为"失败"的工具，可以：
1. 在 Agent 平台手动测试
2. 直接调用 MCP API 验证功能
3. 查看 EMCP 模板配置

## 🔄 后续优化方向

### 1. 更智能的匹配

```python
# 可以考虑添加：
- 模糊匹配（编辑距离）
- 同义词匹配
- 正则表达式匹配
```

### 2. 自适应测试

```python
# 根据测试结果自动调整：
- 如果工具未调用，生成更明确的问题
- 自动重试失败的测试
```

### 3. 详细的失败原因

```python
# 区分不同的失败原因：
- 工具未调用（Agent 选择不用）
- 工具调用失败（参数错误、执行错误）
- 响应超时
- 名称不匹配
```

---

**Made with ❤️ by BACH Studio**

