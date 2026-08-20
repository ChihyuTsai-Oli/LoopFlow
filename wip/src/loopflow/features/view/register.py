# -*- coding: utf-8 -*-
"""LF_Anchor_Frame：在 2D 模型空間登記 View。寫固定 transform，不射線。"""
from __future__ import annotations

import re
import uuid
from typing import Callable, Optional, Sequence

from loopflow.features.view.keys import (
    ANCHOR_COLOR,
    ANCHOR_LAYER,
    CLIPPING_PLANE_ID_KEY,
    DEFAULT_OFFSET,
    DETAIL_ID_KEY,
    INVERT_Y,
    LEGACY_ROLE_KEY,
    LEGACY_ROLE_VALUE,
    MIRROR_KEYWORDS,
    SCHEMA_ID_KEY,
    SCHEMA_VERSION_KEY,
    VIEW_ID_KEY,
    VIEW_SCHEMA_ID,
    VIEW_SCHEMA_VERSION,
    VIEW_TRANSFORM_KEY,
)
from loopflow.features.view.transform import (
    bbox_center_2d,
    bbox_center_local,
    build_transform,
    encode_transform,
    transform_ok,
)
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Anchor_Frame"
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
PickSelection = Callable[[RhinoSession], Optional[Sequence[str]]]
AskOffset = Callable[[RhinoSession], Optional[float]]


def _text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _new_id() -> str:
    return str(uuid.uuid4())


def is_view_host(session: RhinoSession, object_id: str) -> bool:
    schema = _text(session.get_object_user_text(object_id, SCHEMA_ID_KEY))
    if schema == VIEW_SCHEMA_ID:
        return True
    role = _text(session.get_object_user_text(object_id, LEGACY_ROLE_KEY))
    return role == LEGACY_ROLE_VALUE


def mirror_scale(hint: str) -> float:
    upper = hint.upper()
    for keyword in MIRROR_KEYWORDS:
        if keyword.upper() in upper:
            return -1.0
    return 1.0


def unique_named_records(hint: str, records: Sequence, get_name) -> tuple:
    """先完整名稱（不分大小寫）。沒有完全相同時，才看恰好一個名稱包含提示字。"""
    needle = (hint or "").strip().casefold()
    if not needle:
        return ()
    indexed = []
    for record in records:
        name = str(get_name(record) or "").strip().casefold()
        indexed.append((record, name))
    exact = tuple(record for record, name in indexed if name == needle)
    if exact:
        return exact
    return tuple(record for record, name in indexed if needle in name)


def match_clipping_planes(session: RhinoSession, hint: str):
    return unique_named_records(
        hint,
        session.iter_clipping_plane_ids(),
        lambda cp_id: session.object_name(cp_id) or "",
    )


def split_selection(session: RhinoSession, selected_ids: Sequence[str]):
    dots = []
    hosts = []
    geom = []
    for object_id in selected_ids:
        if session.is_text_dot(object_id):
            dots.append(object_id)
        elif is_view_host(session, object_id):
            hosts.append(object_id)
        else:
            geom.append(object_id)
    return tuple(dots), tuple(hosts), tuple(geom)


def _offset_rectangle(box, offset: float):
    min_x, min_y, min_z, max_x, max_y, _max_z = box
    return (
        (min_x - offset, min_y - offset, min_z),
        (max_x + offset, min_y - offset, min_z),
        (max_x + offset, max_y + offset, min_z),
        (min_x - offset, max_y + offset, min_z),
    )


