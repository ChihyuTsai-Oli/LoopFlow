# -*- coding: utf-8 -*-
"""LF_Infuser_Part：當前 Layout 頁把 Registry／Sheet 資料注入 Tag 顯示欄。

不覆寫鎖定、門窗、比例、Detail 編號與其他 manual 欄。圖框與 TAG_ELEV_0
由 Layout ID 負責。第一輪不必等 TAG-O。
"""
from __future__ import annotations

import re
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.infuser import keys as infuser_keys
from loopflow.features.infuser.reader import load_published_registry
from loopflow.features.sheet.metadata import (
    get_sheet_metadata,
    is_title_frame,
    list_active_sheets,
    registered_title_frame_names,
)
from loopflow.features.sheet.keys import SHEET_ID_KEY
from loopflow.features.sheet.naming import (
    format_sheet_ref,
    load_naming_rules,
    parse_drawing_no,
    parse_page_name,
    split_fields,
)
from loopflow.features.tagger.binding import UUID_V4_RE, text
from loopflow.features.tagger.index import listed_details, resolve_view_for_detail
from loopflow.features.tagger.keys import (
    HOST_SHEET_ID_KEY,
    INDEX_TEMPLATE_IDS,
    LAST_SYNCED_REVISION_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
    is_tag_locked,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    ELEVATION_BASIS_KEY as MODEL_ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY as MODEL_ELEVATION_DISPLAY_KEY,
    OBJECT_ID_KEY,
    TYPE_CATEGORY_KEY as MODEL_TYPE_CATEGORY_KEY,
    TYPE_ID_KEY,
    TYPE_SEQUENCE_KEY as MODEL_TYPE_SEQUENCE_KEY,
    read_text,
)
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Infuser_Part"
STAGE = "infuse_tags"
PROJECT_ID_KEY = "lf_project_id"
PAGE_TAG_TEMPLATE_ID = "TAG_ELEV_0"
ITEM_NAME_PATTERN = re.compile(r"^([A-Za-z]+)-([0-9]+)__(.+)$")
SERIES_TOKEN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*$")
ShowMessage = Callable[[str], None]


def _display(value) -> str:
    cleaned = text(value)
    return cleaned if cleaned is not None else infuser_keys.MISSING_DISPLAY


def _norm_id(value) -> Optional[str]:
    raw = text(value)
    if raw is None:
        return None
    return raw.strip("{}").casefold() or None


def _as_uuid(value) -> Optional[str]:
    raw = _norm_id(value)
    if raw is None or not UUID_V4_RE.match(raw):
        return None
    return raw


def _object_index(payload: Optional[Mapping]) -> Tuple[Dict[str, dict], Tuple[str, ...]]:
    by_id = {}
    dupes = []
    if not isinstance(payload, Mapping):
        return {}, ()
    for item in payload.get("objects") or ():
        if not isinstance(item, Mapping):
            continue
        object_id = _as_uuid(item.get("object_id")) or _norm_id(item.get("object_id"))
        if object_id is None:
            continue
        if object_id in by_id:
            if object_id not in dupes:
                dupes.append(object_id)
            continue
        by_id[object_id] = dict(item)
    return by_id, tuple(dupes)


def _types_by_id(payload: Optional[Mapping]) -> Dict[str, dict]:
    found = {}
    if not isinstance(payload, Mapping):
        return found
    for item in payload.get("types") or ():
        if not isinstance(item, Mapping):
            continue
        type_id = text(item.get("type_id"))
        if type_id is None:
            continue
        found[type_id] = dict(item)
    return found


def _enrich_row(row: Mapping, types_by_id: Mapping[str, dict]) -> dict:
    body = dict(row)
    if text(body.get("type_display_name")) is None:
        record = types_by_id.get(str(body.get("type_id") or "").strip())
        if record is not None and text(record.get("type_display_name")) is not None:
            body["type_display_name"] = record.get("type_display_name")
    return body


