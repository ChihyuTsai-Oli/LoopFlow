# -*- coding: utf-8 -*-
"""Space Boundary：封閉曲線建立穩定空間身分。不改模型物件的空間欄。"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from loopflow.features.dictionary.layer_paths import SYSTEM_LAYERS
from loopflow.foundation import results
from loopflow.foundation.usertext import LEVEL_ID_KEY, SPACE_DISPLAY_KEY, SPACE_ID_KEY, read_text, write_text
from loopflow.foundation.version import check_schema
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
SCHEMA_ID = "loopflow.space"
SPACE_BOUNDARY_LAYER = SYSTEM_LAYERS[0]
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@dataclass(frozen=True)
class SpaceDraft:
    object_id: str
    space_display: str
    level_id: str
    space_id: Optional[str] = None


def _xy(point) -> Tuple[float, float]:
    return float(point[0]), float(point[1])


def aabb_overlap_area(polygon_a, polygon_b) -> float:
    ax = [_xy(pt)[0] for pt in polygon_a]
    ay = [_xy(pt)[1] for pt in polygon_a]
    bx = [_xy(pt)[0] for pt in polygon_b]
    by = [_xy(pt)[1] for pt in polygon_b]
    dx = min(max(ax), max(bx)) - max(min(ax), min(bx))
    dy = min(max(ay), max(by)) - max(min(ay), min(by))
    if dx > 1e-9 and dy > 1e-9:
        return dx * dy
    return 0.0


def aabb_contains(polygon, x: float, y: float) -> bool:
    xs = [_xy(pt)[0] for pt in polygon]
    ys = [_xy(pt)[1] for pt in polygon]
    return min(xs) - 1e-9 <= x <= max(xs) + 1e-9 and min(ys) - 1e-9 <= y <= max(ys) + 1e-9


def point_in_polygon(polygon, x: float, y: float) -> bool:
    """射線法。先用 AABB 剔除。"""
    if not aabb_contains(polygon, x, y):
        return False
    pts = [_xy(pt) for pt in polygon]
    inside = False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if (yi > y) != (yj > y):
            at = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < at:
                inside = not inside
        j = i
    return inside


def _new_id() -> str:
    return str(uuid.uuid4())


def find_overlaps(spaces: Sequence[dict]) -> Tuple[Tuple[str, str], ...]:
    conflicts = []
    for i, left in enumerate(spaces):
        for right in spaces[i + 1 :]:
            if left["level_id"] != right["level_id"]:
                continue
            if aabb_overlap_area(left["polygon"], right["polygon"]) > 0:
                conflicts.append((left["space_display"], right["space_display"]))
    return tuple(conflicts)


def find_xy_overlaps_other_level(spaces: Sequence[dict]) -> Tuple[Tuple[str, str], ...]:
    """平面 AABB 重疊但樓層不同：契約允許，實機時需讓使用者看見。"""
    pairs = []
    for i, left in enumerate(spaces):
        for right in spaces[i + 1 :]:
            if left["level_id"] == right["level_id"]:
                continue
            if aabb_overlap_area(left["polygon"], right["polygon"]) > 0:
                pairs.append((left["space_display"], right["space_display"]))
    return tuple(pairs)


def drafts_from_selection(session: RhinoSession) -> Tuple[SpaceDraft, ...]:
    """把目前選取物件當成 Space 候選；名稱與樓層來自 ObjectName／既有 UserText。"""
    drafts = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        state = session.get_view_state(object_id)
        if state is None or not state.selected:
            continue
        display = session.object_name(object_id) or read_text(
            session, object_id, SPACE_DISPLAY_KEY
        ) or ""
        level_id = read_text(session, object_id, LEVEL_ID_KEY) or ""
        space_id = read_text(session, object_id, SPACE_ID_KEY)
        drafts.append(
            SpaceDraft(
                object_id=object_id,
                space_display=display,
                level_id=level_id,
                space_id=space_id,
            )
        )
    return tuple(drafts)


def register_space_boundaries(
    session: RhinoSession,
    drafts: Sequence[SpaceDraft],
    *,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """把有效封閉曲線登記為 Space。不寫入其他模型物件的 lf_space_*。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "register_spaces",
                "使用者取消 Space Boundary。",
                command_id=command_id,
            )
        schema = check_schema(SCHEMA_ID, 1)
        if not schema.ok:
            return schema
        if not drafts:
            return results.blocked(
                "register_spaces",
                "沒有選取 Space Boundary。請選取封閉曲線後再執行。",
                blocking=("missing_space_selection",),
                command_id=command_id,
            )
        parsed = []
        invalid = []
        for draft in drafts:
            if not current.is_closed_curve(draft.object_id):
                invalid.append(draft.object_id)
                continue
            polygon = current.curve_polygon(draft.object_id)
            if not polygon or len(polygon) < 3:
                invalid.append(draft.object_id)
                continue
            if not (draft.space_display or "").strip():
                invalid.append(draft.object_id)
                continue
            if not UUID_V4_RE.match(draft.level_id or ""):
                invalid.append(draft.object_id)
                continue
            space_id = draft.space_id or read_text(current, draft.object_id, SPACE_ID_KEY)
            if space_id == "EXT" or (space_id and not UUID_V4_RE.match(space_id)):
                invalid.append(draft.object_id)
                continue
            parsed.append(
                {
                    "object_id": draft.object_id,
                    "space_display": draft.space_display.strip(),
                    "level_id": draft.level_id,
                    "space_id": space_id,
                    "polygon": polygon,
                }
            )
        if invalid:
            return results.blocked(
                "register_spaces",
                "有 %s 條無效曲線（未封閉、頂點不足、或缺 level_id／名稱）。" % len(invalid),
                blocking=("invalid_space_curve",),
                command_id=command_id,
                details={"invalid_object_ids": tuple(invalid)},
            )
        for item in parsed:
            if not item["space_id"]:
                item["space_id"] = _new_id()
        space_ids = [item["space_id"] for item in parsed]
        if len(space_ids) != len(set(space_ids)):
            return results.blocked(
                "register_spaces",
                "同一個 space_id 出現在多條 boundary，已停止，不靜默換號。",
                blocking=("duplicate_space_id",),
                command_id=command_id,
            )
        conflicts = find_overlaps(parsed)
        if conflicts:
            return results.blocked(
                "register_spaces",
                "Space 面積重疊（同一樓層），已停止。衝突：%s" % "、".join("%s/%s" % pair for pair in conflicts),
                blocking=("space_overlap",),
                command_id=command_id,
                details={"conflicts": conflicts},
            )
        for item in parsed:
            oid = item["object_id"]
            write_text(current, oid, SPACE_ID_KEY, item["space_id"])
            write_text(current, oid, LEVEL_ID_KEY, item["level_id"])
            write_text(current, oid, SPACE_DISPLAY_KEY, item["space_display"])
            current.set_object_name(oid, item["space_display"])
            if current.object_layer(oid) != SPACE_BOUNDARY_LAYER:
                current.ensure_layer(SPACE_BOUNDARY_LAYER)
                current.set_object_layer(oid, SPACE_BOUNDARY_LAYER)
        cross_level = find_xy_overlaps_other_level(parsed)
        payload = {
            "space_ids": tuple(item["space_id"] for item in parsed),
            "count": len(parsed),
            "level_ids": tuple(sorted(set(item["level_id"] for item in parsed))),
            "xy_overlap_other_level": cross_level,
        }
        message = "已登記 %s 個 Space Boundary。未改模型物件空間欄。" % len(parsed)
        if cross_level:
            warning = (
                "平面重疊但樓層不同（已允許）：%s。同樓層請用同一個樓層 ID。"
                % "、".join("%s/%s" % pair for pair in cross_level)
            )
            return results.ok_with_warnings(
                "register_spaces",
                message,
                (warning,),
                command_id=command_id,
                details=payload,
            )
        return results.ok(
            "register_spaces",
            message,
            command_id=command_id,
            details=payload,
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)
