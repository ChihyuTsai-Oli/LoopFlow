# -*- coding: utf-8 -*-
"""Space 命中與高程。不猜尺寸、不 silent 取第一個重疊 Space。"""
from __future__ import annotations

from typing import Callable, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary.layer_paths import read_layer_prefix, system_layers, to_relative_path
from loopflow.features.dictionary.loader import TypeCatalog, load_from_workfiles
from loopflow.features.model_data.identity import iter_scan_targets
from loopflow.features.model_data.space import (
    SPACE_DISPLAY_KEY,
    SPACE_FRAME_DISPLAY_KEY,
    SPACE_ID_KEY,
    UUID_V4_RE,
    collect_level_frames,
    point_in_polygon,
)
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ELEVATION_VALUE_KEY,
    LEVEL_ID_KEY,
    TYPE_ID_KEY,
    read_text,
    write_text,
)
from loopflow.platform.rhino.session import RhinoSession, run_guarded
from loopflow.platform.rhino.state import ObjectViewState

COMMAND_ID = "LF_Nexus"
ALLOWED_BASES = ("BH", "TH", "CH", "BC")
EXT_ID = "EXT"
EXT_NO_LAYER = "no_boundary_layer"
EXT_EMPTY_LAYER = "layer_without_boundary"
EXT_NO_BBOX = "bbox_unavailable"
EXT_MISS = "outside_all_boundaries"
AskSpace = Callable[[str, Sequence[str]], Optional[str]]