def _iter_live_source_ids(session: RhinoSession) -> Sequence[str]:
    objects_fn = getattr(session, "_iter_rhino_objects", None)
    if callable(objects_fn):
        ids = []
        try:
            for obj in objects_fn(include_linked=True) or ():
                try:
                    ids.append(str(obj.Id))
                except Exception:
                    continue
        except TypeError:
            ids = []
        if ids:
            return tuple(ids)
    try:
        return tuple(
            session.iter_object_ids(
                include_hidden=True, include_locked=True, include_linked=True
            )
        )
    except TypeError:
        return tuple(session.iter_object_ids(include_hidden=True, include_locked=True))


def _live_row_score(row: Mapping) -> int:
    keys = (
        "type_id",
        "type_category",
        "type_sequence",
        "type_display_name",
        "elevation_basis",
        "elevation_display",
    )
    return sum(1 for key in keys if text(row.get(key)) is not None)


def _live_ids_by_uuid(session: RhinoSession, cache: dict) -> Dict[str, List[str]]:
    indexed = cache.get("live_by_uuid")
    if indexed is not None:
        return indexed
    found: Dict[str, List[str]] = {}
    for object_id in _iter_live_source_ids(session):
        uid = _as_uuid(read_text(session, object_id, OBJECT_ID_KEY))
        if uid is None:
            continue
        found.setdefault(uid, []).append(object_id)
    cache["live_by_uuid"] = found
    return found


def _row_from_live(
    session: RhinoSession,
    rhino_id: str,
    types_by_id: Mapping[str, dict],
) -> dict:
    type_id = read_text(session, rhino_id, TYPE_ID_KEY)
    record = types_by_id.get(str(type_id or "").strip())
    return {
        "object_id": read_text(session, rhino_id, OBJECT_ID_KEY),
        "type_id": type_id,
        "type_category": read_text(session, rhino_id, MODEL_TYPE_CATEGORY_KEY),
        "type_sequence": read_text(session, rhino_id, MODEL_TYPE_SEQUENCE_KEY),
        "type_display_name": None if record is None else record.get("type_display_name"),
        "elevation_basis": read_text(session, rhino_id, MODEL_ELEVATION_BASIS_KEY),
        "elevation_display": read_text(session, rhino_id, MODEL_ELEVATION_DISPLAY_KEY),
    }


def _lookup_object_row(
    session: RhinoSession,
    source_id: str,
    objects: Mapping[str, dict],
    types_by_id: Mapping[str, dict],
    cache: dict,
) -> Tuple[Optional[dict], bool]:
    key = _as_uuid(source_id) or _norm_id(source_id)
    if key is None:
        return None, False
    row = objects.get(key)
    if row is not None:
        return _enrich_row(row, types_by_id), False
    live_ids = _live_ids_by_uuid(session, cache).get(key) or ()
    if not live_ids:
        return None, False
    best = None
    best_score = -1
    for live_id in live_ids:
        candidate = _enrich_row(_row_from_live(session, live_id, types_by_id), types_by_id)
        score = _live_row_score(candidate)
        if score > best_score:
            best = candidate
            best_score = score
    if best is None:
        return None, False
    return best, True


def _host_sheet_id(
    session: RhinoSession,
    catalog: TagTemplateSet,
    page_name: str,
) -> Optional[str]:
    for sheet in list_active_sheets(session, catalog):
        if sheet.page_name == page_name:
            return sheet.sheet_id
    return None


def _write_fields(session: RhinoSession, tag_id: str, fields: Mapping[str, str]) -> None:
    for key, value in fields.items():
        session.set_object_user_text(tag_id, key, value)


def _stamp(
    session: RhinoSession,
    tag_id: str,
    host_sheet_id: Optional[str],
    revision,
) -> None:
    if host_sheet_id:
        session.set_object_user_text(tag_id, HOST_SHEET_ID_KEY, host_sheet_id)
    if revision not in (None, ""):
        session.set_object_user_text(tag_id, LAST_SYNCED_REVISION_KEY, str(revision))


