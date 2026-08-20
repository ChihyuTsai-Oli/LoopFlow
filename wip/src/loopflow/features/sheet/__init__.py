# -*- coding: utf-8 -*-
"""Sheet metadata：圖號、圖名與系列的真相。Layout ID 寫，其他功能只讀。"""
from loopflow.features.sheet.duplicate import run_duplicate_layout
from loopflow.features.sheet.metadata import (
    get_sheet_metadata,
    list_active_sheets,
    scan_layout_pages,
    sheet_state,
    stale_sheet_ids,
    write_sheet_metadata,
)
from loopflow.features.sheet.naming import (
    assign_sheet_numbers,
    load_naming_rules,
    parse_page_name,
)

__all__ = [
    "assign_sheet_numbers",
    "get_sheet_metadata",
    "list_active_sheets",
    "load_naming_rules",
    "parse_page_name",
    "run_duplicate_layout",
    "scan_layout_pages",
    "sheet_state",
    "stale_sheet_ids",
    "write_sheet_metadata",
]
