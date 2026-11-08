#!/usr/bin/env python3
"""测试对话测试步骤中 EMCP 401 自动重登分支（不访问网络）"""

import json
from datetime import datetime

import requests

from src.signalr_chat_tester import SignalRChatTester

FAKE_PHONE = "10000000000"  # 测试用假号码


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeEMCPManager:
    def __init__(self):
        self.session_key = "expired-token"
        self.login_calls = []

    def login(self, phone_number, validation_code):
        self.login_calls.append((phone_number, validation_code))
        self.session_key = "fresh-token"
        return {"phone": phone_number}


def test_401_relogin_uses_gui_credentials(monkeypatch, tmp_path):
    # GUI 设置页把 EMCP 手机号保存在 ~/.repoflow/config.json
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    config_dir = tmp_path / ".repoflow"
    config_dir.mkdir()
    (config_dir / "config.json").write_text(
        json.dumps({"emcp": {"base_url": "https://emcp.example", "phone_number": FAKE_PHONE}}),
        encoding="utf-8",
    )

    seen_tokens = []

    def fake_get(url, headers=None, timeout=None):
        seen_tokens.append((url.rsplit("/", 2)[-2], headers["token"]))
        if "get_mcp_main_server_id" in url:
            if headers["token"] == "expired-token":
                return FakeResponse(401, {})
            return FakeResponse(200, {"err_code": 0, "body": "server-1"})
        return FakeResponse(200, {"err_code": 0, "body": [
            {"functionApi": "echo", "functionName": "Echo", "parameters": []},
        ]})

    monkeypatch.setattr(requests, "get", fake_get)

    emcp = FakeEMCPManager()
    tester = SignalRChatTester(base_url="https://agent.example")
    tools = tester._get_mcp_tools_from_emcp(
        template_id="tpl-1",
        emcp_base_url="https://emcp.example",
        emcp_token="expired-token",
        emcp_manager=emcp,
    )

    # 用 GUI 保存的手机号 + 当日验证码重新登录，并带新 token 重试
    assert emcp.login_calls == [(FAKE_PHONE, datetime.now().strftime("%m%Y%d"))]
    assert seen_tokens == [
        ("get_mcp_main_server_id", "expired-token"),
        ("get_mcp_main_server_id", "fresh-token"),
        ("get_mcp_test_tools", "fresh-token"),
    ]
    assert tools == [{"name": "echo", "display_name": "Echo", "description": "Echo",
                      "parameters": []}]


def test_401_without_saved_phone_gives_up(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr(requests, "get",
                        lambda url, headers=None, timeout=None: FakeResponse(401, {}))

    emcp = FakeEMCPManager()
    tester = SignalRChatTester(base_url="https://agent.example")
    tools = tester._get_mcp_tools_from_emcp(
        template_id="tpl-1",
        emcp_base_url="https://emcp.example",
        emcp_token="expired-token",
        emcp_manager=emcp,
    )

    assert tools is None
    assert emcp.login_calls == []