def _index_sheet_fields(session: RhinoSession, sheet_id: str) -> Optional[Dict[str, str]]:
    metadata = get_sheet_metadata(session, sheet_id)
    series = text(metadata.get("series"))
    sequence = text(metadata.get("sequence"))
    if series is None or sequence is None:
        prefix, number = parse_drawing_no(metadata.get("drawing_no"))
        series = series or prefix
        sequence = sequence or number
    if series is None and sequence is None:
        return None
    rules = load_naming_rules(session)
    return {
        infuser_keys.SHEET_CODE_KEY: _display(series),
        infuser_keys.SHEET_REF_KEY: (
            format_sheet_ref(rules, sequence)
            if sequence is not None
            else infuser_keys.MISSING_DISPLAY
        ),
    }


def _lookup_sheet_fields(
    session: RhinoSession,
    catalog: TagTemplateSet,
    sheet_id: str,
) -> Tuple[Optional[str], Optional[Dict[str, str]]]:
    candidates = []
    raw = text(sheet_id)
    if raw:
        candidates.append(raw)
    normalized = _as_uuid(sheet_id)
    if normalized and normalized not in candidates:
        candidates.append(normalized)
    for candidate in candidates:
        fields = _index_sheet_fields(session, candidate)
        if fields is not None:
            return candidate, fields
    wanted = _as_uuid(sheet_id)
    if wanted is None:
        return None, None
    for sheet in list_active_sheets(session, catalog):
        if _as_uuid(sheet.sheet_id) == wanted:
            fields = _index_sheet_fields(session, sheet.sheet_id)
            if fields is not None:
                return sheet.sheet_id, fields
    return None, None


def _loose_page_tokens(
    page_name: str, rules
) -> Tuple[Optional[str], Optional[str]]:
    """Infuser 專用：第一段像系列、第二段原樣當圖號。不改 Layout ID 的遞增規則。"""
    raw = str(page_name or "").strip()
    if raw.startswith("//"):
        raw = raw[2:].lstrip()
    elif rules.baseline_mark and raw.startswith(rules.baseline_mark):
        raw = raw[len(rules.baseline_mark) :].lstrip()
    parts = split_fields(raw, rules)
    if len(parts) >= 2 and SERIES_TOKEN_RE.match(parts[0] or "") and (parts[1] or "").strip():
        return parts[0], parts[1]
    if len(parts) == 1:
        prefix, number = parse_drawing_no(parts[0])
        if prefix is not None:
            return prefix, number
        body = parts[0]
        if " " in body:
            left, _, right = body.partition(" ")
            left, right = left.strip(), right.strip()
            if SERIES_TOKEN_RE.match(left) and right:
                return left, right
    return None, None


def _fields_from_page_name(session: RhinoSession, page_name: str) -> Optional[Dict[str, str]]:
    rules = load_naming_rules(session)
    parsed = parse_page_name(page_name, rules)
    prefix, number = parsed.prefix, parsed.number
    if prefix is None or number is None:
        prefix, number = _loose_page_tokens(page_name, rules)
    if prefix is None and number is None:
        return None
    return {
        infuser_keys.SHEET_CODE_KEY: _display(prefix),
        infuser_keys.SHEET_REF_KEY: (
            format_sheet_ref(rules, number)
            if number is not None
            else infuser_keys.MISSING_DISPLAY
        ),
    }


def _strip_page_marks(name: str) -> str:
    raw = str(name or "").strip()
    if raw.startswith("//"):
        return raw[2:].lstrip()
    if raw.startswith("**"):
        return raw[2:].lstrip()
    return raw


def _page_matches_stored(current: str, stored: str) -> bool:
    left = text(current)
    right = text(stored)
    if left is None or right is None:
        return False
    if left == right:
        return True
    body = _strip_page_marks(left)
    hint = _strip_page_marks(right)
    if body == hint:
        return True
    sep = "__"
    return body.startswith(hint + sep) or hint.startswith(body + sep)


def _match_stored_layout(stored: str, candidates: Sequence[str]) -> Optional[str]:
    names = [name for name in candidates if text(name)]
    exact = [name for name in names if name == stored]
    if len(exact) == 1:
        return exact[0]
    fuzzy = [name for name in names if _page_matches_stored(name, stored)]
    if len(fuzzy) == 1:
        return fuzzy[0]
    return None


