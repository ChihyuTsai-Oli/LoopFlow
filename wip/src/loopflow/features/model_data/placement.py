# -*- coding: utf-8 -*-
"""Space 命中與高程。不猜尺寸、不 silent 取第一個重疊 Space。"""
from __future__ import annotations

from typing import List, Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary.layer_paths import to_relative_path
from loopflow.features.dictionary.loader import TypeCatalog, load_from_workfiles
from loopflow.features.model_data.identity import iter_scan_targets
from loopflow.features.model_data.space import (
    SPACE_BOUNDARY_LAYER,
    SPACE_DISPLAY_KEY,
    SPACE_ID_KEY,
    UUID_V4_RE,
    point_in_polygon,
)
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ELEVATION_VALUE_KEY,
    TYPE_ID_KEY,
    read_text,
    write_text,
)
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
ALLOWED_BASES = ("BH", "TH", "CH", "BC")
EXT_ID = "EXT"
EXT_NO_LAYER = "no_boundary_layer"
EXT_EMPTY_LAYER = "layer_without_boundary"
EXT_NO_BBOX = "bbox_unavailable"
EXT_MISS = "outside_all_boundaries"


def _format_elev(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    text = ("%.6f" % value).rstrip("0").rstrip(".")
    return text


def collect_spaces(session: RhinoSession) -> Tuple[Optional[str], Tuple[dict, ...]]:
    """收集 Space_Boundaries 圖層上已登記的封閉曲線。登記時會把曲線搬到該圖層。"""
    found = []
    seen = set()
    if not session.has_layer(SPACE_BOUNDARY_LAYER):
        return EXT_NO_LAYER, ()
    for object_id in session.objects_on_layer(SPACE_BOUNDARY_LAYER) or ():
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
                "space_display": read_text(session, object_id, SPACE_DISPLAY_KEY)
                or session.object_name(object_id)
                or space_id,
                "polygon": polygon,
            }
        )
    if not found:
        return EXT_EMPTY_LAYER, ()
    return None, tuple(found)


def hit_space(point, spaces: Sequence[dict]) -> Tuple[Optional[dict], Optional[str]]:
    """XY 命中多邊形內部。多筆時不取第一個。"""
    matches = [space for space in spaces if point_in_polygon(space["polygon"], point[0], point[1])]
    if not matches:
        return None, EXT_MISS
    if len(matches) > 1:
        return None, "ambiguous_space"
    return matches[0], None


def hit_object_space(bbox, spaces: Sequence[dict]) -> Tuple[Optional[dict], Optional[str]]:
    """底面中心優先；沒命中再用四角，避免牆心落在房間外。"""
    if bbox is None or len(bbox) < 6:
        return None, EXT_NO_BBOX
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
    saw_ambiguous = False
    for point in samples:
        hit, reason = hit_space(point, spaces)
        if reason == "ambiguous_space":
            saw_ambiguous = True
            continue
        if hit is None:
            continue
        if hit["space_id"] in seen:
            continue
        seen.add(hit["space_id"])
        unique.append(hit)
    if len(unique) == 1:
        return unique[0], None
    if len(unique) > 1 or saw_ambiguous:
        return None, "ambiguous_space"
    return None, EXT_MISS


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


def _resolve_basis(session: RhinoSession, object_id: str, catalog: TypeCatalog) -> Optional[str]:
    type_id = read_text(session, object_id, TYPE_ID_KEY)
    record = catalog.by_type_id(type_id) if type_id else None
    if record is None:
        layer = session.object_layer(object_id) or ""
        record = catalog.by_layer_path(to_relative_path(layer))
    if record is None:
        return None
    return record.elevation_basis


def _load_catalog(catalog: Optional[TypeCatalog], environ) -> results.Result:
    if catalog is not None:
        return results.ok("load_dictionary", "已使用注入的 Type Catalog。", details={"catalog": catalog})
    return load_from_workfiles(environ=environ)


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
        loaded = _load_catalog(catalog, environ)
        if not loaded.ok:
            return loaded
        type_catalog = loaded.details["catalog"]
        layer_status, spaces = collect_spaces(current)
        items = []
        ext_items = []
        for object_id in iter_scan_targets(current, selected_only=selected_only):
            bbox = current.object_bbox(object_id)
            issues: List[str] = []
            space_id = EXT_ID
            space_display = EXT_ID
            ext_reason = None
            if layer_status:
                ext_reason = layer_status
            elif bbox is None:
                ext_reason = EXT_NO_BBOX
            else:
                hit, reason = hit_object_space(bbox, spaces)
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


def apply_placement(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
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
        applied = []
        remaining = []
        for item in scanned.details["items"]:
            rhino_id = item["rhino_id"]
            issues = item["issues"]
            hard = [issue for issue in issues if issue not in ("migration_th_bh",)]
            if "ambiguous_space" in hard:
                remaining.append(rhino_id)
                continue
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
