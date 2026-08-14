# -*- coding: utf-8 -*-
"""物件 ID 與 Type 資料化。Scan 不寫入；Apply 不寫 Space／高程／尺寸／quantity。"""
from __future__ import annotations

import re
import uuid
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary.layer_paths import (
    DATA_LAYER,
    DNA_REF_PREFIX,
    LAYER_PREFIX_3D,
    LAYER_TYPE_ID_KEY,
    is_system_layer,
    to_relative_path,
)
from loopflow.features.dictionary.loader import TypeCatalog, load_from_workfiles
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
OBJECT_ID_KEY = "lf_object_id"
TYPE_ID_KEY = "lf_type_id"
TYPE_CATEGORY_KEY = "lf_type_category"
TYPE_SEQUENCE_KEY = "lf_type_sequence"
CONSTRUCTION_KEY = "lf_construction_status"
REMARKS_KEY = "lf_remarks"
DATA_REVISION_KEY = "lf_data_revision"
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def _new_id() -> str:
    return str(uuid.uuid4())


def _in_m3d(layer: str) -> bool:
    return layer == LAYER_PREFIX_3D or layer.startswith(LAYER_PREFIX_3D + "::")


def _is_data_layer(layer: str) -> bool:
    return is_system_layer(layer) or layer == DATA_LAYER or layer.startswith(DATA_LAYER + "::")


def iter_scan_targets(
    session: RhinoSession,
    *,
    selected_only: bool = False,
) -> Tuple[str, ...]:
    targets = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        state = session.get_view_state(object_id)
        if selected_only and (state is None or not state.selected):
            continue
        if not session.is_model_object(object_id):
            continue
        name = session.object_name(object_id) or ""
        if name.startswith(DNA_REF_PREFIX):
            continue
        layer = session.object_layer(object_id) or ""
        if not _in_m3d(layer) or _is_data_layer(layer):
            continue
        targets.append(object_id)
    return tuple(targets)


def _resolve_type(session: RhinoSession, object_id: str, catalog: TypeCatalog):
    layer = session.object_layer(object_id) or ""
    type_id = session.get_layer_user_text(layer, LAYER_TYPE_ID_KEY)
    record = catalog.by_type_id(type_id) if type_id else None
    if record is None:
        record = catalog.by_layer_path(to_relative_path(layer))
    if record is None:
        return None, "unknown_type" if type_id else "unmapped_layer"
    return record, None


def _classify_ids(session: RhinoSession, targets: Sequence[str]) -> Dict[str, List[str]]:
    grouped: Dict[str, List[str]] = {}
    for object_id in targets:
        current = session.get_object_user_text(object_id, OBJECT_ID_KEY)
        if not current:
            continue
        grouped.setdefault(current, []).append(object_id)
    return grouped


def _item_issues(current: Optional[str], grouped: Mapping[str, Sequence[str]], type_issue: Optional[str]):
    issues = []
    if type_issue:
        issues.append(type_issue)
    if not current:
        issues.append("missing_object_id")
    else:
        if not UUID_V4_RE.match(current):
            issues.append("invalid_object_id")
        if len(grouped.get(current, ())) > 1:
            issues.append("duplicate_object_id")
    return tuple(issues)


def _build_items(session: RhinoSession, catalog: TypeCatalog, targets: Sequence[str]) -> Tuple[dict, ...]:
    grouped = _classify_ids(session, targets)
    items = []
    for object_id in targets:
        state = session.get_view_state(object_id)
        record, type_issue = _resolve_type(session, object_id, catalog)
        current = session.get_object_user_text(object_id, OBJECT_ID_KEY)
        issues = _item_issues(current, grouped, type_issue)
        keeper = bool(
            current
            and UUID_V4_RE.match(current)
            and grouped.get(current, [object_id])[0] == object_id
        )
        items.append(
            {
                "rhino_id": object_id,
                "layer": session.object_layer(object_id),
                "hidden": bool(state and state.hidden),
                "locked": bool(state and state.locked),
                "object_id": current,
                "type_id": None if record is None else record.type_id,
                "type_category": None if record is None else record.type_category,
                "type_sequence": None if record is None else record.type_sequence,
                "issues": issues,
                "keeper": keeper,
            }
        )
    return tuple(items)


