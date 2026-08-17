# -*- coding: utf-8 -*-
"""Nexus Project Console。開案檢查、同步 Type Layers、高程／空間框、寫入／檢核 Metadata、匯出字典與發布。"""
from __future__ import annotations

import re
from typing import Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary.loader import load_from_workfiles
from loopflow.foundation import results
from loopflow.foundation.paths import dictionary_filename_from_session, resolve_workfiles
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
        "title": "從字典同步 Type Layers",
        "status": "available",
        "task": "NX-02",
    },
    {
        "id": "level_boundary",
        "title": "登記高程框（封閉曲線）",
        "status": "available",
        "task": "NX-03",
    },
    {
        "id": "space_boundary",
        "title": "登記空間框（封閉曲線，須在高程框內）",
        "status": "available",
        "task": "NX-03",
    },
    {
        "id": "scan_apply_verify",
        "title": "寫入／檢核模型 Metadata",
        "status": "available",
        "task": "NX-04～05",
    },
    {
        "id": "export_dictionary",
        "title": "匯出 Type Layers 為字典",
        "status": "available",
        "task": "NX-02",
    },
    {
        "id": "publish_registry",
        "title": "發布串接資料",
        "status": "available",
        "task": "NX-07",
    },
)


def _is_cm(unit: str) -> bool:
    return (unit or "").strip().lower() in CM_UNITS


def _copy_steps() -> Tuple[dict, ...]:
    return tuple(dict(step) for step in CONSOLE_STEPS)


