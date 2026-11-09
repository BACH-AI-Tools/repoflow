#!/usr/bin/env python3
"""测试设置中的「默认创建私有仓库」会传给 GitHub（不访问网络）"""

import pytest

from src import workflow_executor
from src.workflow_executor import WorkflowExecutor


class FakeConfigManager:
    def __init__(self, config):
        self._config = config

    def load_config(self):
        return self._config


class FakeGitHubManager:
    calls = []

    def __init__(self, token):
        self.token = token

    def create_repository(self, **kwargs):
        FakeGitHubManager.calls.append(kwargs)
        return (f"https://github.com/{kwargs['org_name']}/{kwargs['repo_name']}.git", True)


@pytest.mark.parametrize("other, expected", [
    ({"private_repo": True}, True),
    ({"private_repo": False}, False),
    ({}, False),  # 旧配置没有该字段时保持公开
])
def test_step_create_repo_respects_private_setting(monkeypatch, other, expected):
    FakeGitHubManager.calls = []
    monkeypatch.setattr(workflow_executor, "GitHubManager", FakeGitHubManager)

    executor = WorkflowExecutor(FakeConfigManager({
        "github": {"token": "dummy-token", "org_name": "demo-org"},
        "other": other,
    }))
    executor.org_name = "demo-org"
    executor.repo_name = "demo-repo"

    executor.step_create_repo()

    assert len(FakeGitHubManager.calls) == 1
    assert FakeGitHubManager.calls[0]["private"] is expected
