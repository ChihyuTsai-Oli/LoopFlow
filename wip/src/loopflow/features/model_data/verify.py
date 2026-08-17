# -*- coding: utf-8 -*-
"""Verify：在記憶體算出 Apply 會寫的 UserText，與物件現值比對。不寫入。"""
from __future__ import annotations

from typing import Callable, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.model_data.identity import (
    _load_catalog,
    expected_data_revision,
    iter_scan_targets,
    scan_identity,
)
from loopflow.features.model_data.placement import (
    ALLOWED_BASES,
    _format_elev,
    scan_placement,
)
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    CONSTRUCTION_KEY,
    DATA_REVISION_KEY,
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ELEVATION_VALUE_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    SPACE_DISPLAY_KEY,
    SPACE_ID_KEY,
    STALE_OBJECT_KEYS,
    TYPE_CATEGORY_KEY,
    TYPE_ID_KEY,
    TYPE_SEQUENCE_KEY,
    read_text,
)
from loopflow.platform.rhino.session import RhinoSession, run_guarded
from loopflow.platform.rhino.state import ObjectViewState

COMMAND_ID = "LF_Nexus"
FIELD_LABELS = {
    OBJECT_ID_KEY: "UUID",
    TYPE_ID_KEY: "ID編號",
    TYPE_CATEGORY_KEY: "類型類別",
    TYPE_SEQUENCE_KEY: "類型序號",
    CONSTRUCTION_KEY: "建構狀態",
    REMARKS_KEY: "備註",
    DATA_REVISION_KEY: "資料版次",
    SPACE_ID_KEY: "空間ID",
    SPACE_DISPLAY_KEY: "空間名稱",
    ELEVATION_BASIS_KEY: "高程基準",
    ELEVATION_VALUE_KEY: "高程計算",
    ELEVATION_DISPLAY_KEY: "高程顯示",
}
ISSUE_LABELS = {
    "missing_object_id": "尚未寫入 UUID",
    "invalid_object_id": "UUID 格式不正確",
    "duplicate_object_id": "UUID 重複",
    "unknown_type": "未知 Type",
    "unmapped_layer": "圖層未對應 Dictionary",
    "ambiguous_space": "空間命中不唯一",
    "bc_on_non_block": "高程基準 BC 但不是圖塊",
    "invalid_elevation_basis": "高程基準不合法",
    "bbox_unavailable": "取不到範圍",
    "stale_dimension": "殘留尺寸／數量欄",
}
HARD_PLACEMENT_ISSUES = (
    "ambiguous_space",
    "bc_on_non_block",
    "invalid_elevation_basis",
    "bbox_unavailable",
)
MAX_POPUP_LINES = 12
APPLY_REMINDER = "請執行選單 5 寫入模型 Metadata，把正確資料寫回。"


def _text(value) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()


def _label(object_id: str, session: RhinoSession) -> str:
    layer = session.object_layer(object_id) or ""
    short = layer.split("::")[-1] if layer else object_id
    return short or object_id


def _identity_expected(item: dict, session: RhinoSession, catalog, revision: str) -> dict:
    rhino_id = item["rhino_id"]
    expected = {}
    type_id = item.get("type_id")
    if not type_id:
        return expected
    record = catalog.by_type_id(type_id) if catalog is not None else None
    expected[TYPE_ID_KEY] = type_id
    expected[TYPE_CATEGORY_KEY] = item.get("type_category") or ""
    expected[TYPE_SEQUENCE_KEY] = item.get("type_sequence") or ""
    expected[CONSTRUCTION_KEY] = (
        read_text(session, rhino_id, CONSTRUCTION_KEY)
        or (record.construction_default if record else "")
        or ""
    )
    expected[REMARKS_KEY] = (
        read_text(session, rhino_id, REMARKS_KEY)
        or (record.remarks_default if record else "")
        or ""
    )
    expected[DATA_REVISION_KEY] = revision
    current_id = read_text(session, rhino_id, OBJECT_ID_KEY) or ""
    expected[OBJECT_ID_KEY] = current_id
    return expected


def _placement_expected(item: dict) -> dict:
    expected = {
        SPACE_ID_KEY: item.get("space_id") or "",
        SPACE_DISPLAY_KEY: item.get("space_display") or "",
    }
    issues = tuple(item.get("issues") or ())
    if any(issue in HARD_PLACEMENT_ISSUES for issue in issues):
        return expected
    if item.get("elevation_value") is not None and item.get("elevation_basis") in ALLOWED_BASES:
        formatted = _format_elev(item["elevation_value"])
        expected[ELEVATION_BASIS_KEY] = item["elevation_basis"]
        expected[ELEVATION_VALUE_KEY] = formatted
        expected[ELEVATION_DISPLAY_KEY] = formatted
    return expected


def _field_mismatches(session: RhinoSession, object_id: str, expected: Mapping[str, str]) -> List[str]:
    notes = []
    for key, wanted in expected.items():
        actual = _text(read_text(session, object_id, key))
        want = _text(wanted)
        if actual == want:
            continue
        label = FIELD_LABELS.get(key, key)
        if not actual:
            notes.append("%s 尚未寫入（應為 %s）" % (label, want or "（空）"))
        elif not want:
            notes.append("%s 現值「%s」不應存在" % (label, actual))
        else:
            notes.append("%s「%s」應為「%s」" % (label, actual, want))
    return notes


