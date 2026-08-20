# -*- coding: utf-8 -*-
"""LF_Duplicate_Layout：複製 Layout 頁並依契約發新 ID、清除／保留 Tag。

不以系統剪貼簿複製。取消／失敗不留下半成品頁。
"""
from __future__ import annotations

from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.catalog import keys as catalog_keys
from loopflow.features.drawing import keys as drawing_keys
from loopflow.features.sheet.keys import DRAWING_NAME_KEY, DRAWING_NO_KEY, SHEET_ID_KEY
from loopflow.features.sheet.metadata import is_title_frame
from loopflow.features.sheet.naming import NamingRules, compose_page_name, load_naming_rules, parse_page_name
from loopflow.features.tagger.binding import canonical_uuid, new_id, text
from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    HEALTH_STATE_KEY,
    HOST_SHEET_ID_KEY,
    LAST_SYNCED_REVISION_KEY,
    LOCK_STATE_KEY,
    LOCK_STATE_PREV_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
    is_legacy_lock_key,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Duplicate_Layout"
STAGE = "duplicate_layout"
COPY_SUFFIX = "_Copy"
MIN_COPIES = 1
MAX_COPIES = 100
# 除 TAG_DW 外，來源綁定與健康狀態一律清除；template_id 保留。
BINDING_CLEAR_KEYS = (
    SOURCE_OBJECT_ID_KEY,
    SOURCE_BLOCK_NAME_KEY,
    TARGET_VIEW_ID_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_LAYOUT_KEY,
    HOST_SHEET_ID_KEY,
    LAST_SYNCED_REVISION_KEY,
    HEALTH_STATE_KEY,
)
ShowMessage = Callable[[str], None]
PickPage = Callable[[RhinoSession, Sequence[str]], Optional[str]]
PickCount = Callable[[RhinoSession], Optional[int]]


def next_copy_page_name(
    source_name: str,
    index: int,
    existing: Sequence[str],
    rules: Optional[NamingRules] = None,
) -> str:
    """產生複製頁名。保留三欄契約、不加 `**`／`//`，避免誤當新系列起點。"""
    naming = rules or NamingRules()
    parsed = parse_page_name(source_name, naming)
    if parsed.structured and parsed.prefix and parsed.number:
        label = (parsed.drawing_name or "").strip()
        copied_label = "%s%s%s" % (label, COPY_SUFFIX, index) if label else (
            "Copy%s" % index
        )
        stem = compose_page_name(
            naming,
            parsed.prefix,
            parsed.number,
            copied_label,
            marked=False,
            manual=False,
        )
    else:
        raw = (source_name or "").strip()
        mark = naming.baseline_mark
        if mark and raw.startswith(mark):
            raw = raw[len(mark) :].lstrip()
        if raw.startswith("//"):
            raw = raw[2:].lstrip()
        stem = "%s%s%s" % (raw or "Layout", COPY_SUFFIX, index)
    name = stem
    extra = 0
    original = name
    taken = set(existing)
    while name in taken:
        extra += 1
        name = "%s_%s" % (original, extra)
    return name


def _layout_names(session: RhinoSession) -> Tuple[str, ...]:
    pages_fn = getattr(session, "listed_layout_pages", None)
    if not callable(pages_fn):
        return ()
    names = []
    for page in pages_fn() or ():
        name = str(page.get("name") or "").strip()
        if name:
            names.append(name)
    return tuple(names)


def _source_sheet_id(
    session: RhinoSession,
    page_name: str,
    catalog: TagTemplateSet,
) -> Optional[str]:
    objects_fn = getattr(session, "objects_on_layout_page", None)
    if not callable(objects_fn):
        return None
    for object_id in objects_fn(page_name) or ():
        if not is_title_frame(session, object_id, catalog):
            continue
        sheet_id = canonical_uuid(session.get_object_user_text(object_id, SHEET_ID_KEY))
        if sheet_id:
            return sheet_id
    return None


def _clear_key(session: RhinoSession, object_id: str, key: str) -> None:
    session.set_object_user_text(object_id, key, "")


def _reset_lock(session: RhinoSession, object_id: str, template: TagTemplate) -> None:
    if not template.lock_allowed:
        return
    keys_fn = getattr(session, "object_user_text_keys", None)
    keys = tuple(keys_fn(object_id) or ()) if callable(keys_fn) else ()
    for key in keys:
        if is_legacy_lock_key(key):
            _clear_key(session, object_id, key)
    _clear_key(session, object_id, LOCK_STATE_PREV_KEY)
    state = "true" if template.default_lock_state else "false"
    session.set_object_user_text(object_id, LOCK_STATE_KEY, state)