def _format_elev(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    text = ("%.6f" % value).rstrip("0").rstrip(".")
    return text


def collect_spaces(session: RhinoSession) -> Tuple[Optional[str], Tuple[dict, ...]]:
    """收集 Space_Boundaries 圖層上已登記的封閉曲線。登記時會把曲線搬到該圖層。"""
    found = []
    seen = set()
    space_layer = system_layers(read_layer_prefix(session))[0]
    if not session.has_layer(space_layer):
        return EXT_NO_LAYER, ()
    for object_id in session.objects_on_layer(space_layer) or ():
        if object_id in seen:
            continue
        seen.add(object_id)
        space_id = read_text(session, object_id, SPACE_ID_KEY)
        if not space_id or not UUID_V4_RE.match(space_id):
            continue
        if not session.is_closed_curve(object_id):
            continue
        polygon = session.curve_polygon(object_id)
        if not polygon or len(polygon) < 3:
            continue
        found.append(
            {
                "object_id": object_id,
                "space_id": space_id,
                "space_display": read_text(session, object_id, SPACE_FRAME_DISPLAY_KEY)
                or session.object_name(object_id)
                or space_id,
                "level_id": read_text(session, object_id, LEVEL_ID_KEY) or "",
                "polygon": polygon,
            }
        )
    if not found:
        return EXT_EMPTY_LAYER, ()
    return None, tuple(found)


def has_registered_boundaries(session: RhinoSession) -> bool:
    """選單 5 前置：至少一個高程框、至少一個已登記空間框。"""
    if not collect_level_frames(session):
        return False
    _status, spaces = collect_spaces(session)
    return bool(spaces)


def hit_space(point, spaces: Sequence[dict]) -> Tuple[Optional[dict], Optional[str]]:
    """XY 命中多邊形內部。多筆時不取第一個。"""
    matches = [space for space in spaces if point_in_polygon(space["polygon"], point[0], point[1])]
    if not matches:
        return None, EXT_MISS
    if len(matches) > 1:
        return None, "ambiguous_space"
    return matches[0], None


def object_space_hits(bbox, spaces: Sequence[dict]) -> Tuple[Tuple[dict, ...], Optional[str]]:
    """底面中心與四角命中的不重複空間。多筆時回傳全部候選。"""
    if bbox is None or len(bbox) < 6:
        return (), EXT_NO_BBOX
    xmin, ymin, xmax, ymax = float(bbox[0]), float(bbox[1]), float(bbox[3]), float(bbox[4])
    samples = (
        ((xmin + xmax) / 2.0, (ymin + ymax) / 2.0),
        (xmin, ymin),
        (xmax, ymin),
        (xmin, ymax),
        (xmax, ymax),
    )
    unique = []
    seen = set()
    for point in samples:
        for space in spaces:
            if not point_in_polygon(space["polygon"], point[0], point[1]):
                continue
            if space["space_id"] in seen:
                continue
            seen.add(space["space_id"])
            unique.append(space)
    if len(unique) == 1:
        return tuple(unique), None
    if len(unique) > 1:
        return tuple(unique), "ambiguous_space"
    return (), EXT_MISS


def hit_object_space(bbox, spaces: Sequence[dict]) -> Tuple[Optional[dict], Optional[str]]:
    """底面中心優先；沒命中再用四角，避免牆心落在房間外。"""
    hits, reason = object_space_hits(bbox, spaces)
    if reason is None and hits:
        return hits[0], None
    return None, reason


def _elevation(session: RhinoSession, object_id: str, basis: Optional[str], bbox):
    if basis == "TH/BH":
        return None, "migration_th_bh"
    if basis not in ALLOWED_BASES:
        return None, "invalid_elevation_basis"
    if basis == "BC":
        if not session.is_block_instance(object_id):
            return None, "bc_on_non_block"
        insertion = session.insertion_point(object_id)
        if insertion is None:
            return None, "bbox_unavailable"
        return float(insertion[2]), None
    if bbox is None:
        return None, "bbox_unavailable"
    zmin, zmax = float(bbox[2]), float(bbox[5])
    if basis in ("BH", "CH"):
        return zmin, None
    return zmax, None


def _frames_by_level_id(session: RhinoSession) -> dict:
    mapping = {}
    for frame in collect_level_frames(session):
        level_id = frame.level_id or read_text(session, frame.object_id, LEVEL_ID_KEY)
        if level_id:
            mapping[level_id] = frame
    return mapping


def _composed_elevation(sample_z, frame) -> Optional[float]:
    if sample_z is None:
        return None
    if frame is None:
        return float(sample_z)
    return float(frame.datum) + (float(sample_z) - float(frame.curve_z))


def _frame_for_space(space: Optional[dict], frames_by_id: Mapping[str, object]):
    if not space:
        return None
    level_id = space.get("level_id") or ""
    return frames_by_id.get(level_id)


def _space_ref(space: dict) -> dict:
    return {
        "space_id": space["space_id"],
        "space_display": space["space_display"],
        "level_id": space.get("level_id") or "",
    }


def _resolve_hit(
    session: RhinoSession,
    object_id: str,
    hits: Sequence[dict],
    reason: Optional[str],
) -> Tuple[Optional[dict], Optional[str], Tuple[dict, ...]]:
    if reason != "ambiguous_space":
        if hits:
            return hits[0], None, ()
        return None, reason, ()
    refs = tuple(_space_ref(item) for item in hits)
    current_id = read_text(session, object_id, SPACE_ID_KEY)
    matched = [item for item in hits if item["space_id"] == current_id]
    if len(matched) == 1:
        return matched[0], None, refs
    return None, "ambiguous_space", refs


def _resolve_basis(session: RhinoSession, object_id: str, catalog: TypeCatalog) -> Optional[str]:
    type_id = read_text(session, object_id, TYPE_ID_KEY)
    record = catalog.by_type_id(type_id) if type_id else None
    if record is None:
        layer = session.object_layer(object_id) or ""
        record = catalog.by_layer_path(to_relative_path(layer, read_layer_prefix(session)))
    if record is None:
        return None
    return record.elevation_basis


def _load_catalog(catalog: Optional[TypeCatalog], environ, session=None) -> results.Result:
    if catalog is not None:
        return results.ok("load_dictionary", "已使用注入的 Type Catalog。", details={"catalog": catalog})
    return load_from_workfiles(environ=environ, session=session)


def scan_placement(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """掃描 Space 命中與高程。不寫入、不猜尺寸。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "scan_placement",
                "使用者取消 Space／高程 Scan。",
                command_id=command_id,
            )
        loaded = _load_catalog(catalog, environ, current)
        if not loaded.ok:
            return loaded
        type_catalog = loaded.details["catalog"]
        layer_status, spaces = collect_spaces(current)
        frames_by_id = _frames_by_level_id(current)
        items = []
        ext_items = []
        for object_id in iter_scan_targets(current, selected_only=selected_only):
            bbox = current.object_bbox(object_id)
            issues: List[str] = []
            space_id = EXT_ID
            space_display = EXT_ID
            ext_reason = None
            hit = None
            candidates: Tuple[dict, ...] = ()
            if layer_status:
                ext_reason = layer_status
            elif bbox is None:
                ext_reason = EXT_NO_BBOX
            else:
                hits, reason = object_space_hits(bbox, spaces)
                hit, reason, candidates = _resolve_hit(current, object_id, hits, reason)
                if hit is None:
                    ext_reason = reason
                    if reason == "ambiguous_space":
                        issues.append("ambiguous_space")
                        space_id = None
                        space_display = None
                    else:
                        ext_reason = EXT_MISS
                else:
                    space_id = hit["space_id"]
                    space_display = hit["space_display"]
            if ext_reason and ext_reason != "ambiguous_space":
                space_id = EXT_ID
                space_display = EXT_ID
                ext_items.append({"rhino_id": object_id, "reason": ext_reason})
            basis = _resolve_basis(current, object_id, type_catalog)
            value, elev_issue = _elevation(current, object_id, basis, bbox)
            if hit is not None:
                value = _composed_elevation(value, _frame_for_space(hit, frames_by_id))
            if elev_issue:
                issues.append(elev_issue)
            items.append(
                {
                    "rhino_id": object_id,
                    "space_id": space_id,
                    "space_display": space_display,
                    "ext_reason": ext_reason if ext_reason != "ambiguous_space" else None,
                    "elevation_basis": basis,
                    "elevation_value": value,
                    "candidate_spaces": candidates,
                    "issues": tuple(issues),
                }
            )
        blocking = []
        for item in items:
            for issue in item["issues"]:
                if issue not in blocking and issue != "migration_th_bh":
                    blocking.append(issue)
        payload = {
            "publish_ready": False,
            "items": tuple(items),
            "ext": tuple(ext_items),
            "blocking": tuple(blocking),
            "remaining": tuple(
                item["rhino_id"]
                for item in items
                if any(issue != "migration_th_bh" for issue in item["issues"])
            ),
        }
        message = "Space／高程 Scan 完成，%s 個物件、%s 個 EXT。不可發布。" % (
            len(items),
            len(ext_items),
        )
        warnings = []
        if any("migration_th_bh" in item["issues"] for item in items):
            warnings.append("migration_th_bh")
        warnings.extend(blocking)
        if warnings:
            return results.ok_with_warnings(
                "scan_placement",
                message,
                tuple(dict.fromkeys(warnings)),
                command_id=command_id,
                details=payload,
            )
        return results.ok("scan_placement", message, command_id=command_id, details=payload)

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def _select_only(session: RhinoSession, object_id: str) -> None:
    wanted = {object_id}
    for oid in session.iter_object_ids(include_hidden=True, include_locked=True):
        state = session.get_view_state(oid)
        if state is None or state.selected == (oid in wanted):
            continue
        session.set_view_state(
            ObjectViewState(
                object_id=oid,
                selected=oid in wanted,
                locked=state.locked,
                hidden=state.hidden,
                color=state.color,
                color_by_layer=state.color_by_layer,
            )
        )


def _zoom_object(session: RhinoSession, object_id: str) -> None:
    zoomer = getattr(session, "zoom_to_object", None)
    if callable(zoomer):
        zoomer(object_id)


def _ask_space_name(
    object_id: str,
    names: Sequence[str],
    ask_space: Optional[AskSpace],
) -> Optional[str]:
    if ask_space is not None:
        return ask_space(object_id, names)
    from loopflow.platform.rhino.prompts import ask_popup_choice

    return ask_popup_choice("此物件同時落在多個空間。請選擇所屬空間：", names)


def _pick_candidate(candidates: Sequence[dict], typed: Optional[str]) -> Optional[dict]:
    name = (typed or "").strip()
    if not name:
        return None
    matched = [item for item in candidates if (item.get("space_display") or "") == name]
    if len(matched) != 1:
        return None
    return matched[0]


def _unique_displays(candidates: Sequence[dict]) -> Tuple[str, ...]:
    names = []
    seen = set()
    for item in candidates:
        display = item.get("space_display") or ""
        if display in seen:
            return ()
        seen.add(display)
        names.append(display)
    return tuple(names)


def apply_placement(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
    ask_space: Optional[AskSpace] = None,
) -> results.Result:
    """寫入 lf_space_* 與高程。不寫尺寸。ambiguous／BC 非 Block 不寫該欄。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "apply_placement",
                "使用者取消 Space／高程 Apply。",
                command_id=command_id,
            )
        scanned = scan_placement(
            current,
            catalog=catalog,
            environ=environ,
            selected_only=selected_only,
            cancel=False,
            guarded=False,
            command_id=command_id,
        )
        if not scanned.ok:
            return scanned
        frames_by_id = _frames_by_level_id(current)
        applied = []
        remaining = []
        for item in scanned.details["items"]:
            rhino_id = item["rhino_id"]
            issues = item["issues"]
            hard = [issue for issue in issues if issue not in ("migration_th_bh",)]
            if "ambiguous_space" in hard:
                candidates = item.get("candidate_spaces") or ()
                names = _unique_displays(candidates)
                chosen = None
                if names:
                    _select_only(current, rhino_id)
                    _zoom_object(current, rhino_id)
                    chosen = _pick_candidate(
                        candidates,
                        _ask_space_name(rhino_id, names, ask_space),
                    )
                if chosen is None:
                    remaining.append(rhino_id)
                    continue
                item = dict(item)
                item["space_id"] = chosen["space_id"]
                item["space_display"] = chosen["space_display"]
                item["elevation_value"] = _composed_elevation(
                    item.get("elevation_value"),
                    _frame_for_space(chosen, frames_by_id),
                )
            if item["space_id"]:
                write_text(current, rhino_id, SPACE_ID_KEY, item["space_id"])
                write_text(current, rhino_id, SPACE_DISPLAY_KEY, item["space_display"])
            if item["elevation_value"] is not None and item["elevation_basis"] in ALLOWED_BASES:
                write_text(current, rhino_id, ELEVATION_BASIS_KEY, item["elevation_basis"])
                write_text(current, rhino_id, ELEVATION_VALUE_KEY, _format_elev(item["elevation_value"]))
                write_text(
                    current, rhino_id, ELEVATION_DISPLAY_KEY, _format_elev(item["elevation_value"])
                )
            elif "bc_on_non_block" in hard or "invalid_elevation_basis" in hard:
                remaining.append(rhino_id)
            applied.append(rhino_id)
        payload = {
            "publish_ready": False,
            "applied": tuple(applied),
            "remaining": tuple(dict.fromkeys(remaining)),
            "ext": scanned.details.get("ext", ()),
        }
        if remaining and not applied:
            return results.blocked(
                "apply_placement",
                "沒有可寫入的 Space／高程。",
                blocking=scanned.details.get("blocking") or ("nothing_to_apply",),
                command_id=command_id,
                details=payload,
            )
        message = "已 Apply Space／高程。不可發布。"
        if remaining:
            return results.ok_with_warnings(
                "apply_placement",
                message + " 剩餘 %s 項。" % len(payload["remaining"]),
                ("remaining_placement_work",),
                command_id=command_id,
                details=payload,
            )
        return results.ok("apply_placement", message, command_id=command_id, details=payload)

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)
