"""敏感信息扫描模块"""

import re
from pathlib import Path
from typing import List, Dict


class SecretScanner:
    """扫描代码中的敏感信息"""
    
    # 敏感信息的正则表达式模式
    PATTERNS = {
        'AWS Access Key': r'AKIA[0-9A-Z]{16}',
        'GitHub Token': r'gh[pousr]_[A-Za-z0-9]{36,}',
        'Generic API Key': r'[aA][pP][iI][-_]?[kK][eE][yY][\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'Generic Secret': r'[sS][eE][cC][rR][eE][tT][\s]*[:=][\s]*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
        'Password': r'[pP][aA][sS][sS][wW][oO][rR][dD][\s]*[:=][\s]*["\']([^"\']{8,})["\']',
        'Private Key': r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
        'Bearer Token': r'[bB]earer\s+[a-zA-Z0-9\-._~+/]+=*',
        'JWT Token': r'eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*',
        'Database URL': r'(?:mysql|postgresql|mongodb|redis)://[^:\s]+:[^@\s]+@[^\s]+',
    }
    
    # 忽略的文件和目录
    IGNORE_PATTERNS = {
        '*.pyc', '*.pyo', '*.so', '*.dll', '*.exe',
        'node_modules', '.git', '__pycache__', 'venv', 'env',
        '.env.example', '.env.template', '*.min.js', '*.bundle.js',
        'package-lock.json', 'yarn.lock', 'poetry.lock',
        '*.jpg', '*.png', '*.gif', '*.pdf', '*.zip',
        'secret_scanner.py'  # 忽略扫描器自身和测试文件
    }
    
    def __init__(self):
        self.compiled_patterns = {
            name: re.compile(pattern) 
            for name, pattern in self.PATTERNS.items()
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
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    for secret_type, pattern in self.compiled_patterns.items():
                        matches = pattern.finditer(line)
                        for match in matches:
                            # 过滤掉一些明显的误报
                            if self._is_likely_false_positive(line, secret_type):
                                continue
                            
                            issues.append({
                                'file': str(file_path),
                                'line': line_num,
                                'type': secret_type,
                                'content': line.strip(),
                                'match': match.group(0)
                            })
        except Exception:
            # 忽略无法读取的文件
            pass
        
        return issues
    
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

