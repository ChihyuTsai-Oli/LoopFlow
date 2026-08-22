# -*- coding: utf-8 -*-
"""Space Boundary：封閉曲線建立穩定空間身分。不改模型物件的空間欄。"""
from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from loopflow.features.dictionary.layer_paths import (
    DNA_REF_PREFIX,
    SYSTEM_LAYERS,
    read_layer_prefix,
    system_layers,
)
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    LEVEL_DATUM_KEY,
    LEVEL_ID_KEY,
    SPACE_DISPLAY_KEY,
    SPACE_FRAME_DISPLAY_KEY,
    SPACE_ID_KEY,
    read_text,
    write_text,
)
from loopflow.foundation.version import check_schema
from loopflow.platform.rhino.session import RhinoSession, run_guarded
from loopflow.platform.rhino.state import ObjectViewState
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Nexus"
SCHEMA_ID = "loopflow.space"
SPACE_BOUNDARY_LAYER = SYSTEM_LAYERS[0]
LEVEL_BOUNDARY_LAYERS = SYSTEM_LAYERS[1:3]
LEVEL_FFL_LAYER = SYSTEM_LAYERS[1]
# 模型單位；文件建議 cm 時即 ±20 cm。
LEVEL_Z_TOLERANCE = 20.0
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@dataclass(frozen=True)
class SpaceDraft:
    object_id: str
    space_display: str
    level_id: str
    space_id: Optional[str] = None


@dataclass(frozen=True)
class LevelFrame:
    object_id: str
    polygon: tuple
    curve_z: float
    datum: float
    layer: str
    prefer_ffl: bool
    level_id: Optional[str] = None


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


def _point_on_segment(px: float, py: float, ax: float, ay: float, bx: float, by: float, eps: float = 1e-6) -> bool:
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 < eps * eps:
        return abs(px - ax) <= eps and abs(py - ay) <= eps
    t = ((px - ax) * dx + (py - ay) * dy) / length2
    if t < -eps or t > 1.0 + eps:
        return False
    qx = ax + t * dx
    qy = ay + t * dy
    return abs(px - qx) <= eps and abs(py - qy) <= eps


def point_on_polygon_edge(polygon, x: float, y: float) -> bool:
    pts = [_xy(pt) for pt in polygon]
    if len(pts) < 2:
        return False
    j = len(pts) - 1
    for i, (xi, yi) in enumerate(pts):
        xj, yj = pts[j]
        if _point_on_segment(x, y, xi, yi, xj, yj):
            return True
        j = i
    return False


def polygon_inside(inner, outer) -> bool:
    """內圈頂點都在外圈內或邊上（共邊可）。"""
    if not inner or not outer:
        return False
    for pt in inner:
        x, y = _xy(pt)
        if not (point_in_polygon(outer, x, y) or point_on_polygon_edge(outer, x, y)):
            return False
    return True


