# -*- coding: utf-8 -*-
"""Type layer 路徑規則。Dictionary 存相對 path，Rhino 使用 M3D:: 完整 path。"""
from __future__ import annotations

from typing import Sequence, Tuple

LAYER_PREFIX_3D = "M3D"
DATA_LAYER = "M3D::_Data"
DW_PLAN_LAYER = "M3D::20_DW"
SYSTEM_LAYERS = (
    "M3D::_Data::Space_Boundaries",
    "M3D::_Data::Level_Boundaries_FFL",
    "M3D::_Data::Level_Boundaries_FL",
)
DNA_REF_PREFIX = "DNA_REF_"
LAYER_TYPE_ID_KEY = "lf_type_id"
LAYER_CONSTRUCTION_KEY = "lf_construction_default"
# 顯示色依 1.x COLOR_LAYER_MAP：圖層代號前綴，不是 Dictionary 欄位。
COLOR_DATA_LAYER = (0, 0, 0)
COLOR_LAYER_MAP = {
    "furniture": (190, 190, 190),
    "00": (202, 16, 16),
    "01": (119, 219, 225),
    "02": (219, 179, 120),
    "03": (116, 219, 153),
    "04": (187, 153, 244),
    "05": (236, 216, 110),
    "06": (233, 137, 229),
    "07": (215, 76, 110),
    "08": (62, 97, 255),
    "09": (210, 105, 30),
    "10": (228, 80, 72),
    "20": (206, 255, 0),
}


def to_full_path(relative: str) -> str:
    text = relative or ""
    if not text:
        return LAYER_PREFIX_3D
    if text == LAYER_PREFIX_3D or text.startswith(LAYER_PREFIX_3D + "::"):
        return text
    return LAYER_PREFIX_3D + "::" + text


def to_relative_path(full: str) -> str:
    prefix = LAYER_PREFIX_3D + "::"
    if full.startswith(prefix):
        return full[len(prefix):]
    if full == LAYER_PREFIX_3D:
        return ""
    return full


def ancestor_paths(full: str) -> Tuple[str, ...]:
    parts = full.split("::")
    paths = []
    for index in range(len(parts)):
        paths.append("::".join(parts[: index + 1]))
    return tuple(paths)


def is_dw_child(full: str) -> bool:
    return full.startswith(DW_PLAN_LAYER + "::")


def is_system_layer(full: str) -> bool:
    return full == DATA_LAYER or full in SYSTEM_LAYERS


def is_parent_path(full: str, all_paths: Sequence[str]) -> bool:
    prefix = full + "::"
    return any(path.startswith(prefix) for path in all_paths)


def dna_ref_name(type_id: str) -> str:
    return DNA_REF_PREFIX + type_id


def color_for_layer_path(full: str) -> Tuple[int, int, int]:
    """依完整圖層路徑回傳顯示 RGB。系統層為黑；其餘取第一個已知代號前綴。"""
    path = full or ""
    if is_system_layer(path) or path == DATA_LAYER or path.startswith(DATA_LAYER + "::"):
        return COLOR_DATA_LAYER
    color = COLOR_LAYER_MAP["furniture"] if "_Furniture" in path else COLOR_DATA_LAYER
    for part in path.split("::"):
        prefix = part.split("_")[0]
        if prefix in COLOR_LAYER_MAP:
            return COLOR_LAYER_MAP[prefix]
    return color


def is_exportable_type_layer(full: str, all_paths: Sequence[str]) -> bool:
    if not full.startswith(LAYER_PREFIX_3D):
        return False
    if is_system_layer(full) or is_dw_child(full):
        return False
    if full == DW_PLAN_LAYER:
        return True
    return not is_parent_path(full, all_paths)
