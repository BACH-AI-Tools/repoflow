"""
上游项目的来源与许可证（克隆并发布时用）

重新发布别人的开源项目时，必须保留原作者署名和许可证：
- 识别上游的 LICENSE / COPYING / NOTICE 文件和许可证类型
- 读出上游声明的作者（pyproject.toml / setup.py / package.json）
- 记录上游地址和克隆时的提交号
- 上游没有许可证时默认拒绝发布（没有许可证 = 没有授权）
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

LICENSE_GLOBS = ("LICENSE*", "LICENCE*", "COPYING*", "NOTICE*", "COPYRIGHT*")

# 按「越具体越先匹配」排列：AGPL/LGPL 要排在 GPL 前面，BSD-3 排在 BSD-2 前面
_LICENSE_PATTERNS = [
    ("AGPL-3.0", r"GNU AFFERO GENERAL PUBLIC LICENSE"),
    ("LGPL-3.0", r"GNU LESSER GENERAL PUBLIC LICENSE\s+Version 3"),
    ("LGPL-2.1", r"GNU LESSER GENERAL PUBLIC LICENSE\s+Version 2\.1"),
    ("GPL-3.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 3"),
    ("GPL-2.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 2"),
    ("MPL-2.0", r"Mozilla Public License,? (Version|v\.?) ?2\.0"),
    ("Apache-2.0", r"Apache License,?\s+Version 2\.0"),
    ("BSD-3-Clause", r"Neither the name of .{0,120} nor the names of its\s+contributors"),
    ("BSD-2-Clause", r"Redistribution and use in source and binary forms"),
    ("MIT", r"Permission is hereby granted, free of charge, to any person obtaining a copy"),
    ("ISC", r"Permission to use, copy, modify, and(/or)? distribute this software for any"),
    ("Unlicense", r"This is free and unencumbered software released into the public domain"),
]

# 重新发布时会带来额外义务的许可证
_OBLIGATIONS = {
    "Apache-2.0": "Apache-2.0：必须原样保留 NOTICE 文件（如果有），并在修改过的文件里注明改动",
    "GPL-3.0": "GPL-3.0（copyleft）：衍生作品必须同样以 GPL-3.0 发布并公开源码",
    "GPL-2.0": "GPL-2.0（copyleft）：衍生作品必须同样以 GPL-2.0 发布并公开源码",
    "AGPL-3.0": "AGPL-3.0（强 copyleft）：作为网络服务提供时也必须公开源码",
    "LGPL-3.0": "LGPL-3.0：修改库本身时必须以 LGPL 公开修改",
    "LGPL-2.1": "LGPL-2.1：修改库本身时必须以 LGPL 公开修改",
    "MPL-2.0": "MPL-2.0：修改过的 MPL 文件必须以 MPL 公开",
}

# 生成的元数据里绝不能出现的「冒名」默认值
PLACEHOLDER_AUTHOR = "BACH Studio"


class UnlicensedUpstreamError(Exception):
    """上游没有可识别的许可证，且没有显式确认"""


def find_license_files(repo_path: Path) -> List[str]:
    found = []
    for pattern in LICENSE_GLOBS:
        for p in sorted(Path(repo_path).glob(pattern)):
            if p.is_file() and p.name not in found:
                found.append(p.name)
    return found


def detect_license_id(repo_path: Path, files: Optional[List[str]] = None) -> Optional[str]:
    """从许可证文件全文识别 SPDX 标识；识别不出返回 None（不猜）"""
    for name in files if files is not None else find_license_files(repo_path):
        if name.upper().startswith("NOTICE"):
            continue
        try:
            text = (Path(repo_path) / name).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        flat = re.sub(r"\s+", " ", text)
        for spdx, pattern in _LICENSE_PATTERNS:
            if re.search(pattern, flat, re.IGNORECASE):
                return spdx
    return None


def _declared_license(repo_path: Path) -> Optional[str]:
    """包元数据里声明的许可证（只在许可证文件识别不出时作参考）"""
    pj = Path(repo_path) / "package.json"
    if pj.exists():
        try:
            lic = json.loads(pj.read_text(encoding="utf-8")).get("license")
            if isinstance(lic, str) and lic.strip():
                return lic.strip()
        except (ValueError, OSError):
            pass
    pt = Path(repo_path) / "pyproject.toml"
    if pt.exists():
        m = re.search(r'^\s*license\s*=\s*(?:\{\s*text\s*=\s*)?"([^"]+)"', pt.read_text(encoding="utf-8", errors="replace"), re.M)
        if m:
            return m.group(1).strip()
    return None


def _pyproject_authors(repo_path: Path) -> List[str]:
    pt = repo_path / "pyproject.toml"
    if not pt.exists():
        return []
    block = re.search(r"^\s*authors\s*=\s*\[(.*?)\]", pt.read_text(encoding="utf-8", errors="replace"), re.S | re.M)
    return re.findall(r'name\s*=\s*"([^"]+)"', block.group(1)) if block else []


def _setup_py_authors(repo_path: Path) -> List[str]:
    sp = repo_path / "setup.py"
    if not sp.exists():
        return []
    m = re.search(r'author\s*=\s*["\']([^"\']+)["\']', sp.read_text(encoding="utf-8", errors="replace"))
    return [m.group(1)] if m else []


def _package_json_authors(repo_path: Path) -> List[str]:
    pj = repo_path / "package.json"
    if not pj.exists():
        return []
    try:
        a = json.loads(pj.read_text(encoding="utf-8")).get("author")
    except (ValueError, OSError):
        return []
    if isinstance(a, dict):
        a = a.get("name")
    if not isinstance(a, str):
        return []
    # "Name <mail> (url)" -> "Name"（不用正则，避免回溯）
    name = a.split("<", 1)[0].split("(", 1)[0].strip()
    return [name] if name else []


def detect_authors(repo_path: Path) -> List[str]:
    """上游声明的作者，按 pyproject.toml → setup.py → package.json 取第一个有的；
    一个都读不到时返回空列表（不要用我们自己的名字顶上）"""
    repo_path = Path(repo_path)
    for source in (_pyproject_authors, _setup_py_authors, _package_json_authors):
        authors = [a for a in dict.fromkeys(source(repo_path)) if a and a != PLACEHOLDER_AUTHOR]
        if authors:
            return authors
    return []


def _git_head(repo_path: Path) -> Optional[str]:
    try:
        r = subprocess.run(["git", "-C", str(repo_path), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=30)
        return r.stdout.strip() or None if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def _owner_from_url(url: str) -> Optional[str]:
    m = re.search(r"github\.com[/:]([^/]+)/", url or "")
    return m.group(1) if m else None


def detect(repo_path: Path, upstream_url: str) -> Dict:
    """克隆之后、改名之前调用：读出上游的来源、作者、许可证"""
    repo_path = Path(repo_path)
    files = find_license_files(repo_path)
    license_id = detect_license_id(repo_path, files) or (_declared_license(repo_path) if files else None)
    authors = detect_authors(repo_path)
    if not authors and _owner_from_url(upstream_url):
        authors = [_owner_from_url(upstream_url)]
    warnings = []
    if license_id in _OBLIGATIONS:
        warnings.append(_OBLIGATIONS[license_id])
    if files and not license_id:
        warnings.append(f"有许可证文件（{', '.join(files)}）但识别不出是哪种许可证，发布前请人工确认")
    return {
        "upstream_url": upstream_url,
        "commit": _git_head(repo_path),
        "license_files": files,
        "license": license_id,
        "authors": authors,
        "warnings": warnings,
        "acknowledged_unlicensed": False,
    }


def require_license(prov: Dict, allow_unlicensed: bool = False) -> Dict:
    """上游没有许可证文件：默认拒绝。显式允许时记录下来（写进 UPSTREAM.md）"""
    if prov.get("license_files"):
        return prov
    if not allow_unlicensed:
        raise UnlicensedUpstreamError(
            f"上游项目 {prov.get('upstream_url')} 没有许可证文件（LICENSE / COPYING）。"
            "没有许可证就没有授权，不能重新发布。请先取得原作者许可；"
            "如果已经取得书面许可，用 --allow-unlicensed 显式确认（会记录在 UPSTREAM.md）。"
        )
    return {**prov, "acknowledged_unlicensed": True}


def author_line(prov: Optional[Dict]) -> str:
    """生成元数据用的作者；没有上游信息时（我们自己的项目）才用 BACH Studio"""
    if not prov:
        return PLACEHOLDER_AUTHOR
    return ", ".join(prov.get("authors") or []) or "Unknown (see UPSTREAM.md)"


def repo_description(repo_name: str, prov: Optional[Dict]) -> str:
    if not prov:
        return f"{repo_name} - 由 MCP工厂自动创建"
    lic = prov.get("license") or "license unknown"
    return f"{repo_name} - based on {prov['upstream_url']} ({lic})"[:350]


def write_upstream_file(repo_path: Path, prov: Dict) -> Path:
    """在仓库根目录写 UPSTREAM.md：上游地址、提交号、原作者、许可证。上游自己的 LICENSE / NOTICE 原样保留"""
    lines = [
        "# Upstream / 上游项目",
        "",
        "This repository is a republished copy of an upstream open-source project.",
        "本仓库是对下列开源项目的重新发布，版权归原作者所有。",
        "",
        f"- Source / 上游地址: {prov.get('upstream_url')}",
        f"- Commit at clone time / 克隆时的提交: {prov.get('commit') or 'unknown'}",
        f"- Original author(s) / 原作者: {', '.join(prov.get('authors') or []) or 'unknown'}",
        f"- License / 许可证: {prov.get('license') or 'not detected'}"
        + (f" (files: {', '.join(prov['license_files'])})" if prov.get("license_files") else ""),
    ]
    if prov.get("acknowledged_unlicensed"):
        lines.append("- ⚠️ Upstream has no license file; republished with an explicit acknowledgement (--allow-unlicensed) that permission was obtained from the author.")
    for w in prov.get("warnings") or []:
        lines.append(f"- ⚠️ {w}")
    path = Path(repo_path) / "UPSTREAM.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
