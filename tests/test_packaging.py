#!/usr/bin/env python3
"""测试 pyproject.toml 中的依赖声明与打包配置（不需要网络）"""

import ast
import sys
from pathlib import Path

import pytest

tomllib = pytest.importorskip("tomllib")

ROOT = Path(__file__).resolve().parent.parent

# 程序入口：GUI、CLI 以及它们依赖的 src/ 包
ENTRY_FILES = ["mcp_factory_gui.py", "settings_window.py", "repoflow.py"]

# 导入名 → PyPI 包名（不一致的才需要列出）
IMPORT_TO_DIST = {
    "PIL": "pillow",
    "nacl": "pynacl",
    "github": "pygithub",
    "git": "gitpython",
    "sseclient": "sseclient-py",
    "yaml": "pyyaml",
    "dotenv": "python-dotenv",
}

# 在 try/except ImportError 中按需使用的可选依赖
OPTIONAL_IMPORTS = {"opencc"}


def _load_pyproject():
    with open(ROOT / "pyproject.toml", "rb") as f:
        return tomllib.load(f)


def _dist_name(requirement: str) -> str:
    for sep in "<>=!~;[ ":
        requirement = requirement.split(sep)[0]
    return requirement.strip().lower().replace("_", "-")


def _third_party_imports():
    first_party = {"src"} | {p.stem for p in ROOT.glob("*.py")} | {
        p.stem for p in (ROOT / "src").glob("*.py")
    }
    files = [ROOT / name for name in ENTRY_FILES] + sorted((ROOT / "src").glob("*.py"))
    found = {}
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module]
            else:
                continue
            for name in names:
                top = name.split(".")[0]
                if top in sys.stdlib_module_names or top in first_party:
                    continue
                if top in OPTIONAL_IMPORTS:
                    continue
                found.setdefault(top, f"{path.relative_to(ROOT)}:{node.lineno}")
    return found


def test_runtime_imports_are_declared():
    """pip install . 必须装上程序运行时会导入的所有第三方包"""
    declared = {_dist_name(r) for r in _load_pyproject()["project"]["dependencies"]}
    missing = {
        top: where
        for top, where in _third_party_imports().items()
        if IMPORT_TO_DIST.get(top, top).lower() not in declared
    }
    assert not missing, f"pyproject.toml 缺少运行时依赖: {missing}"


def test_console_script_module_is_packaged():
    """[project.scripts] 指向的模块必须被打进安装包，否则 repoflow 命令无法导入"""
    pyproject = _load_pyproject()
    setuptools_cfg = pyproject.get("tool", {}).get("setuptools", {})
    py_modules = set(setuptools_cfg.get("py-modules", []))
    packages = setuptools_cfg.get("packages", {}).get("find", {}).get("include", [])
    for target in pyproject["project"]["scripts"].values():
        module = target.split(":")[0].split(".")[0]
        assert module in py_modules or any(
            p.rstrip("*") == module for p in packages
        ), f"{module} 未被打包"
    assert "src*" in packages, "src/ 包未被打包"


def test_build_tools_are_not_runtime_dependencies():
    """pyinstaller 只用于打包 EXE，不应成为运行时依赖"""
    declared = {_dist_name(r) for r in _load_pyproject()["project"]["dependencies"]}
    assert "pyinstaller" not in declared