def _listed_page_names(session: RhinoSession) -> Tuple[str, ...]:
    pages_fn = getattr(session, "listed_layout_pages", None)
    if not callable(pages_fn):
        return ()
    names = []
    for item in pages_fn() or ():
        name = str(item.get("name") or "").strip()
        if name:
            names.append(name)
    return tuple(names)


def _sheet_ids_on_pages(
    session: RhinoSession,
    catalog: TagTemplateSet,
    page_names: Sequence[str],
) -> Tuple[str, ...]:
    registered = registered_title_frame_names(session)
    objects_fn = getattr(session, "objects_on_layout_page", None)
    if not callable(objects_fn):
        return ()
    found = []
    for page_name in page_names:
        for object_id in objects_fn(page_name) or ():
            if not session.is_block_instance(object_id):
                continue
            if not is_title_frame(session, object_id, catalog, registered):
                continue
            sheet_id = text(session.get_object_user_text(object_id, SHEET_ID_KEY))
            if _as_uuid(sheet_id) is None:
                continue
            if sheet_id not in found:
                found.append(sheet_id)
    return tuple(found)


def _prefer_target_pages(
    pages: Sequence[str],
    host_page_name: Optional[str],
) -> Tuple[str, ...]:
    unique = tuple(dict.fromkeys(pages))
    host = text(host_page_name)
    if host is None:
        return unique
    others = tuple(name for name in unique if name != host)
    return others if others else unique


def _unique_page_name_fields(
    session: RhinoSession,
    page_names: Sequence[str],
) -> Optional[Dict[str, str]]:
    parsed_fields = []
    for page_name in page_names:
        fields = _fields_from_page_name(session, page_name)
        if fields is not None and fields not in parsed_fields:
            parsed_fields.append(fields)
    if len(parsed_fields) == 1:
        return parsed_fields[0]
    return None


def _fields_from_pages(
    session: RhinoSession,
    catalog: TagTemplateSet,
    page_names: Sequence[str],
) -> results.Result:
    unique_pages = tuple(dict.fromkeys(name for name in page_names if text(name)))
    if not unique_pages:
        return results.blocked(
            STAGE,
            "目標 View 的頁沒有 Sheet metadata。請先跑 Layout ID。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    sheet_by_page = {
        sheet.page_name: sheet.sheet_id for sheet in list_active_sheets(session, catalog)
    }
    sheet_ids = tuple(
        sheet_by_page[name] for name in unique_pages if name in sheet_by_page
    )
    unique_sheets = tuple(dict.fromkeys(sheet_ids))
    if len(unique_sheets) > 1:
        return results.blocked(
            STAGE,
            "目標 View 對到兩個以上 Sheet，不猜測。",
            ("ambiguous_sheet",),
            command_id=COMMAND_ID,
        )
    if len(unique_sheets) != 1:
        extra = _sheet_ids_on_pages(session, catalog, unique_pages)
        extra_unique = tuple(dict.fromkeys(extra))
        if len(extra_unique) > 1:
            return results.blocked(
                STAGE,
                "目標 View 對到兩個以上 Sheet，不猜測。",
                ("ambiguous_sheet",),
                command_id=COMMAND_ID,
            )
        if len(extra_unique) == 1:
            unique_sheets = extra_unique
        else:
            parsed = _unique_page_name_fields(session, unique_pages)
            if parsed is not None:
                return results.ok(
                    STAGE,
                    "已從目標頁名讀到圖號。",
                    command_id=COMMAND_ID,
                    details={"sheet_id": None, "fields": parsed},
                )
            return results.blocked(
                STAGE,
                "目標 View 的頁沒有 Sheet metadata。請先跑 Layout ID。",
                ("missing_sheet",),
                command_id=COMMAND_ID,
            )
    sheet_id = unique_sheets[0]
    fields = _index_sheet_fields(session, sheet_id)
    if fields is None:
        parsed = _unique_page_name_fields(session, unique_pages)
        if parsed is not None:
            return results.ok(
                STAGE,
                "已從目標頁名讀到圖號。",
                command_id=COMMAND_ID,
                details={"sheet_id": sheet_id, "fields": parsed},
            )
        return results.blocked(
            STAGE,
            "目標 Sheet 沒有圖號資料。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    return results.ok(
        STAGE,
        "已從目標 View 對到 Sheet。",
        command_id=COMMAND_ID,
        details={"sheet_id": sheet_id, "fields": fields},
    )


