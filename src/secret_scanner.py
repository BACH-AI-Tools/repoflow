"""敏感信息扫描模块

支持检测多种类型的敏感信息：
- API Keys (AWS, Azure, Google Cloud, GitHub, GitLab, etc.)
- 私钥和证书
- 数据库连接字符串
- OAuth tokens
- 密码和凭证
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Optional
from enum import Enum


class SeverityLevel(Enum):
    """严重程度级别"""
    CRITICAL = "critical"  # 必须立即处理
    HIGH = "high"          # 高风险
    MEDIUM = "medium"      # 中等风险
    LOW = "low"            # 低风险


class SecretScanner:
    """扫描代码中的敏感信息"""
    
    # 敏感信息的正则表达式模式（增强版）
    PATTERNS = {
        # === 云服务商密钥 ===
        'AWS Access Key': {
            'pattern': r'AKIA[0-9A-Z]{16}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'AWS Access Key ID'
        },
        'AWS Secret Key': {
            'pattern': r'(?i)aws_secret_access_key[\s]*[:=][\s]*["\']?([a-zA-Z0-9/+=]{40})["\']?',
            'severity': SeverityLevel.CRITICAL,
            'description': 'AWS Secret Access Key'
        },
        'Azure Storage Key': {
            'pattern': r'(?i)(?:AccountKey|azure_storage_key)[\s]*[:=][\s]*["\']?([a-zA-Z0-9+/=]{88})["\']?',
            'severity': SeverityLevel.CRITICAL,
            'description': 'Azure Storage Account Key'
        },
        'Google API Key': {
            'pattern': r'AIza[0-9A-Za-z\-_]{35}',
            'severity': SeverityLevel.HIGH,
            'description': 'Google API Key'
        },
        'Google OAuth': {
            'pattern': r'[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com',
            'severity': SeverityLevel.HIGH,
            'description': 'Google OAuth Client ID'
        },
        
        # === 代码托管平台 ===
        'GitHub Token': {
            'pattern': r'gh[pousr]_[A-Za-z0-9]{36,}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'GitHub Personal Access Token'
        },
        'GitHub OAuth': {
            'pattern': r'gho_[A-Za-z0-9]{36}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'GitHub OAuth Access Token'
        },
        'GitLab Token': {
            'pattern': r'glpat-[A-Za-z0-9\-]{20,}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'GitLab Personal Access Token'
        },
        'Bitbucket Token': {
            'pattern': r'(?i)bitbucket.*[:=][\s]*["\']?([a-zA-Z0-9]{32,})["\']?',
            'severity': SeverityLevel.HIGH,
            'description': 'Bitbucket Access Token'
        },
        
        # === 支付和金融 ===
        'Stripe API Key': {
            'pattern': r'sk_(?:live|test)_[0-9a-zA-Z]{24,}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'Stripe Secret Key'
        },
        'Stripe Publishable Key': {
            'pattern': r'pk_(?:live|test)_[0-9a-zA-Z]{24,}',
            'severity': SeverityLevel.MEDIUM,
            'description': 'Stripe Publishable Key'
        },
        'PayPal Client ID': {
            'pattern': r'(?i)paypal.*client.*id[\s]*[:=][\s]*["\']?([A-Za-z0-9\-]{50,})["\']?',
            'severity': SeverityLevel.HIGH,
            'description': 'PayPal Client ID'
        },
        
        # === 通信服务 ===
        'Slack Token': {
            'pattern': r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24}',
            'severity': SeverityLevel.HIGH,
            'description': 'Slack API Token'
        },
        'Slack Webhook': {
            'pattern': r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]{8}/B[a-zA-Z0-9_]{8,}/[a-zA-Z0-9_]{24}',
            'severity': SeverityLevel.MEDIUM,
            'description': 'Slack Webhook URL'
        },
        'Discord Webhook': {
            'pattern': r'https://discord(?:app)?\.com/api/webhooks/[0-9]{18}/[a-zA-Z0-9_\-]{68}',
            'severity': SeverityLevel.MEDIUM,
            'description': 'Discord Webhook URL'
        },
        'Twilio API Key': {
            'pattern': r'SK[a-f0-9]{32}',
            'severity': SeverityLevel.HIGH,
            'description': 'Twilio API Key'
        },
        'SendGrid API Key': {
            'pattern': r'SG\.[a-zA-Z0-9_\-]{22}\.[a-zA-Z0-9_\-]{43}',
            'severity': SeverityLevel.HIGH,
            'description': 'SendGrid API Key'
        },
        
        # === 通用模式 ===
        'Generic API Key': {
            'pattern': r'(?i)(?:api[_-]?key|apikey)[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'severity': SeverityLevel.MEDIUM,
            'description': 'Generic API Key'
        },
        'Generic Secret': {
            'pattern': r'(?i)(?:secret|secret[_-]?key)[\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
            'severity': SeverityLevel.HIGH,
            'description': 'Generic Secret Key'
        },
        'Password': {
            'pattern': r'(?i)(?:password|passwd|pwd)[\s]*[:=][\s]*["\']([^"\']{8,})["\']',
            'severity': SeverityLevel.HIGH,
            'description': 'Hardcoded Password'
        },
        'Private Key': {
            'pattern': r'-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY(?:\sBLOCK)?-----',
            'severity': SeverityLevel.CRITICAL,
            'description': 'Private Key File'
        },
        'SSH Private Key': {
            'pattern': r'-----BEGIN OPENSSH PRIVATE KEY-----',
            'severity': SeverityLevel.CRITICAL,
            'description': 'SSH Private Key'
        },
        
        # === 认证令牌 ===
        'Bearer Token': {
            'pattern': r'(?i)bearer[\s]+[a-zA-Z0-9\-._~+/]+=*',
            'severity': SeverityLevel.HIGH,
            'description': 'Bearer Token'
        },
        'JWT Token': {
            'pattern': r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
            'severity': SeverityLevel.HIGH,
            'description': 'JWT Token'
        },
        'Basic Auth': {
            # 更精确的模式：Basic 后面必须是有效的 base64 编码（至少20字符，包含数字）
            'pattern': r'(?i)basic[\s]+[a-zA-Z0-9+/]{20,}=*',
            'severity': SeverityLevel.HIGH,
            'description': 'Basic Authentication Header'
        },
        
        # === 数据库 ===
        'Database URL': {
            'pattern': r'(?:mysql|postgresql|postgres|mongodb|redis|mssql|oracle)://[^:\s]+:[^@\s]+@[^\s]+',
            'severity': SeverityLevel.CRITICAL,
            'description': 'Database Connection String'
        },
        'MongoDB Connection': {
            'pattern': r'mongodb(?:\+srv)?://[^:\s]+:[^@\s]+@[^\s]+',
            'severity': SeverityLevel.CRITICAL,
            'description': 'MongoDB Connection String'
        },
        
        # === 中国服务商 ===
        'Aliyun Access Key': {
            'pattern': r'LTAI[a-zA-Z0-9]{12,}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'Aliyun (阿里云) Access Key'
        },
        'Tencent Cloud SecretId': {
            'pattern': r'AKID[a-zA-Z0-9]{32}',
            'severity': SeverityLevel.CRITICAL,
            'description': 'Tencent Cloud (腾讯云) Secret ID'
        },
        'WeChat AppSecret': {
            'pattern': r'(?i)(?:wechat|weixin).*(?:secret|appsecret)[\s]*[:=][\s]*["\']?([a-f0-9]{32})["\']?',
            'severity': SeverityLevel.HIGH,
            'description': 'WeChat AppSecret'
        },
    }
    
    # 转换为兼容旧格式（保持向后兼容）
    @property
    def _legacy_patterns(self) -> Dict[str, str]:
        return {name: info['pattern'] for name, info in self.PATTERNS.items()}
    
    # 忽略的文件和目录
    IGNORE_PATTERNS = {
        # 编译文件
        '*.pyc', '*.pyo', '*.so', '*.dll', '*.exe', '*.class',
        # 目录
        'node_modules', '.git', '__pycache__', 'venv', 'env', '.venv',
        '.tox', '.pytest_cache', '.mypy_cache', 'dist', 'build',
        # 示例和模板文件
        '.env.example', '.env.template', '.env.sample',
        # 锁文件
        '*.min.js', '*.bundle.js', '*.map',
        'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock',
        # 二进制和媒体文件
        '*.jpg', '*.jpeg', '*.png', '*.gif', '*.ico', '*.svg',
        '*.pdf', '*.zip', '*.tar', '*.gz', '*.rar',
        '*.mp3', '*.mp4', '*.avi', '*.mov',
        '*.ttf', '*.woff', '*.woff2', '*.eot',
        # 本文件
        'secret_scanner.py',
        # 测试数据
        '**/test/**', '**/tests/**', '**/__tests__/**',
        '**/fixtures/**', '**/mocks/**',
    }
    
    def __init__(self, min_severity: SeverityLevel = SeverityLevel.LOW):
        """
        初始化扫描器
        
        Args:
            min_severity: 最低报告的严重程度级别
        """
        self.min_severity = min_severity
        self.compiled_patterns = {}
        
        for name, info in self.PATTERNS.items():
            pattern = info['pattern'] if isinstance(info, dict) else info
            self.compiled_patterns[name] = {
                'regex': re.compile(pattern),
                'severity': info.get('severity', SeverityLevel.MEDIUM) if isinstance(info, dict) else SeverityLevel.MEDIUM,
                'description': info.get('description', name) if isinstance(info, dict) else name
            }
    
    def should_ignore(self, file_path: Path) -> bool:
        """检查文件是否应该被忽略"""
        file_str = str(file_path)
        
        for pattern in self.IGNORE_PATTERNS:
            if pattern.startswith('*.'):
                if file_path.suffix == pattern[1:]:
                    return True
            elif pattern in file_str:
                return True
        
        return False
    
    def scan_file(self, file_path: Path) -> List[Dict]:
        """
        扫描单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            发现的敏感信息列表
        """
        issues = []
        severity_order = [SeverityLevel.CRITICAL, SeverityLevel.HIGH, SeverityLevel.MEDIUM, SeverityLevel.LOW]
        min_index = severity_order.index(self.min_severity)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for secret_type, pattern_info in self.compiled_patterns.items():
                        # 检查严重程度是否达到最低要求
                        severity = pattern_info['severity']
                        if severity_order.index(severity) > min_index:
                            continue
                        
                        regex = pattern_info['regex']
                        matches = regex.finditer(line)
                        
                        for match in matches:
                            # 过滤掉一些明显的误报
                            if self._is_likely_false_positive(line, secret_type):
                                continue
                            
                            # 脱敏处理匹配内容
                            matched_text = match.group(0)
                            redacted = self._redact_secret(matched_text)
                            
                            issues.append({
                                'file': str(file_path),
                                'line': line_num,
                                'type': secret_type,
                                'severity': severity.value,
                                'description': pattern_info['description'],
                                'content': line.strip()[:100] + ('...' if len(line.strip()) > 100 else ''),
                                'match': matched_text,
                                'redacted': redacted
                            })
        except Exception as e:
            # 忽略无法读取的文件，但可以记录日志
            pass
        
        return issues
    
    def _redact_secret(self, secret: str) -> str:
        """
        脱敏处理敏感信息
        
        Args:
            secret: 原始敏感信息
            
        Returns:
            脱敏后的字符串
        """
        if len(secret) <= 8:
            return '*' * len(secret)
        return secret[:4] + '*' * (len(secret) - 8) + secret[-4:]
    
    def scan_directory(self, directory: Path) -> List[Dict]:
        """
        扫描整个目录
        
        Args:
            directory: 目录路径
            
        Returns:
            发现的所有敏感信息列表
        """
        all_issues = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and not self.should_ignore(file_path):
                issues = self.scan_file(file_path)
                all_issues.extend(issues)
        
        return all_issues
    
    def _is_likely_false_positive(self, line: str, secret_type: str) -> bool:
        """检查是否可能是误报"""
        # 如果是注释或文档
        if any(marker in line for marker in ['#', '//', '/*', '*/', '<!--', '-->']):
            # 但如果看起来像真实的密钥，仍然报告
            if 'example' in line.lower() or 'sample' in line.lower():
                return True
        
        # 如果包含明显的占位符文本
        placeholders = [
            'your_api_key', 'your_secret', 'your_password',
            'insert_key_here', 'replace_with', 'todo',
            'xxx', '***', '...'
        ]
        if any(ph in line.lower() for ph in placeholders):
            return True
        
        # 如果是空值或默认值
        if any(val in line.lower() for val in ['= ""', "= ''", '= null', '= None']):
            return True
        
        return False
    
    def generate_gitignore_secrets(self, issues: List[Dict]) -> str:
        """
        基于发现的问题生成 .gitignore 建议
        
        Args:
            issues: 敏感信息列表
            
        Returns:
            .gitignore 内容建议
        """
        files = set(issue['file'] for issue in issues)
        
        lines = ["# 敏感信息文件 (由 RepoFlow 生成)"]
        for file in sorted(files):
            lines.append(Path(file).name)
        
        return '\n'.join(lines)
    
    def generate_report(self, issues: List[Dict], format: str = 'text') -> str:
        """
        生成扫描报告
        
        Args:
            issues: 敏感信息列表
            format: 报告格式 ('text', 'json', 'markdown', 'sarif')
            
        Returns:
            格式化的报告字符串
        """
        if format == 'json':
            return json.dumps(issues, indent=2, ensure_ascii=False)
        
        elif format == 'sarif':
            # SARIF 格式用于 GitHub Code Scanning
            return self._generate_sarif_report(issues)
        
        elif format == 'markdown':
            return self._generate_markdown_report(issues)
        
        else:  # text
            return self._generate_text_report(issues)
    
    def _generate_text_report(self, issues: List[Dict]) -> str:
        """生成文本格式报告"""
        if not issues:
            return "✅ 未发现敏感信息泄露"
        
        lines = [
            "=" * 60,
            "🔐 敏感信息扫描报告",
            "=" * 60,
            f"共发现 {len(issues)} 个潜在问题",
            ""
        ]
        
        # 按严重程度分组
        by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'medium')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)
        
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }
        
        for severity in ['critical', 'high', 'medium', 'low']:
            if severity in by_severity:
                lines.append(f"\n{severity_icons[severity]} {severity.upper()} ({len(by_severity[severity])} 个)")
                lines.append("-" * 40)
                for issue in by_severity[severity]:
                    lines.append(f"  📄 {issue['file']}:{issue['line']}")
                    lines.append(f"     类型: {issue['type']}")
                    lines.append(f"     发现: {issue['redacted']}")
                    lines.append("")
        
        lines.extend([
            "=" * 60,
            "建议操作:",
            "  1. 移除硬编码的敏感信息",
            "  2. 使用环境变量或配置文件",
            "  3. 将敏感文件添加到 .gitignore",
            "  4. 如果已提交，清理 git 历史",
            "=" * 60
        ])
        
        return '\n'.join(lines)
    
    def _generate_markdown_report(self, issues: List[Dict]) -> str:
        """生成 Markdown 格式报告"""
        if not issues:
            return "## ✅ 扫描通过\n\n未发现敏感信息泄露。"
        
        lines = [
            "# 🔐 敏感信息扫描报告",
            "",
            f"**共发现 {len(issues)} 个潜在问题**",
            "",
            "| 严重程度 | 文件 | 行号 | 类型 | 描述 |",
            "|---------|------|-----|------|------|"
        ]
        
        severity_icons = {
            'critical': '🔴 Critical',
            'high': '🟠 High',
            'medium': '🟡 Medium',
            'low': '🟢 Low'
        }
        
        for issue in sorted(issues, key=lambda x: ['critical', 'high', 'medium', 'low'].index(x.get('severity', 'medium'))):
            severity = severity_icons.get(issue.get('severity', 'medium'), '⚪ Unknown')
            file_name = Path(issue['file']).name
            lines.append(f"| {severity} | `{file_name}` | {issue['line']} | {issue['type']} | {issue.get('description', '')} |")
        
        lines.extend([
            "",
            "## 建议操作",
            "",
            "1. 移除硬编码的敏感信息",
            "2. 使用环境变量或安全的配置管理",
            "3. 将敏感文件添加到 `.gitignore`",
            "4. 如果敏感信息已提交到 Git，需要[清理历史](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)"
        ])
        
        return '\n'.join(lines)
    
    def _generate_sarif_report(self, issues: List[Dict]) -> str:
        """生成 SARIF 格式报告（用于 GitHub Code Scanning）"""
        sarif = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [{
                "tool": {
                    "driver": {
                        "name": "RepoFlow Secret Scanner",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/your-org/repoflow",
                        "rules": []
                    }
                },
                "results": []
            }]
        }
        
        rules_added = set()
        
        for issue in issues:
            rule_id = issue['type'].replace(' ', '_').lower()
            
            # 添加规则定义
            if rule_id not in rules_added:
                sarif["runs"][0]["tool"]["driver"]["rules"].append({
                    "id": rule_id,
                    "name": issue['type'],
                    "shortDescription": {"text": issue.get('description', issue['type'])},
                    "defaultConfiguration": {
                        "level": "error" if issue.get('severity') in ['critical', 'high'] else "warning"
                    }
                })
                rules_added.add(rule_id)
            
            # 添加结果
            sarif["runs"][0]["results"].append({
                "ruleId": rule_id,
                "level": "error" if issue.get('severity') in ['critical', 'high'] else "warning",
                "message": {"text": f"发现 {issue['type']}: {issue['redacted']}"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": issue['file']},
                        "region": {"startLine": issue['line']}
                    }
                }]
            })
        
        return json.dumps(sarif, indent=2, ensure_ascii=False)


def main():
    """CLI 入口点"""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(
        description='🔐 RepoFlow Secret Scanner - 扫描代码中的敏感信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s .                      # 扫描当前目录
  %(prog)s /path/to/project       # 扫描指定目录
  %(prog)s . --format markdown    # 输出 Markdown 格式
  %(prog)s . --severity high      # 只显示 high 及以上
  %(prog)s . --output report.json # 保存到文件
        """
    )
    
    parser.add_argument('path', nargs='?', default='.', help='要扫描的目录路径 (默认: 当前目录)')
    parser.add_argument('-f', '--format', choices=['text', 'json', 'markdown', 'sarif'], 
                       default='text', help='输出格式 (默认: text)')
    parser.add_argument('-s', '--severity', choices=['critical', 'high', 'medium', 'low'],
                       default='low', help='最低严重程度 (默认: low，显示所有)')
    parser.add_argument('-o', '--output', help='输出文件路径')
    parser.add_argument('--fail-on', choices=['critical', 'high', 'medium', 'low', 'none'],
                       default='high', help='在发现此级别及以上问题时返回非零退出码 (默认: high)')
    parser.add_argument('-q', '--quiet', action='store_true', help='安静模式，只输出发现的问题')
    
    args = parser.parse_args()
    
    # 映射严重程度
    severity_map = {
        'critical': SeverityLevel.CRITICAL,
        'high': SeverityLevel.HIGH,
        'medium': SeverityLevel.MEDIUM,
        'low': SeverityLevel.LOW
    }
    
    scanner = SecretScanner(min_severity=severity_map[args.severity])
    
    if not args.quiet:
        print(f"🔍 正在扫描: {args.path}")
    
    issues = scanner.scan_directory(Path(args.path))
    report = scanner.generate_report(issues, format=args.format)
    
    # 输出报告
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(report)
        if not args.quiet:
            print(f"📄 报告已保存到: {args.output}")
    else:
        print(report)
    
    # 检查是否需要失败
    if args.fail_on != 'none' and issues:
        fail_levels = ['critical', 'high', 'medium', 'low']
        fail_index = fail_levels.index(args.fail_on)
        
        for issue in issues:
            issue_severity = issue.get('severity', 'medium')
            if fail_levels.index(issue_severity) <= fail_index:
                sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()

