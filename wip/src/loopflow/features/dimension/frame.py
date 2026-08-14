# -*- coding: utf-8 -*-
"""local frame 驗證、沿用與推導。禁止 World bbox 猜測。"""
from __future__ import annotations

import json
import math
from typing import Optional, Sequence, Tuple

from loopflow.foundation.usertext import DIM_D_KEY, DIM_H_KEY, DIM_W_KEY, FRAME_KEY, read_text

FRAME_SCHEMA_ID = "loopflow.local_frame"
FRAME_SCHEMA_VERSION = 1
METHODS = ("block_insertion", "extrusion_base", "unique_plane", "oriented_box")
ISSUE_NO_PLANE = "no_unique_plane"
ISSUE_CORRUPT = "corrupt_frame"
ISSUE_NO_BBOX = "bbox_unavailable"
ORTHO_EPS = 1e-6
UNIT_EPS = 1e-6
WORLD_Z = (0.0, 0.0, 1.0)

DERIVE_KIND = {
    "block_instance": "block_insertion",
    "extrusion": "extrusion_base",
    "planar_curve": "unique_plane",
    "planar_surface": "unique_plane",
    "oriented_box": "oriented_box",
}


def _vec(values) -> Tuple[float, float, float]:
    return (float(values[0]), float(values[1]), float(values[2]))


def _length(vector) -> float:
    return math.sqrt(sum(part * part for part in vector))


def _unit(vector) -> Optional[Tuple[float, float, float]]:
    length = _length(vector)
    if length < UNIT_EPS:
        return None
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def _dot(a, b) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _nearly_unit(vector) -> bool:
    return abs(_length(vector) - 1.0) < UNIT_EPS


def _nearly_ortho(a, b) -> bool:
    return abs(_dot(a, b)) < ORTHO_EPS


def validate_frame(frame) -> Optional[str]:
    """合法回傳 None；否則回傳 corrupt_frame。"""
    if not isinstance(frame, dict):
        return ISSUE_CORRUPT
    if frame.get("schema_id") != FRAME_SCHEMA_ID or frame.get("schema_version") != FRAME_SCHEMA_VERSION:
        return ISSUE_CORRUPT
    if frame.get("derivation_method") not in METHODS:
        return ISSUE_CORRUPT
    try:
        origin = _vec(frame["origin"])
        x_axis = _vec(frame["x_axis"])
        y_axis = _vec(frame["y_axis"])
        z_axis = _vec(frame["z_axis"])
    except (KeyError, TypeError, ValueError, IndexError):
        return ISSUE_CORRUPT
    axes = (x_axis, y_axis, z_axis)
    if not all(_nearly_unit(axis) for axis in axes):
        return ISSUE_CORRUPT
    if not (_nearly_ortho(x_axis, y_axis) and _nearly_ortho(x_axis, z_axis) and _nearly_ortho(y_axis, z_axis)):
        return ISSUE_CORRUPT
    if origin is None:
        return ISSUE_CORRUPT
    return None