def compose_scan_apply_message(mode: str, identity, placement) -> str:
    """把 ID／空間兩句合併成一句，避免「未寫／已寫」互相打架。"""
    details = identity.details or {}
    count = details.get("count")
    if count is None:
        count = len(details.get("applied") or details.get("items") or ())
    ext = len((placement.details or {}).get("ext") or ())
    if mode == "scan":
        return "Scan 完成，%s 個物件。尚未寫入。空間 %s 個 EXT。不可發布。" % (count, ext)
    written = []
    if details.get("applied"):
        written.append("ID／Type")
    if (placement.details or {}).get("applied"):
        written.append("空間／高程")
    n_applied = len(details.get("applied") or ())
    if written:
        message = "已寫入 %s 個物件的 %s。" % (n_applied, "、".join(written))
    else:
        message = "沒有可寫入的欄位。"
    return message + " 不可發布。"


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
    filename = dictionary_filename_from_session(session) if session is not None else None
    catalog = load_from_workfiles(environ=environ, dictionary_filename=filename, session=session)
    extra_warnings: Sequence[str] = ()
    catalog_warnings: Sequence[str] = ()
    type_count = None
    if not catalog.ok and catalog.stage == "resolve_dictionary":
        extra_warnings = (
            "找不到 Dictionary 檔案 %s。請用選單 2 指定工作檔資料夾內的 .xlsx。"
            % ((catalog.details or {}).get("filename") or filename or "LoopFlow_Dictionary.xlsx"),
        )
    elif not catalog.ok:
        return catalog
    else:
        catalog_warnings = catalog.warnings
        type_count = catalog.details.get("type_count")
    paths_result = resolve_workfiles(environ=environ, dictionary_filename=filename)
    if not paths_result.ok:
        return paths_result
    paths = paths_result.details["paths"]
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
    warnings: Sequence[str] = catalog_warnings
    extra = []
    if not _is_cm(unit):
        extra.append("文件單位為 %s，不是 cm。可繼續，但量綱尚未保證安全，建議切換為 cm。" % unit)
    if session.__class__.__name__ == "LiveSession":
        from loopflow.platform.rhino.live import LIVE_VERIFIED_IN_RHINO

        if not LIVE_VERIFIED_IN_RHINO:
            extra.append("live_adapter_unverified")
    warnings = tuple(catalog_warnings) + tuple(extra) + tuple(extra_warnings)
    payload = {
        "project_id": project_id,
        "schema_id": schema_id,
        "schema_version": schema_version,
        "model_unit": unit,
        "dictionary_filename": paths.dictionary.name,
        "type_count": type_count,
        "exchange_exists": paths.exchange_root.exists(),
        "package_version": PACKAGE_VERSION,
        "steps": _copy_steps(),
        "executable_steps": (
            "open_check",
            "sync_type_layers",
            "level_boundary",
            "space_boundary",
            "scan_apply_verify",
            "export_dictionary",
            "publish_registry",
        ),
    }
    message = "開案檢查完成。可執行 Type Layers、高程／空間框、寫入／檢核 Metadata、匯出字典與發布。"
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
    mappings=None,
    selected_only: bool = False,
    identity_action: str = "scan",
    command_id: str = COMMAND_ID,
    layer_prefix=None,
    ask_prefix=None,
    pick_objects=None,
    ask_text=None,
    ask_kind=None,
    object_ids=None,
    space_name=None,
    datum=None,
    level_kind=None,
    isolate: bool = True,
    show_message=None,
    ask_space=None,
    ask_dictionary=None,
) -> results.Result:
    """開案檢查並列出 Console 步驟。step 指定時才執行該步。"""
    from loopflow.features.dictionary.sync import export_dictionary, sync_type_layers
    from loopflow.features.model_data.identity import (
        apply_identity,
        rollback_identity,
        scan_identity,
    )
    from loopflow.features.model_data.placement import (
        apply_placement,
        has_registered_boundaries,
        scan_placement,
    )
    from loopflow.features.model_data.space import (
        drafts_from_selection,
        register_level_boundaries_interactive,
        register_space_boundaries,
        register_space_boundaries_interactive,
    )
    from loopflow.features.model_data.verify import select_only, verify_model_data

    def action(current: RhinoSession) -> results.Result:
        checked = _open_check(
            current,
            environ=environ,
            cancel=cancel,
        )
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
                layer_prefix=layer_prefix,
                ask_prefix=ask_prefix,
                ask_dictionary=ask_dictionary,
            )
        if step == "export_dictionary":
            return export_dictionary(
                current,
                environ=environ,
                export_path=export_path,
                guarded=False,
                command_id=command_id,
                show_message=show_message,
            )
        if step == "publish_registry":
            from loopflow.features.registry.handoff import publish_from_session

            return publish_from_session(
                current,
                environ=environ,
                selected_only=selected_only,
                cancel=False,
                guarded=False,
                command_id=command_id,
                show_message=show_message,
            )
        if step == "level_boundary":
            return register_level_boundaries_interactive(
                current,
                kind=level_kind,
                object_ids=object_ids,
                datum=datum,
                ask_kind=ask_kind,
                pick_objects=pick_objects,
                ask_text=ask_text,
                isolate=isolate,
                guarded=False,
                command_id=command_id,
            )
        if step == "space_boundary":
            if drafts is not None:
                return register_space_boundaries(
                    current,
                    drafts,
                    cancel=False,
                    guarded=False,
                    command_id=command_id,
                )
            return register_space_boundaries_interactive(
                current,
                object_ids=object_ids,
                space_name=space_name,
                pick_objects=pick_objects,
                ask_text=ask_text,
                isolate=isolate,
                guarded=False,
                command_id=command_id,
            )
        if step in ("scan_apply_verify", "scan_identity", "apply_identity", "verify_identity", "rollback_identity"):
            kwargs = {
                "environ": environ,
                "selected_only": selected_only,
                "cancel": False,
                "guarded": False,
                "command_id": command_id,
            }

            def _merge(stage, mode, *named):
                primary = named[0][1]
                details = dict(primary.details)
                warnings = list(primary.warnings)
                by_name = {key: result for key, result in named}
                for key, result in named[1:]:
                    details[key] = result.details
                    warnings.extend(result.warnings)
                    if result.blocking:
                        warnings.extend(result.blocking)
                details["publish_ready"] = False
                message = compose_scan_apply_message(
                    mode,
                    by_name["identity"],
                    by_name["placement"],
                )
                unique = tuple(dict.fromkeys(warnings))
                if unique:
                    return results.ok_with_warnings(
                        stage,
                        message,
                        unique,
                        command_id=command_id,
                        details=details,
                    )
                return results.ok(stage, message, command_id=command_id, details=details)

            def scan_all():
                identity = scan_identity(current, **kwargs)
                if not identity.ok:
                    return identity
                placement = scan_placement(current, **kwargs)
                if not placement.ok:
                    return placement
                return _merge(
                    "scan_identity",
                    "scan",
                    ("identity", identity),
                    ("placement", placement),
                )

            def apply_all():
                if not has_registered_boundaries(current):
                    return results.blocked(
                        "apply_identity",
                        "請先登記高程框（3）與空間框（4）。",
                        blocking=("missing_level_or_space_boundary",),
                        command_id=command_id,
                        details={"publish_ready": False},
                    )
                identity = apply_identity(current, mappings=mappings, **kwargs)
                if not identity.ok:
                    return identity
                placement = apply_placement(current, ask_space=ask_space, **kwargs)
                return _merge(
                    "apply_identity",
                    "apply",
                    ("identity", identity),
                    ("placement", placement),
                )

            action_name = identity_action if step == "scan_apply_verify" else step
            if action_name in ("scan", "scan_identity", "scan_apply_verify"):
                if step == "scan_apply_verify":
                    return scan_all()
                return scan_identity(current, **kwargs)
            if action_name == "apply_identity" or action_name == "apply":
                if step == "scan_apply_verify":
                    return apply_all()
                return apply_identity(current, mappings=mappings, **kwargs)
            if action_name == "verify_identity" or action_name == "verify":
                return verify_model_data(
                    current,
                    environ=environ,
                    selected_only=selected_only,
                    guarded=False,
                    command_id=command_id,
                    show_popup=False,
                )
            if action_name == "rollback_identity" or action_name == "rollback":
                return rollback_identity(
                    current,
                    mappings or (),
                    cancel=False,
                    guarded=False,
                    command_id=command_id,
                )
            return results.not_implemented(
                "dispatch",
                "未知 Identity 動作：%s" % action_name,
                command_id=command_id,
            )
        return results.not_implemented(
            "dispatch",
            "Console 步驟尚未實作：%s" % step,
            command_id=command_id,
        )

    if session is None:
        return _open_check(None, environ=environ, cancel=cancel)
    outcome = run_guarded(session, action, command_id=command_id)
    if identity_action in ("verify", "verify_identity") and step in (
        "scan_apply_verify",
        "verify_identity",
    ):
        from loopflow.features.model_data.verify import format_verify_popup

        popup = format_verify_popup(outcome)
        if callable(show_message):
            show_message(popup)
        elif outcome.ok:
            from loopflow.platform.rhino.prompts import show_message as live_popup

            live_popup(popup)
    mismatch_ids = (outcome.details or {}).get("mismatch_object_ids")
    if mismatch_ids:
        select_only(session, mismatch_ids)
    return outcome
