# -*- coding: utf-8 -*-
"""LF_Anchor_Update：3D 尺寸變更且 2D 剖面重出後，就地更新既有 Anchor Frame。"""
from __future__ import annotations

from typing import Optional

from loopflow.features.view.keys import (
    CLIPPING_PLANE_ID_KEY,
    DEFAULT_OFFSET,
    DETAIL_ID_KEY,
    SCHEMA_ID_KEY,
    VIEW_ID_KEY,
    VIEW_NAME_KEY,
    VIEW_SCHEMA_ID,
    VIEW_TRANSFORM_KEY,
)
from loopflow.features.view.register import (
    UUID_V4_RE,
    _offset_rectangle,
    _text,
    _write_view_usertext,
    section_block_name,
    unique_named_records,
)
from loopflow.features.view.transform import (
    bbox_center_2d,
    bbox_center_local,
    build_transform,
    decode_transform,
    transform_ok,
)
from loopflow.foundation import results
from loopflow.foundation.i18n import t
from loopflow.platform.rhino.session import (
    RhinoSession,
    is_extract_layer,
    is_loopflow_layer,
    run_guarded,
)

COMMAND_ID = "LF_Anchor_Update"
STAGE = "update_anchor_frames"


def recover_offset(frame_box, geom_box) -> float:
    """從舊框四邊留白取出現最多次、且不小於 0 的距離。對不齊時用預設 50。"""
    gaps = (
        float(geom_box[0]) - float(frame_box[0]),
        float(frame_box[3]) - float(geom_box[3]),
        float(geom_box[1]) - float(frame_box[1]),
        float(frame_box[4]) - float(geom_box[4]),
    )
    counts = {}
    for gap in gaps:
        if gap < -1e-6:
            continue
        key = round(max(gap, 0.0), 6)
        counts[key] = counts.get(key, 0) + 1
    if not counts:
        return float(DEFAULT_OFFSET)
    best = max(counts.values())
    winners = [key for key, count in counts.items() if count == best]
    if best < 2 or len(winners) != 1:
        return float(DEFAULT_OFFSET)
    return float(winners[0])


def section_root(path: Optional[str]) -> Optional[str]:
    """剖圖圖層的根名稱。Visible／Hatch／Curve 子層回到上一層。"""
    text = str(path or "").strip()
    if not text or is_loopflow_layer(text) or is_extract_layer(text):
        return None
    parts = text.split("::")
    terminal = parts[-1].upper()
    if "VISIBLE" in terminal or "HATCH" in terminal or "CURVE" in terminal:
        if len(parts) < 2:
            return None
        return "::".join(parts[:-1])
    return text


def _frame_ids(session: RhinoSession) -> tuple:
    found = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        if _text(session.get_object_user_text(object_id, SCHEMA_ID_KEY)) != VIEW_SCHEMA_ID:
            continue
        view_id = _text(session.get_object_user_text(object_id, VIEW_ID_KEY))
        if view_id and UUID_V4_RE.match(view_id):
            found.append(object_id)
    return tuple(found)


def _section_geometry(session: RhinoSession, frame_id: str, view_name: str):
    """先對唯一剖面圖塊；沒有圖塊時對同名剖圖圖層上的線與填充。不要求落在舊框內。"""
    blocks = []
    loose = {}
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        if object_id == frame_id or session.is_clipping_plane(object_id):
            continue
        if session.is_text_dot(object_id):
            continue
        if session.is_block_instance(object_id):
            blocks.append(object_id)
            continue
        if not session.is_curve_or_hatch(object_id):
            continue
        layer = session.object_layer(object_id) or ""
        terminal = layer.rsplit("::", 1)[-1].upper()
        if "VISIBLE" in terminal:
            continue
        root = section_root(layer)
        if root:
            loose.setdefault(root, []).append(object_id)
    matched_blocks = unique_named_records(
        view_name,
        blocks,
        lambda object_id: section_block_name(session, object_id) or "",
    )
    if len(matched_blocks) > 1:
        return None, "ambiguous_section"
    if len(matched_blocks) == 1:
        return (matched_blocks[0],), None
    matched_roots = unique_named_records(view_name, tuple(loose), lambda name: name)
    if len(matched_roots) > 1:
        return None, "ambiguous_section"
    if len(matched_roots) == 1:
        return tuple(loose[matched_roots[0]]), None
    return None, "missing_section"


