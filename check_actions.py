#!/usr/bin/env python3
"""检查正在运行的 GitHub Actions"""

import requests
from src.unified_config_manager import UnifiedConfigManager

cfg = UnifiedConfigManager().load_config()
token = cfg.get('github', {}).get('token', '')
headers = {'Authorization': 'token ' + token}

# 获取组织的仓库
repos_url = 'https://api.github.com/orgs/BACH-AI-Tools/repos?per_page=100'
repos = requests.get(repos_url, headers=headers).json()

in_progress = []
queued = []
completed = []
failed = []

print("检查仓库 Actions 状态...")
for i, repo in enumerate(repos):
    runs_url = f"https://api.github.com/repos/BACH-AI-Tools/{repo['name']}/actions/runs?per_page=1"
    runs = requests.get(runs_url, headers=headers).json()
    if runs.get('workflow_runs'):
        run = runs['workflow_runs'][0]
        info = f"{repo['name']}: {run['name']}"
        if run['status'] == 'in_progress':
            in_progress.append(info)
        elif run['status'] == 'queued':
            queued.append(info)
        elif run['status'] == 'completed':
            if run['conclusion'] == 'success':
                completed.append(info)
            else:
                failed.append(f"{info} ({run['conclusion']})")
    
    if (i + 1) % 20 == 0:
        print(f"  已检查 {i + 1}/{len(repos)} 个仓库...")

print()
print("=" * 50)
print(f"🟡 正在执行: {len(in_progress)}")
for item in in_progress[:5]:
    print(f"  - {item}")
if len(in_progress) > 5:
    print(f"  ... 还有 {len(in_progress) - 5} 个")

print()
print(f"⏳ 排队中: {len(queued)}")
for item in queued[:5]:
    print(f"  - {item}")
if len(queued) > 5:
    print(f"  ... 还有 {len(queued) - 5} 个")

print()
print(f"✅ 已完成 (成功): {len(completed)}")
print(f"❌ 已完成 (失败): {len(failed)}")
for item in failed[:5]:
    print(f"  - {item}")











