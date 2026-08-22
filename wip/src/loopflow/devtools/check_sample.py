# -*- coding: utf-8 -*-
"""G01：檢查目前開啟的 .3dm 是否為乾淨 2.0 範例資料。只讀、不寫入。

不是產品指令，也不做 1.x 轉 2.0。責任見 `wip/docs/開發任務與路徑.md` LF-G01。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from loopflow.devtools.migrate_block_display_keys import (
    FRAME_LEGACY_KEYS,
    FRAME_STRAY_KEYS,
    load_template_migrations,
)
from loopflow.features.dictionary.loader import load_from_path
from loopflow.features.sheet.keys import (
    DRAWING_NAME_KEY,
    DRAWING_NO_KEY,
    SCALE_KEY,
    SHEET_ID_KEY,
)
from loopflow.features.tagger.keys import (
    LOCK_LEGACY_KEY,
    LOCK_STATE_PREV_KEY,
    is_legacy_lock_key,
)
from loopflow.foundation import results
from loopflow.foundation.paths import (
    CONFIG_DIR_NAME,
    DICTIONARY_FILENAME,
    REGISTRY_FILENAME,
    resolve_project_folder,
)
from loopflow.foundation.project_config import (
    CONFIG_FILENAME,
    LEGACY_DOCUMENT_KEYS,
    PROJECT_ID_FIELD,
    PROJECT_SCHEMA_ID,
    SCHEMA_ID_FIELD,
    SCHEMA_VERSION_FIELD,
    config_path_for_paths,
)
from loopflow.foundation.usertext import LEGACY_KEYS, STALE_OBJECT_KEYS
from loopflow.foundation.version import check_schema
from loopflow.platform.rhino.session import RhinoSession

COMMAND_ID = "LF_G01_Check_Sample"
STAGE = "check_sample"
MAX_WHERE = 8
ALLOWED_DOCUMENT_KEYS = frozenset(("lf_title_frame_blocks",))
ALLOWED_DOCUMENT_PREFIXES = ("lf_sheet.", "lf_sheet_naming.")
# 2.0 圖塊／圖框／抽出／View 合法 lf_*；其餘 lf_object_id 這類 1.x 名字另列禁止。
ALLOWED_LF_PREFIXES = (
    "lf_00_lock_state",
    "lf_tag_id",
    "lf_template_id",
    "lf_template_version",
    "lf_binding_mode",
    "lf_source_object_id",
    "lf_source_object_ids",
    "lf_source_block_name",
    "lf_target_view_id",
    "lf_target_sheet_id",
    "lf_target_layout",
    "lf_host_sheet_id",
    "lf_last_synced_revision",
    "lf_health_state",
    "lf_sheet_id",
    "lf_drawing_no",
    "lf_drawing_name",
    "lf_scale",
    "lf_sheet_code",
    "lf_view_id",
    "lf_clipping_plane_id",
    "lf_view_transform",
    "lf_drawing_id",
    "lf_provenance_state",
    "lf_catalog_id",
    "lf_elevation_basis",
    "lf_elevation_display",
    "lf_type_category",
    "lf_type_sequence",
    "lf_type_display_name",
    "lf_remarks_manual",
    "lf_type_id",
    "lf_construction_default",
)


@dataclass(frozen=True)
class Finding:
    severity: str  # block | warn
    code: str
    message: str
    where: str = ""


def _text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _object_legacy_keys() -> Tuple[str, ...]:
    found = []
    seen = set()
    for aliases in LEGACY_KEYS.values():
        for key in aliases:
            if key in seen:
                continue
            seen.add(key)
            found.append(key)
    return tuple(found)


def _tag_legacy_keys() -> Tuple[str, ...]:
    mapping, _lock = load_template_migrations()
    found = []
    seen = set()
    for pairs in mapping.values():
        for old_key, _new in pairs:
            if old_key in seen:
                continue
            seen.add(old_key)
            found.append(old_key)
    return tuple(found)


def _document_keys(session: RhinoSession) -> Tuple[str, ...]:
    getter = getattr(session, "document_user_text_keys", None)
    if callable(getter):
        return tuple(str(item) for item in (getter() or ()) if str(item).strip())
    listed = []
    try:
        keys = session._rs.GetDocumentUserText()  # type: ignore[attr-defined]
        if keys:
            listed = [str(item) for item in keys if str(item).strip()]
    except Exception:
        listed = []
    if listed:
        return tuple(listed)
    probed = []
    for key, _field in LEGACY_DOCUMENT_KEYS:
        if _text(session.document_user_text(key)):
            probed.append(key)
    return tuple(probed)


def _where_object(session: RhinoSession, object_id: str) -> str:
    layer = ""
    getter = getattr(session, "object_layer", None)
    if callable(getter):
        layer = str(getter(object_id) or "").strip()
    block = ""
    if getattr(session, "is_block_instance", None) and session.is_block_instance(object_id):
        block = str(session.block_definition_name(object_id) or "").strip()
    parts = [p for p in (block, layer, object_id[:8]) if p]
    return "／".join(parts) if parts else object_id[:8]


def _add(findings: List[Finding], seen: set, finding: Finding) -> None:
    key = (finding.severity, finding.code, finding.message, finding.where)
    if key in seen:
        return
    seen.add(key)
    findings.append(finding)


def _group_lines(findings: Sequence[Finding], severity: str) -> List[str]:
    groups = {}
    for item in findings:
        if item.severity != severity:
            continue
        groups.setdefault((item.code, item.message), []).append(item.where)
    lines = []
    label = "阻擋" if severity == "block" else "警告"
    for (_code, message), wheres in groups.items():
        places = [w for w in wheres if w]
        extra = ""
        if places:
            show = places[:MAX_WHERE]
            extra = "（%s）" % "、".join(show)
            if len(places) > MAX_WHERE:
                extra += " 還有 %s 處" % (len(places) - MAX_WHERE)
        lines.append("[%s] %s%s" % (label, message, extra))
    return lines


def _scan_document(session: RhinoSession, findings: List[Finding], seen: set) -> None:
    allowed_legacy = {key for key, _field in LEGACY_DOCUMENT_KEYS}
    for key in _document_keys(session):
        value = _text(session.document_user_text(key))
        if key in allowed_legacy and value:
            _add(
                findings,
                seen,
                Finding(
                    "block",
                    "legacy_document_env",
                    "文件仍有環境設定 %s。應只在 %s\\%s，不寫進 .3dm。"
                    % (key, CONFIG_DIR_NAME, CONFIG_FILENAME),
                    "文件",
                ),
            )
            continue
        if key in ALLOWED_DOCUMENT_KEYS or key.startswith(ALLOWED_DOCUMENT_PREFIXES):
            continue
        if value:
            _add(
                findings,
                seen,
                Finding(
                    "warn",
                    "unexpected_document_key",
                    "文件有未預期的 UserText：%s。" % key,
                    "文件",
                ),
            )


def _scan_project_files(session: RhinoSession, findings: List[Finding], seen: set) -> Optional[Path]:
    resolved = resolve_project_folder(session)
    if not resolved.ok:
        _add(
            findings,
            seen,
            Finding("block", resolved.status, resolved.message, "檔案"),
        )
        return None
    paths = resolved.details["paths"]
    config_path = config_path_for_paths(paths)
    values = {}
    if config_path.is_file():
        try:
            payload = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _add(
                findings,
                seen,
                Finding(
                    "block",
                    "bad_project_config",
                    "%s 無法解析：%s。" % (CONFIG_FILENAME, exc),
                    str(config_path),
                ),
            )
            payload = None
        if isinstance(payload, dict):
            values = payload
        elif payload is not None:
            _add(
                findings,
                seen,
                Finding(
                    "block",
                    "bad_project_config",
                    "%s 內容不是設定物件。" % CONFIG_FILENAME,
                    str(config_path),
                ),
            )
    else:
        _add(
            findings,
            seen,
            Finding(
                "warn",
                "missing_project_config",
                "沒有 %s。上傳前請先跑 Nexus 選單 2 寫入專案名稱與 schema。"
                % (CONFIG_DIR_NAME + "\\" + CONFIG_FILENAME),
                str(paths.config_dir),
            ),
        )

    schema_id = str(values.get(SCHEMA_ID_FIELD) or "").strip()
    version_raw = values.get(SCHEMA_VERSION_FIELD)
    if schema_id or version_raw not in (None, ""):
        try:
            version = int(version_raw)
        except (TypeError, ValueError):
            _add(
                findings,
                seen,
                Finding(
                    "block",
                    "bad_schema",
                    "專案 schema_version 無法解析：%s。" % version_raw,
                    str(config_path),
                ),
            )
        else:
            checked = check_schema(schema_id or PROJECT_SCHEMA_ID, version)
            if not checked.ok:
                _add(
                    findings,
                    seen,
                    Finding("block", "bad_schema", checked.message, str(config_path)),
                )
            elif schema_id and schema_id != PROJECT_SCHEMA_ID:
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "bad_schema",
                        "專案 schema_id 應為 %s，實際為 %s。" % (PROJECT_SCHEMA_ID, schema_id),
                        str(config_path),
                    ),
                )

    filename = str(values.get("dictionary_filename") or "").strip() or DICTIONARY_FILENAME
    dictionary = Path(paths.root) / filename
    if filename.lower().endswith("_export.xlsx"):
        _add(
            findings,
            seen,
            Finding(
                "block",
                "export_as_dictionary",
                "不能把匯出檔當正式 Dictionary：%s。" % filename,
                str(dictionary),
            ),
        )
    elif not dictionary.is_file():
        _add(
            findings,
            seen,
            Finding(
                "warn",
                "missing_dictionary",
                "找不到 Dictionary %s。請放在 .3dm 同一層。" % filename,
                str(paths.root),
            ),
        )
    else:
        loaded = load_from_path(dictionary)
        if not loaded.ok:
            _add(
                findings,
                seen,
                Finding("block", "bad_dictionary", loaded.message, str(dictionary)),
            )

    project_id = str(values.get(PROJECT_ID_FIELD) or values.get("layer_prefix") or "").strip()
    if project_id:
        registry = Path(paths.config_dir) / project_id / REGISTRY_FILENAME
        if not registry.is_file():
            _add(
                findings,
                seen,
                Finding(
                    "warn",
                    "missing_registry",
                    "尚未發布 Registry。範例若要示範發布結果，請先跑發布。",
                    str(Path(paths.config_dir) / project_id),
                ),
            )
    old_exchange = Path(paths.root) / "exchange"
    if old_exchange.is_dir():
        _add(
            findings,
            seen,
            Finding(
                "warn",
                "legacy_exchange_folder",
                "工作資料夾仍有舊的 exchange\\。2.0 只用 %s。" % CONFIG_DIR_NAME,
                str(old_exchange),
            ),
        )
    return Path(paths.document)


def _is_allowed_lf_key(key: str) -> bool:
    if key in ALLOWED_LF_PREFIXES:
        return True
    return any(key == prefix or key.startswith(prefix + ".") for prefix in ALLOWED_LF_PREFIXES)


def _scan_objects(session: RhinoSession, findings: List[Finding], seen: set) -> None:
    object_legacy = set(_object_legacy_keys())
    tag_legacy = set(_tag_legacy_keys())
    stale = set(STALE_OBJECT_KEYS)
    frame_legacy = set(FRAME_LEGACY_KEYS) | set(FRAME_STRAY_KEYS)
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        where = _where_object(session, object_id)
        keys = []
        getter = getattr(session, "object_user_text_keys", None)
        if callable(getter):
            keys = [str(item) for item in (getter(object_id) or ()) if str(item).strip()]
        if LOCK_LEGACY_KEY not in keys and session.get_object_user_text(object_id, LOCK_LEGACY_KEY) is not None:
            keys.append(LOCK_LEGACY_KEY)
        for key in keys:
            if key in stale:
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "stale_dimension",
                        "物件殘留尺寸／數量欄 %s。2.0 不寫這些欄。" % key,
                        where,
                    ),
                )
                continue
            if key in object_legacy:
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "legacy_object_key",
                        "物件仍有 1.x／過渡 UserText %s。" % key,
                        where,
                    ),
                )
                continue
            if key in tag_legacy or key in frame_legacy:
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "legacy_tag_key",
                        "圖塊仍有舊顯示欄 %s。應改為 lf_*（可跑 D08 清除實例舊欄）。" % key,
                        where,
                    ),
                )
                continue
            if is_legacy_lock_key(key) or key == LOCK_STATE_PREV_KEY:
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "legacy_lock_key",
                        "鎖定欄仍是舊名字 %s。應為 lf_00_lock_state。" % key,
                        where,
                    ),
                )
                continue
            if key.startswith("_CB.") or key.startswith("Q_0"):
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "forbidden_quantity_or_cb",
                        "物件有禁止欄 %s。2.0 不算尺寸／數量，也不處理 _CB.*。" % key,
                        where,
                    ),
                )
                continue
            if key.startswith("lf_") and not _is_allowed_lf_key(key):
                _add(
                    findings,
                    seen,
                    Finding(
                        "warn",
                        "unknown_lf_key",
                        "未列入 2.0 契約的 lf_ 欄：%s。" % key,
                        where,
                    ),
                )
                continue
            if key.startswith("attr_"):
                _add(
                    findings,
                    seen,
                    Finding(
                        "block",
                        "legacy_tag_key",
                        "圖塊仍有舊顯示欄 %s。" % key,
                        where,
                    ),
                )


def _scan_layers(session: RhinoSession, findings: List[Finding], seen: set) -> None:
    paths_fn = getattr(session, "layer_paths", None)
    if not callable(paths_fn):
        return
    allowed = frozenset(("lf_type_id", "lf_construction_default"))
    for path in paths_fn() or ():
        layer = str(path or "")
        if not layer:
            continue
        for key in ("lf_type_id", "lf_construction_default", "lf_object_id", "lf_space_id"):
            value = _text(session.get_layer_user_text(layer, key))
            if not value:
                continue
            if key in allowed:
                continue
            _add(
                findings,
                seen,
                Finding(
                    "warn",
                    "legacy_layer_key",
                    "圖層有未預期 UserText %s。" % key,
                    layer,
                ),
            )


def format_report(findings: Sequence[Finding], document_path: Optional[Path]) -> str:
    blocks = [item for item in findings if item.severity == "block"]
    warns = [item for item in findings if item.severity == "warn"]
    lines = [
        "G01 範例檔檢查（只讀，沒有改檔）",
        "檔案：%s" % (document_path if document_path else "（尚未存成 .3dm）"),
        "阻擋 %s、警告 %s" % (len(_group_lines(blocks, "block")), len(_group_lines(warns, "warn"))),
        "",
    ]
    if not findings:
        lines.append("這份檔看起來是乾淨的 2.0 資料，可以當上傳範例。")
        return "\n".join(lines)
    lines.extend(_group_lines(blocks, "block"))
    lines.extend(_group_lines(warns, "warn"))
    if blocks:
        lines.append("")
        lines.append("有阻擋項就還不能當正式範例上傳。請在副本上改，不要改正式專案。")
    return "\n".join(lines)


def check_sample(session: Optional[RhinoSession]) -> results.Result:
    """掃描目前文件與同層 Dictionary／專案設定。不寫 UserText、不建檔。"""
    if session is None:
        return results.failed(STAGE, "沒有 Rhino session。", command_id=COMMAND_ID)
    findings: List[Finding] = []
    seen = set()
    document_path = _scan_project_files(session, findings, seen)
    _scan_document(session, findings, seen)
    _scan_objects(session, findings, seen)
    _scan_layers(session, findings, seen)
    report = format_report(findings, document_path)
    blocks = tuple(item.code for item in findings if item.severity == "block")
    warns = tuple(item.code for item in findings if item.severity == "warn")
    details = {
        "findings": [
            {
                "severity": item.severity,
                "code": item.code,
                "message": item.message,
                "where": item.where,
            }
            for item in findings
        ],
        "report": report,
        "document_path": str(document_path) if document_path else None,
    }
    if blocks:
        return results.blocked(
            STAGE,
            report,
            blocking=tuple(dict.fromkeys(blocks)),
            command_id=COMMAND_ID,
            details=details,
        )
    if warns:
        return results.ok_with_warnings(
            STAGE,
            report,
            tuple(dict.fromkeys(warns)),
            command_id=COMMAND_ID,
            details=details,
        )
    return results.ok(STAGE, report, command_id=COMMAND_ID, details=details)
