"""环境变量检测器 - 从 README.md 中检测需要的环境变量"""

import re
from typing import List, Dict
from pathlib import Path


class EnvVarDetector:
    """检测项目需要的环境变量"""
    
    # 常见的环境变量模式
    ENV_PATTERNS = [
        # 明确的环境变量声明
        r'(?:export\s+)?([A-Z][A-Z0-9_]+)=',  # export API_KEY=xxx 或 API_KEY=xxx
        r'\$\{?([A-Z][A-Z0-9_]+)\}?',  # ${API_KEY} 或 $API_KEY
        r'process\.env\.([A-Z][A-Z0-9_]+)',  # process.env.API_KEY (Node.js)
        r'os\.environ\.get\(["\']([A-Z][A-Z0-9_]+)["\']\)',  # os.environ.get("API_KEY") (Python)
        r'os\.getenv\(["\']([A-Z][A-Z0-9_]+)["\']\)',  # os.getenv("API_KEY") (Python)
        r'ENV\[["\']([A-Z][A-Z0-9_]+)["\']\]',  # ENV["API_KEY"] (Ruby)
    ]
    
    # 常见的环境变量关键词
    COMMON_ENV_KEYWORDS = [
        'API_KEY', 'API_SECRET', 'API_TOKEN',
        'DATABASE_URL', 'DB_HOST', 'DB_PORT', 'DB_PASSWORD',
        'SECRET_KEY', 'JWT_SECRET',
        'OPENAI_API_KEY', 'AZURE_API_KEY',
        'AWS_ACCESS_KEY', 'AWS_SECRET_KEY',
        'REDIS_URL', 'MONGODB_URL',
        'PORT', 'HOST', 'BASE_URL',
    ]
    
    def __init__(self):
        self.compiled_patterns = [re.compile(pattern) for pattern in self.ENV_PATTERNS]
    
    def detect_from_readme(self, readme_content: str) -> List[Dict]:
        """
        从 README 中检测环境变量
        
        Args:
            readme_content: README.md 内容
            
        Returns:
            环境变量列表 [{"name": "API_KEY", "description": "", "required": True}]
        """
        env_vars = {}
        
        # 1. 查找 .env 示例部分
        env_section = self._extract_env_section(readme_content)
        if env_section:
            vars_from_section = self._parse_env_section(env_section)
            env_vars.update(vars_from_section)
        
        # 2. 使用正则表达式查找
        for pattern in self.compiled_patterns:
            matches = pattern.findall(readme_content)
            for match in matches:
                var_name = match.strip()
                # 过滤掉明显不是环境变量的
                if len(var_name) >= 3 and var_name.isupper():
                    if var_name not in env_vars:
                        env_vars[var_name] = {
                            "name": var_name,
                            "description": self._guess_description(var_name),
                            "required": self._is_likely_required(var_name, readme_content)
                        }
        
        # 3. 检查常见的环境变量关键词
        for keyword in self.COMMON_ENV_KEYWORDS:
            if keyword in readme_content and keyword not in env_vars:
                env_vars[keyword] = {
                    "name": keyword,
                    "description": self._guess_description(keyword),
                    "required": True
                }
        
        # 转换为列表并排序（必需的在前）
        result = list(env_vars.values())
        result.sort(key=lambda x: (not x['required'], x['name']))
        
        return result
    
    def detect_from_project(self, project_path: Path) -> List[Dict]:
        """
        从项目文件中检测环境变量
        
        Args:
            project_path: 项目路径
            
        Returns:
            环境变量列表
        """
        env_vars = {}
        
        # 1. 从 README.md 检测
        readme_path = project_path / "README.md"
        if readme_path.exists():
            try:
                readme_content = readme_path.read_text(encoding='utf-8')
                vars_from_readme = self.detect_from_readme(readme_content)
                for var in vars_from_readme:
                    env_vars[var['name']] = var
            except:
                pass
        
        # 2. 从 .env.example 检测
        env_example = project_path / ".env.example"
        if env_example.exists():
            try:
                content = env_example.read_text(encoding='utf-8')
                vars_from_example = self._parse_env_file(content)
                for var in vars_from_example:
                    if var['name'] not in env_vars:
                        env_vars[var['name']] = var
            except:
                pass
        
        # 3. 从 .env.template 检测
        env_template = project_path / ".env.template"
        if env_template.exists():
            try:
                content = env_template.read_text(encoding='utf-8')
                vars_from_template = self._parse_env_file(content)
                for var in vars_from_template:
                    if var['name'] not in env_vars:
                        env_vars[var['name']] = var
            except:
                pass
        
        result = list(env_vars.values())
        result.sort(key=lambda x: (not x['required'], x['name']))
        
        return result
    
    def _extract_env_section(self, content: str) -> str:
        """提取环境变量配置部分"""
        # 查找常见的环境变量配置章节
        patterns = [
            r'##?\s*[Ee]nvironment [Vv]ariables?\s*\n(.*?)(?=\n##|\Z)',
            r'##?\s*[Cc]onfiguration\s*\n(.*?)(?=\n##|\Z)',
            r'##?\s*\.env.*?\s*\n(.*?)(?=\n##|\Z)',
            r'```(?:bash|sh|env)\n(.*?)```',  # 代码块
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _parse_env_section(self, section: str) -> Dict:
        """解析环境变量章节"""
        env_vars = {}
        lines = section.split('\n')
        
        current_var = None
        current_desc = []
        
        for line in lines:
            line = line.strip()
            
            # 检测环境变量定义
            if '=' in line or (line.isupper() and len(line) > 2):
                # 保存前一个变量
                if current_var:
                    env_vars[current_var] = {
                        "name": current_var,
                        "description": ' '.join(current_desc).strip(),
                        "required": True
                    }
                
                # 提取新变量名
                if '=' in line:
                    var_name = line.split('=')[0].strip()
                else:
                    var_name = line
                
                # 清理变量名
                var_name = re.sub(r'[^A-Z0-9_]', '', var_name)
                
                if var_name and len(var_name) >= 3:
                    current_var = var_name
                    current_desc = []
            elif current_var and line:
                # 收集描述
                if not line.startswith('```') and not line.startswith('#'):
                    current_desc.append(line)
        
        # 保存最后一个变量
        if current_var:
            env_vars[current_var] = {
                "name": current_var,
                "description": ' '.join(current_desc).strip(),
                "required": True
            }
        
        return env_vars
    
    def _parse_env_file(self, content: str) -> List[Dict]:
        """解析 .env.example 或 .env.template 文件"""
        env_vars = []
        lines = content.split('\n')
        
        current_var = None
        current_comment = []
        
        for line in lines:
            stripped = line.strip()
            
            # 注释行（收集作为描述）
            if stripped.startswith('#'):
                comment = stripped.lstrip('#').strip()
                if comment:
                    current_comment.append(comment)
            # 环境变量定义
            elif '=' in stripped and not stripped.startswith('#'):
                var_name = stripped.split('=')[0].strip()
                var_value = stripped.split('=', 1)[1].strip()
                
                if var_name and var_name.isupper():
                    env_vars.append({
                        "name": var_name,
                        "description": ' '.join(current_comment) or self._guess_description(var_name),
                        "required": not var_value or 'your_' in var_value.lower() or 'xxx' in var_value.lower()
                    })
                    current_comment = []
            # 空行重置注释
            elif not stripped:
                current_comment = []
        
        return env_vars
    
    def _guess_description(self, var_name: str) -> str:
        """猜测环境变量的用途"""
        name_lower = var_name.lower()
        
        descriptions = {
            'api_key': 'API 密钥',
            'api_secret': 'API 密钥',
            'api_token': 'API Token',
            'secret_key': '密钥',
            'jwt_secret': 'JWT 密钥',
            'database_url': '数据库连接URL',
            'db_host': '数据库主机地址',
            'db_port': '数据库端口',
            'db_password': '数据库密码',
            'redis_url': 'Redis 连接URL',
            'mongodb_url': 'MongoDB 连接URL',
            'openai_api_key': 'OpenAI API Key',
            'azure_api_key': 'Azure API Key',
            'port': '服务端口',
            'host': '服务主机地址',
            'base_url': '基础URL',
        }
        
        for key, desc in descriptions.items():
            if key in name_lower:
                return desc
        
        # 根据后缀猜测
        if name_lower.endswith('_key'):
            return '密钥'
        elif name_lower.endswith('_secret'):
            return '密钥'
        elif name_lower.endswith('_token'):
            return 'Token'
        elif name_lower.endswith('_url'):
            return 'URL地址'
        elif name_lower.endswith('_port'):
            return '端口号'
        elif name_lower.endswith('_host'):
            return '主机地址'
        
        return var_name.replace('_', ' ').title()
    
    def _is_likely_required(self, var_name: str, context: str) -> bool:
        """判断环境变量是否可能是必需的"""
        name_lower = var_name.lower()
        
        # 关键的环境变量通常是必需的
        if any(keyword in name_lower for keyword in ['key', 'secret', 'token', 'password', 'database', 'redis', 'mongodb']):
            return True
        
        # 检查上下文中是否有"必需"、"required"等词
        context_around = self._get_context_around(var_name, context)
        if any(keyword in context_around.lower() for keyword in ['required', 'must', '必需', '必须', '必填']):
            return True
        
        return False
    
    def _get_context_around(self, var_name: str, content: str, window: int = 100) -> str:
        """获取变量名周围的上下文"""
        try:
            index = content.index(var_name)
            start = max(0, index - window)
            end = min(len(content), index + len(var_name) + window)
            return content[start:end]
        except:
            return ""


# 测试代码
if __name__ == '__main__':
    detector = EnvVarDetector()
    
    # 测试 README
    readme = """
# My Project

## Configuration

需要配置以下环境变量：

- `API_KEY` - OpenAI API Key（必需）
- `DATABASE_URL` - 数据库连接地址
- `PORT` - 服务端口（默认3000）

## Usage

```bash
export API_KEY=your_key_here
export DATABASE_URL=postgresql://...
npm start
```
"""
    
    result = detector.detect_from_readme(readme)
    print("检测到的环境变量：")
    for var in result:
        print(f"  - {var['name']}: {var['description']} ({'必需' if var['required'] else '可选'})")

