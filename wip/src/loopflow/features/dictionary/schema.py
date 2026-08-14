# -*- coding: utf-8 -*-
"""Dictionary schema_version 1 的欄位、量綱與 Type ID 拆分。"""
from __future__ import annotations

from typing import Optional, Tuple

from loopflow.foundation import results

SCHEMA_ID = "loopflow.dictionary"
SCHEMA_VERSION = 1
TITLE_ROW = "LoopFlow Dictionary v2.0"

DISPLAY_COLUMNS = (
    "__Rhino Layer",
    "_01_空間名稱",
    "_02_建構狀態",
    "_03_ID編號",
    "_04_ID名稱",
    "_05_高程基準",
    "_06_高程計算",
    "_07_UUID",
    "_08_備註",
    "Q_01_寬度W",
    "Q_02_深度D",
    "Q_03_高度H",
    "Q_04_單位",
    "Q_05_計量規則",
    "Q_06_實作數量",
)

MACHINE_KEYS = (
    "layer_path",
    "space_id",
    "construction_default",
    "type_id",
    "type_display_name",
    "elevation_basis",
    "elevation_value",
    "object_id",
    "remarks_default",
    "dimension_w",
    "dimension_d",
    "dimension_h",
    "estimation_unit",
    "measurement_rule",
    "quantity",
)

COMPUTED_DISPLAY_COLUMNS = (
    "_01_空間名稱",
    "_06_高程計算",
    "_07_UUID",
    "Q_01_寬度W",
    "Q_02_深度D",
    "Q_03_高度H",
    "Q_06_實作數量",
)

TYPE_CATEGORIES = (
    "CB",
    "CL",
    "DW",
    "EL",
    "EQ",
    "EX",
    "FL",
    "FP",
    "LS",
    "MP",
    "SA",
    "WL",
)

RULE_DIMENSIONS = {
    "COUNT": "count",
    "LEN_W": "length",
    "LEN_D": "length",
    "LEN_H": "length",
    "AREA_WD": "area",
    "AREA_WH": "area",
    "AREA_DH": "area",
    "VOL_WDH": "volume",
}

UNIT_DIMENSIONS = {
    "樘": "count",
    "片": "count",
    "組": "count",
    "台": "count",
    "座": "count",
    "cm": "length",
    "mm": "length",
    "坪": "area",
    "才": "area",
    "m3": "volume",
}

ELEVATION_BASES = ("BH", "TH", "CH", "BC")

DISPLAY_TO_MACHINE = dict(zip(DISPLAY_COLUMNS, MACHINE_KEYS))
MACHINE_TO_DISPLAY = dict(zip(MACHINE_KEYS, DISPLAY_COLUMNS))
_CATEGORY_PREFIXES = tuple(
    sorted(("%s-" % code for code in TYPE_CATEGORIES), key=len, reverse=True)
)


def classify_measurement(unit: Optional[str], rule: Optional[str]) -> str:
    """量綱檢查：pass／warn_no_quantity／block。不計算 quantity。"""
    if rule in (None, ""):
        return "warn_no_quantity"
    if rule not in RULE_DIMENSIONS:
        return "block"
    if unit not in UNIT_DIMENSIONS:
        return "block"
    if RULE_DIMENSIONS[rule] != UNIT_DIMENSIONS[unit]:
        return "block"
    return "pass"


def split_type_id(raw: Optional[str]) -> results.Result:
    """用 12 個類別碼當前綴拆分，不只切第一個 '-'。"""
    text = (raw or "").strip()
    if not text:
        return results.blocked(
            "validate_dictionary",
            "缺少 type_id。",
            blocking=("missing_type_id",),
        )
    for prefix in _CATEGORY_PREFIXES:
        if text.startswith(prefix):
            category = prefix[:-1]
            sequence = text[len(prefix):]
            if not sequence:
                return results.blocked(
                    "validate_dictionary",
                    "type_id 缺少序號：%s" % text,
                    blocking=("invalid_type_id",),
                    details={"type_id": text, "type_category": category},
                )
            return results.ok(
                "validate_dictionary",
                "已拆分 type_id",
                details={
                    "type_id": "%s-%s" % (category, sequence),
                    "type_category": category,
                    "type_sequence": sequence,
                },
            )
    return results.blocked(
        "validate_dictionary",
        "未知 type_category，無法拆分 type_id：%s" % text,
        blocking=("unknown_type_category",),
        details={"type_id": text},
    )


def is_forbidden_cb_column(name: str) -> bool:
    return name.startswith("_CB.")
