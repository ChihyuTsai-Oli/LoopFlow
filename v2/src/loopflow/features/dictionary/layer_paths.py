# -*- coding: utf-8 -*-
"""Type layer 路徑規則。Dictionary 存相對 path，Rhino 使用「專案名稱::」完整 path。"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

LAYER_PREFIX_3D = "M3D"
DATA_SUFFIX = "_Data"
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


def normalize_layer_prefix(name: Optional[str]) -> Optional[str]:
    """專案名稱＝3D 圖層樹根。禁止空白與圖層非法字元。"""
    text = (name or "").strip()
    if not text:
        return None
    if any(ch in text for ch in ':\\/:*?<>|"'):
        return None
    return text


def project_id_from_session(session) -> Optional[str]:
    """專案身分＝圖層專案名稱，存在 .3dm 旁的專案設定檔，不在文件 UserText。"""
    if session is None:
        return None
    from loopflow.foundation.project_config import (
        LAYER_PREFIX_FIELD,
        PROJECT_ID_FIELD,
        read_config,
    )

    loaded = read_config(session)
    if not loaded.ok:
        return None
    values = loaded.details["values"]
    return normalize_layer_prefix(values.get(LAYER_PREFIX_FIELD)) or normalize_layer_prefix(
        values.get(PROJECT_ID_FIELD)
    )


def read_layer_prefix(session) -> str:
    """圖層樹前綴。設定檔還沒有 layer_prefix 時用 M3D。"""
    if session is None:
        return LAYER_PREFIX_3D
    from loopflow.foundation.project_config import LAYER_PREFIX_FIELD, read_config

    loaded = read_config(session)
    if not loaded.ok:
        return LAYER_PREFIX_3D
    stored = normalize_layer_prefix(loaded.details["values"].get(LAYER_PREFIX_FIELD))
    return stored or LAYER_PREFIX_3D


def data_layer(prefix: str = LAYER_PREFIX_3D) -> str:
    return prefix + "::" + DATA_SUFFIX


def dw_plan_layer(prefix: str = LAYER_PREFIX_3D) -> str:
    return prefix + "::20_DW"


STRUCTURE_GROUP_CODE = "00_STR"


def system_layers(prefix: str = LAYER_PREFIX_3D) -> Tuple[str, ...]:
    root = data_layer(prefix)
    return (
        root + "::Space_Boundaries",
        root + "::Level_Boundaries_FFL",
        root + "::Level_Boundaries_FL",
    )


DATA_LAYER = data_layer()
DW_PLAN_LAYER = dw_plan_layer()
SYSTEM_LAYERS = system_layers()


def to_full_path(relative: str, prefix: str = LAYER_PREFIX_3D) -> str:
    text = relative or ""
    if not text:
        return prefix
    if text == prefix or text.startswith(prefix + "::"):
        return text
    return prefix + "::" + text


def to_relative_path(full: str, prefix: str = LAYER_PREFIX_3D) -> str:
    token = prefix + "::"
    if full.startswith(token):
        return full[len(token):]
    if full == prefix:
        return ""
    return full


def material_name_for_layer(full: str, prefix: str = LAYER_PREFIX_3D) -> str:
    """材質名稱＝去掉專案前綴的相對路徑，保留一個父圖層。"""
    relative = to_relative_path(full, prefix)
    return relative or full


def ancestor_paths(full: str) -> Tuple[str, ...]:
    parts = full.split("::")
    paths = []
    for index in range(len(parts)):
        paths.append("::".join(parts[: index + 1]))
    return tuple(paths)


def is_dw_child(full: str, prefix: str = LAYER_PREFIX_3D) -> bool:
    return full.startswith(dw_plan_layer(prefix) + "::")


def is_structure_layer(full: str, prefix: str = LAYER_PREFIX_3D) -> bool:
    """相對路徑第一段代號為 00_STR（含 00_STR_結構 與子層）。"""
    relative = to_relative_path(full or "", prefix)
    if not relative:
        return False
    first = relative.split("::", 1)[0]
    return first == STRUCTURE_GROUP_CODE or first.startswith(STRUCTURE_GROUP_CODE + "_")


def is_structure_object(session, object_id: str) -> bool:
    layer = session.object_layer(object_id) or ""
    return is_structure_layer(layer, read_layer_prefix(session))


def is_system_layer(full: str, prefix: str = LAYER_PREFIX_3D) -> bool:
    root = data_layer(prefix)
    return full == root or full in system_layers(prefix)


def is_in_project(full: str, prefix: str = LAYER_PREFIX_3D) -> bool:
    return full == prefix or (full or "").startswith(prefix + "::")


def is_parent_path(full: str, all_paths: Sequence[str]) -> bool:
    token = full + "::"
    return any(path.startswith(token) for path in all_paths)


def dna_ref_name(type_id: str) -> str:
    return DNA_REF_PREFIX + type_id


def color_for_layer_path(full: str, prefix: str = LAYER_PREFIX_3D) -> Tuple[int, int, int]:
    """依完整圖層路徑回傳顯示 RGB。系統層為黑；其餘取第一個已知代號前綴。"""
    path = full or ""
    root = data_layer(prefix)
    if is_system_layer(path, prefix) or path == root or path.startswith(root + "::"):
        return COLOR_DATA_LAYER
    color = COLOR_LAYER_MAP["furniture"] if "_Furniture" in path else COLOR_DATA_LAYER
    for part in path.split("::"):
        code = part.split("_")[0]
        if code in COLOR_LAYER_MAP:
            return COLOR_LAYER_MAP[code]
    return color


def is_exportable_type_layer(full: str, all_paths: Sequence[str], prefix: str = LAYER_PREFIX_3D) -> bool:
    if not is_in_project(full, prefix):
        return False
    if is_system_layer(full, prefix) or is_dw_child(full, prefix):
        return False
    if full == dw_plan_layer(prefix):
        return True
    return not is_parent_path(full, all_paths)
