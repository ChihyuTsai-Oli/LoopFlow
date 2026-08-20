# -*- coding: utf-8 -*-
"""固定 2D↔3D View transform。登記時寫死，Laser 不再靠名稱重算 bbox。"""
from __future__ import annotations

import json
import math
from typing import Mapping, Optional, Sequence, Tuple

from loopflow.features.view.keys import TRANSFORM_SCHEMA_ID, TRANSFORM_SCHEMA_VERSION

TRANSFORM_KEYS = (
    "schema_id",
    "schema_version",
    "origin_2d",
    "origin_3d_local",
    "scale_x",
    "scale_y",
    "cp_origin",
    "cp_x_axis",
    "cp_y_axis",
    "cp_z_axis",
)


def _vec(values, size: int) -> Optional[Tuple[float, ...]]:
    if values is None or len(values) < size:
        return None
    try:
        return tuple(float(values[i]) for i in range(size))
    except (TypeError, ValueError):
        return None


def _len(vec) -> float:
    return math.sqrt(sum(x * x for x in vec))


def _unit_ok(vec) -> bool:
    return abs(_len(vec) - 1.0) < 1e-6


def _ortho_ok(a, b) -> bool:
    return abs(sum(x * y for x, y in zip(a, b))) < 1e-6


def _dot(a, b) -> float:
    return sum(float(x) * float(y) for x, y in zip(a, b))


def facing_direction(payload: Mapping, model_center) -> Tuple[float, float, float]:
    """射線朝向帶 UUID 的 3D 模型所在側；幾乎共面維持原 CP 法線。"""
    z_axis = (
        float(payload["cp_z_axis"][0]),
        float(payload["cp_z_axis"][1]),
        float(payload["cp_z_axis"][2]),
    )
    center = _vec(model_center, 3)
    origin = _vec(payload.get("cp_origin"), 3)
    if center is None or origin is None:
        return z_axis
    rel = (
        center[0] - origin[0],
        center[1] - origin[1],
        center[2] - origin[2],
    )
    side = _dot(rel, z_axis)
    if abs(side) < 1e-6:
        return z_axis
    if side < 0:
        return (-z_axis[0], -z_axis[1], -z_axis[2])
    return z_axis


def bbox_center_2d(box) -> Optional[Tuple[float, float, float]]:
    values = _vec(box, 6)
    if values is None:
        return None
    return (
        (values[0] + values[3]) * 0.5,
        (values[1] + values[4]) * 0.5,
        values[2],
    )


def bbox_center_local(box) -> Optional[Tuple[float, float]]:
    values = _vec(box, 4)
    if values is None:
        return None
    return ((values[0] + values[2]) * 0.5, (values[1] + values[3]) * 0.5)


def build_transform(
    *,
    origin_2d: Sequence[float],
    origin_3d_local: Sequence[float],
    scale_x: float,
    scale_y: float,
    plane: Mapping[str, Sequence[float]],
) -> dict:
    return {
        "schema_id": TRANSFORM_SCHEMA_ID,
        "schema_version": TRANSFORM_SCHEMA_VERSION,
        "origin_2d": [float(v) for v in origin_2d[:3]],
        "origin_3d_local": [float(v) for v in origin_3d_local[:2]],
        "scale_x": float(scale_x),
        "scale_y": float(scale_y),
        "cp_origin": [float(v) for v in plane["origin"][:3]],
        "cp_x_axis": [float(v) for v in plane["x_axis"][:3]],
        "cp_y_axis": [float(v) for v in plane["y_axis"][:3]],
        "cp_z_axis": [float(v) for v in plane["z_axis"][:3]],
    }


def transform_ok(payload) -> bool:
    if not isinstance(payload, dict):
        return False
    if payload.get("schema_id") != TRANSFORM_SCHEMA_ID:
        return False
    if payload.get("schema_version") != TRANSFORM_SCHEMA_VERSION:
        return False
    if set(payload) != set(TRANSFORM_KEYS):
        return False
    try:
        scale_x = float(payload["scale_x"])
        scale_y = float(payload["scale_y"])
    except (TypeError, ValueError):
        return False
    if abs(abs(scale_x) - 1.0) > 1e-9 or abs(abs(scale_y) - 1.0) > 1e-9:
        return False
    if _vec(payload.get("origin_2d"), 3) is None:
        return False
    if _vec(payload.get("origin_3d_local"), 2) is None:
        return False
    axes = [
        _vec(payload.get("cp_origin"), 3),
        _vec(payload.get("cp_x_axis"), 3),
        _vec(payload.get("cp_y_axis"), 3),
        _vec(payload.get("cp_z_axis"), 3),
    ]
    if any(item is None for item in axes):
        return False
    x_axis, y_axis, z_axis = axes[1], axes[2], axes[3]
    if not (_unit_ok(x_axis) and _unit_ok(y_axis) and _unit_ok(z_axis)):
        return False
    return _ortho_ok(x_axis, y_axis) and _ortho_ok(x_axis, z_axis) and _ortho_ok(y_axis, z_axis)


def encode_transform(payload: Mapping) -> str:
    return json.dumps(dict(payload), ensure_ascii=True, separators=(",", ":"))


def decode_transform(text: Optional[str]):
    if text in (None, ""):
        return None
    try:
        payload = json.loads(text)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not transform_ok(payload):
        return None
    return payload


def map_2d_to_cp_local(payload: Mapping, point_2d: Sequence[float]) -> Tuple[float, float]:
    """把 2D 模型點映到 CP 局部 XY，對齊 1.x Laser 的 dx／dy。"""
    origin = payload["origin_2d"]
    local = payload["origin_3d_local"]
    dx = (float(point_2d[0]) - float(origin[0])) * float(payload["scale_x"])
    dy = (float(point_2d[1]) - float(origin[1])) * float(payload["scale_y"])
    return (float(local[0]) + dx, float(local[1]) + dy)


def ray_from_transform(payload: Mapping, point_2d: Sequence[float]):
    """固定 transform：2D 點 → 射線原點與 CP 法線。"""
    local_x, local_y = map_2d_to_cp_local(payload, point_2d)
    origin = payload["cp_origin"]
    x_axis = payload["cp_x_axis"]
    y_axis = payload["cp_y_axis"]
    z_axis = payload["cp_z_axis"]
    world = (
        float(origin[0]) + local_x * float(x_axis[0]) + local_y * float(y_axis[0]),
        float(origin[1]) + local_x * float(x_axis[1]) + local_y * float(y_axis[1]),
        float(origin[2]) + local_x * float(x_axis[2]) + local_y * float(y_axis[2]),
    )
    direction = (float(z_axis[0]), float(z_axis[1]), float(z_axis[2]))
    return world, direction
