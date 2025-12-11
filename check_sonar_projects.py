#!/usr/bin/env python3
"""检查 SonarQube 最近扫描的项目"""

import requests
from src.unified_config_manager import UnifiedConfigManager

cfg = UnifiedConfigManager().load_config()
sonar_config = cfg.get('sonarqube', {})
sonar_url = sonar_config.get('server_url', 'https://sonar.kaleido.guru')
sonar_token = sonar_config.get('token', '')

headers = {'Authorization': f'Bearer {sonar_token}'}

# 获取项目列表，按分析时间排序
url = f"{sonar_url}/api/components/search_projects?ps=20&s=analysis_date&asc=false"
resp = requests.get(url, headers=headers)
data = resp.json()

print(f"总项目数: {data.get('paging', {}).get('total', 0)}")
print()
print("最近扫描的 20 个项目:")
print("-" * 60)

for p in data.get('components', []):
    key = p.get('key', '')
    name = p.get('name', '')
    last_analysis = p.get('analysisDate', 'Never')
    print(f"  {name}")
    print(f"    Key: {key}")
    print(f"    Last Analysis: {last_analysis}")
    print()











