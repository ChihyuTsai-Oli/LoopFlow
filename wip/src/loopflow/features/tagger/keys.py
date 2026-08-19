# -*- coding: utf-8 -*-
"""Tag 共通身分欄。顯示欄由 Infuser 寫，Grab／Laser／Index 不碰。"""
from __future__ import annotations

TAG_ID_KEY = "lf_tag_id"
TEMPLATE_ID_KEY = "lf_template_id"
TEMPLATE_VERSION_KEY = "lf_template_version"
BINDING_MODE_KEY = "lf_binding_mode"
SOURCE_OBJECT_ID_KEY = "lf_source_object_id"
SOURCE_BLOCK_NAME_KEY = "lf_source_block_name"
TARGET_VIEW_ID_KEY = "lf_target_view_id"
TARGET_SHEET_ID_KEY = "lf_target_sheet_id"
# Index 綁定時記下所選 Detail 的 Layout 頁名，方便 Infuser 在改名後仍對到那一頁。
# 不是 Sheet 身分；圖號仍來自目標 Sheet／頁名。Layout ID 改頁名時會同步更新。
TARGET_LAYOUT_KEY = "lf_target_layout"
HOST_SHEET_ID_KEY = "lf_host_sheet_id"
LAST_SYNCED_REVISION_KEY = "lf_last_synced_revision"
# `00` 讓 Rhino Attribute User Text 依字母排序時排在其他 lf_* 之前。
LOCK_STATE_KEY = "lf_00_lock_state"
LOCK_STATE_PREV_KEY = "lf_lock_state"
LOCK_LEGACY_KEY = "attr_Lock_不更新>寫入x或X"
LOCK_LEGACY_HINT = "x為不更新"
LOCK_CANONICAL_HINT = "x to lock"
LOCK_HINTS = frozenset((LOCK_LEGACY_HINT, LOCK_CANONICAL_HINT))

GRAB_OBJECT_TEMPLATE_IDS = frozenset(("TAG_HEIGHT_GRAB", "TAG_FINISH_GRAB"))
GRAB_BLOCK_TEMPLATE_IDS = frozenset(("TAG_ITEM",))
GRAB_TEMPLATE_IDS = GRAB_OBJECT_TEMPLATE_IDS | GRAB_BLOCK_TEMPLATE_IDS
LASER_OBJECT_TEMPLATE_IDS = frozenset(("TAG_HEIGHT_LASER", "TAG_FINISH_LASER"))
INDEX_TEMPLATE_IDS = frozenset(("TAG_SECTION_DETAIL", "TAG_ELEV"))


def is_lock_true(value) -> bool:
    if value in (None, ""):
        return False
    return str(value).strip().lower() in ("true", "1")


def is_legacy_lock_x(value) -> bool:
    """trim 後恰為單一 x／X。空值與中／英預設提示不算。"""
    if value in (None, ""):
        return False
    text = str(value).strip()
    if text.casefold() in {hint.casefold() for hint in LOCK_HINTS}:
        return False
    return text.upper() == "X"


def is_legacy_lock_key(key: str) -> bool:
    text = str(key or "")
    if not text or text in (LOCK_STATE_KEY, LOCK_STATE_PREV_KEY):
        return False
    if text == LOCK_LEGACY_KEY:
        return True
    return "LOCK" in text.upper() or "不更新" in text


def _object_user_text_keys(session, object_id):
    getter = getattr(session, "object_user_text_keys", None)
    if callable(getter):
        return tuple(getter(object_id) or ())
    return ()


def is_tag_locked(session, object_id) -> bool:
    """canonical true／1 或 x／X。只讀不寫舊 key。"""
    for key in (LOCK_STATE_KEY, LOCK_STATE_PREV_KEY):
        lock_value = session.get_object_user_text(object_id, key)
        if is_lock_true(lock_value) or is_legacy_lock_x(lock_value):
            return True
    seen = set()
    for key in _object_user_text_keys(session, object_id):
        seen.add(key)
        if is_legacy_lock_key(key) and is_legacy_lock_x(
            session.get_object_user_text(object_id, key)
        ):
            return True
    if LOCK_LEGACY_KEY not in seen and is_legacy_lock_x(
        session.get_object_user_text(object_id, LOCK_LEGACY_KEY)
    ):
        return True
    return False
