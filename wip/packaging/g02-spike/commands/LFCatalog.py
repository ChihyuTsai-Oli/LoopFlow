#! python 3
# -*- coding: utf-8 -*-
"""G02 套件登錄的正式指令 LFCatalog。開發期入口仍是 LF_Catalog.py，不要改那個檔名。"""
from __future__ import annotations

import sys
from pathlib import Path


def _has_loopflow(root: Path) -> bool:
    return (root / "loopflow" / "bootstrap.py").exists()


def _loopflow_src() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        for folder in ("src", "lib"):
            candidate = parent / folder
            if _has_loopflow(candidate):
                return candidate
        if _has_loopflow(parent):
            return parent
    try:
        import Rhino

        rhp = Rhino.PlugIns.PlugIn.PathFromName("LoopFlow")
    except Exception:
        rhp = None
    if rhp:
        package_dir = Path(str(rhp)).resolve().parent
        for candidate in (package_dir / "lib", package_dir / "src", package_dir):
            if _has_loopflow(candidate):
                return candidate
    raise RuntimeError("找不到 loopflow 套件（src 或 lib）。")


_SRC = str(_loopflow_src())
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from loopflow.bootstrap import run_command  # noqa: E402

run_command("LF_Catalog")
