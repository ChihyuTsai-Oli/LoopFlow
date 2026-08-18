# -*- coding: utf-8 -*-
"""Sheet 身分、metadata 欄位與命名設定的 key。

與 `wip/fixtures/schema/sheet.json` 必須一致，由 `test_sheet_metadata.py` 檢查。
"""
from __future__ import annotations

SHEET_SCHEMA_ID = "loopflow.sheet"
SHEET_SCHEMA_VERSION = 1

# 文件 UserText 命名空間：lf_sheet.<sheet_id>.<field>
DOCUMENT_NAMESPACE = "lf_sheet"

SHEET_ID_KEY = "lf_sheet_id"
DRAWING_NO_KEY = "lf_drawing_no"
DRAWING_NAME_KEY = "lf_drawing_name"
SCALE_KEY = "lf_scale"
SHEET_CODE_KEY = "lf_sheet_code"

METADATA_FIELDS = (
    "drawing_no",
    "drawing_name",
    "series",
    "sequence",
    "page_position",
    "level",
    "zone",
    "scale",
    "issue",
)
LAYOUT_ID_WRITTEN_FIELDS = (
    "drawing_no",
    "drawing_name",
    "series",
    "sequence",
    "page_position",
)
MANUAL_FIELDS = ("level", "zone", "scale", "issue")
PERSISTENT_FIELDS = ("sheet_id", "series", "drawing_name")
DERIVED_FIELDS = ("sequence", "drawing_no")

NAMING_KEYS = {
    "separator": "lf_sheet_naming.separator",
    "baseline_mark": "lf_sheet_naming.baseline_mark",
    "drawing_no_format": "lf_sheet_naming.drawing_no_format",
    "sheet_ref_format": "lf_sheet_naming.sheet_ref_format",
}
NAMING_DEFAULTS = {
    "separator": "__",
    "baseline_mark": ".01",
    "drawing_no_format": "{prefix} {major:03d}.{minor:02d}",
    "sheet_ref_format": "{major:03d}.{minor:02d}",
    "prefix_pattern": r"([A-Za-z\s]+?)[\s]*(\d+)$",
}

# 本份 .3dm 額外認可的圖框 Block；manifest 的 title_frame 恆定有效。
TITLE_FRAME_REGISTRY_KEY = "lf_title_frame_blocks"
TITLE_FRAME_REGISTRY_SEPARATOR = ";"

# 保留給尚未實作的 LF_Catalog，其他功能不得占用。
CATALOG_RESERVED_PREFIX = "lf_catalog_"
