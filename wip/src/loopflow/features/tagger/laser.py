# -*- coding: utf-8 -*-
"""LF_Tagger_Laser：Layout 點 Detail，用固定 View transform 射線。只寫 binding。"""
from __future__ import annotations

import math
from typing import Callable, Optional, Sequence, Tuple

from loopflow.features.tagger.binding import UUID_V4_RE, write_object_binding
from loopflow.features.tagger.keys import (
    LASER_OBJECT_TEMPLATE_IDS,
    is_tag_locked,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.view.keys import (
    SCHEMA_ID_KEY,
    VIEW_SCHEMA_ID,
    VIEW_TRANSFORM_KEY,
)
from loopflow.features.view.transform import (
    bbox_center_2d,
    decode_transform,
    ray_from_transform,
)
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.foundation.usertext import OBJECT_ID_KEY, read_text
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Tagger_Laser"
DRAW_DEBUG_RAY = False
DEBUG_RAY_LENGTH = 2000.0
DEBUG_RAY_LAYER = "LoopFlow::Debug_Laser"
DEBUG_RAY_COLOR = (255, 0, 255)
MAX_HIT_OBJECTS = 2
ORIGIN_BACK = 5.0
HIT_PRIORITY = {"FRONTAL": 0, "GRAZING": 1, "BACKFACE": 2}
PickTag = Callable[[RhinoSession], Optional[str]]
PickPoint = Callable[[RhinoSession], Optional[Sequence[float]]]
Probe = Callable[[RhinoSession, Sequence[float], Sequence[float]], Sequence[dict]]
ChooseHit = Callable[[Sequence[dict]], Optional[dict]]


def _refuse_reason(template: TagTemplate) -> str:
    if template.template_id in ("TAG_HEIGHT_GRAB", "TAG_FINISH_GRAB") or "GRAB" in template.template_id:
        return "「%s」請用 Grab 綁定，Laser 不寫入。" % template.template_id
    if template.template_id == "TAG_ITEM":
        return "家具 Tag 請用 Grab 綁定，Laser 不寫入。"
    if template.template_id == "TAG_DW" or "manual" in template.binding_modes:
        return "「%s」是純手動標籤，不接受 Laser 綁定。" % template.template_id
    if template.family == "index":
        return "「%s」請用 Index 綁定，Laser 不寫入。" % template.template_id
    if template.role == "title_frame" or "none" in template.binding_modes:
        return "「%s」不綁模型來源，Laser 不寫入。" % template.template_id
    return "「%s」不是 Laser 可用的標籤，已停止，不寫入。" % template.template_id


def bbox_contains_xy(box, point) -> bool:
    if not box or point is None or len(point) < 2:
        return False
    return box[0] - 1e-9 <= float(point[0]) <= box[3] + 1e-9 and box[1] - 1e-9 <= float(point[1]) <= box[4] + 1e-9


def view_frames_containing(session: RhinoSession, point_2d: Sequence[float]):
    hits = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        schema = session.get_object_user_text(object_id, SCHEMA_ID_KEY)
        if schema != VIEW_SCHEMA_ID:
            continue
        if bbox_contains_xy(session.object_bbox(object_id), point_2d):
            hits.append(object_id)
    return tuple(hits)


def origin_behind_plane(origin, direction, back: float = ORIGIN_BACK) -> Tuple[float, float, float]:
    """把射線原點往射出方向的反方向微移，才能打到貼在剖平面上的牆。"""
    dx, dy, dz = float(direction[0]), float(direction[1]), float(direction[2])
    length = math.sqrt(dx * dx + dy * dy + dz * dz)
    if length < 1e-9:
        return (float(origin[0]), float(origin[1]), float(origin[2]))
    scale = float(back) / length
    return (
        float(origin[0]) - dx * scale,
        float(origin[1]) - dy * scale,
        float(origin[2]) - dz * scale,
    )


def debug_ray_end(origin, direction, length: float = DEBUG_RAY_LENGTH) -> Tuple[float, float, float]:
    dx, dy, dz = float(direction[0]), float(direction[1]), float(direction[2])
    size = math.sqrt(dx * dx + dy * dy + dz * dz)
    if size < 1e-9:
        return (float(origin[0]), float(origin[1]), float(origin[2]))
    scale = float(length) / size
    return (
        float(origin[0]) + dx * scale,
        float(origin[1]) + dy * scale,
        float(origin[2]) + dz * scale,
    )


def apply_live_view_origins(session: RhinoSession, frame_id: str, payload: dict) -> dict:
    """2D 用框內剖面現況中心；3D 維持登記時寫死的 cp 與 origin_3d_local。"""
    updated = dict(payload)
    content_fn = getattr(session, "drawing_content_bbox", None)
    content_box = content_fn(frame_id) if callable(content_fn) else None
    live_2d = bbox_center_2d(content_box) or bbox_center_2d(session.object_bbox(frame_id))
    if live_2d is not None:
        updated["origin_2d"] = [live_2d[0], live_2d[1], live_2d[2]]
    return updated


def debug_ray_enabled() -> bool:
    """命令列 DebugRay 優先；沒有 sticky 時用模組開關（測試用）。"""
    from loopflow.platform.rhino.prompts import debug_ray_sticky

    sticky = debug_ray_sticky()
    if sticky is not None:
        return sticky
    return bool(DRAW_DEBUG_RAY)


def draw_debug_ray(session: RhinoSession, plane_point, origin, direction) -> None:
    """測試用：在 3D 畫出實際射線。預設關閉，命令列 DebugRay=Yes 才畫。"""
    if not debug_ray_enabled():
        return
    drawer = getattr(session, "draw_laser_debug_ray", None)
    if not callable(drawer):
        return
    drawer(plane_point, origin, debug_ray_end(origin, direction))


def cluster_hits(hits: Sequence[dict]):
    """依距離排序，同一物件只留一次，穿過兩個物件就停止。"""
    if not hits:
        return ()
    ordered = sorted(
        hits,
        key=lambda item: (
            float(item.get("dist") or 0.0),
            HIT_PRIORITY.get(item.get("hit_type") or "", 9),
        ),
    )
    unique = []
    seen = set()
    for item in ordered:
        object_id = item.get("object_id")
        if not object_id or object_id in seen:
            continue
        seen.add(object_id)
        unique.append(item)
        if len(unique) >= MAX_HIT_OBJECTS:
            break
    return tuple(unique)


def _default_pick_tag(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_block_instance

    return pick_block_instance(
        "選取要綁定的 Laser Tag（Esc 取消）",
        debug_ray_option=True,
    )


def _default_pick_point(_session: RhinoSession):
    from loopflow.platform.rhino.prompts import pick_layout_detail_model_point

    return pick_layout_detail_model_point(debug_ray_option=True)


def _default_probe(session: RhinoSession, origin, direction):
    shooter = getattr(session, "shoot_ray_hits", None)
    if not callable(shooter):
        return ()
    return shooter(origin, direction) or ()


def hit_choice_label(item: dict) -> str:
    """選取清單只顯示圖層終端名；有物件名稱才附上。不顯示 GUID／UUID。"""
    layer = str(item.get("layer") or "").split("::")[-1].strip() or "（無圖層）"
    name = str(item.get("name") or "").strip()
    if name:
        return "%s  %s" % (layer, name)
    return layer


def choice_labels(hits: Sequence[dict]):
    """同名列加上（2）（3），避免 ListBox 回傳值對不到第二筆。"""
    base = [hit_choice_label(item) for item in hits]
    counts = {}
    for label in base:
        counts[label] = counts.get(label, 0) + 1
    seen = {}
    labels = []
    for label in base:
        if counts[label] == 1:
            labels.append(label)
            continue
        seen[label] = seen.get(label, 0) + 1
        labels.append("%s（%s）" % (label, seen[label]))
    return tuple(labels)


def _default_choose(hits: Sequence[dict]):
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    from loopflow.platform.rhino.prompts import ask_popup_choice

    labels = list(choice_labels(hits))
    chosen = ask_popup_choice("多個重疊物件，請選要標註的來源", labels)
    if chosen is None:
        return None
    return hits[labels.index(chosen)]


def bind_laser_hit(
    session: RhinoSession,
    tag_id: str,
    source_id: str,
    catalog: TagTemplateSet,
) -> results.Result:
    """把命中物件的 UUID 寫進 Laser Tag。測試可直接呼叫。"""
    if not session.is_block_instance(tag_id):
        return results.blocked(
            "bind_tag",
            "請選 Tag 圖塊。已停止，不寫入。",
            ("not_a_block",),
            command_id=COMMAND_ID,
        )
    block_name = session.block_definition_name(tag_id)
    template = catalog.by_block_name(block_name or "")
    if template is None:
        return results.blocked(
            "bind_tag",
            "未知圖塊「%s」，已停止，不寫入。" % (block_name or "（未命名）"),
            ("unknown_block",),
            command_id=COMMAND_ID,
            details={"block_name": block_name},
        )
    if is_tag_locked(session, tag_id):
        return results.blocked(
            "bind_tag",
            "此 Tag 已鎖定，請先解除鎖定再綁定。",
            ("tag_locked",),
            command_id=COMMAND_ID,
        )
    if template.template_id not in LASER_OBJECT_TEMPLATE_IDS:
        return results.blocked(
            "bind_tag",
            _refuse_reason(template),
            ("unsupported_template",),
            command_id=COMMAND_ID,
            details={"template_id": template.template_id},
        )
    object_uuid = read_text(session, source_id, OBJECT_ID_KEY)
    if object_uuid is None or not UUID_V4_RE.match(object_uuid):
        return results.blocked(
            "bind_tag",
            "來源物件尚未寫入 UUID。請先跑 Nexus 寫入模型 Metadata。",
            ("missing_object_id",),
            command_id=COMMAND_ID,
        )
    write_object_binding(session, tag_id, template, object_uuid)
    return results.ok(
        "bind_tag",
        "已綁定來源 UUID。",
        command_id=COMMAND_ID,
        details={
            "tag_id": tag_id,
            "template_id": template.template_id,
            "binding_mode": "object",
            "source_object_id": object_uuid,
        },
    )


def run_tagger_laser(
    session: RhinoSession,
    *,
    pick_tag: Optional[PickTag] = None,
    pick_point: Optional[PickPoint] = None,
    probe: Optional[Probe] = None,
    choose_hit: Optional[ChooseHit] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    """選 Laser Tag，在 Detail 內點一下射線。Esc 取消不寫入。"""
    schema = check_document_schema(session)
    if not schema.ok:
        return results.failed(
            schema.stage,
            schema.message,
            command_id=COMMAND_ID,
            details=schema.details,
        )
    if "missing_document_schema" in (schema.warnings or ()):
        return results.blocked(
            "check_schema",
            "文件尚未寫入 schema，已停止，不寫入。",
            ("missing_document_schema",),
            command_id=COMMAND_ID,
        )
    loaded = catalog
    if loaded is None:
        templates = load_tag_templates()
        if not templates.ok:
            return templates
        loaded = templates.details["catalog"]
    tag_picker = pick_tag or _default_pick_tag
    point_picker = pick_point or _default_pick_point
    probe_fn = probe or _default_probe
    chooser = choose_hit or _default_choose

    def action(current: RhinoSession) -> results.Result:
        tag_id = tag_picker(current)
        if not tag_id:
            return results.cancelled(
                "bind_tag",
                "已取消 Laser。",
                command_id=COMMAND_ID,
            )
        if current.get_view_state(tag_id) is None:
            return results.blocked(
                "bind_tag",
                "找不到選取的 Tag。",
                ("missing_tag",),
                command_id=COMMAND_ID,
            )
        if not current.is_block_instance(tag_id):
            return results.blocked(
                "bind_tag",
                "請選 Tag 圖塊。已停止，不寫入。",
                ("not_a_block",),
                command_id=COMMAND_ID,
            )
        block_name = current.block_definition_name(tag_id)
        template = loaded.by_block_name(block_name or "")
        if template is None:
            return results.blocked(
                "bind_tag",
                "未知圖塊「%s」，已停止，不寫入。" % (block_name or "（未命名）"),
                ("unknown_block",),
                command_id=COMMAND_ID,
                details={"block_name": block_name},
            )
        if template.template_id not in LASER_OBJECT_TEMPLATE_IDS:
            return results.blocked(
                "bind_tag",
                _refuse_reason(template),
                ("unsupported_template",),
                command_id=COMMAND_ID,
                details={"template_id": template.template_id},
            )
        if is_tag_locked(current, tag_id):
            return results.blocked(
                "bind_tag",
                "此 Tag 已鎖定，請先解除鎖定再綁定。",
                ("tag_locked",),
                command_id=COMMAND_ID,
            )
        point_2d = point_picker(current)
        if not point_2d:
            return results.cancelled(
                "probe_view",
                "已取消 Laser。",
                command_id=COMMAND_ID,
            )
        frames = view_frames_containing(current, point_2d)
        if not frames:
            return results.blocked(
                "probe_view",
                "這一點不在任何已登記的 View 框內。請先執行 Anchor Frame。",
                ("missing_view",),
                command_id=COMMAND_ID,
            )
        if len(frames) > 1:
            return results.blocked(
                "probe_view",
                "這一點落在 %s 個重疊的 View 框內，已停止，不猜測。" % len(frames),
                ("ambiguous_view",),
                command_id=COMMAND_ID,
                details={"frame_ids": list(frames)},
            )
        payload = decode_transform(current.get_object_user_text(frames[0], VIEW_TRANSFORM_KEY))
        if payload is None:
            return results.blocked(
                "probe_view",
                "View 框沒有合法的固定 transform。請重新執行 Anchor Frame。",
                ("invalid_transform",),
                command_id=COMMAND_ID,
                details={"frame_id": frames[0]},
            )
        payload = apply_live_view_origins(current, frames[0], payload)
        origin, direction = ray_from_transform(payload, point_2d)
        probe_origin = origin_behind_plane(origin, direction)
        draw_debug_ray(current, origin, probe_origin, direction)
        hits = cluster_hits(probe_fn(current, probe_origin, direction))
        if not hits:
            if debug_ray_enabled():
                return results.ok(
                    "probe_view",
                    "已畫出射線。沒打到帶 UUID 的 3D 物件。請到 3D 視窗查看。",
                    command_id=COMMAND_ID,
                    details={"debug_ray": True, "hit_count": 0},
                )
            return results.blocked(
                "probe_view",
                "射線沒有打到帶 UUID 的 3D 物件。",
                ("no_hit",),
                command_id=COMMAND_ID,
            )
        chosen = chooser(hits)
        if not chosen:
            return results.cancelled(
                "probe_view",
                "已取消 Laser。",
                command_id=COMMAND_ID,
            )
        source_id = chosen.get("object_id")
        if not source_id:
            return results.blocked(
                "probe_view",
                "射線命中沒有物件 ID，已停止，不寫入。",
                ("no_hit",),
                command_id=COMMAND_ID,
            )
        bound = bind_laser_hit(current, tag_id, source_id, loaded)
        if bound.ok:
            details = dict(bound.details)
            details["frame_id"] = frames[0]
            details["hit_count"] = len(hits)
            return results.ok(bound.stage, bound.message, command_id=COMMAND_ID, details=details)
        return bound

    return run_guarded(session, action, command_id=COMMAND_ID)
