#!/usr/bin/env python3
"""测试克隆发布的许可证检查和上游署名（#5）"""

import subprocess
from pathlib import Path

import pytest

from src.pipeline_generator import PipelineGenerator
from src.repo_cloner import RepoCloner
from src.workflow_executor import WorkflowExecutor

UPSTREAM_URL = "https://github.com/alice/awesome-mcp"

MIT_TEXT = """MIT License

Copyright (c) 2025 Alice

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
"""


def make_upstream(tmp_path: Path, license_text=None, setup_py=True) -> Path:
    """构造一个只有 setup.py（没有 pyproject.toml）的上游仓库"""
    repo = tmp_path / "awesome-mcp"
    repo.mkdir()
    (repo / "README.md").write_text("# awesome-mcp\n", encoding="utf-8")
    if setup_py:
        (repo / "setup.py").write_text(
            'from setuptools import setup\n'
            'setup(name="awesome-mcp", version="0.1.0", author="Alice Upstream")\n',
            encoding="utf-8",
        )
    if license_text is not None:
        (repo / "LICENSE").write_text(license_text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    return repo


def prepare(repo: Path, accept_unknown_license=False) -> RepoCloner:
    """按 clone_and_modify 的顺序处理（跳过 git clone）"""
    cloner = RepoCloner(prefix="bachai", accept_unknown_license=accept_unknown_license)
    cloner.detect_project_type(repo)
    cloner.get_original_package_name(repo)
    cloner.check_license(repo)
    cloner.modify_package_name(repo)
    cloner.add_attribution(repo, UPSTREAM_URL + ".git")
    return cloner


def test_no_license_is_refused(tmp_path):
    repo = make_upstream(tmp_path, license_text=None)
    with pytest.raises(Exception, match="LICENSE"):
        RepoCloner().check_license(repo)


def test_unknown_license_needs_explicit_accept(tmp_path):
    repo = make_upstream(tmp_path, license_text="All rights reserved by Alice.\n")
    with pytest.raises(Exception, match="--accept-license"):
        RepoCloner().check_license(repo)
    assert RepoCloner(accept_unknown_license=True).check_license(repo) == "see LICENSE"


def test_license_and_author_preserved(tmp_path):
    repo = make_upstream(tmp_path, license_text=MIT_TEXT)
    cloner = prepare(repo)

    assert cloner.license_id == "MIT"
    assert cloner.original_author == "Alice Upstream"
    # 上游 LICENSE 原样保留
    assert (repo / "LICENSE").read_text(encoding="utf-8") == MIT_TEXT

    upstream_md = (repo / "UPSTREAM.md").read_text(encoding="utf-8")
    assert UPSTREAM_URL in upstream_md
    assert "Alice Upstream" in upstream_md
    assert "MIT" in upstream_md

    readme = (repo / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("> **Fork notice:**")
    assert UPSTREAM_URL in readme


def test_author_falls_back_to_github_owner(tmp_path):
    repo = make_upstream(tmp_path, license_text=MIT_TEXT)
    (repo / "setup.py").write_text(
        'from setuptools import setup\nsetup(name="awesome-mcp")\n', encoding="utf-8"
    )
    assert prepare(repo).original_author == "alice"


def test_generated_metadata_does_not_claim_bach_studio(tmp_path):
    repo = make_upstream(tmp_path, license_text=MIT_TEXT)
    prepare(repo)

    PipelineGenerator()._generate_pypi_pipeline(repo)

    # 上游只有 setup.py 时不再补生成带 BACH Studio / MIT 的 pyproject.toml
    assert not (repo / "pyproject.toml").exists()
    setup_py = (repo / "setup.py").read_text(encoding="utf-8")
    assert "BACH Studio" not in setup_py
    assert 'author="Alice Upstream"' in setup_py


def test_catalog_description_carries_attribution():
    executor = WorkflowExecutor.__new__(WorkflowExecutor)
    executor.upstream_url = None
    assert executor._upstream_attribution() == {"zh_cn": "", "zh_tw": "", "en": ""}

    executor.upstream_url = UPSTREAM_URL
    executor.upstream_author = "Alice Upstream"
    executor.upstream_license = "MIT"
    attribution = executor._upstream_attribution()
    for text in attribution.values():
        assert UPSTREAM_URL in text
        assert "Alice Upstream" in text
        assert "MIT" in text
