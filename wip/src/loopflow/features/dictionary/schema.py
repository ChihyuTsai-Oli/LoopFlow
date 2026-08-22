# -*- coding: utf-8 -*-
"""Dictionary schema_version 1 的欄位、量綱與 Type ID 拆分。"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from loopflow.foundation import results
from loopflow.foundation.i18n import t

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

DISPLAY_COLUMNS_EN = (
    "Rhino Layer",
    "_01_Space Name",
    "_02_Construction",
    "_03_Type ID",
    "_04_Type Name",
    "_05_Elevation Basis",
    "_06_Elevation Value",
    "_07_UUID",
    "_08_Remarks",
    "Q_01_Width W",
    "Q_02_Depth D",
    "Q_03_Height H",
    "Q_04_Unit",
    "Q_05_Measurement Rule",
    "Q_06_Quantity",
)

HEADER_DIALECT_ZH = "zh-TW"
HEADER_DIALECT_EN = "en"

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

COMPUTED_DISPLAY_COLUMNS_EN = (
    "_01_Space Name",
    "_06_Elevation Value",
    "_07_UUID",
    "Q_01_Width W",
    "Q_02_Depth D",
    "Q_03_Height H",
    "Q_06_Quantity",
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
    "m2": "area",
    "m3": "volume",
    "ea": "count",
}

ELEVATION_BASES = ("BH", "TH", "CH", "BC")

DISPLAY_TO_MACHINE = dict(zip(DISPLAY_COLUMNS, MACHINE_KEYS))
DISPLAY_TO_MACHINE.update(zip(DISPLAY_COLUMNS_EN, MACHINE_KEYS))
MACHINE_TO_DISPLAY = dict(zip(MACHINE_KEYS, DISPLAY_COLUMNS))
MACHINE_TO_DISPLAY_EN = dict(zip(MACHINE_KEYS, DISPLAY_COLUMNS_EN))
_CATEGORY_PREFIXES = tuple(
    sorted(("%s-" % code for code in TYPE_CATEGORIES), key=len, reverse=True)
)


def display_columns_for(dialect: str) -> Tuple[str, ...]:
    if dialect == HEADER_DIALECT_EN:
        return DISPLAY_COLUMNS_EN
    return DISPLAY_COLUMNS


def computed_display_columns_for(dialect: str) -> Tuple[str, ...]:
    if dialect == HEADER_DIALECT_EN:
        return COMPUTED_DISPLAY_COLUMNS_EN
    return COMPUTED_DISPLAY_COLUMNS


def resolve_display_columns(
    headers: Sequence[Optional[str]],
) -> Optional[Tuple[str, Tuple[str, ...]]]:
    """整列等於繁中或整列等於英文才接受；混用回傳 None。"""
    names = ["" if h in (None, "") else str(h) for h in headers]
    if names == list(DISPLAY_COLUMNS):
        return HEADER_DIALECT_ZH, DISPLAY_COLUMNS
    if names == list(DISPLAY_COLUMNS_EN):
        return HEADER_DIALECT_EN, DISPLAY_COLUMNS_EN
    return None


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
            t("dictionary.027"),
            blocking=("missing_type_id",),
        )
    for prefix in _CATEGORY_PREFIXES:
        if text.startswith(prefix):
            category = prefix[:-1]
            sequence = text[len(prefix):]
            if not sequence:
                return results.blocked(
                    "validate_dictionary",
                    t("dictionary.030") % text,
                    blocking=("invalid_type_id",),
                    details={"type_id": text, "type_category": category},
                )
            return results.ok(
                "validate_dictionary",
                t("dictionary.029"),
                details={
                    "type_id": "%s-%s" % (category, sequence),
                    "type_category": category,
                    "type_sequence": sequence,
                },
            )
    return results.blocked(
        "validate_dictionary",
        t("dictionary.028") % text,
        blocking=("unknown_type_category",),
        details={"type_id": text},
    )


def is_forbidden_cb_column(name: str) -> bool:
    return name.startswith("_CB.")
