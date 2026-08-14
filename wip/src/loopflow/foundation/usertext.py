# -*- coding: utf-8 -*-
"""Rhino 物件 UserText：編號中文 key（面板依類別編號排序），JSON 仍用英文。"""
from __future__ import annotations

from typing import Optional

# 編號對齊 1.x Dictionary 欄序，讓 Attribute User Text 依 _01、_02… 排列。
OBJECT_ID_KEY = "_12_UUID"
TYPE_ID_KEY = "_03_ID編號"
TYPE_CATEGORY_KEY = "_03_類型類別"
TYPE_SEQUENCE_KEY = "_03_類型序號"
CONSTRUCTION_KEY = "_02_建構狀態"
SPACE_ID_KEY = "_01_空間ID"
SPACE_DISPLAY_KEY = "_01_空間名稱"
LEVEL_ID_KEY = "_01_樓層ID"
DIM_W_KEY = "_05_寬度W"
DIM_D_KEY = "_06_深度D"
DIM_H_KEY = "_07_高度H"
QUANTITY_KEY = "_09_實作數量"
ELEVATION_BASIS_KEY = "_10_高程基準"
ELEVATION_VALUE_KEY = "_11_高程計算"
ELEVATION_DISPLAY_KEY = "_11_高程顯示"
REMARKS_KEY = "_13_備註"
FRAME_KEY = "_14_座標框"
DATA_REVISION_KEY = "_15_資料版次"

LEGACY_KEYS = {
    OBJECT_ID_KEY: "lf_object_id",
    TYPE_ID_KEY: "lf_type_id",
    TYPE_CATEGORY_KEY: "lf_type_category",
    TYPE_SEQUENCE_KEY: "lf_type_sequence",
    CONSTRUCTION_KEY: "lf_construction_status",
    SPACE_ID_KEY: "lf_space_id",
    SPACE_DISPLAY_KEY: "lf_space_display",
    LEVEL_ID_KEY: "lf_level_id",
    DIM_W_KEY: "lf_dimension_w",
    DIM_D_KEY: "lf_dimension_d",
    DIM_H_KEY: "lf_dimension_h",
    QUANTITY_KEY: "lf_quantity",
    ELEVATION_BASIS_KEY: "lf_elevation_basis",
    ELEVATION_VALUE_KEY: "lf_elevation_value",
    ELEVATION_DISPLAY_KEY: "lf_elevation_display",
    REMARKS_KEY: "lf_remarks",
    FRAME_KEY: "lf_local_frame",
    DATA_REVISION_KEY: "lf_data_revision",
}


def read_text(session, object_id: str, key: str) -> Optional[str]:
    value = session.get_object_user_text(object_id, key)
    if value not in (None, ""):
        return value
    legacy = LEGACY_KEYS.get(key)
    if legacy:
        return session.get_object_user_text(object_id, legacy)
    return None


def write_text(session, object_id: str, key: str, value: str) -> None:
    session.set_object_user_text(object_id, key, value)
    legacy = LEGACY_KEYS.get(key)
    if legacy and legacy != key:
        session.set_object_user_text(object_id, legacy, "")