def _sanitize_tag(
    session: RhinoSession,
    object_id: str,
    template: TagTemplate,
) -> None:
    session.set_object_user_text(object_id, TAG_ID_KEY, new_id())
    if template.template_id == "TAG_DW":
        _clear_key(session, object_id, HOST_SHEET_ID_KEY)
        return
    for key in BINDING_CLEAR_KEYS:
        _clear_key(session, object_id, key)
    for field in template.fields:
        if field.clear_on_duplicate and field.usertext:
            _clear_key(session, object_id, field.usertext)
    _reset_lock(session, object_id, template)


def _sanitize_title_frame(
    session: RhinoSession,
    object_id: str,
    sheet_id: str,
) -> None:
    session.set_object_user_text(object_id, SHEET_ID_KEY, sheet_id)
    _clear_key(session, object_id, DRAWING_NO_KEY)
    _clear_key(session, object_id, DRAWING_NAME_KEY)
    if text(session.get_object_user_text(object_id, TAG_ID_KEY)):
        session.set_object_user_text(object_id, TAG_ID_KEY, new_id())
    # lf_scale 保留；不寫 lock。


def _remap_catalog(
    session: RhinoSession,
    object_id: str,
    id_map: Mapping[str, str],
    catalog_id_map: Dict[str, str],
    source_sheet_id: Optional[str],
    new_sheet_id: Optional[str],
) -> None:
    old_catalog = text(session.get_object_user_text(object_id, catalog_keys.CATALOG_ID_KEY))
    if old_catalog is None:
        return
    if old_catalog not in catalog_id_map:
        catalog_id_map[old_catalog] = new_id()
    session.set_object_user_text(
        object_id, catalog_keys.CATALOG_ID_KEY, catalog_id_map[old_catalog]
    )
    old_point = text(session.get_object_user_text(object_id, catalog_keys.POINT_ID_KEY))
    if old_point and old_point in id_map:
        session.set_object_user_text(
            object_id, catalog_keys.POINT_ID_KEY, id_map[old_point]
        )
    bound = canonical_uuid(
        session.get_object_user_text(object_id, catalog_keys.SHEET_ID_KEY)
    )
    if bound and source_sheet_id and bound == source_sheet_id and new_sheet_id:
        session.set_object_user_text(
            object_id, catalog_keys.SHEET_ID_KEY, new_sheet_id
        )


def _remap_drawing(
    session: RhinoSession,
    object_id: str,
    drawing_id_map: Dict[str, str],
) -> None:
    old_drawing = text(session.get_object_user_text(object_id, drawing_keys.DRAWING_ID_KEY))
    if old_drawing is None:
        return
    if old_drawing not in drawing_id_map:
        drawing_id_map[old_drawing] = new_id()
    session.set_object_user_text(
        object_id, drawing_keys.DRAWING_ID_KEY, drawing_id_map[old_drawing]
    )
    if text(session.get_object_user_text(object_id, drawing_keys.DRAWING_ELEMENT_ID_KEY)):
        session.set_object_user_text(
            object_id, drawing_keys.DRAWING_ELEMENT_ID_KEY, new_id()
        )


def sanitize_copied_objects(
    session: RhinoSession,
    id_map: Mapping[str, str],
    catalog: TagTemplateSet,
    source_sheet_id: Optional[str],
) -> str:
    """依契約改寫複製物件。回傳此頁新 `sheet_id`（無圖框則空字串）。"""
    has_frame = any(
        is_title_frame(session, new_id_value, catalog)
        for new_id_value in id_map.values()
    )
    new_sheet_id = new_id() if has_frame else None
    catalog_id_map: Dict[str, str] = {}
    drawing_id_map: Dict[str, str] = {}
    for new_object in id_map.values():
        _remap_catalog(
            session,
            new_object,
            id_map,
            catalog_id_map,
            source_sheet_id,
            new_sheet_id,
        )
        _remap_drawing(session, new_object, drawing_id_map)
        if is_title_frame(session, new_object, catalog) and new_sheet_id:
            _sanitize_title_frame(session, new_object, new_sheet_id)
            continue
        if not session.is_block_instance(new_object):
            continue
        block_name = session.block_definition_name(new_object) or ""
        template = catalog.by_block_name(block_name)
        if template is None or template.role != "tag":
            continue
        _sanitize_tag(session, new_object, template)
    return new_sheet_id or ""


def _rollback_pages(session: RhinoSession, page_names: Sequence[str]) -> None:
    deleter = getattr(session, "delete_layout_page", None)
    if not callable(deleter):
        return
    for name in reversed(list(page_names)):
        deleter(name)


def _default_pick_page(_session: RhinoSession, names: Sequence[str]) -> Optional[str]:
    from loopflow.platform.rhino.prompts import ask_popup_choice

    return ask_popup_choice("選擇要複製的 Layout：", list(names), COMMAND_ID)


def _default_pick_count(_session: RhinoSession) -> Optional[int]:
    from loopflow.platform.rhino.prompts import ask_integer

    return ask_integer("要複製幾份？", 1, MIN_COPIES, MAX_COPIES)


