# -*- coding: utf-8 -*-
"""把 entrypoint 轉交給 loopflow.bootstrap，不含業務邏輯。"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loopflow.bootstrap import run_command  # noqa: E402


def run(command_id: str) -> dict:
    return run_command(command_id)
