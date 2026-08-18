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
LOCK_STATE_KEY = "lf_lock_state"
LOCK_LEGACY_KEY = "attr_Lock_不更新>寫入x或X"
LOCK_LEGACY_HINT = "x為不更新"

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
    """1.x 鎖定欄：trim 後恰為單一 x／X。空值與預設提示不算。"""
    if value in (None, ""):
        return False
    text = str(value).strip()
    if text == LOCK_LEGACY_HINT:
        return False
    return text.upper() == "X"


def is_legacy_lock_key(key: str) -> bool:
    text = str(key or "")
    if not text or text == LOCK_STATE_KEY:
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
    """D08 前：canonical true／1，或舊 lock 欄寫 x／X。只讀不寫舊 key。"""
    if is_lock_true(session.get_object_user_text(object_id, LOCK_STATE_KEY)):
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
