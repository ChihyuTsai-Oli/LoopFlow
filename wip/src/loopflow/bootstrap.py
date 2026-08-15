# -*- coding: utf-8 -*-
"""套件載入與指令轉交。尚未實作的指令回報 Result，不假裝成功。"""
from __future__ import annotations

import sys
from pathlib import Path

from loopflow.command_catalog import get_command
from loopflow.foundation.results import Result, not_implemented, unknown_command

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
        print("警告：%s" % warning)
    return result


def _run_nexus() -> Result:
    from loopflow.features.project.menu import run_nexus_console
    from loopflow.platform.rhino.live import open_session

    opened = open_session()
    session = opened.details.get("session") if opened.ok else None
    return run_nexus_console(session, interactive=session is not None)


def _run_publish() -> Result:
    from loopflow.features.project.console import open_console
    from loopflow.platform.rhino.live import open_session

    opened = open_session()
    if not opened.ok:
        return opened
    return open_console(opened.details["session"], step="publish_registry")


def _run_data_viewer() -> Result:
    from loopflow.features.viewer.command import run_data_viewer
    from loopflow.platform.rhino.live import open_session

    opened = open_session()
    if not opened.ok:
        return opened
    return run_data_viewer(opened.details["session"])


def run_command(command_id: str) -> Result:
    """轉交已登錄指令。尚未實作時回報 not_implemented。"""
    ensure_src_on_path()
    spec = get_command(command_id)
    if spec is None:
        result = unknown_command(
            "dispatch",
            "未知指令：%s" % command_id,
            command_id=command_id,
        )
        return _emit_result(result)
    if command_id == "LF_Nexus":
        return _emit_result(_run_nexus())
    if command_id == "LF_Push_3D_to_JSON":
        return _emit_result(_run_publish())
    if command_id == "LF_Data_Viewer":
        return _emit_result(_run_data_viewer())
    result = not_implemented(
        "dispatch",
        "這是 2.0 測試入口「%s」，功能尚未實作（%s）。" % (
            command_id,
            spec.get("task") or "待排程",
        ),
        command_id=command_id,
        details={"task": spec.get("task")},
    )
    return _emit_result(result)