def dump_frame(frame: dict) -> str:
    payload = {
        "schema_id": FRAME_SCHEMA_ID,
        "schema_version": FRAME_SCHEMA_VERSION,
        "origin": list(_vec(frame["origin"])),
        "x_axis": list(_vec(frame["x_axis"])),
        "y_axis": list(_vec(frame["y_axis"])),
        "z_axis": list(_vec(frame["z_axis"])),
        "derivation_method": frame["derivation_method"],
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def parse_frame(raw: Optional[str]) -> Tuple[Optional[dict], Optional[str]]:
    if raw in (None, ""):
        return None, None
    try:
        frame = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None, ISSUE_CORRUPT
    issue = validate_frame(frame)
    if issue:
        return None, issue
    return frame, None


def identity_frame(method: str) -> dict:
    return {
        "schema_id": FRAME_SCHEMA_ID,
        "schema_version": FRAME_SCHEMA_VERSION,
        "origin": [0.0, 0.0, 0.0],
        "x_axis": [1.0, 0.0, 0.0],
        "y_axis": [0.0, 1.0, 0.0],
        "z_axis": [0.0, 0.0, 1.0],
        "derivation_method": method,
    }


def _cross(a, b) -> Tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _flip(vector):
    return (-vector[0], -vector[1], -vector[2])


def axes_from_plane(origin, x_axis, y_axis, z_axis, *, normal_is_depth: bool = False):
    """組成正交單位軸。高對齊世界垂直軸；唯一平面時深對齊法線。"""
    origin_v = _vec(origin)
    ux, uy, uz = _unit(_vec(x_axis)), _unit(_vec(y_axis)), _unit(_vec(z_axis))
    if ux is None or uy is None or uz is None:
        return None
    if normal_is_depth:
        normal = uz
        if abs(_dot(normal, WORLD_Z)) > 0.999:
            z_out = normal if _dot(normal, WORLD_Z) > 0 else _flip(normal)
            y_out = uy
            x_out = _unit(_cross(y_out, z_out)) or ux
            y_out = _unit(_cross(z_out, x_out))
            x_out = _unit(_cross(y_out, z_out))
        else:
            z_out = WORLD_Z
            y_out = normal
            x_out = _unit(_cross(y_out, z_out))
            if x_out is None:
                x_out = ux
            y_out = _unit(_cross(z_out, x_out))
            x_out = _unit(_cross(y_out, z_out))
        if x_out is None or y_out is None:
            return None
        return (origin_v, x_out, y_out, z_out)
    axes = (ux, uy, uz)
    idx = max(range(3), key=lambda i: abs(_dot(axes[i], WORLD_Z)))
    z_out = axes[idx]
    if _dot(z_out, WORLD_Z) < 0:
        z_out = _flip(z_out)
    remaining = [axes[i] for i in range(3) if i != idx]
    x_out = remaining[0]
    y_out = _unit(_cross(z_out, x_out))
    if y_out is None:
        x_out = remaining[1]
        y_out = _unit(_cross(z_out, x_out))
    if y_out is None:
        return None
    x_out = _unit(_cross(y_out, z_out))
    if x_out is None:
        return None
    return (origin_v, x_out, y_out, z_out)


def frame_from_axes(origin, x_axis, y_axis, z_axis, method: str) -> Optional[dict]:
    ux, uy, uz = _unit(_vec(x_axis)), _unit(_vec(y_axis)), _unit(_vec(z_axis))
    if ux is None or uy is None or uz is None:
        return None
    frame = {
        "schema_id": FRAME_SCHEMA_ID,
        "schema_version": FRAME_SCHEMA_VERSION,
        "origin": list(_vec(origin)),
        "x_axis": list(ux),
        "y_axis": list(uy),
        "z_axis": list(uz),
        "derivation_method": method,
    }
    if validate_frame(frame):
        return None
    return frame


def dimensions_in_frame(frame: dict, bbox: Sequence[float]) -> Optional[Tuple[float, float, float]]:
    if bbox is None or len(bbox) < 6:
        return None
    xmin, ymin, zmin, xmax, ymax, zmax = [float(v) for v in bbox[:6]]
    origin = _vec(frame["origin"])
    axes = (_vec(frame["x_axis"]), _vec(frame["y_axis"]), _vec(frame["z_axis"]))
    corners = []
    for x in (xmin, xmax):
        for y in (ymin, ymax):
            for z in (zmin, zmax):
                rel = (x - origin[0], y - origin[1], z - origin[2])
                corners.append(tuple(_dot(rel, axis) for axis in axes))
    if not corners:
        return None
    xs = [pt[0] for pt in corners]
    ys = [pt[1] for pt in corners]
    zs = [pt[2] for pt in corners]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))


def resolve_frame(session, object_id: str, *, rederive: bool = False) -> dict:
    """沿用合法舊框；否則依幾何推導。不使用 World bbox。"""
    stored_raw = read_text(session, object_id, FRAME_KEY)
    stored, stored_issue = parse_frame(stored_raw)
    if stored_issue:
        return {"frame": None, "status": "block", "reason": stored_issue, "reused": False}
    if stored is not None and not rederive:
        return {"frame": stored, "status": "reuse", "reason": None, "reused": True}
    kind = session.geometry_kind(object_id)
    method = DERIVE_KIND.get(kind or "")
    if method is None:
        if stored is not None:
            return {"frame": stored, "status": "reuse", "reason": ISSUE_NO_PLANE, "reused": True}
        return {"frame": None, "status": "block", "reason": ISSUE_NO_PLANE, "reused": False}
    derived = session.derive_local_frame(object_id)
    if derived is None or validate_frame(derived):
        if stored is not None:
            return {"frame": stored, "status": "reuse", "reason": ISSUE_NO_PLANE, "reused": True}
        return {"frame": None, "status": "block", "reason": ISSUE_NO_PLANE, "reused": False}
    derived = dict(derived)
    derived["derivation_method"] = method
    return {"frame": derived, "status": "derive", "reason": None, "reused": False}
