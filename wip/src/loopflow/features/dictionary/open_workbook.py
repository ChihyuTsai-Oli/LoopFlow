# -*- coding: utf-8 -*-
"""用系統開啟 Dictionary 正式檔或匯出檔。不編輯、不建檔。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from loopflow.foundation import results
from loopflow.foundation.paths import (
    DICTIONARY_FILENAME,
    export_dictionary_filename,
    resolve_project_folder,
)
from loopflow.foundation.project_config import remembered_dictionary_filename
from loopflow.platform.rhino.session import RhinoSession
from loopflow.foundation.i18n import t

KIND_OFFICIAL = "official"
KIND_EXPORT = "export"
COMMAND_OPEN_OFFICIAL = "LF_Open_Dictionary"
COMMAND_OPEN_EXPORT = "LF_Open_Dictionary_Export"

Opener = Callable[[str], None]


def command_id_for_kind(kind: str) -> str:
    if kind == KIND_EXPORT:
        return COMMAND_OPEN_EXPORT
    return COMMAND_OPEN_OFFICIAL


def default_opener(path: str) -> None:
    os.startfile(path)


def resolve_workbook_path(
    session: Optional[RhinoSession],
    *,
    kind: str,
) -> results.Result:
    """解析要開啟的 xlsx。檔不存在就停止，不建立。"""
    command_id = command_id_for_kind(kind)
    if kind not in (KIND_OFFICIAL, KIND_EXPORT):
        return results.failed(
            "open_dictionary",
            t("dictionary.025") % kind,
            command_id=command_id,
        )
    filename = remembered_dictionary_filename(session)
    if not filename:
        return results.blocked(
            "open_dictionary",
            t("dictionary.019"),
            blocking=("dictionary_not_selected",),
            command_id=command_id,
        )
    resolved = resolve_project_folder(session, dictionary_filename=filename)
    if not resolved.ok:
        return resolved
    root = resolved.details["paths"].root
    if kind == KIND_OFFICIAL:
        target = root / filename
        missing = t("dictionary.020") % target.name
        blocking = "dictionary_file_missing"
    else:
        target = root / export_dictionary_filename(filename)
        missing = (
            t("dictionary.021")
            % target.name
        )
        blocking = "export_file_missing"
    if not target.is_file():
        return results.blocked(
            "open_dictionary",
            missing,
            blocking=(blocking,),
            command_id=command_id,
            details={"path": str(target), "filename": target.name, "kind": kind},
        )
    return results.ok(
        "open_dictionary",
        t("dictionary.022") % target.name,
        command_id=command_id,
        details={"path": str(target), "filename": target.name, "kind": kind},
    )


def open_workbook(
    session: Optional[RhinoSession],
    *,
    kind: str,
    opener: Optional[Opener] = None,
    command_id: Optional[str] = None,
) -> results.Result:
    """開啟已存在的 Dictionary xlsx。"""
    cid = command_id or command_id_for_kind(kind)
    resolved = resolve_workbook_path(session, kind=kind)
    if not resolved.ok:
        return resolved
    path = Path(resolved.details["path"])
    launch = opener or default_opener
    try:
        launch(str(path))
    except OSError as exc:
        return results.failed(
            "open_dictionary",
            t("dictionary.026") % (path.name, exc),
            command_id=cid,
            details={"path": str(path), "filename": path.name, "kind": kind},
        )
    if kind == KIND_EXPORT:
        message = t("dictionary.023") % path.name
    else:
        message = t("dictionary.024") % (path.name or DICTIONARY_FILENAME)
    return results.ok(
        "open_dictionary",
        message,
        command_id=cid,
        details={"path": str(path), "filename": path.name, "kind": kind},
    )
