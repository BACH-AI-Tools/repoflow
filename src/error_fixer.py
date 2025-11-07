"""AI 错误修复器 - 让 LLM 自动识别并修复 API 错误"""

from openai import AzureOpenAI
import json
from typing import Dict, Optional, Tuple


class AIErrorFixer:
    """使用 LLM 自动修复 API 错误"""
    
    def __init__(self, azure_openai_client: AzureOpenAI, deployment_name: str = "gpt-4o"):
        """
        初始化错误修复器
        
        Args:
            azure_openai_client: Azure OpenAI 客户端
            deployment_name: 部署名称
        """
        self.client = azure_openai_client
        self.deployment_name = deployment_name
    
    def fix_template_data(
        self,
        template_data: Dict,
        error_response: Dict,
        error_message: str
    ) -> Optional[Dict]:
        """
        使用 LLM 分析错误并修复模板数据
        
        Args:
            template_data: 原始模板数据
            error_response: API 错误响应
            error_message: 错误信息
        
        Returns:
            修复后的模板数据，或 None（无法修复）
        """
        # 构建修复 prompt
        prompt = self._build_fix_prompt(template_data, error_response, error_message)
        
        try:
            # 调用 LLM 分析并修复
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个 API 错误诊断和修复专家。
你需要分析 EMCP 平台 API 的错误响应，找出问题所在，并修复数据。

常见问题：
1. 字段类型错误（如字符串传成了数字）
2. 必填字段缺失
3. 字段值不符合规则
4. 多语言数组格式错误

你必须返回修复后的完整数据，格式为 JSON。"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 降低温度，提高准确性
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            # 解析修复结果
            result_text = response.choices[0].message.content
            fixed_data = json.loads(result_text)
            
            # 返回修复后的数据
            return fixed_data.get('fixed_template_data')
            
        except Exception as e:
            print(f"❌ LLM 修复失败: {e}")
            return None
    
    def _build_fix_prompt(
        self,
        template_data: Dict,
        error_response: Dict,
        error_message: str
    ) -> str:
        """构建错误修复 prompt"""
        
        # 将数据转为 JSON 字符串
        template_json = json.dumps(template_data, indent=2, ensure_ascii=False)
        error_json = json.dumps(error_response, indent=2, ensure_ascii=False)
        
        prompt = f"""
# EMCP API 调用失败，请分析并修复数据

## 错误信息
HTTP 状态码: {error_message}

## API 错误响应
```json
{error_json}
```

## 当前发送的数据
```json
{template_json}
```

---

## EMCP 模板数据格式要求

### 必需字段及类型

1. **多语言字段**（必须是数组，包含3个元素）
```json
"name": [
  {{"type": 1, "content": "中文简体名称"}},
  {{"type": 2, "content": "中文繁體名稱"}},
  {{"type": 3, "content": "English Name"}}
],
"summary": [ /* 同上结构 */ ],
"description": [ /* 同上结构 */ ]
```

2. **字符串字段**（不能是 null，用 "" 代替）
- logo_url: 字符串，如 "/api/proxyStorage/NoAuth/xxx.png"
- template_category_id: 字符串UUID，如 "1" 或 "uuid-xxx-xxx"
- template_source_id: 字符串，如 "bach-001"
- command: 字符串，如 "package-name" 或 ""
- route_prefix: 字符串，仅 a-z0-9，不以数字开头，≤10字符
- auth_method_id: 字符串，默认 ""
- container_port: 字符串，默认 ""
- server_image: 字符串，默认 ""
- attach_container_path: 字符串，默认 ""
- targetSseServerHost: 字符串，默认 ""

3. **整数字段**（不能是字符串）
- package_type: 整数 (1=npx, 2=uvx, 3=deno, 4=container)
- mcp_host: 整数，默认 1
- publish_type: 整数，默认 1
- expose_protocal: 整数，默认 0
- targetSseServerPort: 整数，默认 0

4. **布尔字段**
- enable_display: true 或 false
- is_attach_user_storage: true 或 false

5. **数组字段**
- args: 数组，默认 []

---

## 常见错误及修复

### 错误1: 字段类型错误
- 问题: 整数字段传了字符串
- 修复: 转换为整数

### 错误2: 空值错误
- 问题: 字符串字段传了 null
- 修复: 改为 ""

### 错误3: 多语言数组格式错误
- 问题: 数组元素不是3个，或缺少 type/content
- 修复: 确保3个元素，每个都有 type 和 content

### 错误4: 路由前缀不符合规则
- 问题: 包含特殊字符或以数字开头
- 修复: 移除特殊字符，数字开头添加前缀

---

## 请完成以下任务

1. 仔细分析 API 错误响应
2. 找出具体哪个字段有问题
3. 修复该字段
4. 返回修复后的完整数据

**返回 JSON 格式**：
```json
{{
  "error_analysis": "错误原因分析（1-2句话）",
  "fixed_fields": ["字段1", "字段2"],
  "fixed_template_data": {{
    // 完整的修复后的模板数据（包含所有字段）
  }}
}}
```

**重要**：
- fixed_template_data 必须包含所有字段
- 多语言数组必须有3个元素
- 字符串不能是 null
- 整数不能是字符串
- 必须返回有效的 JSON
"""
        return prompt


# 测试代码
if __name__ == '__main__':
    # 这里需要 Azure OpenAI 客户端
    pass

