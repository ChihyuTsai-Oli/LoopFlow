# -*- coding: utf-8 -*-
"""LF_Data_Viewer：點選物件、只讀顯示 canonical 資料。"""
from __future__ import annotations

from typing import Callable, List, Mapping, Optional

from loopflow.features.dictionary.loader import TypeCatalog, load_from_workfiles
from loopflow.features.viewer.inspect import (
    COMMAND_ID,
    check_document_schema,
    format_report,
    inspect_object,
)
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

PickObject = Callable[[RhinoSession], Optional[str]]
ShowReport = Callable[[str], None]
Notify = Callable[[str], None]


def _optional_catalog(
    catalog: Optional[TypeCatalog],
    environ: Optional[Mapping[str, str]],
) -> Optional[TypeCatalog]:
    if catalog is not None:
        return catalog
    loaded = load_from_workfiles(environ=environ)
    if loaded.ok:
        return loaded.details.get("catalog")
    return None


def _notify(notify: Optional[Notify], message: str) -> None:
    if notify is not None:
        notify(message)
        return
    from loopflow.platform.rhino.prompts import show_message

    show_message(message, "LF Data Viewer")


def _default_pick(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_object

    return pick_object()


def _default_show(text: str) -> None:
    from loopflow.platform.rhino.prompts import show_readonly_text

    show_readonly_text(text, "LF Data Viewer")


def run_data_viewer(
    session: RhinoSession,
    *,
    pick_object: Optional[PickObject] = None,
    show_report: Optional[ShowReport] = None,
    notify: Optional[Notify] = None,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> results.Result:
    """點選物件並顯示 canonical 報告。不寫入來源。"""
    schema = check_document_schema(session)
    if not schema.ok:
        _notify(notify, schema.message)
        return schema
    loaded_catalog = _optional_catalog(catalog, environ)
    picker = pick_object or _default_pick
    shower = show_report or _default_show
    warnings = list(schema.warnings or ())

    def action(current: RhinoSession) -> results.Result:
        viewed = 0
        texts: List[str] = []
        while True:
            object_id = picker(current)
            if not object_id:
                if viewed == 0:
                    return results.cancelled(
                        "inspect_object",
                        "已結束檢視。",
                        command_id=COMMAND_ID,
                        warnings=tuple(warnings),
                        details={"viewed": 0, "reports": ()},
                    )
                return results.ok(
                    "inspect_object",
                    "已檢視 %s 個物件。" % viewed,
                    command_id=COMMAND_ID,
                    warnings=tuple(warnings),
                    details={"viewed": viewed, "reports": tuple(texts)},
                )
            if current.get_view_state(object_id) is None:
                _notify(notify, "找不到物件。")
                continue
            report = inspect_object(current, object_id, catalog=loaded_catalog)
            text = format_report(report)
            texts.append(text)
            shower(text)
            viewed += 1

    return run_guarded(session, action, command_id=COMMAND_ID)
