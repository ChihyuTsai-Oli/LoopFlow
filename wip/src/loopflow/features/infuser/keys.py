# -*- coding: utf-8 -*-
"""Infuser 顯示欄 UserText。manual 欄只列出來供測試對照，程式不得寫入。"""
from __future__ import annotations

from loopflow.features.sheet.keys import SHEET_CODE_KEY
from loopflow.features.tagger.keys import HOST_SHEET_ID_KEY, LAST_SYNCED_REVISION_KEY

MISSING_DISPLAY = "-"

ELEVATION_BASIS_KEY = "lf_elevation_basis"
ELEVATION_DISPLAY_KEY = "lf_elevation_display"
TYPE_CATEGORY_KEY = "lf_type_category"
TYPE_SEQUENCE_KEY = "lf_type_sequence"
TYPE_DISPLAY_NAME_KEY = "lf_type_display_name"
ITEM_CATEGORY_KEY = "lf_item_category"
ITEM_CODE_KEY = "lf_item_code"
ITEM_NAME_KEY = "lf_item_name"
SHEET_REF_KEY = "lf_sheet_ref"

REMARKS_MANUAL_KEY = "lf_remarks_manual"
DETAIL_NO_KEY = "lf_detail_no"
DW_ID_KEY = "lf_dw_id"
DW_WIDTH_KEY = "lf_dw_width"
DW_HEIGHT_KEY = "lf_dw_height"

HEIGHT_RENDER_KEYS = (
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    TYPE_CATEGORY_KEY,
    TYPE_SEQUENCE_KEY,
    TYPE_DISPLAY_NAME_KEY,
)
FINISH_RENDER_KEYS = (
    TYPE_CATEGORY_KEY,
    TYPE_SEQUENCE_KEY,
    TYPE_DISPLAY_NAME_KEY,
)
ITEM_RENDER_KEYS = (
    ITEM_CATEGORY_KEY,
    ITEM_CODE_KEY,
    ITEM_NAME_KEY,
)
INDEX_RENDER_KEYS = (
    SHEET_CODE_KEY,
    SHEET_REF_KEY,
)
MANUAL_KEYS = (
    REMARKS_MANUAL_KEY,
    DETAIL_NO_KEY,
    DW_ID_KEY,
    DW_WIDTH_KEY,
    DW_HEIGHT_KEY,
)

LEGACY_DISPLAY_KEYS = (
    "attr_ch_key",
    "attr_ch_val",
    "attr_mat_key",
    "attr_mat_val",
    "attr_note",
    "attr_item_key",
    "attr_item_val",
    "Category",
    "REF_ID",
)

__all__ = [
    "DETAIL_NO_KEY",
    "DW_HEIGHT_KEY",
    "DW_ID_KEY",
    "DW_WIDTH_KEY",
    "ELEVATION_BASIS_KEY",
    "ELEVATION_DISPLAY_KEY",
    "FINISH_RENDER_KEYS",
    "HEIGHT_RENDER_KEYS",
    "HOST_SHEET_ID_KEY",
    "INDEX_RENDER_KEYS",
    "ITEM_CATEGORY_KEY",
    "ITEM_CODE_KEY",
    "ITEM_NAME_KEY",
    "ITEM_RENDER_KEYS",
    "LAST_SYNCED_REVISION_KEY",
    "LEGACY_DISPLAY_KEYS",
    "MANUAL_KEYS",
    "MISSING_DISPLAY",
    "REMARKS_MANUAL_KEY",
    "SHEET_CODE_KEY",
    "SHEET_REF_KEY",
    "TYPE_CATEGORY_KEY",
    "TYPE_DISPLAY_NAME_KEY",
    "TYPE_SEQUENCE_KEY",
]
