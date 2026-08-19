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
from loopflow.features.sheet.naming import format_sheet_ref, load_naming_rules, parse_drawing_no
from loopflow.features.tagger.binding import UUID_V4_RE, text
from loopflow.features.tagger.index import listed_details, resolve_view_for_detail
from loopflow.features.tagger.keys import (
    HOST_SHEET_ID_KEY,
    INDEX_TEMPLATE_IDS,
    LAST_SYNCED_REVISION_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
    is_tag_locked,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Infuser_Part"
STAGE = "infuse_tags"
PROJECT_ID_KEY = "lf_project_id"
PAGE_TAG_TEMPLATE_ID = "TAG_ELEV_0"
ITEM_NAME_PATTERN = re.compile(r"^([A-Za-z]+)-([0-9]+)__(.+)$")
ShowMessage = Callable[[str], None]


def _display(value) -> str:
    cleaned = text(value)
    return cleaned if cleaned is not None else infuser_keys.MISSING_DISPLAY


def _object_index(payload: Optional[Mapping]) -> Tuple[Dict[str, dict], Tuple[str, ...]]:
    by_id = {}
    dupes = []
    if not isinstance(payload, Mapping):
        return {}, ()
    for item in payload.get("objects") or ():
        if not isinstance(item, Mapping):
            continue
        object_id = text(item.get("object_id"))
        if object_id is None:
            continue
        if object_id in by_id:
            if object_id not in dupes:
                dupes.append(object_id)
            continue
        by_id[object_id] = dict(item)
    return by_id, tuple(dupes)


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


def _resolve_index_sheet(
    session: RhinoSession,
    catalog: TagTemplateSet,
    tag_id: str,
    cache: Dict[str, object],
) -> results.Result:
    existing = text(session.get_object_user_text(tag_id, TARGET_SHEET_ID_KEY))
    if existing and UUID_V4_RE.match(existing):
        fields = _index_sheet_fields(session, existing)
        if fields is not None:
            return results.ok(
                STAGE,
                "已用目標 Sheet。",
                command_id=COMMAND_ID,
                details={"sheet_id": existing, "fields": fields},
            )
        return results.blocked(
            STAGE,
            "目標 Sheet 沒有圖號資料。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    view_id = text(session.get_object_user_text(tag_id, TARGET_VIEW_ID_KEY))
    if view_id is None or not UUID_V4_RE.match(view_id):
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
    pages = pages_by_view.get(view_id) or ()
    if not pages:
        return results.blocked(
            STAGE,
            "目標 View 對不到 Layout 頁。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    unique_pages = tuple(dict.fromkeys(pages))
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
        return results.blocked(
            STAGE,
            "目標 View 的頁沒有 Sheet metadata。請先跑 Layout ID。",
            ("missing_sheet",),
            command_id=COMMAND_ID,
        )
    sheet_id = unique_sheets[0]
    fields = _index_sheet_fields(session, sheet_id)
    if fields is None:
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


def _pages_for_views(session: RhinoSession) -> Dict[str, Tuple[str, ...]]:
    mapping = {}
    for item in listed_details(session):
        resolved = resolve_view_for_detail(session, item)
        if not resolved.ok:
            continue
        view_id = resolved.details.get("view_id")
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
            payload is not None,
            host_sheet_id,
            revision,
            catalog,
            cache,
        )
        counts[status] = counts.get(status, 0) + 1
        if status == "updated":
            continue
        if status == "unknown_template":
            notes.append("未知圖塊「%s」" % (block_name or "（未命名）"))
    return {"counts": counts, "notes": notes, "host_sheet_id": host_sheet_id}


def _infuse_tag(
    session: RhinoSession,
    tag_id: str,
    template: TagTemplate,
    objects: Mapping[str, dict],
    dupes: Sequence[str],
    has_registry: bool,
    host_sheet_id: Optional[str],
    revision,
    catalog: TagTemplateSet,
    cache: dict,
) -> str:
    family = template.family
    if family in ("height", "finish"):
        source_id = text(session.get_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY))
        missing = _missing_object_fields(family)
        if source_id is None:
            _write_fields(session, tag_id, missing)
            _stamp(session, tag_id, host_sheet_id, revision)
            return "missing_source"
        if source_id in dupes:
            _write_fields(session, tag_id, missing)
            _stamp(session, tag_id, host_sheet_id, revision)
            return "ambiguous"
        row = objects.get(source_id)
        if row is None:
            _write_fields(session, tag_id, missing)
            _stamp(session, tag_id, host_sheet_id, revision)
            return "orphaned" if has_registry else "missing_registry"
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
        resolved = _resolve_index_sheet(session, catalog, tag_id, cache)
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
        ("missing_registry", "沒有 Registry"),
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
        result = _result_from_counts(
            page_name,
            revision,
            outcome["counts"],
            outcome["notes"],
            extra=extra_warnings,
        )
        if show_message and result.ok:
            show_message(result.message)
        return result

    return run_guarded(session, action, command_id=COMMAND_ID)
