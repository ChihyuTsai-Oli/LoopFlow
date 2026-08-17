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
