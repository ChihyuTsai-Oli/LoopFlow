# -*- coding: utf-8 -*-
"""Rhino 物件 UserText：編號中文 key（面板依編號排序），JSON 仍用英文。

`_01`～`_08` 對齊 Dictionary 圖面欄，一個編號只給一個 key。
可手動欄的鍵名帶 `*`：物件上是 `_02`／`_08`，空間框是 `_01*`，高程框是 `_15*`。
物件 `_01_空間名稱` 由 Apply 寫入，不加 `*`。Dictionary Excel 欄名不加 `*`。
`Q_01`～`Q_06` 是數量欄，留在 Dictionary 給後續 GH 使用，2.0 不寫進物件。
Dictionary 沒有的內部欄位從 `_09` 起。
"""
from __future__ import annotations

from typing import Optional, Tuple

SPACE_DISPLAY_KEY = "_01_空間名稱"
SPACE_FRAME_DISPLAY_KEY = "_01_空間名稱*"
CONSTRUCTION_KEY = "_02_建構狀態*"
TYPE_ID_KEY = "_03_ID編號"
ELEVATION_BASIS_KEY = "_05_高程基準"
ELEVATION_VALUE_KEY = "_06_高程計算"
OBJECT_ID_KEY = "_07_UUID"
REMARKS_KEY = "_08_備註*"

SPACE_ID_KEY = "_09_空間ID"
LEVEL_ID_KEY = "_10_樓層ID"
TYPE_CATEGORY_KEY = "_11_類型類別"
TYPE_SEQUENCE_KEY = "_12_類型序號"
ELEVATION_DISPLAY_KEY = "_13_高程顯示"
DATA_REVISION_KEY = "_14_資料版次"
LEVEL_DATUM_KEY = "_15_樓層高程*"

# 讀得到、寫入時清掉的舊 key：1.x 的 `lf_*`，以及 2.0 開發期改過編號的過渡 key。
LEGACY_KEYS = {
    SPACE_DISPLAY_KEY: (SPACE_FRAME_DISPLAY_KEY, "lf_space_display"),
    SPACE_FRAME_DISPLAY_KEY: (SPACE_DISPLAY_KEY, "lf_space_display"),
    CONSTRUCTION_KEY: ("_02_建構狀態", "lf_construction_status"),
    TYPE_ID_KEY: ("lf_type_id",),
    ELEVATION_BASIS_KEY: ("_10_高程基準", "lf_elevation_basis"),
    ELEVATION_VALUE_KEY: ("_11_高程計算", "lf_elevation_value"),
    OBJECT_ID_KEY: ("_12_UUID", "lf_object_id"),
    REMARKS_KEY: ("_08_備註", "_13_備註", "lf_remarks"),
    SPACE_ID_KEY: ("_01_空間ID", "_14_空間ID", "lf_space_id"),
    LEVEL_ID_KEY: ("_01_樓層ID", "_15_樓層ID", "lf_level_id"),
    TYPE_CATEGORY_KEY: ("_03_類型類別", "_16_類型類別", "lf_type_category"),
    TYPE_SEQUENCE_KEY: ("_03_類型序號", "_17_類型序號", "lf_type_sequence"),
    ELEVATION_DISPLAY_KEY: ("_11_高程顯示", "_18_高程顯示", "lf_elevation_display"),
    DATA_REVISION_KEY: ("_15_資料版次", "_20_資料版次", "lf_data_revision"),
    LEVEL_DATUM_KEY: ("_15_樓層高程", "lf_level_datum"),
}

# 2.0 不再寫尺寸／數量／座標框；Apply 時清掉面板上的殘留。
# 3D 物件 instance 欄；結構層 Apply 時整組清掉。不含框線專用 `_01*`／`_15*`。
OBJECT_INSTANCE_KEYS = (
    SPACE_DISPLAY_KEY,
    CONSTRUCTION_KEY,
    TYPE_ID_KEY,
    ELEVATION_BASIS_KEY,
    ELEVATION_VALUE_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    SPACE_ID_KEY,
    LEVEL_ID_KEY,
    TYPE_CATEGORY_KEY,
    TYPE_SEQUENCE_KEY,
    ELEVATION_DISPLAY_KEY,
    DATA_REVISION_KEY,
)

STALE_OBJECT_KEYS = (
    "_05_寬度W",
    "_06_深度D",
    "_07_高度H",
    "_09_實作數量",
    "_14_座標框",
    "_19_座標框",
    "Q_01_寬度W",
    "Q_02_深度D",
    "Q_03_高度H",
    "Q_06_實作數量",
    "lf_dimension_w",
    "lf_dimension_d",
    "lf_dimension_h",
    "lf_quantity",
    "lf_local_frame",
)


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


def clear_stale_object_text(session, object_id: str) -> None:
    for key in STALE_OBJECT_KEYS:
        if session.get_object_user_text(object_id, key) not in (None, ""):
            session.set_object_user_text(object_id, key, "")


def clear_object_metadata(session, object_id: str) -> None:
    """清掉 3D 物件 canonical／舊鍵／尺寸殘留。不碰圖層 UserText。"""
    clear_stale_object_text(session, object_id)
    for key in OBJECT_INSTANCE_KEYS:
        session.set_object_user_text(object_id, key, "")
        for legacy in legacy_keys(key):
            if legacy != key:
                session.set_object_user_text(object_id, legacy, "")