def _resolve_index_sheet(
    session: RhinoSession,
    catalog: TagTemplateSet,
    tag_id: str,
    cache: Dict[str, object],
    host_page_name: Optional[str] = None,
) -> results.Result:
    existing = text(session.get_object_user_text(tag_id, TARGET_SHEET_ID_KEY))
    if _as_uuid(existing) is not None:
        sheet_id, fields = _lookup_sheet_fields(session, catalog, existing)
        if fields is not None:
            return results.ok(
                STAGE,
                "已用目標 Sheet。",
                command_id=COMMAND_ID,
                details={"sheet_id": sheet_id, "fields": fields},
            )
        return results.blocked(
            STAGE,
            "目標 Sheet 沒有圖號資料。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    stored_layout = text(session.get_object_user_text(tag_id, TARGET_LAYOUT_KEY))
    if stored_layout:
        matched = _match_stored_layout(stored_layout, _listed_page_names(session))
        if matched:
            stored = _fields_from_pages(session, catalog, (matched,))
            if stored.ok:
                return stored
    view_id = _as_uuid(session.get_object_user_text(tag_id, TARGET_VIEW_ID_KEY))
    if view_id is None:
        return results.blocked(
            STAGE,
            "Index Tag 沒有目標 View。",
            ("missing_source",),
            command_id=COMMAND_ID,
        )
    pages_by_view = cache.get("pages_by_view")
    if pages_by_view is None:
        pages_by_view = _pages_for_views(session)
        cache["pages_by_view"] = pages_by_view
    pages = tuple(dict.fromkeys(pages_by_view.get(view_id) or ()))
    if stored_layout:
        matched = _match_stored_layout(stored_layout, pages)
        if matched:
            stored = _fields_from_pages(session, catalog, (matched,))
            if stored.ok:
                return stored
    if not pages:
        return results.blocked(
            STAGE,
            "目標 View 對不到 Layout 頁。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    preferred = _prefer_target_pages(pages, host_page_name)
    resolved = _fields_from_pages(session, catalog, preferred)
    if resolved.ok:
        return resolved
    host = text(host_page_name)
    if host and host in pages:
        host_result = _fields_from_pages(session, catalog, (host,))
        if host_result.ok:
            return host_result
    return resolved


def _pages_for_views(session: RhinoSession) -> Dict[str, Tuple[str, ...]]:
    mapping = {}
    for item in listed_details(session):
        resolved = resolve_view_for_detail(session, item)
        if not resolved.ok:
            continue
        view_id = _as_uuid(resolved.details.get("view_id"))
        page_name = str(item.get("layout") or "")
        if not view_id or not page_name:
            continue
        mapping.setdefault(view_id, [])
        mapping[view_id].append(page_name)
    return {key: tuple(value) for key, value in mapping.items()}


def _height_fields(row: Mapping) -> Dict[str, str]:
    return {
        infuser_keys.ELEVATION_BASIS_KEY: _display(row.get("elevation_basis")),
        infuser_keys.ELEVATION_DISPLAY_KEY: _display(row.get("elevation_display")),
        infuser_keys.TYPE_CATEGORY_KEY: _display(row.get("type_category")),
        infuser_keys.TYPE_SEQUENCE_KEY: _display(row.get("type_sequence")),
        infuser_keys.TYPE_DISPLAY_NAME_KEY: _display(row.get("type_display_name")),
    }


def _finish_fields(row: Mapping) -> Dict[str, str]:
    return {
        infuser_keys.TYPE_CATEGORY_KEY: _display(row.get("type_category")),
        infuser_keys.TYPE_SEQUENCE_KEY: _display(row.get("type_sequence")),
        infuser_keys.TYPE_DISPLAY_NAME_KEY: _display(row.get("type_display_name")),
    }


def _missing_object_fields(family: str) -> Dict[str, str]:
    keys = (
        infuser_keys.HEIGHT_RENDER_KEYS
        if family == "height"
        else infuser_keys.FINISH_RENDER_KEYS
    )
    return {key: infuser_keys.MISSING_DISPLAY for key in keys}


def _item_fields(block_name: Optional[str], pattern: Optional[str]) -> results.Result:
    name = text(block_name)
    if name is None:
        return results.blocked(
            STAGE,
            "家具 Tag 沒有來源 Block 名稱。",
            ("missing_source",),
            command_id=COMMAND_ID,
        )
    matcher = re.compile(pattern) if pattern else ITEM_NAME_PATTERN
    matched = matcher.match(name)
    if matched is None:
        return results.blocked(
            STAGE,
            "家具 Block 名稱「%s」不符合 FF-01__Chair-1。" % name,
            ("invalid_block_name",),
            command_id=COMMAND_ID,
        )
    return results.ok(
        STAGE,
        "已解析家具名稱。",
        command_id=COMMAND_ID,
        details={
            "fields": {
                infuser_keys.ITEM_CATEGORY_KEY: matched.group(1),
                infuser_keys.ITEM_CODE_KEY: matched.group(2),
                infuser_keys.ITEM_NAME_KEY: matched.group(3),
            }
        },
    )


def _skip_reason(template: Optional[TagTemplate]) -> Optional[str]:
    if template is None:
        return "unknown_template"
    if template.role == "title_frame":
        return "title_frame"
    if template.template_id == PAGE_TAG_TEMPLATE_ID:
        return "elev_0"
    if template.template_id == "TAG_DW" or "manual" in template.binding_modes:
        return "manual"
    return None


def infuse_page(
    session: RhinoSession,
    page_name: str,
    catalog: TagTemplateSet,
    payload: Optional[Mapping],
    revision,
) -> dict:
    """注入一頁。回傳計數與警告，不組 Result。"""
    objects, dupes = _object_index(payload)
    types_by_id = _types_by_id(payload)
    host_sheet_id = _host_sheet_id(session, catalog, page_name)
    cache = {}
    counts = {
        "updated": 0,
        "skipped_locked": 0,
        "skipped_manual": 0,
        "skipped_title_frame": 0,
        "skipped_elev_0": 0,
        "unknown_template": 0,
        "missing_source": 0,
        "orphaned": 0,
        "ambiguous": 0,
        "invalid_block_name": 0,
        "missing_sheet": 0,
        "missing_registry": 0,
    }
    notes: List[str] = []
    objects_fn = getattr(session, "objects_on_layout_page", None)
    page_ids = tuple(objects_fn(page_name) or ()) if callable(objects_fn) else ()
    registered = registered_title_frame_names(session)

    for object_id in page_ids:
        if not session.is_block_instance(object_id):
            continue
        block_name = session.block_definition_name(object_id) or ""
        template = catalog.by_block_name(block_name)
        if template is None:
            if is_title_frame(session, object_id, catalog, registered):
                counts["skipped_title_frame"] += 1
                continue
            counts["unknown_template"] += 1
            notes.append("未知圖塊「%s」" % (block_name or "（未命名）"))
            continue
        skip = _skip_reason(template)
        if skip == "title_frame":
            counts["skipped_title_frame"] += 1
            continue
        if skip == "elev_0":
            counts["skipped_elev_0"] += 1
            continue
        if skip == "manual":
            counts["skipped_manual"] += 1
            continue
        if is_tag_locked(session, object_id):
            counts["skipped_locked"] += 1
            continue
        status = _infuse_tag(
            session,
            object_id,
            template,
            objects,
            dupes,
            types_by_id,
            payload is not None,
            host_sheet_id,
            revision,
            catalog,
            cache,
            page_name,
        )
        counts[status] = counts.get(status, 0) + 1
        if status == "updated":
            continue
        if status == "unknown_template":
            notes.append("未知圖塊「%s」" % (block_name or "（未命名）"))
    if cache.get("used_live_object"):
        notes.append("有些 Height／Finish 是從模型現況讀的，尚未進 Registry。")
    redraw = getattr(session, "redraw", None)
    if callable(redraw):
        redraw()
    return {
        "counts": counts,
        "notes": notes,
        "host_sheet_id": host_sheet_id,
        "used_live_object": bool(cache.get("used_live_object")),
    }


def _infuse_tag(
    session: RhinoSession,
    tag_id: str,
    template: TagTemplate,
    objects: Mapping[str, dict],
    dupes: Sequence[str],
    types_by_id: Mapping[str, dict],
    has_registry: bool,
    host_sheet_id: Optional[str],
    revision,
    catalog: TagTemplateSet,
    cache: dict,
    host_page_name: Optional[str] = None,
) -> str:
    family = template.family
    if family in ("height", "finish"):
        source_id = text(session.get_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY))
        missing = _missing_object_fields(family)
        if source_id is None:
            _write_fields(session, tag_id, missing)
            _stamp(session, tag_id, host_sheet_id, revision)
            return "missing_source"
        source_key = _as_uuid(source_id) or _norm_id(source_id)
        if source_key in dupes:
            _write_fields(session, tag_id, missing)
            _stamp(session, tag_id, host_sheet_id, revision)
            return "ambiguous"
        row, from_live = _lookup_object_row(
            session, source_id, objects, types_by_id, cache
        )
        if row is None:
            _write_fields(session, tag_id, missing)
            _stamp(session, tag_id, host_sheet_id, revision)
            return "orphaned" if has_registry else "missing_registry"
        if from_live:
            cache["used_live_object"] = True
        fields = _height_fields(row) if family == "height" else _finish_fields(row)
        _write_fields(session, tag_id, fields)
        _stamp(session, tag_id, host_sheet_id, revision)
        return "updated"
    if family == "item":
        parsed = _item_fields(
            session.get_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY),
            template.source_block_name_pattern,
        )
        if not parsed.ok:
            _write_fields(
                session,
                tag_id,
                {key: infuser_keys.MISSING_DISPLAY for key in infuser_keys.ITEM_RENDER_KEYS},
            )
            _stamp(session, tag_id, host_sheet_id, revision)
            reason = (parsed.blocking or ("missing_source",))[0]
            return reason if reason in ("missing_source", "invalid_block_name") else "missing_source"
        _write_fields(session, tag_id, parsed.details["fields"])
        _stamp(session, tag_id, host_sheet_id, revision)
        return "updated"
    if template.template_id in INDEX_TEMPLATE_IDS or family == "index":
        resolved = _resolve_index_sheet(
            session, catalog, tag_id, cache, host_page_name
        )
        if not resolved.ok:
            _write_fields(
                session,
                tag_id,
                {key: infuser_keys.MISSING_DISPLAY for key in infuser_keys.INDEX_RENDER_KEYS},
            )
            _stamp(session, tag_id, host_sheet_id, revision)
            reason = (resolved.blocking or ("missing_sheet",))[0]
            if reason == "missing_source":
                return "missing_source"
            if reason == "ambiguous_sheet":
                return "ambiguous"
            return "missing_sheet"
        _write_fields(session, tag_id, resolved.details["fields"])
        _stamp(session, tag_id, host_sheet_id, revision)
        return "updated"
    return "unknown_template"


