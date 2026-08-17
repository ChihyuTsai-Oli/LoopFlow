# -*- coding: utf-8 -*-
"""已實作指令的 live runner 表。bootstrap 只查表，不為各指令堆 if。"""
from __future__ import annotations

from typing import Callable, Dict

from loopflow.command_catalog import get_command
from loopflow.foundation.results import Result, not_implemented

Runner = Callable[[], Result]


def _open_live_session() -> Result:
    from loopflow.platform.rhino.live import open_session

    return open_session()


def _present_failure(result: Result) -> Result:
    if not result.ok:
        from loopflow.platform.rhino.prompts import show_failure_popup

        show_failure_popup(result)
    return result


def run_nexus() -> Result:
    from loopflow.features.project.menu import run_nexus_console

    opened = _open_live_session()
    session = opened.details.get("session") if opened.ok else None
    return run_nexus_console(session, interactive=session is not None)


def run_open_dictionary() -> Result:
    from loopflow.features.dictionary.open_workbook import KIND_OFFICIAL, open_workbook

    opened = _open_live_session()
    session = opened.details.get("session") if opened.ok else None
    return _present_failure(open_workbook(session, kind=KIND_OFFICIAL))


def run_open_dictionary_export() -> Result:
    from loopflow.features.dictionary.open_workbook import KIND_EXPORT, open_workbook

    opened = _open_live_session()
    session = opened.details.get("session") if opened.ok else None
    return _present_failure(open_workbook(session, kind=KIND_EXPORT))


def run_export_type_layers() -> Result:
    from loopflow.features.dictionary.export_command import run_export_type_layers as run_export

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_export(opened.details["session"]))


def run_publish_exchange() -> Result:
    from loopflow.features.registry.handoff import run_publish_exchange as run_publish

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_publish(opened.details["session"]))


def run_data_viewer() -> Result:
    from loopflow.features.viewer.command import run_data_viewer as run_viewer

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return run_viewer(opened.details["session"])


def run_tagger_grab() -> Result:
    from loopflow.features.tagger.grab import run_tagger_grab as run_grab

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_grab(opened.details["session"]))


def run_anchor_frame() -> Result:
    from loopflow.features.view.register import run_anchor_frame as run_register

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_register(opened.details["session"]))


RUNNERS: Dict[str, Runner] = {
    "LF_Nexus": run_nexus,
    "LF_Open_Dictionary": run_open_dictionary,
    "LF_Open_Dictionary_Export": run_open_dictionary_export,
    "LF_Export_Type_Layers": run_export_type_layers,
    "LF_Publish_Exchange": run_publish_exchange,
    "LF_Data_Viewer": run_data_viewer,
    "LF_Tagger_Grab": run_tagger_grab,
    "LF_Anchor_Frame": run_anchor_frame,
}


def dispatch(command_id: str) -> Result:
    """依指令 ID 查 runner。未實作回報 not_implemented，不假裝成功。"""
    spec = get_command(command_id) or {}
    runner = RUNNERS.get(command_id)
    if runner is None:
        return not_implemented(
            "dispatch",
            "這是 2.0 測試入口「%s」，功能尚未實作（%s）。"
            % (command_id, spec.get("task") or "待排程"),
            command_id=command_id,
            details={"task": spec.get("task")},
        )
    return runner()
