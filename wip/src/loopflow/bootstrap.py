# -*- coding: utf-8 -*-
"""套件載入與指令轉交。尚未實作的指令回報 Result，不假裝成功。"""
from __future__ import annotations

import sys
from pathlib import Path

from loopflow.command_catalog import get_command
from loopflow.foundation.results import Result, unknown_command
from loopflow.foundation.i18n import t

SRC_ROOT = Path(__file__).resolve().parents[1]


def ensure_src_on_path() -> Path:
    path = str(SRC_ROOT)
    if path not in sys.path:
        sys.path.insert(0, path)
    return SRC_ROOT


def _emit_result(result: Result) -> Result:
    print(result.message)
    details = result.details or {}
    exception = details.get("exception")
    if exception and str(exception) not in result.message:
        print(exception)
    traceback_text = details.get("traceback")
    if traceback_text:
        print(traceback_text)
    seen = []
    for warning in result.warnings or ():
        if warning in seen:
            continue
        seen.append(warning)
        print(t("dispatch.001") % warning)
    return result


def run_command(command_id: str) -> Result:
    """轉交已登錄指令。尚未實作時回報 not_implemented。"""
    ensure_src_on_path()
    spec = get_command(command_id)
    if spec is None:
        result = unknown_command(
            "dispatch",
            t("dispatch.002") % command_id,
            command_id=command_id,
        )
        return _emit_result(result)
    if command_id != "LF_Language":
        from loopflow.features.document.language import ensure_locale

        pending = ensure_locale()
        if pending is not None:
            return _emit_result(pending)
    from loopflow.runners import dispatch

    return _emit_result(dispatch(command_id))
