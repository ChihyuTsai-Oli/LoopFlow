# -*- coding: utf-8 -*-
"""Nexus Project Console。開案檢查、Type layer 同步、Space Boundary；不 Scan／不發布。"""
from __future__ import annotations

import re
from typing import Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary.loader import load_from_workfiles
from loopflow.foundation import results
from loopflow.foundation.paths import resolve_workfiles
from loopflow.foundation.version import PACKAGE_VERSION, check_schema
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
PROJECT_SCHEMA_ID = "loopflow.project"
PROJECT_ID_KEY = "lf_project_id"
SCHEMA_ID_KEY = "lf_schema_id"
SCHEMA_VERSION_KEY = "lf_schema_version"
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
CM_UNITS = frozenset(("cm", "centimeter", "centimeters"))

CONSOLE_STEPS: Tuple[dict, ...] = (
    {"id": "open_check", "title": "開案檢查", "status": "available"},
    {
        "id": "sync_type_layers",
        "title": "驗證 Dictionary／同步 Type Layers",
        "status": "available",
        "task": "NX-02",
    },
    {
        "id": "space_boundary",
        "title": "建立 Space Boundaries",
        "status": "available",
        "task": "NX-03",
    },
    {
        "id": "scan_apply_verify",
        "title": "Scan → Apply → Verify",
        "status": "not_implemented",
        "task": "NX-04",
    },
    {
        "id": "publish_registry",
        "title": "Publish Registry",
        "status": "not_implemented",
        "task": "NX-07",
    },
)


def _is_cm(unit: str) -> bool:
    return (unit or "").strip().lower() in CM_UNITS


def _copy_steps() -> Tuple[dict, ...]:
    return tuple(dict(step) for step in CONSOLE_STEPS)


def _open_check(
    session: Optional[RhinoSession],
    *,
    environ: Optional[Mapping[str, str]],
    cancel: bool,
) -> results.Result:
    if cancel:
        return results.cancelled(
            "open_check",
            "使用者取消開案檢查。",
            command_id=COMMAND_ID,
        )
    workfiles = resolve_workfiles(environ=environ)
    if not workfiles.ok:
        return workfiles
    paths = workfiles.details["paths"]
    catalog = load_from_workfiles(environ=environ)
    if not catalog.ok:
        return catalog
    if session is None:
        return results.failed(
            "rhino_session",
            "目前不在 Rhino 內，無法讀取 project_id 與文件單位。不修改檔案。",
            command_id=COMMAND_ID,
        )
    project_id = session.document_user_text(PROJECT_ID_KEY)
    if not project_id:
        return results.blocked(
            "open_check",
            "尚未有 project_id。請先建立專案身分，不從檔名猜測，也不建立檔案。",
            blocking=("missing_project_id",),
            command_id=COMMAND_ID,
        )
    if not UUID_V4_RE.match(project_id):
        return results.blocked(
            "open_check",
            "project_id 必須是小寫 UUID v4，已停止。不自動改寫。",
            blocking=("invalid_project_id",),
            command_id=COMMAND_ID,
            details={"project_id": project_id},
        )
    schema_id = session.document_user_text(SCHEMA_ID_KEY)
    raw_version = session.document_user_text(SCHEMA_VERSION_KEY)
    if not schema_id or raw_version is None:
        return results.blocked(
            "open_check",
            "文件缺少 loopflow.project 的 schema_id／schema_version。已停止，不猜測。",
            blocking=("missing_project_schema",),
            command_id=COMMAND_ID,
        )
    try:
        schema_version = int(raw_version)
    except (TypeError, ValueError):
        return results.failed(
            "check_schema",
            "未知 schema_version：%s。已停止，不猜測解析。" % raw_version,
            command_id=COMMAND_ID,
        )
    version = check_schema(schema_id, schema_version)
    if not version.ok:
        return version

    unit = session.model_unit_system()
    warnings: Sequence[str] = catalog.warnings
    extra = []
    if not _is_cm(unit):
        extra.append("文件單位為 %s，不是 cm。可繼續，但量綱尚未保證安全，建議切換為 cm。" % unit)
    if session.__class__.__name__ == "LiveSession":
        extra.append("live_adapter_unverified")
    warnings = tuple(warnings) + tuple(extra)
    payload = {
        "project_id": project_id,
        "schema_id": schema_id,
        "schema_version": schema_version,
        "model_unit": unit,
        "dictionary_filename": paths.dictionary.name,
        "type_count": catalog.details.get("type_count"),
        "exchange_exists": paths.exchange_root.exists(),
        "package_version": PACKAGE_VERSION,
        "steps": _copy_steps(),
        "executable_steps": ("open_check", "sync_type_layers", "space_boundary"),
    }
    message = "開案檢查完成。可執行 Type layer 同步與 Space Boundary。Scan／Apply／發布尚未實作。"
    if warnings:
        return results.ok_with_warnings(
            "open_check",
            message,
            tuple(warnings),
            command_id=COMMAND_ID,
            details=payload,
        )
    return results.ok("open_check", message, command_id=COMMAND_ID, details=payload)


def open_console(
    session: Optional[RhinoSession] = None,
    *,
    environ: Optional[Mapping[str, str]] = None,
    cancel: bool = False,
    step: str = "open_check",
    export_path=None,
    drafts=None,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """開案檢查並列出 Console 步驟。step 指定時才執行該步。"""
    from loopflow.features.dictionary.sync import sync_type_layers
    from loopflow.features.model_data.space import drafts_from_selection, register_space_boundaries

    def action(current: RhinoSession) -> results.Result:
        checked = _open_check(current, environ=environ, cancel=cancel)
        if not checked.ok or step in (None, "open_check"):
            return checked
        if step == "sync_type_layers":
            return sync_type_layers(
                current,
                environ=environ,
                cancel=False,
                export_path=export_path,
                guarded=False,
                command_id=command_id,
            )
        if step == "space_boundary":
            selected = drafts if drafts is not None else drafts_from_selection(current)
            return register_space_boundaries(
                current,
                selected,
                cancel=False,
                guarded=False,
                command_id=command_id,
            )
        return results.not_implemented(
            "dispatch",
            "Console 步驟尚未實作：%s" % step,
            command_id=command_id,
        )

    if session is None:
        return _open_check(None, environ=environ, cancel=cancel)
    return run_guarded(session, action, command_id=command_id)
