#!/usr/bin/env python3
"""测试 build_exe.py 的 PyInstaller 参数（不真正打包）"""

from pathlib import Path

import pytest

pytest.importorskip("PyInstaller")

import build_exe  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def test_entry_script_exists(monkeypatch, tmp_path):
    """打包入口必须是仓库里真实存在的 GUI 主程序，且不依赖当前工作目录"""
    captured = {}

    def fake_run(args):
        captured["args"] = list(args)
        captured["cwd"] = Path.cwd()
        raise SystemExit(0)  # 不真正打包

    monkeypatch.setattr(build_exe.PyInstaller.__main__, "run", fake_run)
    monkeypatch.chdir(tmp_path)  # 模拟从其他目录调用脚本

    with pytest.raises(SystemExit):
        build_exe.build()

    entry = captured["cwd"] / captured["args"][0]
    assert entry.is_file(), f"打包入口不存在: {entry}"
    assert entry.resolve() == (ROOT / "mcp_factory_gui.py").resolve()