def _skip_message(name: str, reason: str) -> str:
    key = {
        "missing_clipping_plane": "anchor_update.003",
        "ambiguous_section": "anchor_update.004",
        "missing_section": "anchor_update.004",
        "missing_section_intersection": "anchor_update.005",
        "invalid_transform": "anchor_update.006",
    }.get(reason, "anchor_update.006")
    return t(key) % name


def _frame_label(session: RhinoSession, frame_id: str) -> str:
    return (
        _text(session.get_object_user_text(frame_id, VIEW_NAME_KEY))
        or _text(session.object_name(frame_id))
        or frame_id
    )


def update_frame(session: RhinoSession, frame_id: str):
    """更新一張框。回傳 (updated, reason)。reason 為 None 代表已寫入。"""
    view_name = _text(session.get_object_user_text(frame_id, VIEW_NAME_KEY))
    view_id = _text(session.get_object_user_text(frame_id, VIEW_ID_KEY))
    cp_id = _text(session.get_object_user_text(frame_id, CLIPPING_PLANE_ID_KEY))
    if not view_name or not view_id:
        return False, "invalid_transform"
    if not cp_id or not session.is_clipping_plane(cp_id):
        return False, "missing_clipping_plane"
    stored = decode_transform(session.get_object_user_text(frame_id, VIEW_TRANSFORM_KEY))
    if stored is None:
        return False, "invalid_transform"
    geometry, reason = _section_geometry(session, frame_id, view_name)
    if geometry is None:
        return False, reason or "missing_section"
    geom_box = session.objects_bbox(geometry)
    frame_box = session.object_bbox(frame_id)
    if not geom_box or not frame_box:
        return False, "missing_section"
    plane = session.clipping_plane_plane(cp_id)
    section_box = session.clipping_plane_section_bbox_local(cp_id)
    origin_2d = bbox_center_2d(geom_box)
    origin_3d_local = bbox_center_local(section_box)
    if plane is None or origin_2d is None or origin_3d_local is None:
        return False, "missing_section_intersection"
    payload = build_transform(
        origin_2d=origin_2d,
        origin_3d_local=origin_3d_local,
        scale_x=float(stored["scale_x"]),
        scale_y=float(stored["scale_y"]),
        plane=plane,
    )
    if not transform_ok(payload):
        return False, "invalid_transform"
    offset = recover_offset(frame_box, geom_box)
    replaced = session.replace_closed_polyline(frame_id, _offset_rectangle(geom_box, offset))
    if not replaced:
        return False, "invalid_transform"
    _write_view_usertext(
        session,
        frame_id,
        view_id=view_id,
        clipping_plane_id=cp_id,
        transform_payload=payload,
        hint=view_name,
        detail_id=_text(session.get_object_user_text(frame_id, DETAIL_ID_KEY)),
    )
    return True, None


def update_anchor_frames(session: RhinoSession) -> results.Result:
    """更新檔案裡既有的 Anchor Frame。對不到的維持原框。"""
    if session.is_layout_active():
        return results.blocked(
            STAGE,
            t("anchor_update.007"),
            ("layout_active",),
            command_id=COMMAND_ID,
        )
    frames = _frame_ids(session)
    if not frames:
        return results.blocked(
            STAGE,
            t("anchor_update.008"),
            ("missing_frame",),
            command_id=COMMAND_ID,
        )
    updated = []
    skipped = []
    for frame_id in frames:
        changed, reason = update_frame(session, frame_id)
        if changed:
            updated.append(frame_id)
            continue
        skipped.append(_skip_message(_frame_label(session, frame_id), reason or "invalid_transform"))
    if not updated:
        return results.blocked(
            STAGE,
            "\n".join([t("anchor_update.009")] + skipped),
            tuple(skipped),
            command_id=COMMAND_ID,
            details={"updated": [], "skipped": skipped},
        )
    message = t("anchor_update.001") % len(updated)
    if skipped:
        return results.ok_with_warnings(
            STAGE,
            message,
            tuple(skipped),
            command_id=COMMAND_ID,
            details={"updated": updated, "skipped": skipped},
        )
    return results.ok(
        STAGE,
        message,
        command_id=COMMAND_ID,
        details={"updated": updated, "skipped": []},
    )


def run_anchor_update(session: RhinoSession) -> results.Result:
    """在 2D 模型空間更新既有框。不詢問外擴。"""

    def action(current: RhinoSession) -> results.Result:
        return update_anchor_frames(current)

    return run_guarded(session, action, command_id=COMMAND_ID)
