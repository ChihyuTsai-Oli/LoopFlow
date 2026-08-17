# -*- coding: utf-8 -*-
"""用系統開啟 Dictionary 正式檔或匯出檔。不編輯、不建檔。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Mapping, Optional

from loopflow.foundation import results
from loopflow.foundation.paths import (
    DICTIONARY_FILENAME,
    dictionary_filename_from_session,
    export_dictionary_filename,
    resolve_workfiles,
)
from loopflow.platform.rhino.session import RhinoSession

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
    environ: Optional[Mapping[str, str]] = None,
) -> results.Result:
    """解析要開啟的 xlsx。檔不存在就停止，不建立。"""
    command_id = command_id_for_kind(kind)
    if kind not in (KIND_OFFICIAL, KIND_EXPORT):
        return results.failed(
            "open_dictionary",
            "未知的字典檔種類：%s" % kind,
            command_id=command_id,
        )
    filename = dictionary_filename_from_session(session)
    workfiles = resolve_workfiles(environ=environ, dictionary_filename=filename)
    if not workfiles.ok:
        return workfiles
    root = workfiles.details["paths"].root
    if kind == KIND_OFFICIAL:
        target = root / filename
        missing = (
            "找不到 Dictionary 檔案 %s。請用 Nexus 選單 2 指定工作檔資料夾內的 .xlsx。"
            % target.name
        )
        blocking = "dictionary_file_missing"
    else:
        target = root / export_dictionary_filename(filename)
        missing = (
            "找不到匯出檔 %s。請先執行 LF_Export_Type_Layers。"
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
        "已找到 %s" % target.name,
        command_id=command_id,
        details={"path": str(target), "filename": target.name, "kind": kind},
    )


def open_workbook(
    session: Optional[RhinoSession],
    *,
    kind: str,
    environ: Optional[Mapping[str, str]] = None,
    opener: Optional[Opener] = None,
    command_id: Optional[str] = None,
) -> results.Result:
    """開啟已存在的 Dictionary xlsx。"""
    cid = command_id or command_id_for_kind(kind)
    resolved = resolve_workbook_path(session, kind=kind, environ=environ)
    if not resolved.ok:
        return resolved
    path = Path(resolved.details["path"])
    launch = opener or default_opener
    try:
        launch(str(path))
    except OSError as exc:
        return results.failed(
            "open_dictionary",
            "無法開啟 %s：%s" % (path.name, exc),
            command_id=cid,
            details={"path": str(path), "filename": path.name, "kind": kind},
        )
    if kind == KIND_EXPORT:
        message = "已開啟匯出字典 %s。" % path.name
    else:
        message = "已開啟原字典 %s。" % (path.name or DICTIONARY_FILENAME)
    return results.ok(
        "open_dictionary",
        message,
        command_id=cid,
        details={"path": str(path), "filename": path.name, "kind": kind},
    )