def parse_level_datum(name: str):
    text = (name or "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def collect_level_frames(session: RhinoSession) -> Tuple[LevelFrame, ...]:
    frames = []
    prefix = read_layer_prefix(session)
    layers = system_layers(prefix)
    ffl_layer = layers[1]
    for layer in layers[1:3]:
        if not session.has_layer(layer):
            continue
        for object_id in session.objects_on_layer(layer):
            if not session.is_closed_curve(object_id):
                continue
            polygon = session.curve_polygon(object_id)
            if not polygon or len(polygon) < 3:
                continue
            curve_z = session.curve_elevation(object_id)
            if curve_z is None:
                continue
            raw = read_text(session, object_id, LEVEL_DATUM_KEY) or session.object_name(object_id) or ""
            datum = parse_level_datum(raw)
            if datum is None:
                continue
            level_id = read_text(session, object_id, LEVEL_ID_KEY)
            if not UUID_V4_RE.match(level_id or ""):
                level_id = None
            frames.append(
                LevelFrame(
                    object_id=object_id,
                    polygon=tuple(tuple(pt) for pt in polygon),
                    curve_z=float(curve_z),
                    datum=datum,
                    layer=layer,
                    prefer_ffl=layer == ffl_layer,
                    level_id=level_id,
                )
            )
    return tuple(frames)


def match_level_frame(polygon, space_z: float, frames: Sequence[LevelFrame]):
    """同高程 ±20 且空間整圈在樓層框內。同距離時優先 FFL。"""
    candidates = []
    for frame in frames:
        if abs(frame.curve_z - space_z) > LEVEL_Z_TOLERANCE + 1e-9:
            continue
        if not polygon_inside(polygon, frame.polygon):
            continue
        candidates.append(frame)
    if not candidates:
        return None, "space_not_in_level"

    def sort_key(frame: LevelFrame):
        return (abs(frame.curve_z - space_z), 0 if frame.prefer_ffl else 1, frame.object_id)

    ranked = sorted(candidates, key=sort_key)
    best = ranked[0]
    best_dz = abs(best.curve_z - space_z)
    ties = [
        frame
        for frame in ranked[1:]
        if abs(abs(frame.curve_z - space_z) - best_dz) <= 1e-9 and frame.prefer_ffl == best.prefer_ffl
    ]
    if ties:
        return None, "ambiguous_level_frame"
    return best, None


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
    """把目前選取物件當成 Space 候選；樓層框不列入，由文件上的 FFL／FL 曲線對應。"""
    drafts = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        state = session.get_view_state(object_id)
        if state is None or not state.selected:
            continue
        if session.object_layer(object_id) in system_layers(read_layer_prefix(session))[1:3]:
            continue
        display = read_text(session, object_id, SPACE_FRAME_DISPLAY_KEY) or session.object_name(
            object_id
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


def isolate_closed_curves(session: RhinoSession) -> int:
    """選線對齊 1.x：用曲線過濾，不鎖全檔物件。

    只把已鎖定／隱藏的封閉曲線解開並顯示。回傳解開數量。
    """
    redraw = getattr(session, "set_redraw_enabled", None)
    if callable(redraw):
        redraw(False)
    revealed = 0
    try:
        curve_ids = getattr(session, "iter_curve_ids", None)
        ids = curve_ids() if callable(curve_ids) else session.iter_object_ids(
            include_hidden=True, include_locked=True
        )
        for object_id in ids:
            name = session.object_name(object_id) or ""
            if name.startswith(DNA_REF_PREFIX):
                continue
            if not session.is_closed_curve(object_id):
                continue
            state = session.get_view_state(object_id)
            if state is None:
                continue
            if not state.locked and not state.hidden:
                continue
            session.set_view_state(
                ObjectViewState(
                    object_id=object_id,
                    selected=state.selected,
                    locked=False,
                    hidden=False,
                    color=state.color,
                    color_by_layer=state.color_by_layer,
                )
            )
            revealed += 1
    finally:
        if callable(redraw):
            redraw(True)
    return revealed


def register_level_boundaries(
    session: RhinoSession,
    object_ids: Sequence[str],
    *,
    kind: str,
    datum: str,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """把封閉曲線登記為高程框。高程寫入 `_15_樓層高程`，曲線搬到 FFL 或 FL。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "register_levels",
                t("nexus_metadata.023"),
                command_id=command_id,
            )
        chosen = (kind or "").strip().upper()
        if chosen not in ("FFL", "FL"):
            return results.blocked(
                "register_levels",
                t("nexus_metadata.024"),
                blocking=("invalid_level_kind",),
                command_id=command_id,
            )
        display = (datum or "").strip()
        if parse_level_datum(display) is None:
            return results.blocked(
                "register_levels",
                t("nexus_metadata.025"),
                blocking=("invalid_level_datum",),
                command_id=command_id,
            )
        ids = tuple(object_ids)
        if not ids:
            return results.blocked(
                "register_levels",
                t("nexus_metadata.026"),
                blocking=("missing_level_selection",),
                command_id=command_id,
            )
        invalid = []
        parsed = []
        for object_id in ids:
            if not current.is_closed_curve(object_id):
                invalid.append(object_id)
                continue
            polygon = current.curve_polygon(object_id)
            if not polygon or len(polygon) < 3:
                invalid.append(object_id)
                continue
            parsed.append(object_id)
        if invalid:
            return results.blocked(
                "register_levels",
                t("nexus_metadata.032") % len(invalid),
                blocking=("invalid_level_curve",),
                command_id=command_id,
                details={"invalid_object_ids": tuple(invalid)},
            )
        prefix = read_layer_prefix(current)
        target = system_layers(prefix)[1 if chosen == "FFL" else 2]
        current.ensure_layer(target)
        written = []
        for object_id in parsed:
            level_id = read_text(current, object_id, LEVEL_ID_KEY)
            if not UUID_V4_RE.match(level_id or ""):
                level_id = _new_id()
            write_text(current, object_id, LEVEL_ID_KEY, level_id)
            write_text(current, object_id, LEVEL_DATUM_KEY, display)
            if current.object_layer(object_id) != target:
                current.set_object_layer(object_id, target)
            written.append(level_id)
        return results.ok(
            "register_levels",
            t("nexus_metadata.027") % (len(written), chosen, display),
            command_id=command_id,
            details={
                "count": len(written),
                "kind": chosen,
                "datum": display,
                "layer": target,
                "level_ids": tuple(written),
            },
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def _ask_or_live(injected, live_name: str, *args):
    if injected is not None:
        return injected(*args) if callable(injected) else injected
    from loopflow.platform.rhino import prompts
    return getattr(prompts, live_name)(*args)


def register_level_boundaries_interactive(
    session: RhinoSession,
    *,
    kind: Optional[str] = None,
    object_ids: Optional[Sequence[str]] = None,
    datum: Optional[str] = None,
    ask_kind: Optional[Callable] = None,
    pick_objects: Optional[Callable] = None,
    ask_text: Optional[Callable] = None,
    isolate: bool = True,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """先彈出清單選 FFL／FL，選線用曲線過濾（不鎖全檔），再彈出視窗輸入高程。"""

    def action(current: RhinoSession) -> results.Result:
        chosen = kind
        if chosen is None:
            if ask_kind is not None:
                chosen = ask_kind(t("nexus_metadata.033"), ("FFL", "FL"), "FFL")
            else:
                chosen = _ask_or_live(None, "ask_popup_choice", t("nexus_metadata.034"), ("FFL", "FL"))
            if chosen is None:
                return results.cancelled(
                    "register_levels",
                    t("nexus_metadata.035"),
                    command_id=command_id,
                )
        if isolate:
            isolate_closed_curves(current)
        ids = object_ids
        if ids is None:
            if pick_objects is not None:
                ids = pick_objects()
            else:
                ids = _ask_or_live(None, "pick_curves")
            if not ids:
                return results.cancelled(
                    "register_levels",
                    t("nexus_metadata.036"),
                    command_id=command_id,
                )
        text = datum
        if text is None:
            if ask_text is not None:
                text = ask_text(t("nexus_metadata.037"), "")
            else:
                text = _ask_or_live(None, "ask_popup_string", t("nexus_metadata.037"), "", "LoopFlow")
            if text is None:
                return results.cancelled(
                    "register_levels",
                    t("nexus_metadata.038"),
                    command_id=command_id,
                )
        return register_level_boundaries(
            current,
            ids,
            kind=chosen,
            datum=text,
            cancel=False,
            guarded=False,
            command_id=command_id,
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def register_space_boundaries_interactive(
    session: RhinoSession,
    *,
    object_ids: Optional[Sequence[str]] = None,
    space_name: Optional[str] = None,
    pick_objects: Optional[Callable] = None,
    ask_text: Optional[Callable] = None,
    isolate: bool = True,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """選線用曲線過濾（不鎖全檔），可複選空間框，彈出視窗輸入同一個空間名稱。"""

    def action(current: RhinoSession) -> results.Result:
        if isolate:
            isolate_closed_curves(current)
        ids = object_ids
        if ids is None:
            if pick_objects is not None:
                ids = pick_objects()
            else:
                ids = _ask_or_live(None, "pick_curves")
            if not ids:
                return results.cancelled(
                    "register_spaces",
                    t("nexus_metadata.039"),
                    command_id=command_id,
                )
        name = space_name
        if name is None:
            if ask_text is not None:
                name = ask_text(t("nexus_metadata.040"), "")
            else:
                name = _ask_or_live(None, "ask_popup_string", t("nexus_metadata.040"), "", "LoopFlow")
            if name is None:
                return results.cancelled(
                    "register_spaces",
                    t("nexus_metadata.041"),
                    command_id=command_id,
                )
        display = (name or "").strip()
        drafts = tuple(
            SpaceDraft(
                object_id=oid,
                space_display=display,
                level_id=read_text(current, oid, LEVEL_ID_KEY) or "",
                space_id=read_text(current, oid, SPACE_ID_KEY),
            )
            for oid in ids
        )
        return register_space_boundaries(
            current,
            drafts,
            cancel=False,
            guarded=False,
            command_id=command_id,
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


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
                t("nexus_metadata.028"),
                command_id=command_id,
            )
        schema = check_schema(SCHEMA_ID, 1)
        if not schema.ok:
            return schema
        if not drafts:
            return results.blocked(
                "register_spaces",
                t("nexus_metadata.029"),
                blocking=("missing_space_selection",),
                command_id=command_id,
            )
        frames = collect_level_frames(current)
        parsed = []
        invalid = []
        not_in_level = []
        ambiguous = []
        pending_level_ids = {}

        def resolve_frame_level_id(frame: LevelFrame) -> str:
            if frame.object_id in pending_level_ids:
                return pending_level_ids[frame.object_id]
            existing = read_text(current, frame.object_id, LEVEL_ID_KEY)
            if UUID_V4_RE.match(existing or ""):
                pending_level_ids[frame.object_id] = existing
                return existing
            created = _new_id()
            pending_level_ids[frame.object_id] = created
            return created

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
            space_id = draft.space_id or read_text(current, draft.object_id, SPACE_ID_KEY)
            if space_id == "EXT" or (space_id and not UUID_V4_RE.match(space_id)):
                invalid.append(draft.object_id)
                continue
            level_id = draft.level_id or ""
            if frames:
                space_z = current.curve_elevation(draft.object_id)
                if space_z is None:
                    not_in_level.append(draft.object_id)
                    continue
                hit, reason = match_level_frame(polygon, float(space_z), frames)
                if hit is None:
                    if reason == "ambiguous_level_frame":
                        ambiguous.append(draft.object_id)
                    else:
                        not_in_level.append(draft.object_id)
                    continue
                level_id = resolve_frame_level_id(hit)
            elif not UUID_V4_RE.match(level_id):
                invalid.append(draft.object_id)
                continue
            parsed.append(
                {
                    "object_id": draft.object_id,
                    "space_display": draft.space_display.strip(),
                    "level_id": level_id,
                    "space_id": space_id,
                    "polygon": polygon,
                }
            )
        if invalid:
            return results.blocked(
                "register_spaces",
                t("nexus_metadata.042") % len(invalid),
                blocking=("invalid_space_curve",),
                command_id=command_id,
                details={"invalid_object_ids": tuple(invalid)},
            )
        if ambiguous:
            return results.blocked(
                "register_spaces",
                t("nexus_metadata.043") % len(ambiguous),
                blocking=("ambiguous_level_frame",),
                command_id=command_id,
                details={"invalid_object_ids": tuple(ambiguous)},
            )
        if not_in_level:
            return results.blocked(
                "register_spaces",
                t("nexus_metadata.044")
                % (len(not_in_level), int(LEVEL_Z_TOLERANCE) if LEVEL_Z_TOLERANCE == int(LEVEL_Z_TOLERANCE) else LEVEL_Z_TOLERANCE),
                blocking=("space_not_in_level",),
                command_id=command_id,
                details={"invalid_object_ids": tuple(not_in_level)},
            )
        for item in parsed:
            if not item["space_id"]:
                item["space_id"] = _new_id()
        space_ids = [item["space_id"] for item in parsed]
        if len(space_ids) != len(set(space_ids)):
            return results.blocked(
                "register_spaces",
                t("nexus_metadata.030"),
                blocking=("duplicate_space_id",),
                command_id=command_id,
            )
        conflicts = find_overlaps(parsed)
        if conflicts:
            return results.blocked(
                "register_spaces",
                t("nexus_metadata.045") % "、".join("%s/%s" % pair for pair in conflicts),
                blocking=("space_overlap",),
                command_id=command_id,
                details={"conflicts": conflicts},
            )
        for frame_id, level_id in pending_level_ids.items():
            write_text(current, frame_id, LEVEL_ID_KEY, level_id)
        for item in parsed:
            oid = item["object_id"]
            write_text(current, oid, SPACE_ID_KEY, item["space_id"])
            write_text(current, oid, LEVEL_ID_KEY, item["level_id"])
            write_text(current, oid, SPACE_FRAME_DISPLAY_KEY, item["space_display"])
            space_layer = system_layers(read_layer_prefix(current))[0]
            if current.object_layer(oid) != space_layer:
                current.ensure_layer(space_layer)
                current.set_object_layer(oid, space_layer)
        cross_level = find_xy_overlaps_other_level(parsed)
        payload = {
            "space_ids": tuple(item["space_id"] for item in parsed),
            "count": len(parsed),
            "level_ids": tuple(sorted(set(item["level_id"] for item in parsed))),
            "xy_overlap_other_level": cross_level,
        }
        message = t("nexus_metadata.022") % len(parsed)
        if cross_level:
            warning = (
                t("nexus_metadata.031")
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
