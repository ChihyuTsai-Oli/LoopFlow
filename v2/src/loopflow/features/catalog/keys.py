# -*- coding: utf-8 -*-
"""Catalog Anchor 的 UserText、圖層與容差。與 `v2/fixtures/schema/catalog.json` 必須一致。"""
from __future__ import annotations

CATALOG_SCHEMA_ID = "loopflow.catalog"
CATALOG_SCHEMA_VERSION = 1

CATALOG_ID_KEY = "lf_catalog_id"
FIELD_KEY = "lf_catalog_field"
SHEET_ID_KEY = "lf_catalog_sheet_id"
GENERATED_BY_KEY = "lf_generated_by"
GENERATED_BY_VALUE = "LF_Catalog"

FIELD_DRAWING_NO = "drawing_no"
FIELD_DRAWING_NAME = "drawing_name"
ALLOWED_FIELDS = (FIELD_DRAWING_NO, FIELD_DRAWING_NAME)

NUMBER_LAYER = "LoopFlow::Drawing_Number"
NAME_LAYER = "LoopFlow::Drawing_Name"
TEXT_LAYER = "LoopFlow::Drawing_Text"
NUMBER_COLOR = (255, 0, 0)
NAME_COLOR = (0, 255, 0)
TEXT_COLOR = (205, 179, 139)  # #CDB38B

POINT_ID_KEY = "lf_catalog_point_id"
HOME_LAYER_KEY = "lf_catalog_home_layer"
TEXT_FONT_KEY = "lf_catalog_text_font"
TEXT_HEIGHT_KEY = "lf_catalog_text_height"
TEXT_LAYER_KEY = "lf_catalog_text_layer"
TEXT_COLOR_KEY = "lf_catalog_text_color"
COLOR_BY_LAYER_VALUE = "by_layer"

# 文件單位為公分時的空間容差。
COLUMN_TOLERANCE = 2.0
ROW_TOLERANCE = 2.0
TEXT_HEIGHT = 3.0
DEFAULT_TEXT_FONT = "Arial"
# rhinoscriptsyntax：Left + Bottom，文字左下角對齊定位點。
TEXT_JUSTIFICATION_BOTTOM_LEFT = 1 | 65536
