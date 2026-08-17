# -*- coding: utf-8 -*-
"""Tag 共通身分欄。顯示欄由 Infuser 寫，Grab 不碰。"""
from __future__ import annotations

TAG_ID_KEY = "lf_tag_id"
TEMPLATE_ID_KEY = "lf_template_id"
TEMPLATE_VERSION_KEY = "lf_template_version"
BINDING_MODE_KEY = "lf_binding_mode"
SOURCE_OBJECT_ID_KEY = "lf_source_object_id"
SOURCE_BLOCK_NAME_KEY = "lf_source_block_name"
TARGET_VIEW_ID_KEY = "lf_target_view_id"
TARGET_SHEET_ID_KEY = "lf_target_sheet_id"
LOCK_STATE_KEY = "lf_lock_state"

GRAB_OBJECT_TEMPLATE_IDS = frozenset(("TAG_HEIGHT_GRAB", "TAG_FINISH_GRAB"))
GRAB_BLOCK_TEMPLATE_IDS = frozenset(("TAG_ITEM",))
GRAB_TEMPLATE_IDS = GRAB_OBJECT_TEMPLATE_IDS | GRAB_BLOCK_TEMPLATE_IDS


def is_lock_true(value) -> bool:
    if value in (None, ""):
        return False
    return str(value).strip().lower() in ("true", "1")