def _stale_notes(session: RhinoSession, object_id: str) -> List[str]:
    leftover = [
        key for key in STALE_OBJECT_KEYS if session.get_object_user_text(object_id, key) not in (None, "")
    ]
    if leftover:
        return [ISSUE_LABELS["stale_dimension"]]
    return []


def compare_apply_usertext(
    session: RhinoSession,
    *,
    catalog=None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """算出 Apply 會寫的欄位，與現有 UserText 比對。不寫入。"""
    identity = scan_identity(
        session,
        catalog=catalog,
        environ=environ,
        selected_only=selected_only,
        guarded=False,
        command_id=command_id,
    )
    if not identity.ok:
        return identity
    placement = scan_placement(
        session,
        catalog=catalog,
        environ=environ,
        selected_only=selected_only,
        guarded=False,
        command_id=command_id,
    )
    if not placement.ok:
        return placement
    loaded = _load_catalog(catalog, environ, session)
    if not loaded.ok:
        return loaded
    type_catalog = loaded.details["catalog"]
    revision = expected_data_revision(session, environ)

    identity_by_id = {item["rhino_id"]: item for item in identity.details.get("items") or ()}
    placement_by_id = {item["rhino_id"]: item for item in placement.details.get("items") or ()}
    mismatches = []
    for object_id in iter_scan_targets(session, selected_only=selected_only):
        ident = identity_by_id.get(object_id) or {}
        place = placement_by_id.get(object_id) or {}
        notes = []
        for issue in ident.get("issues") or ():
            notes.append(ISSUE_LABELS.get(issue, issue))
        for issue in place.get("issues") or ():
            if issue == "migration_th_bh":
                continue
            notes.append(ISSUE_LABELS.get(issue, issue))
        expected = {}
        expected.update(_identity_expected(ident, session, type_catalog, revision))
        expected.update(_placement_expected(place))
        notes.extend(_field_mismatches(session, object_id, expected))
        notes.extend(_stale_notes(session, object_id))
        unique = tuple(dict.fromkeys(notes))
        if unique:
            mismatches.append(
                {
                    "rhino_id": object_id,
                    "label": _label(object_id, session),
                    "notes": unique,
                }
            )

    count = len(identity.details.get("items") or ())
    mismatch_ids = tuple(item["rhino_id"] for item in mismatches)
    payload = {
        "publish_ready": False,
        "count": count,
        "mismatch_count": len(mismatches),
        "mismatch_object_ids": mismatch_ids,
        "mismatches": tuple(mismatches),
        "identity": identity.details,
        "placement": placement.details,
    }
    if not mismatches:
        message = "Verify 通過。%s 個物件的 UserText 與 Apply 結果相符。" % count
        return results.ok("verify_model", message, command_id=command_id, details=payload)
    message = "Verify 發現 %s 個物件不符。" % len(mismatches)
    return results.ok_with_warnings(
        "verify_model",
        message,
        ("usertext_mismatch",),
        command_id=command_id,
        details=payload,
    )


def select_only(session: RhinoSession, object_ids: Sequence[str]) -> None:
    selector = getattr(session, "select_objects", None)
    if callable(selector):
        selector(tuple(object_ids))
        return
    wanted = set(object_ids)
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        state = session.get_view_state(object_id)
        if state is None:
            continue
        selected = object_id in wanted
        if state.selected == selected:
            continue
        session.set_view_state(
            ObjectViewState(
                object_id=object_id,
                selected=selected,
                locked=state.locked,
                hidden=state.hidden,
                color=state.color,
                color_by_layer=state.color_by_layer,
            )
        )


def format_verify_popup(result: results.Result) -> str:
    details = result.details or {}
    mismatches = details.get("mismatches") or ()
    if not mismatches:
        return result.message
    lines = [result.message, "不符合的物件已選取："]
    for item in mismatches[:MAX_POPUP_LINES]:
        notes = "；".join(item["notes"])
        lines.append("- %s：%s" % (item["label"], notes))
    extra = len(mismatches) - MAX_POPUP_LINES
    if extra > 0:
        lines.append("…其餘 %s 項。" % extra)
    lines.append(APPLY_REMINDER)
    return "\n".join(lines)


def verify_model_data(
    session: RhinoSession,
    *,
    catalog=None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
    show_message: Optional[Callable[[str], None]] = None,
    show_popup: bool = True,
) -> results.Result:
    """核對 UserText 是否等於再跑一次 Apply 的結果。符合／不符都彈窗；不符則選取那些物件。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "verify_model",
                "使用者取消 Verify。",
                command_id=command_id,
            )
        return compare_apply_usertext(
            current,
            catalog=catalog,
            environ=environ,
            selected_only=selected_only,
            command_id=command_id,
        )

    compared = action(session) if not guarded else run_guarded(session, action, command_id=command_id)
    if compared.ok and show_popup:
        popup = format_verify_popup(compared)
        if callable(show_message):
            show_message(popup)
        else:
            from loopflow.platform.rhino.prompts import show_message_with_red_hint

            show_message_with_red_hint(popup, APPLY_REMINDER)
        if guarded:
            select_only(session, compared.details.get("mismatch_object_ids") or ())
    return compared