def _write_view_usertext(
    session: RhinoSession,
    frame_id: str,
    *,
    view_id: str,
    clipping_plane_id: str,
    transform_payload: dict,
    hint: str,
    detail_id: Optional[str],
) -> None:
    session.set_object_name(frame_id, hint)
    session.set_object_layer(frame_id, ANCHOR_LAYER)
    session.set_object_user_text(frame_id, VIEW_ID_KEY, view_id)
    session.set_object_user_text(frame_id, SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
    session.set_object_user_text(frame_id, SCHEMA_VERSION_KEY, VIEW_SCHEMA_VERSION)
    session.set_object_user_text(frame_id, CLIPPING_PLANE_ID_KEY, clipping_plane_id)
    session.set_object_user_text(frame_id, VIEW_TRANSFORM_KEY, encode_transform(transform_payload))
    if detail_id:
        session.set_object_user_text(frame_id, DETAIL_ID_KEY, detail_id)


def register_view(
    session: RhinoSession,
    selected_ids: Sequence[str],
    offset: float,
    *,
    detail_id: Optional[str] = None,
) -> results.Result:
    """依選取寫入 View。測試可直接呼叫，不經選取。"""
    dots, hosts, geom = split_selection(session, selected_ids)
    if len(dots) != 1:
        reason = "missing_text_dot" if not dots else "ambiguous_text_dot"
        return results.blocked(
            "register_view",
            "請恰好選一個 Text Dot 作為剖面名稱提示。已停止，不寫入。",
            (reason,),
            command_id=COMMAND_ID,
            details={"text_dot_count": len(dots)},
        )
    hint = session.text_dot_text(dots[0])
    if hint is None:
        return results.blocked(
            "register_view",
            "Text Dot 沒有文字，已停止，不寫入。",
            ("missing_text_dot",),
            command_id=COMMAND_ID,
        )
    if len(hosts) > 1:
        return results.blocked(
            "register_view",
            "選到多個既有 View 框，已停止，不猜測要升級哪一個。",
            ("ambiguous_host",),
            command_id=COMMAND_ID,
            details={"host_count": len(hosts)},
        )
    source_ids = geom if geom else hosts
    if not source_ids:
        return results.blocked(
            "register_view",
            "沒有可用的剖面幾何，已停止，不寫入。",
            ("missing_geometry",),
            command_id=COMMAND_ID,
        )
    box = session.objects_bbox(source_ids)
    if not box:
        return results.blocked(
            "register_view",
            "無法計算剖面範圍，已停止，不寫入。",
            ("missing_geometry",),
            command_id=COMMAND_ID,
        )
    hits = match_clipping_planes(session, hint)
    if not hits:
        return results.blocked(
            "register_view",
            "找不到名稱包含「%s」的 Clipping Plane。已停止，不寫入。" % hint,
            ("missing_clipping_plane",),
            command_id=COMMAND_ID,
            details={"hint": hint},
        )
    if len(hits) > 1:
        return results.blocked(
            "register_view",
            "名稱包含「%s」的 Clipping Plane 有 %s 個，已停止，不猜測。" % (hint, len(hits)),
            ("ambiguous_clipping_plane",),
            command_id=COMMAND_ID,
            details={"hint": hint, "clipping_plane_ids": list(hits)},
        )
    cp_id = hits[0]
    plane = session.clipping_plane_plane(cp_id)
    section_box = session.clipping_plane_section_bbox_local(cp_id)
    origin_2d = bbox_center_2d(box)
    origin_3d_local = bbox_center_local(section_box)
    if plane is None or origin_2d is None or origin_3d_local is None:
        return results.blocked(
            "register_view",
            "找不到與 Clipping Plane 相交的 3D 模型，無法寫入固定 transform。",
            ("missing_section_intersection",),
            command_id=COMMAND_ID,
            details={"clipping_plane_id": cp_id},
        )
    payload = build_transform(
        origin_2d=origin_2d,
        origin_3d_local=origin_3d_local,
        scale_x=mirror_scale(hint),
        scale_y=-1.0 if INVERT_Y else 1.0,
        plane=plane,
    )
    if not transform_ok(payload):
        return results.failed(
            "register_view",
            "計算出的 View transform 不合法，已停止，不寫入。",
            command_id=COMMAND_ID,
        )
    session.ensure_layer(ANCHOR_LAYER)
    session.set_layer_appearance(ANCHOR_LAYER, ANCHOR_COLOR)
    created = False
    if hosts:
        frame_id = hosts[0]
        existing = _text(session.get_object_user_text(frame_id, VIEW_ID_KEY))
        view_id = existing if existing and UUID_V4_RE.match(existing) else _new_id()
    else:
        frame_id = session.add_closed_polyline(
            _offset_rectangle(box, float(offset)),
            layer=ANCHOR_LAYER,
            name=hint,
        )
        created = True
        view_id = _new_id()
    try:
        _write_view_usertext(
            session,
            frame_id,
            view_id=view_id,
            clipping_plane_id=cp_id,
            transform_payload=payload,
            hint=hint,
            detail_id=_text(detail_id),
        )
    except Exception:
        if created:
            session.delete_object(frame_id)
        raise
    return results.ok(
        "register_view",
        "已登記 View。",
        command_id=COMMAND_ID,
        details={
            "frame_id": frame_id,
            "view_id": view_id,
            "clipping_plane_id": cp_id,
            "upgraded": bool(hosts),
            "created": created,
        },
    )


def _default_pick(session: RhinoSession) -> Optional[Sequence[str]]:
    from loopflow.platform.rhino.prompts import pick_anchor_selection

    return pick_anchor_selection()


def _default_offset(_session: RhinoSession) -> Optional[float]:
    from loopflow.platform.rhino.prompts import ask_real

    return ask_real("輸入框線外擴距離", DEFAULT_OFFSET, 0.0)


def run_anchor_frame(
    session: RhinoSession,
    *,
    pick_selection: Optional[PickSelection] = None,
    ask_offset: Optional[AskOffset] = None,
) -> results.Result:
    """框選剖面物件與 Text Dot，再問 offset。Esc 取消不寫入。"""
    picker = pick_selection or _default_pick
    offsetter = ask_offset or _default_offset

    def action(current: RhinoSession) -> results.Result:
        selected = picker(current)
        if not selected:
            return results.cancelled(
                "register_view",
                "已取消登記 View。",
                command_id=COMMAND_ID,
            )
        offset = offsetter(current)
        if offset is None:
            return results.cancelled(
                "register_view",
                "已取消登記 View。",
                command_id=COMMAND_ID,
            )
        return register_view(current, selected, offset)

    return run_guarded(session, action, command_id=COMMAND_ID)
