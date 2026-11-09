"""
Issue #5: clone-and-publish must keep the upstream author and license, and refuse to republish unlicensed code.
No network: the clone step is replaced by a local copy of a fixture repo.
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import provenance  # noqa: E402
from src.pipeline_generator import PipelineGenerator  # noqa: E402
from src.repo_cloner import RepoCloner  # noqa: E402

UPSTREAM = "https://github.com/alice/weather-mcp"
MIT_TEXT = """MIT License

Copyright (c) 2025 Alice Example

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
"""
APACHE_TEXT = """                                 Apache License
                           Version 2.0, January 2004
                        http://www.apache.org/licenses/
"""


def make_upstream(tmp_path: Path, license_text=None, notice=None, setup_author="Alice Example") -> Path:
    repo = tmp_path / "weather-mcp"
    repo.mkdir()
    (repo / "README.md").write_text("# weather-mcp\n", encoding="utf-8")
    # only setup.py, no pyproject.toml: the generator path that used to write BACH Studio / MIT
    (repo / "setup.py").write_text(f'from setuptools import setup\nsetup(name="weather-mcp", version="0.3.0", author="{setup_author}")\n', encoding="utf-8")
    if license_text:
        (repo / "LICENSE").write_text(license_text, encoding="utf-8")
    if notice:
        (repo / "NOTICE").write_text(notice, encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "init"], check=True)
    return repo


def fake_clone(src: Path):
    def _clone(self, github_url, target_dir=None):
        dest = Path(target_dir or (src.parent / "clone")) / src.name if target_dir else src.parent / "clone"
        shutil.copytree(src, dest)
        self.cloned_repo_path = dest
        return dest
    return _clone


# ---------- detection ----------

def test_detects_mit_license_authors_and_commit(tmp_path):
    repo = make_upstream(tmp_path, MIT_TEXT)
    prov = provenance.detect(repo, UPSTREAM)
    assert prov["license"] == "MIT"
    assert prov["license_files"] == ["LICENSE"]
    assert prov["authors"] == ["Alice Example"]
    assert prov["commit"] and len(prov["commit"]) == 40
    assert prov["upstream_url"] == UPSTREAM


def test_apache_license_warns_about_notice(tmp_path):
    repo = make_upstream(tmp_path, APACHE_TEXT, notice="Weather MCP\nCopyright 2025 Alice Example\n")
    prov = provenance.detect(repo, UPSTREAM)
    assert prov["license"] == "Apache-2.0"
    assert "NOTICE" in prov["license_files"]
    assert any("NOTICE" in w for w in prov["warnings"])


def test_falls_back_to_github_owner_not_bach_studio(tmp_path):
    repo = make_upstream(tmp_path, MIT_TEXT, setup_author="BACH Studio")
    prov = provenance.detect(repo, UPSTREAM)
    assert prov["authors"] == ["alice"]


# ---------- unlicensed upstream ----------

def test_unlicensed_upstream_is_refused(tmp_path):
    repo = make_upstream(tmp_path, license_text=None)
    with pytest.raises(provenance.UnlicensedUpstreamError):
        provenance.require_license(provenance.detect(repo, UPSTREAM))


def test_unlicensed_upstream_needs_explicit_ack_and_is_recorded(tmp_path):
    repo = make_upstream(tmp_path, license_text=None)
    prov = provenance.require_license(provenance.detect(repo, UPSTREAM), allow_unlicensed=True)
    assert prov["acknowledged_unlicensed"] is True
    text = provenance.write_upstream_file(repo, prov).read_text(encoding="utf-8")
    assert "--allow-unlicensed" in text


def test_clone_and_modify_fails_without_license(tmp_path, monkeypatch):
    src = make_upstream(tmp_path, license_text=None)
    monkeypatch.setattr(RepoCloner, "clone_repository", fake_clone(src))
    result = RepoCloner(prefix="bachai").clone_and_modify(UPSTREAM)
    assert result["success"] is False
    assert "许可证" in result["error"]


def test_clone_and_modify_reads_authors_before_renaming(tmp_path, monkeypatch):
    src = make_upstream(tmp_path, MIT_TEXT)
    monkeypatch.setattr(RepoCloner, "clone_repository", fake_clone(src))
    result = RepoCloner(prefix="bachai").clone_and_modify(UPSTREAM)
    assert result["success"] is True, result.get("error")
    prov = result["provenance"]
    assert prov["authors"] == ["Alice Example"]
    assert prov["license"] == "MIT"


# ---------- generated metadata ----------

def test_generated_pyproject_keeps_upstream_author_and_license(tmp_path):
    repo = make_upstream(tmp_path, APACHE_TEXT)
    gen = PipelineGenerator(org_name="BACH-AI-Tools")
    gen.provenance = provenance.detect(repo, UPSTREAM)
    gen._generate_pypi_pipeline(repo)
    pyproject = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "BACH Studio" not in pyproject
    assert "MIT" not in pyproject
    assert 'name = "Alice Example"' in pyproject
    assert 'license = {text = "Apache-2.0"}' in pyproject
    assert "Apache Software License" in pyproject
    assert f'Upstream = "{UPSTREAM}"' in pyproject


def test_generated_metadata_never_claims_mit_for_unlicensed_upstream(tmp_path):
    repo = make_upstream(tmp_path, license_text=None)
    (repo / "setup.py").unlink()
    gen = PipelineGenerator()
    gen.provenance = provenance.require_license(provenance.detect(repo, UPSTREAM), allow_unlicensed=True)
    gen._generate_pypi_pipeline(repo)
    for name in ("setup.py", "pyproject.toml"):
        text = (repo / name).read_text(encoding="utf-8")
        assert "BACH Studio" not in text, name
        assert "MIT" not in text, name


def test_generated_package_json_uses_upstream_author(tmp_path):
    repo = make_upstream(tmp_path, MIT_TEXT)
    gen = PipelineGenerator()
    gen.provenance = provenance.detect(repo, UPSTREAM)
    gen._generate_npm_pipeline(repo)
    import json
    pkg = json.loads((repo / "package.json").read_text(encoding="utf-8"))
    assert pkg["author"] == "Alice Example"
    assert pkg["license"] == "MIT"


def test_own_projects_keep_previous_metadata(tmp_path):
    """No provenance = our own project: behaviour unchanged."""
    repo = tmp_path / "ours"
    repo.mkdir()
    (repo / "README.md").write_text("# ours\n", encoding="utf-8")
    PipelineGenerator()._generate_pypi_pipeline(repo)
    pyproject = (repo / "pyproject.toml").read_text(encoding="utf-8")
    assert "BACH Studio" in pyproject and 'license = {text = "MIT"}' in pyproject


# ---------- provenance in the published repo ----------

def test_upstream_file_and_license_preserved(tmp_path):
    repo = make_upstream(tmp_path, MIT_TEXT)
    before = (repo / "LICENSE").read_bytes()
    prov = provenance.detect(repo, UPSTREAM)
    text = provenance.write_upstream_file(repo, prov).read_text(encoding="utf-8")
    assert (repo / "LICENSE").read_bytes() == before
    assert UPSTREAM in text and prov["commit"] in text and "Alice Example" in text and "MIT" in text


def test_repo_description_and_catalog_author():
    prov = {"upstream_url": UPSTREAM, "license": "MIT", "authors": ["Alice Example"]}
    assert provenance.repo_description("bachai-weather-mcp", prov) == f"bachai-weather-mcp - based on {UPSTREAM} (MIT)"
    assert provenance.author_line(prov) == "Alice Example"
    assert provenance.author_line(None) == "BACH Studio"
    assert provenance.repo_description("ours", None) == "ours - 由 MCP工厂自动创建"