def _blocking_codes(items: Sequence[dict]) -> Tuple[str, ...]:
    codes = []
    for item in items:
        for issue in item["issues"]:
            if issue not in codes:
                codes.append(issue)
    return tuple(codes)


def _load_catalog(catalog: Optional[TypeCatalog], environ) -> results.Result:
    if catalog is not None:
        return results.ok("load_dictionary", "已使用注入的 Type Catalog。", details={"catalog": catalog})
    loaded = load_from_workfiles(environ=environ)
    if not loaded.ok:
        return loaded
    return loaded


def scan_identity(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """全案或局部掃描物件 ID／Type。不寫入。局部不得標可發布。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "scan_identity",
                "使用者取消 Scan。",
                command_id=command_id,
            )
        loaded = _load_catalog(catalog, environ)
        if not loaded.ok:
            return loaded
        type_catalog = loaded.details["catalog"]
        targets = iter_scan_targets(current, selected_only=selected_only)
        items = _build_items(current, type_catalog, targets)
        blocking = _blocking_codes(items)
        payload = {
            "scope": "partial" if selected_only else "full",
            "publish_ready": False,
            "count": len(items),
            "items": items,
            "blocking": blocking,
            "remaining": tuple(item["rhino_id"] for item in items if item["issues"]),
        }
        if selected_only:
            message = "局部 Scan 完成，%s 個物件。不得宣告全案可發布。" % len(items)
        else:
            message = "正式 Scan 完成，%s 個物件。尚未寫入。不可發布。" % len(items)
        if blocking:
            return results.ok_with_warnings(
                "scan_identity",
                message,
                blocking,
                command_id=command_id,
                details=payload,
            )
        return results.ok("scan_identity", message, command_id=command_id, details=payload)

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def _planned_id(
    item: dict,
    mappings: Mapping[str, str],
    assigned: Dict[str, str],
) -> Optional[str]:
    rhino_id = item["rhino_id"]
    if rhino_id in mappings:
        return mappings[rhino_id]
    issues = item["issues"]
    current = item["object_id"]
    if "unknown_type" in issues or "unmapped_layer" in issues:
        return None
    if "duplicate_object_id" in issues and not item["keeper"]:
        return None
    if "invalid_object_id" in issues:
        return None
    if "missing_object_id" in issues:
        new_id = _new_id()
        assigned[rhino_id] = new_id
        return new_id
    return current


def apply_identity(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    mappings: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """確認後寫入 object_id／Type／construction／remarks／revision。不靜默換號。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "apply_identity",
                "使用者取消 Apply。",
                command_id=command_id,
            )
        loaded = _load_catalog(catalog, environ)
        if not loaded.ok:
            return loaded
        type_catalog = loaded.details["catalog"]
        mapping_table = dict(mappings or {})
        for new_id in mapping_table.values():
            if not UUID_V4_RE.match(new_id):
                return results.blocked(
                    "apply_identity",
                    "mapping 的新 ID 必須是小寫 UUID v4。",
                    blocking=("invalid_mapping",),
                    command_id=command_id,
                )
        targets = iter_scan_targets(current, selected_only=selected_only)
        items = _build_items(current, type_catalog, targets)
        assigned: Dict[str, str] = {}
        planned = []
        remaining = []
        for item in items:
            object_id = _planned_id(item, mapping_table, assigned)
            if object_id is None:
                remaining.append(item)
                continue
            planned.append((item, object_id))
        seen = {}
        for item, object_id in planned:
            if object_id in seen:
                return results.blocked(
                    "apply_identity",
                    "Apply 後仍會發生 object_id 碰撞，已停止，不靜默換號。",
                    blocking=("duplicate_object_id",),
                    command_id=command_id,
                )
            seen[object_id] = item["rhino_id"]
        id_mappings = []
        applied = []
        for item, object_id in planned:
            rhino_id = item["rhino_id"]
            record, _issue = _resolve_type(current, rhino_id, type_catalog)
            if record is None:
                remaining.append(item)
                continue
            old_id = item["object_id"]
            current.set_object_user_text(rhino_id, OBJECT_ID_KEY, object_id)
            current.set_object_user_text(rhino_id, TYPE_ID_KEY, record.type_id)
            current.set_object_user_text(rhino_id, TYPE_CATEGORY_KEY, record.type_category)
            current.set_object_user_text(rhino_id, TYPE_SEQUENCE_KEY, record.type_sequence)
            if not current.get_object_user_text(rhino_id, CONSTRUCTION_KEY) and record.construction_default:
                current.set_object_user_text(rhino_id, CONSTRUCTION_KEY, record.construction_default)
            if not current.get_object_user_text(rhino_id, REMARKS_KEY) and record.remarks_default:
                current.set_object_user_text(rhino_id, REMARKS_KEY, record.remarks_default)
            if not current.get_object_user_text(rhino_id, DATA_REVISION_KEY):
                current.set_object_user_text(rhino_id, DATA_REVISION_KEY, "0")
            applied.append(rhino_id)
            if old_id and old_id != object_id:
                id_mappings.append({"object_id": rhino_id, "old_id": old_id, "new_id": object_id})
        payload = {
            "publish_ready": False,
            "applied": tuple(applied),
            "remaining": tuple(item["rhino_id"] for item in remaining),
            "id_mappings": tuple(id_mappings),
            "scope": "partial" if selected_only else "full",
        }
        if not applied and remaining:
            return results.blocked(
                "apply_identity",
                "沒有可寫入的物件。剩餘 %s 項需 mapping 或修正 Type。" % len(remaining),
                blocking=_blocking_codes(remaining) or ("nothing_to_apply",),
                command_id=command_id,
                details=payload,
            )
        message = "已 Apply %s 個物件的 ID／Type。未寫 Space／高程／尺寸。不可發布。" % len(applied)
        if remaining:
            return results.ok_with_warnings(
                "apply_identity",
                message + " 剩餘 %s 項。" % len(remaining),
                ("remaining_identity_work",),
                command_id=command_id,
                details=payload,
            )
        return results.ok("apply_identity", message, command_id=command_id, details=payload)

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def verify_identity(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """Apply 後再 Scan。NX-04 仍不得宣告可發布。"""
    scanned = scan_identity(
        session,
        catalog=catalog,
        environ=environ,
        selected_only=selected_only,
        cancel=cancel,
        guarded=guarded,
        command_id=command_id,
    )
    if not scanned.ok or scanned.status == "cancelled":
        return scanned
    details = dict(scanned.details)
    details["publish_ready"] = False
    remaining = details.get("remaining") or ()
    if remaining:
        return results.ok_with_warnings(
            "verify_identity",
            "Verify 仍有 %s 項未完成。不可發布。" % len(remaining),
            scanned.warnings or ("remaining_identity_work",),
            command_id=command_id,
            details=details,
        )
    return results.ok(
        "verify_identity",
        "Identity Verify 通過。Space／高程／尺寸尚未資料化，不可發布。",
        command_id=command_id,
        details=details,
    )


def rollback_identity(
    session: RhinoSession,
    mappings: Sequence[Mapping[str, str]],
    *,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """依 mapping 把 object_id 還原成 old_id。不猜其他欄位。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "rollback_identity",
                "使用者取消 rollback。",
                command_id=command_id,
            )
        if not mappings:
            return results.blocked(
                "rollback_identity",
                "沒有 ID mapping 可還原。",
                blocking=("missing_mapping",),
                command_id=command_id,
            )
        restored = []
        for item in mappings:
            rhino_id = item["object_id"]
            old_id = item["old_id"]
            new_id = item["new_id"]
            current_id = current.get_object_user_text(rhino_id, OBJECT_ID_KEY)
            if current_id != new_id:
                continue
            current.set_object_user_text(rhino_id, OBJECT_ID_KEY, old_id)
            restored.append(rhino_id)
        return results.ok(
            "rollback_identity",
            "已還原 %s 個 object_id。" % len(restored),
            command_id=command_id,
            details={"restored": tuple(restored), "publish_ready": False},
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)
