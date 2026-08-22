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
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Nexus"


def field_labels():
    return {
        OBJECT_ID_KEY: "UUID",
        TYPE_ID_KEY: t("nexus_metadata.047"),
        TYPE_CATEGORY_KEY: t("nexus_metadata.048"),
        TYPE_SEQUENCE_KEY: t("nexus_metadata.049"),
        CONSTRUCTION_KEY: t("nexus_metadata.050"),
        REMARKS_KEY: t("nexus_metadata.051"),
        DATA_REVISION_KEY: t("nexus_metadata.052"),
        SPACE_ID_KEY: t("nexus_metadata.053"),
        SPACE_DISPLAY_KEY: t("nexus_metadata.040"),
        ELEVATION_BASIS_KEY: t("nexus_metadata.054"),
        ELEVATION_VALUE_KEY: t("nexus_metadata.055"),
        ELEVATION_DISPLAY_KEY: t("nexus_metadata.056"),
    }


def issue_labels():
    return {
        "missing_object_id": t("nexus_metadata.057"),
        "invalid_object_id": t("nexus_metadata.058"),
        "duplicate_object_id": t("nexus_metadata.059"),
        "unknown_type": t("nexus_metadata.060"),
        "unmapped_layer": t("nexus_metadata.061"),
        "ambiguous_space": t("nexus_metadata.062"),
        "bc_on_non_block": t("nexus_metadata.063"),
        "invalid_elevation_basis": t("nexus_metadata.064"),
        "bbox_unavailable": t("nexus_metadata.065"),
        "stale_dimension": t("nexus_metadata.066"),
    }


HARD_PLACEMENT_ISSUES = (
    "ambiguous_space",
    "bc_on_non_block",
    "invalid_elevation_basis",
    "bbox_unavailable",
)
MAX_POPUP_LINES = 12


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
        label = field_labels().get(key, key)
        if not actual:
            notes.append(t("nexus_metadata.073") % (label, want or t("nexus_metadata.076")))
        elif not want:
            notes.append(t("nexus_metadata.074") % (label, actual))
        else:
            notes.append(t("nexus_metadata.075") % (label, actual, want))
    return notes


def _stale_notes(session: RhinoSession, object_id: str) -> List[str]:
    leftover = [
        key for key in STALE_OBJECT_KEYS if session.get_object_user_text(object_id, key) not in (None, "")
    ]
    if leftover:
        return [issue_labels()["stale_dimension"]]
    return []


def compare_apply_usertext(
    session: RhinoSession,
    *,
    catalog=None,
    selected_only: bool = False,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """算出 Apply 會寫的欄位，與現有 UserText 比對。不寫入。"""
    identity = scan_identity(
        session,
        catalog=catalog,
        selected_only=selected_only,
        guarded=False,
        command_id=command_id,
    )
    if not identity.ok:
        return identity
    placement = scan_placement(
        session,
        catalog=catalog,
        selected_only=selected_only,
        guarded=False,
        command_id=command_id,
    )
    if not placement.ok:
        return placement
    loaded = _load_catalog(catalog, session)
    if not loaded.ok:
        return loaded
    type_catalog = loaded.details["catalog"]
    revision = expected_data_revision(session)

    identity_by_id = {item["rhino_id"]: item for item in identity.details.get("items") or ()}
    placement_by_id = {item["rhino_id"]: item for item in placement.details.get("items") or ()}
    mismatches = []
    for object_id in iter_scan_targets(session, selected_only=selected_only):
        ident = identity_by_id.get(object_id) or {}
        place = placement_by_id.get(object_id) or {}
        notes = []
        for issue in ident.get("issues") or ():
            notes.append(issue_labels().get(issue, issue))
        for issue in place.get("issues") or ():
            if issue == "migration_th_bh":
                continue
            notes.append(issue_labels().get(issue, issue))
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
        message = t("nexus_metadata.069") % count
        return results.ok("verify_model", message, command_id=command_id, details=payload)
    message = t("nexus_metadata.067") % len(mismatches)
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


def format_verify_popup(result: results.Result, *, cannot_publish: bool = False) -> str:
    """選單 6 與 Publish Exchange 共用同一份不符清單。"""
    details = result.details or {}
    mismatches = details.get("mismatches") or ()
    lines = []
    if cannot_publish:
        lines.append(t("nexus_metadata.070"))
    if not mismatches:
        if result.message:
            lines.append(result.message)
        return "\n".join(lines) if lines else (result.message or "")
    lines.append(result.message)
    lines.append(t("nexus_metadata.068"))
    for item in mismatches[:MAX_POPUP_LINES]:
        notes = "；".join(item["notes"])
        lines.append("- %s：%s" % (item["label"], notes))
    extra = len(mismatches) - MAX_POPUP_LINES
    if extra > 0:
        lines.append(t("nexus_metadata.071") % extra)
    lines.append(t("nexus_metadata.046"))
    return "\n".join(lines)


def verify_model_data(
    session: RhinoSession,
    *,
    catalog=None,
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
                t("nexus_metadata.072"),
                command_id=command_id,
            )
        return compare_apply_usertext(
            current,
            catalog=catalog,
            selected_only=selected_only,
            command_id=command_id,
        )

    compared = action(session) if not guarded else run_guarded(session, action, command_id=command_id)
    if compared.ok and show_popup:
        popup = format_verify_popup(compared)
        if callable(show_message):
            show_message(popup)
        else:
            from loopflow.platform.rhino.prompts import show_message as live_popup

            live_popup(popup)
        if guarded:
            select_only(session, compared.details.get("mismatch_object_ids") or ())
    return compared
