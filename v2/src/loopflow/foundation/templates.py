# -*- coding: utf-8 -*-
"""官方 Tag 圖塊與 Dictionary 範本：套件內留一份，載入時拷到文件\\LoopFlow。"""
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from .version import PACKAGE_VERSION

SOURCE_ENV = "LOOPFLOW_TEMPLATES_SOURCE"
DEST_ENV = "LOOPFLOW_TEMPLATES_DEST"
NO_OPEN_ENV = "LOOPFLOW_TEMPLATES_NO_OPEN"
STAMP_FILENAME = "assets_version.txt"

TEMPLATE_FILES = (
    "Tag_Blocks.3dm",
    "LoopFlow_Dictionary_tw.xlsx",
    "LoopFlow_Dictionary_en.xlsx",
)


def _in_unittest() -> bool:
    return "unittest.case" in sys.modules or "unittest.loader" in sys.modules


def _package_and_src_roots() -> Tuple[Path, Path]:
    """loopflow 套件的上一層（src 或 lib）與其再上一層（v2 或 yak 目錄）。"""
    src_or_lib = Path(__file__).resolve().parents[2]
    return src_or_lib, src_or_lib.parent


def documents_loopflow_dir() -> Path:
    """%USERPROFILE%\\Documents\\LoopFlow；中文 Windows 即「文件\\LoopFlow」。"""
    override = str(os.environ.get(DEST_ENV) or "").strip().strip('"')
    if override:
        return Path(override)
    profile = os.environ.get("USERPROFILE") or str(Path.home())
    return Path(profile) / "Documents" / "LoopFlow"


def source_search_roots() -> Tuple[Path, ...]:
    """套件 templates\\、開發期 v2\\docs 對應目錄；測試可設 LOOPFLOW_TEMPLATES_SOURCE 只搜該層。"""
    override = str(os.environ.get(SOURCE_ENV) or "").strip().strip('"')
    if override:
        return (Path(override),)
    roots = []
    src_or_lib, package_dir = _package_and_src_roots()
    roots.append(package_dir / "templates")
    roots.append(src_or_lib / "templates")
    if src_or_lib.name == "src":
        docs = src_or_lib.parent / "docs"
        roots.append(docs / "Tag_Blocks_3dm")
        roots.append(docs / "字典")
    return tuple(roots)


def find_template_source(name: str) -> Optional[Path]:
    if name not in TEMPLATE_FILES:
        return None
    for root in source_search_roots():
        candidate = root / name
        if candidate.is_file():
            return candidate
    return None


@dataclass(frozen=True)
class SeedResult:
    """這次拷了哪些、略過哪些（目的地已有且版號相同）、套件裡找不到哪些。"""

    dest: Path
    copied: Tuple[str, ...]
    skipped: Tuple[str, ...]
    missing: Tuple[str, ...]

    @property
    def copied_any(self) -> bool:
        return bool(self.copied)


def _should_open_folder() -> bool:
    if str(os.environ.get(NO_OPEN_ENV) or "").strip():
        return False
    if _in_unittest():
        return False
    return True


def _open_folder(path: Path) -> None:
    if os.name == "nt":
        os.startfile(str(path))  # type: ignore[attr-defined]


def _read_stamp(target: Path) -> Optional[str]:
    path = target / STAMP_FILENAME
    if not path.is_file():
        return None
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _write_stamp(target: Path, version: str) -> None:
    (target / STAMP_FILENAME).write_text("%s\n" % version, encoding="utf-8")


def _official_files_present(target: Path) -> bool:
    return all((target / name).is_file() for name in TEMPLATE_FILES)


def seed_official_templates(
    *,
    dest: Optional[Path] = None,
    open_folder: Optional[bool] = None,
) -> SeedResult:
    """把官方範本拷到文件\\LoopFlow。套件版號與戳記相同時已有不蓋；版號不同或沒有戳記則先刪官方三檔再拷。失敗不擋指令。"""
    if (
        _in_unittest()
        and dest is None
        and not str(os.environ.get(DEST_ENV) or "").strip()
        and not str(os.environ.get(SOURCE_ENV) or "").strip()
    ):
        target = documents_loopflow_dir()
        return SeedResult(dest=target, copied=(), skipped=(), missing=())

    target = Path(dest) if dest is not None else documents_loopflow_dir()
    copied = []
    skipped = []
    missing = []
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        return SeedResult(
            dest=target,
            copied=(),
            skipped=(),
            missing=TEMPLATE_FILES,
        )
    refresh = _read_stamp(target) != PACKAGE_VERSION
    for name in TEMPLATE_FILES:
        source = find_template_source(name)
        if source is None:
            missing.append(name)
            continue
        destination = target / name
        if destination.is_file() and not refresh:
            skipped.append(name)
            continue
        if destination.is_file() and refresh:
            try:
                destination.unlink()
            except OSError:
                pass
        try:
            shutil.copy2(str(source), str(destination))
        except OSError:
            missing.append(name)
            continue
        copied.append(name)
    if _official_files_present(target):
        try:
            _write_stamp(target, PACKAGE_VERSION)
        except OSError:
            pass
    result = SeedResult(
        dest=target,
        copied=tuple(copied),
        skipped=tuple(skipped),
        missing=tuple(missing),
    )
    should_open = _should_open_folder() if open_folder is None else open_folder
    if result.copied_any and should_open:
        try:
            _open_folder(target)
        except OSError:
            pass
    return result
