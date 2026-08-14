# -*- coding: utf-8 -*-
"""Rhino 物件 UserText：編號中文 key（面板依編號排序），JSON 仍用英文。

`_01`～`_13` 與 Dictionary 顯示欄一對一，每個編號只對應一個 key；
Dictionary 沒有的內部欄位放在 `_14` 之後，避免面板出現重複編號。
"""
from __future__ import annotations

from typing import Optional, Tuple

# 對齊 Dictionary 顯示欄（_08_單位 與 (單位計量規則) 是 Type 規則，不下放到物件）。
SPACE_DISPLAY_KEY = "_01_空間名稱"
CONSTRUCTION_KEY = "_02_建構狀態"
TYPE_ID_KEY = "_03_ID編號"
DIM_W_KEY = "_05_寬度W"
DIM_D_KEY = "_06_深度D"
DIM_H_KEY = "_07_高度H"
QUANTITY_KEY = "_09_實作數量"
ELEVATION_BASIS_KEY = "_10_高程基準"
ELEVATION_VALUE_KEY = "_11_高程計算"
OBJECT_ID_KEY = "_12_UUID"
REMARKS_KEY = "_13_備註"

# Dictionary 沒有對應欄的內部欄位，接在顯示欄之後編號。
SPACE_ID_KEY = "_14_空間ID"
LEVEL_ID_KEY = "_15_樓層ID"
TYPE_CATEGORY_KEY = "_16_類型類別"
TYPE_SEQUENCE_KEY = "_17_類型序號"
ELEVATION_DISPLAY_KEY = "_18_高程顯示"
FRAME_KEY = "_19_座標框"
DATA_REVISION_KEY = "_20_資料版次"

# 讀得到、寫入時清掉的舊 key：1.x 的 `lf_*`，以及 2.0 開發中編號重複的過渡 key。
LEGACY_KEYS = {
    SPACE_DISPLAY_KEY: ("lf_space_display",),
    CONSTRUCTION_KEY: ("lf_construction_status",),
    TYPE_ID_KEY: ("lf_type_id",),
    DIM_W_KEY: ("lf_dimension_w",),
    DIM_D_KEY: ("lf_dimension_d",),
    DIM_H_KEY: ("lf_dimension_h",),
    QUANTITY_KEY: ("lf_quantity",),
    ELEVATION_BASIS_KEY: ("lf_elevation_basis",),
    ELEVATION_VALUE_KEY: ("lf_elevation_value",),
    OBJECT_ID_KEY: ("lf_object_id",),
    REMARKS_KEY: ("lf_remarks",),
    SPACE_ID_KEY: ("_01_空間ID", "lf_space_id"),
    LEVEL_ID_KEY: ("_01_樓層ID", "lf_level_id"),
    TYPE_CATEGORY_KEY: ("_03_類型類別", "lf_type_category"),
    TYPE_SEQUENCE_KEY: ("_03_類型序號", "lf_type_sequence"),
    ELEVATION_DISPLAY_KEY: ("_11_高程顯示", "lf_elevation_display"),
    FRAME_KEY: ("_14_座標框", "lf_local_frame"),
    DATA_REVISION_KEY: ("_15_資料版次", "lf_data_revision"),
}


def legacy_keys(key: str) -> Tuple[str, ...]:
    return LEGACY_KEYS.get(key, ())


def read_text(session, object_id: str, key: str) -> Optional[str]:
    value = session.get_object_user_text(object_id, key)
    if value not in (None, ""):
        return value
    for legacy in legacy_keys(key):
        value = session.get_object_user_text(object_id, legacy)
        if value not in (None, ""):
            return value
    return None


def write_text(session, object_id: str, key: str, value: str) -> None:
    session.set_object_user_text(object_id, key, value)
    for legacy in legacy_keys(key):
        if legacy != key:
            session.set_object_user_text(object_id, legacy, "")
