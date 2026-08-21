#! python3
# -*- coding: utf-8 -*-
"""G02 最小套件登錄的正式指令 LFDocument。開發期入口仍是 LF_Document.py，不要改那個檔名。"""
from __future__ import annotations

import sys
from pathlib import Path


def _loopflow_src() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "src"
        if (candidate / "loopflow" / "bootstrap.py").exists():
            return candidate
        installed = parent / "lib"
        if (installed / "loopflow" / "bootstrap.py").exists():
            return installed
    raise RuntimeError("找不到 loopflow 套件（src 或 lib）。")


_SRC = str(_loopflow_src())
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from loopflow.bootstrap import run_command  # noqa: E402

run_command("LF_Document")
