# -*- coding: utf-8 -*-
"""已實作指令的 live runner 表。bootstrap 只查表，不為各指令堆 if。"""
from __future__ import annotations

from typing import Callable, Dict

from loopflow.command_catalog import get_command
from loopflow.foundation.results import Result, not_implemented
from loopflow.foundation.i18n import t

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


def run_tagger_laser() -> Result:
    from loopflow.features.tagger.laser import run_tagger_laser as run_laser

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_laser(opened.details["session"]))


def run_tagger_index() -> Result:
    from loopflow.features.tagger.index import run_tagger_index as run_index

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_index(opened.details["session"]))


def run_tagger_layout_id() -> Result:
    from loopflow.features.tagger.layout_id import run_tagger_layout_id as run_layout_id

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_layout_id(opened.details["session"]))


def run_anchor_frame() -> Result:
    from loopflow.features.view.register import run_anchor_frame as run_register

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_register(opened.details["session"]))


def run_catalog() -> Result:
    from loopflow.features.catalog.catalog import run_catalog as run_catalog_command

    opened = _open_live_session()
    if not opened.ok:
        return opened
    return _present_failure(run_catalog_command(opened.details["session"]))


def run_infuser_part() -> Result:
    from loopflow.features.infuser.part import run_infuser_part as run_part
    from loopflow.platform.rhino.prompts import show_message

    opened = _open_live_session()
    if not opened.ok:
        return opened
    result = run_part(opened.details["session"], show_message=show_message)
    if not result.ok:
        return _present_failure(result)
    return result


def run_infuser_all() -> Result:
    from loopflow.features.infuser.all import run_infuser_all as run_all
    from loopflow.platform.rhino.prompts import show_message

    opened = _open_live_session()
    if not opened.ok:
        return opened
    result = run_all(opened.details["session"], show_message=show_message)
    if not result.ok:
        return _present_failure(result)
    return result


def run_tag_o() -> Result:
    from loopflow.features.health.tag_o import run_tag_o as run_health
    from loopflow.platform.rhino.prompts import show_colored_log_panel

    opened = _open_live_session()
    if not opened.ok:
        return opened
    session = opened.details["session"]

    def _panel(lines) -> None:
        zoom = getattr(session, "zoom_to_layout_object", None)

        def _select(tag_id: str, page_name: str) -> None:
            if callable(zoom):
                zoom(page_name, tag_id)

        show_colored_log_panel(lines, on_select=_select)

    result = run_health(session, show_panel=_panel)
    if not result.ok:
        return _present_failure(result)
    return result


def run_extract_cp() -> Result:
    from loopflow.features.drawing.extract import run_extract_cp as run_extract
    from loopflow.platform.rhino.prompts import show_message

    opened = _open_live_session()
    if not opened.ok:
        return opened
    result = run_extract(opened.details["session"], show_message=show_message)
    if not result.ok:
        return _present_failure(result)
    return result


def run_duplicate_layout() -> Result:
    from loopflow.features.sheet.duplicate import run_duplicate_layout as run_duplicate
    from loopflow.platform.rhino.prompts import show_message

    opened = _open_live_session()
    if not opened.ok:
        return opened
    result = run_duplicate(opened.details["session"], show_message=show_message)
    if not result.ok:
        return _present_failure(result)
    return result


def run_sync_worksession() -> Result:
    from loopflow.features.worksession.sync import run_sync_worksession as run_sync
    from loopflow.foundation.config import DEFAULT_CONFIG
    from loopflow.platform.rhino.worksession import LiveWorksessionHost, sticky_store

    opened = _open_live_session()
    if not opened.ok:
        return opened
    result = run_sync(
        LiveWorksessionHost(),
        sticky_store(),
        delay_seconds=DEFAULT_CONFIG.worksession_refresh_delay,
    )
    if not result.ok:
        return _present_failure(result)
    from loopflow.platform.rhino.prompts import show_message

    show_message(result.message)
    return result


def run_document() -> Result:
    from loopflow.features.document.open_guide import open_document

    opened = _open_live_session()
    if not opened.ok:
        return opened
    result = open_document()
    if not result.ok:
        return _present_failure(result)
    return result


def run_language() -> Result:
    from loopflow.features.document.language import run_language as run_locale

    return run_locale()


RUNNERS: Dict[str, Runner] = {
    "LF_Nexus": run_nexus,
    "LF_Open_Dictionary": run_open_dictionary,
    "LF_Open_Dictionary_Export": run_open_dictionary_export,
    "LF_Export_Type_Layers": run_export_type_layers,
    "LF_Publish_Exchange": run_publish_exchange,
    "LF_Data_Viewer": run_data_viewer,
    "LF_Tagger_Grab": run_tagger_grab,
    "LF_Tagger_Laser": run_tagger_laser,
    "LF_Tagger_Index": run_tagger_index,
    "LF_Tagger_Layout_ID": run_tagger_layout_id,
    "LF_Anchor_Frame": run_anchor_frame,
    "LF_Catalog": run_catalog,
    "LF_Infuser_Part": run_infuser_part,
    "LF_Infuser_All": run_infuser_all,
    "LF_TAG-O": run_tag_o,
    "LF_Extract_CP": run_extract_cp,
    "LF_Duplicate_Layout": run_duplicate_layout,
    "LF_Sync_Worksession": run_sync_worksession,
    "LF_Document": run_document,
    "LF_Language": run_language,
}


def dispatch(command_id: str) -> Result:
    """依指令 ID 查 runner。未實作回報 not_implemented，不假裝成功。"""
    spec = get_command(command_id) or {}
    runner = RUNNERS.get(command_id)
    if runner is None:
        return not_implemented(
            "dispatch",
            t("runners.001")
            % (command_id, spec.get("task") or t("runners.002")),
            command_id=command_id,
            details={"task": spec.get("task")},
        )
    return runner()