def _summary(source: str, created: Sequence[str]) -> str:
    lines = [
        "已複製 %s 份 Layout。" % len(created),
        "來源：%s" % source,
    ]
    for name in created:
        lines.append("  • %s" % name)
    lines.append("請重新綁定新頁 Tag，並視需要跑 Layout ID。")
    return "\n".join(lines)


def duplicate_layout_pages(
    session: RhinoSession,
    source_name: str,
    count: int,
    catalog: TagTemplateSet,
) -> results.Result:
    names = list(_layout_names(session))
    if source_name not in names:
        return results.blocked(
            STAGE,
            "找不到 Layout「%s」。" % source_name,
            ("missing_layout",),
            command_id=COMMAND_ID,
        )
    objects_fn = getattr(session, "objects_on_layout_page", None)
    if not callable(objects_fn) or not tuple(objects_fn(source_name) or ()):
        return results.blocked(
            STAGE,
            "來源 Layout 沒有物件。",
            ("empty_layout",),
            command_id=COMMAND_ID,
        )
    adder = getattr(session, "add_layout_page", None)
    copier = getattr(session, "copy_layout_page_objects", None)
    size_fn = getattr(session, "layout_page_size", None)
    if not callable(adder) or not callable(copier):
        return results.failed(
            STAGE,
            "此 Rhino session 不能複製 Layout 頁。",
            command_id=COMMAND_ID,
        )
    size = size_fn(source_name) if callable(size_fn) else None
    width, height = (float(size[0]), float(size[1])) if size else (297.0, 210.0)
    rules = load_naming_rules(session)
    source_sheet = _source_sheet_id(session, source_name, catalog)
    created: List[str] = []
    try:
        existing = list(_layout_names(session))
        for index in range(1, count + 1):
            new_name = next_copy_page_name(source_name, index, existing, rules)
            added = adder(new_name, width, height)
            if not added:
                _rollback_pages(session, created)
                return results.failed(
                    STAGE,
                    "無法建立 Layout「%s」。" % new_name,
                    command_id=COMMAND_ID,
                )
            created.append(added)
            existing.append(added)
            mapping = copier(source_name, added) or {}
            if not mapping:
                _rollback_pages(session, created)
                return results.failed(
                    STAGE,
                    "複製「%s」的物件失敗。" % source_name,
                    command_id=COMMAND_ID,
                )
            sanitize_copied_objects(session, mapping, catalog, source_sheet)
    except Exception:
        _rollback_pages(session, created)
        raise
    activate = getattr(session, "activate_layout_page", None)
    if callable(activate):
        activate(source_name)
    return results.ok(
        STAGE,
        _summary(source_name, created),
        command_id=COMMAND_ID,
        details={
            "source": source_name,
            "created": tuple(created),
            "count": len(created),
        },
    )


def run_duplicate_layout(
    session: RhinoSession,
    *,
    pick_page: Optional[PickPage] = None,
    pick_count: Optional[PickCount] = None,
    show_message: Optional[ShowMessage] = None,
) -> results.Result:
    if session is None:
        return results.failed(STAGE, "沒有 Rhino session。", command_id=COMMAND_ID)

    def _action(current: RhinoSession) -> results.Result:
        loaded = load_tag_templates()
        if not loaded.ok:
            return loaded
        catalog = loaded.details["catalog"]
        names = _layout_names(current)
        if not names:
            return results.blocked(
                STAGE,
                "目前文件沒有 Layout。請先建立至少一頁。",
                ("no_layouts",),
                command_id=COMMAND_ID,
            )
        chosen = (pick_page or _default_pick_page)(current, names)
        if chosen is None:
            return results.cancelled(STAGE, "已取消複製 Layout。", command_id=COMMAND_ID)
        if chosen not in names:
            return results.blocked(
                STAGE,
                "找不到 Layout「%s」。" % chosen,
                ("missing_layout",),
                command_id=COMMAND_ID,
            )
        objects_fn = getattr(current, "objects_on_layout_page", None)
        if not callable(objects_fn) or not tuple(objects_fn(chosen) or ()):
            return results.blocked(
                STAGE,
                "來源 Layout 沒有物件。",
                ("empty_layout",),
                command_id=COMMAND_ID,
            )
        count = (pick_count or _default_pick_count)(current)
        if count is None:
            return results.cancelled(STAGE, "已取消複製 Layout。", command_id=COMMAND_ID)
        try:
            copies = int(count)
        except (TypeError, ValueError):
            copies = 0
        if copies < MIN_COPIES or copies > MAX_COPIES:
            return results.blocked(
                STAGE,
                "份數須為 %s 到 %s。" % (MIN_COPIES, MAX_COPIES),
                ("invalid_count",),
                command_id=COMMAND_ID,
            )
        outcome = duplicate_layout_pages(current, chosen, copies, catalog)
        if outcome.ok and callable(show_message):
            show_message(outcome.message)
        return outcome

    return run_guarded(session, _action, command_id=COMMAND_ID)
