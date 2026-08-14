# -*- coding: utf-8 -*-
"""計量規則求值。模型單位先換成 cm，再轉成 Type 的估算單位。"""
from __future__ import annotations

from typing import Optional, Tuple

from loopflow.features.dictionary.schema import classify_measurement

PING_FROM_M2 = 0.3025
CAI_SIDE_CM = 30.3
CAI_CM2 = CAI_SIDE_CM * CAI_SIDE_CM
CM_PER_M = 100.0
CM2_PER_M2 = 10000.0
CM3_PER_M3 = 1_000_000.0

TO_CM = {
    "cm": 1.0,
    "centimeter": 1.0,
    "centimeters": 1.0,
    "mm": 0.1,
    "millimeter": 0.1,
    "millimeters": 0.1,
    "m": 100.0,
    "meter": 1.0 * CM_PER_M,
    "meters": 1.0 * CM_PER_M,
}

ISSUE_NO_RULE = "measurement_rule_undefined"
ISSUE_MISMATCH = "dimension_mismatch"
ISSUE_NON_CM = "model_unit_not_cm"
ISSUE_UNKNOWN_UNIT = "unknown_model_unit"


def model_unit_to_cm(model_unit: Optional[str]) -> Tuple[float, Optional[str]]:
    key = (model_unit or "").strip().lower()
    if key in TO_CM:
        warning = ISSUE_NON_CM if TO_CM[key] != 1.0 else None
        return TO_CM[key], warning
    return 1.0, ISSUE_UNKNOWN_UNIT


def to_cm(value: float, model_unit: Optional[str]) -> Tuple[float, Optional[str]]:
    factor, warning = model_unit_to_cm(model_unit)
    return float(value) * factor, warning


def evaluate_quantity(
    rule: Optional[str],
    unit: Optional[str],
    w: float,
    d: float,
    h: float,
    *,
    model_unit: str = "Centimeters",
) -> dict:
    """回傳 quantity、issues。不符量綱不計算。"""
    classified = classify_measurement(unit, rule)
    issues = []
    w_cm, unit_issue = to_cm(w, model_unit)
    d_cm, _ = to_cm(d, model_unit)
    h_cm, _ = to_cm(h, model_unit)
    if unit_issue:
        issues.append(unit_issue)
    if classified == "warn_no_quantity":
        issues.append(ISSUE_NO_RULE)
        return {"quantity": None, "issues": tuple(issues), "classified": classified}
    if classified == "block":
        issues.append(ISSUE_MISMATCH)
        return {"quantity": None, "issues": tuple(issues), "classified": classified}
    quantity = None
    if rule == "COUNT":
        quantity = 1.0
    elif rule == "LEN_W":
        quantity = _length(w_cm, unit)
    elif rule == "LEN_D":
        quantity = _length(d_cm, unit)
    elif rule == "LEN_H":
        quantity = _length(h_cm, unit)
    elif rule == "AREA_WD":
        quantity = _area(w_cm * d_cm, unit)
    elif rule == "AREA_WH":
        quantity = _area(w_cm * h_cm, unit)
    elif rule == "AREA_DH":
        quantity = _area(d_cm * h_cm, unit)
    elif rule == "VOL_WDH":
        quantity = (w_cm * d_cm * h_cm) / CM3_PER_M3
    return {"quantity": quantity, "issues": tuple(issues), "classified": classified}


def _length(cm_value: float, unit: Optional[str]) -> float:
    if unit == "mm":
        return cm_value * 10.0
    return cm_value


def _area(cm2: float, unit: Optional[str]) -> float:
    if unit == "才":
        return cm2 / CAI_CM2
    if unit == "坪":
        return (cm2 / CM2_PER_M2) * PING_FROM_M2
    return cm2
