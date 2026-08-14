# -*- coding: utf-8 -*-
"""套件載入與指令轉交。

B01 只保證 import 與「尚未實作」回報。Result、路徑與 Rhino adapter 屬後續任務。
"""
from __future__ import annotations

import sys
from pathlib import Path

from loopflow.command_catalog import get_command

SRC_ROOT = Path(__file__).resolve().parents[1]


def ensure_src_on_path() -> Path:
    path = str(SRC_ROOT)
    if path not in sys.path:
        sys.path.insert(0, path)
    return SRC_ROOT


def run_command(command_id: str) -> dict:
    """轉交已登錄指令。尚未實作時回報 not_implemented，不假裝成功。"""
    ensure_src_on_path()
    spec = get_command(command_id)
    if spec is None:
        result = {
            "ok": False,
            "status": "unknown_command",
            "command_id": command_id,
            "message": "未知指令：%s" % command_id,
        }
        print(result["message"])
        return result
    result = {
        "ok": False,
        "status": spec["status"],
        "command_id": command_id,
        "task": spec.get("task"),
        "message": "這是 2.0 測試入口「%s」，功能尚未實作（%s）。" % (
            command_id,
            spec.get("task") or "待排程",
        ),
    }
    print(result["message"])
    return result
