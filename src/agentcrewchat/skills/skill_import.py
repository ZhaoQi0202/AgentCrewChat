from __future__ import annotations

import io
import re
import shutil
import zipfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from agentcrewchat.config.loader import load_all
from agentcrewchat.config.models import SkillEntry
from agentcrewchat.paths import config_dir, install_root


def discover_skill_roots(base: Path) -> list[Path]:
    if not base.is_dir():
        return []
    if (base / "SKILL.md").is_file():
        return [base.resolve()]
    out: list[Path] = []
    for child in sorted(base.iterdir()):
        if child.is_dir() and (child / "SKILL.md").is_file():
            out.append(child.resolve())
    return out


def _zip_root_dir(extract_to: Path) -> Path:
    dirs = [p for p in extract_to.iterdir() if p.is_dir()]
    if len(dirs) == 1:
        return dirs[0]
    return extract_to


def parse_github_skill_url(url: str) -> tuple[str, str, str, str]:
    u = url.strip().rstrip("/")
    if "github.com" not in u.lower():
        raise ValueError("不是 GitHub 链接")
    u = re.sub(r"^https?://github\.com/", "", u, flags=re.I)
    parts = u.split("/")
    if len(parts) < 2:
        raise ValueError("无法解析 owner/repo")
    owner, repo = parts[0], parts[1].removesuffix(".git")
    ref = "main"
    subpath = ""
    if len(parts) > 2 and parts[2] == "tree" and len(parts) > 3:
        ref = parts[3]
        subpath = "/".join(parts[4:]) if len(parts) > 4 else ""
    return owner, repo, ref, subpath


def _download_zip(owner: str, repo: str, ref: str) -> bytes:
    zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{ref}"
    req = Request(zip_url, headers={"User-Agent": "AgentCrewChat/1.0"})
    try:
        with urlopen(req, timeout=120) as resp:
            return resp.read()
    except HTTPError as e:
        if e.code == 404 and ref == "main":
            return _download_zip(owner, repo, "master")
        raise ValueError(f"下载失败（{e.code}）：{zip_url}") from e
    except URLError as e:
        raise ValueError(f"网络错误：{e}") from e


def import_github_skills_url(url: str, *, config_root: Path | None = None) -> list[SkillEntry]:
    import tempfile

    owner, repo, ref, subpath = parse_github_skill_url(url)
    raw = _download_zip(owner, repo, ref)
    buf = io.BytesIO(raw)
    with tempfile.TemporaryDirectory() as staging:
        with zipfile.ZipFile(buf) as zf:
            zf.extractall(staging)
        root = _zip_root_dir(Path(staging))
        target = root.joinpath(*subpath.split("/")) if subpath else root
        if not target.is_dir():
            raise ValueError(f"仓库内路径不存在：{subpath or '(根)'}")
        roots = discover_skill_roots(target)
        if not roots:
            raise ValueError("该路径下未找到含 SKILL.md 的目录（单层子目录或当前目录）")
        return install_skill_roots_to_data(roots, config_root=config_root)


def materialize_local_folder(path: Path) -> list[Path]:
    p = path.expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(str(p))
    return discover_skill_roots(p)


def import_local_skills_path(path: str | Path, *, config_root: Path | None = None) -> list[SkillEntry]:
    roots = materialize_local_folder(Path(path))
    if not roots:
        raise ValueError("该路径下未找到含 SKILL.md 的目录（单层子目录或当前目录）")
    return install_skill_roots_to_data(roots, config_root=config_root)


def import_skills_from_input(text: str, *, config_root: Path | None = None) -> list[SkillEntry]:
    s = text.strip()
    if s.startswith("https://") or s.startswith("http://"):
        if "github.com" not in s:
            raise ValueError("目前仅支持 github.com 链接")
        return import_github_skills_url(s, config_root=config_root)
    return import_local_skills_path(s, config_root=config_root)


def _slug(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "_", name.strip()).strip("_").lower()
    return s or "skill"


def _allocate_ids(base_slug: str, taken: set[str]) -> str:
    if base_slug not in taken:
        return base_slug
    n = 2
    while f"{base_slug}_{n}" in taken:
        n += 1
    return f"{base_slug}_{n}"


def install_skill_roots_to_data(
    roots: list[Path], *, config_root: Path | None = None
) -> list[SkillEntry]:
    root_install = install_root().resolve()
    dest_parent = root_install / "data" / "skills_install"
    dest_parent.mkdir(parents=True, exist_ok=True)
    base = config_dir() if config_root is None else config_root
    cfg = load_all(base)
    taken: set[str] = {e.id for e in cfg.skills}
    out: list[SkillEntry] = []
    for src in roots:
        base_slug = _slug(src.name)
        sid = _allocate_ids(base_slug, taken)
        taken.add(sid)
        dest = dest_parent / sid
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        rel = dest.relative_to(root_install).as_posix()
        out.append(
            SkillEntry(
                id=sid,
                name=None,
                description=None,
                skill_dir=rel,
                enabled=True,
                scope="app",
            )
        )
    return out


def install_skill_roots_to_task_workspace(
    roots: list[Path],
    task_workspace: Path,
) -> list[SkillEntry]:
    root_install = install_root().resolve()
    tw = task_workspace.expanduser().resolve()
    try:
        tw.relative_to(root_install)
    except ValueError as e:
        raise ValueError("任务目录须位于安装根（workspaces/…）下") from e
    dest_parent = tw / ".agentcrewchat" / "skills"
    dest_parent.mkdir(parents=True, exist_ok=True)
    taken: set[str] = set()
    for p in dest_parent.iterdir():
        if p.is_dir():
            taken.add(p.name)
    cfg = load_all()
    taken |= {e.id for e in cfg.skills}
    out: list[SkillEntry] = []
    for src in roots:
        base_slug = _slug(src.name)
        sid = _allocate_ids(base_slug, taken)
        taken.add(sid)
        dest = dest_parent / sid
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        rel = dest.relative_to(root_install).as_posix()
        out.append(
            SkillEntry(
                id=sid,
                name=None,
                description=None,
                skill_dir=rel,
                enabled=True,
                scope="task",
            )
        )
    return out