def _summary(page_name: str, revision, counts: Mapping[str, int], notes: Sequence[str]) -> str:
    lines = [
        "已處理 Layout 頁「%s」。" % (page_name or "（未命名頁）"),
    ]
    if revision not in (None, ""):
        lines.append("Registry revision %s。" % revision)
    lines.append(
        "已注入 %s 個 Tag。" % counts.get("updated", 0)
    )
    skipped = []
    labels = (
        ("skipped_locked", "鎖定"),
        ("skipped_manual", "門窗／手動"),
        ("skipped_title_frame", "圖框"),
        ("skipped_elev_0", "TAG_ELEV_0"),
    )
    for key, label in labels:
        if counts.get(key):
            skipped.append("%s %s" % (label, counts[key]))
    if skipped:
        lines.append("跳過：%s。" % "、".join(skipped))
    problems = []
    problem_labels = (
        ("unknown_template", "未知圖塊"),
        ("missing_source", "缺來源"),
        ("orphaned", "Registry 找不到物件"),
        ("missing_registry", "沒有 Registry（請先發布）"),
        ("ambiguous", "來源歧義"),
        ("invalid_block_name", "家具名稱不符"),
        ("missing_sheet", "缺目標圖號"),
    )
    for key, label in problem_labels:
        if counts.get(key):
            problems.append("%s %s" % (label, counts[key]))
    if problems:
        lines.append("警告：%s。" % "、".join(problems))
    for note in notes[:8]:
        lines.append(note)
    if len(notes) > 8:
        lines.append("…另有 %s 則。" % (len(notes) - 8))
    return "\n".join(lines)


