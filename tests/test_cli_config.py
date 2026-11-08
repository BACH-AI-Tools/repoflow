#!/usr/bin/env python3
"""测试 CLI 与 GUI 共用同一份配置（~/.repoflow/config.json），不访问网络"""

import json

import pytest
from click.testing import CliRunner

import repoflow
from src.unified_config_manager import UnifiedConfigManager


class StopAfterGitHubLogin(Exception):
    pass


@pytest.fixture
def home(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    return tmp_path


@pytest.fixture
def github_calls(monkeypatch):
    calls = []

    class FakeProjectDetector:
        # 只测试配置读取，项目检测不在本测试范围内
        def __init__(self, project_path):
            pass

        def validate_pipeline(self, pipeline):
            return {"valid": True, "warning": None, "message": ""}

    class FakeGitHubManager:
        def __init__(self, token):
            calls.append({"token": token})

        def create_repository(self, org_name, repo_name, **kwargs):
            calls[-1]["org"] = org_name
            raise StopAfterGitHubLogin()

    monkeypatch.setattr(repoflow, "GitHubManager", FakeGitHubManager)
    monkeypatch.setattr(repoflow, "ProjectDetector", FakeProjectDetector)
    return calls


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _run_init(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    return CliRunner().invoke(repoflow.cli, [
        "init", "--repo", "demo", "--path", str(project), "--pipeline", "docker", "--skip-scan",
    ])


def test_init_uses_token_saved_by_gui(home, github_calls):
    # GUI 设置页保存的是嵌套结构 github.token
    _write_json(home / ".repoflow" / "config.json",
                {"github": {"token": "gui-token", "org_name": "gui-org"}})

    result = _run_init(home)

    assert "请先运行" not in result.output
    assert github_calls == [{"token": "gui-token", "org": "gui-org"}]


def test_init_falls_back_to_legacy_cli_config(home, github_calls):
    # 旧版 `repoflow config` 写在 ~/.emcpflow/config.json 的扁平结构
    _write_json(home / ".emcpflow" / "config.json",
                {"github_token": "legacy-token", "default_org": "legacy-org"})

    _run_init(home)

    assert github_calls == [{"token": "legacy-token", "org": "legacy-org"}]


def test_init_without_any_token_exits(home, github_calls):
    result = _run_init(home)

    assert result.exit_code == 1
    assert github_calls == []


def test_config_command_writes_shared_store_and_keeps_gui_settings(home):
    _write_json(home / ".repoflow" / "config.json",
                {"github": {"token": "old"}, "other": {"private_repo": True}})

    result = CliRunner().invoke(repoflow.cli, ["config"], input="cli-token\ncli-org\ndocker-user\n")
    assert result.exit_code == 0, result.output

    mgr = UnifiedConfigManager()
    assert mgr.get_github_token() == "cli-token"
    assert mgr.get_github_org() == "cli-org"
    saved = mgr.load_config()
    assert saved["other"]["private_repo"] is True  # GUI 的其他设置不能被覆盖
    assert saved["dockerhub"]["username"] == "docker-user"