def _result_from_counts(
    page_name: str,
    revision,
    counts: Mapping[str, int],
    notes: Sequence[str],
    extra: Optional[dict] = None,
) -> results.Result:
    warnings = []
    warning_keys = (
        "unknown_template",
        "missing_source",
        "orphaned",
        "missing_registry",
        "ambiguous",
        "invalid_block_name",
        "missing_sheet",
        "used_last_good",
        "used_live_object",
        "missing_project_id",
    )
    for key in warning_keys:
        if extra and extra.get(key):
            warnings.append(key)
        elif counts.get(key):
            warnings.append(key)
    details = {
        "page_name": page_name,
        "registry_revision": revision,
        "counts": dict(counts),
        "notes": tuple(notes),
    }
    if extra:
        details.update(extra)
    message = _summary(page_name, revision, counts, notes)
    if warnings:
        return results.ok_with_warnings(
            STAGE,
            message,
            tuple(warnings),
            command_id=COMMAND_ID,
            details=details,
        )
    return results.ok(STAGE, message, command_id=COMMAND_ID, details=details)


def run_infuser_part(
    session: RhinoSession,
    *,
    catalog: Optional[TagTemplateSet] = None,
    environ: Optional[Mapping[str, str]] = None,
    registry: Optional[Mapping] = None,
    show_message: Optional[ShowMessage] = None,
) -> results.Result:
    """當前 Layout 頁注入。取消／失敗不寫入。"""
    schema = check_document_schema(session)
    if not schema.ok:
        return results.failed(
            schema.stage,
            schema.message,
            command_id=COMMAND_ID,
            details=schema.details,
        )
    if "missing_document_schema" in (schema.warnings or ()):
        return results.blocked(
            "check_schema",
            "文件尚未寫入 schema，已停止，不寫入。",
            ("missing_document_schema",),
            command_id=COMMAND_ID,
        )
    if not session.is_layout_active():
        return results.blocked(
            STAGE,
            "請在 Layout 頁執行 Infuser Part。已停止，不寫入。",
            ("not_on_layout",),
            command_id=COMMAND_ID,
        )
    page_name = ""
    page_fn = getattr(session, "current_layout_page_name", None)
    if callable(page_fn):
        page_name = str(page_fn() or "").strip()
    if not page_name:
        return results.blocked(
            STAGE,
            "無法判斷目前 Layout 頁，已停止，不寫入。",
            ("missing_layout_page",),
            command_id=COMMAND_ID,
        )
    loaded = catalog
    if loaded is None:
        templates = load_tag_templates()
        if not templates.ok:
            return templates
        loaded = templates.details["catalog"]

    registry_result = None
    payload = registry
    revision = None
    extra_warnings = {}
    if payload is None:
        registry_result = load_published_registry(
            session.document_user_text(PROJECT_ID_KEY),
            environ=environ,
            command_id=COMMAND_ID,
        )
        if not registry_result.ok:
            return registry_result
        payload = registry_result.details.get("payload")
        revision = registry_result.details.get("registry_revision")
        for warning in registry_result.warnings or ():
            extra_warnings[warning] = True
    elif isinstance(payload, Mapping):
        revision = payload.get("registry_revision")

    def action(current: RhinoSession) -> results.Result:
        outcome = infuse_page(current, page_name, loaded, payload, revision)
        extra = dict(extra_warnings)
        if outcome.get("used_live_object"):
            extra["used_live_object"] = True
        result = _result_from_counts(
            page_name,
            revision,
            outcome["counts"],
            outcome["notes"],
            extra=extra,
        )
        if show_message and result.ok:
            show_message(result.message)
        return result

    return run_guarded(session, action, command_id=COMMAND_ID)
