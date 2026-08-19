# -*- coding: utf-8 -*-
"""LF_TAG-O：只讀檢查全檔 Layout 頁的 Tag 是否活著或斷連。

不寫 UserText、不改顏色、不做 Repair。鎖定 Tag 仍判斷 stale／orphaned。
`TAG_DW` 與 `TAG_ELEV_0` 無來源屬正常。家具不判 orphaned。
"""
from __future__ import annotations

from typing import Callable, Dict, List, Mapping, Optional, Sequence

from loopflow.features.infuser.part import (
    PAGE_TAG_TEMPLATE_ID,
    PROJECT_ID_KEY,
    _as_uuid,
    _item_fields,
    _lookup_object_row,
    _object_index,
    _resolve_index_sheet,
    _types_by_id,
)
from loopflow.features.infuser.reader import load_published_registry
from loopflow.features.sheet.metadata import is_title_frame, registered_title_frame_names
from loopflow.features.tagger.binding import text
from loopflow.features.tagger.keys import (
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
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_TAG-O"
STAGE = "health_check"
ShowMessage = Callable[[str], None]

STATUS_HEALTHY = "healthy"
STATUS_UNBOUND = "unbound"
STATUS_ORPHANED = "orphaned"
STATUS_STALE = "stale"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_UNCHECKED = "unchecked"

PROBLEM_STATUSES = (
    STATUS_UNBOUND,
    STATUS_ORPHANED,
    STATUS_STALE,
    STATUS_AMBIGUOUS,
)


def _layout_page_names(session: RhinoSession):
    pages_fn = getattr(session, "listed_layout_pages", None)
    if not callable(pages_fn):
        return ()
    names = []
    for item in pages_fn() or ():
        name = str(item.get("name") or "").strip()
        if name and name not in names:
            names.append(name)
    return tuple(names)


def _revision_int(value) -> Optional[int]:
    raw = text(value)
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return None


def _is_stale(last_synced, registry_revision) -> bool:
    current = _revision_int(registry_revision)
    if current is None:
        return False
    synced = _revision_int(last_synced)
    if synced is None:
        return True
    return synced < current


def _empty_counts() -> Dict[str, int]:
    return {
        "scanned": 0,
        "healthy": 0,
        "unbound": 0,
        "orphaned": 0,
        "stale": 0,
        "ambiguous": 0,
        "unchecked": 0,
        "skipped_title_frame": 0,
        "skipped_manual": 0,
        "skipped_elev_0": 0,
        "locked": 0,
        "locked_disconnected": 0,
    }


def _classify_object_tag(
    session: RhinoSession,
    tag_id: str,
    objects: Mapping[str, dict],
    dupes: Sequence[str],
    types_by_id: Mapping[str, dict],
    cache: dict,
) -> str:
    source_id = text(session.get_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY))
    if source_id is None:
        return STATUS_UNBOUND
    source_key = _as_uuid(source_id) or (source_id.strip("{}").casefold() or None)
    if source_key in dupes:
        return STATUS_AMBIGUOUS
    row, _from_live = _lookup_object_row(
        session, source_id, objects, types_by_id, cache
    )
    if row is None:
        return STATUS_ORPHANED
    return STATUS_HEALTHY


def _classify_item_tag(session: RhinoSession, tag_id: str, template: TagTemplate) -> str:
    parsed = _item_fields(
        session.get_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY),
        template.source_block_name_pattern,
    )
    if parsed.ok:
        return STATUS_HEALTHY
    return STATUS_UNBOUND


def _classify_index_tag(
    session: RhinoSession,
    tag_id: str,
    catalog: TagTemplateSet,
    cache: dict,
    host_page_name: Optional[str],
) -> str:
    has_hint = any(
        text(session.get_object_user_text(tag_id, key))
        for key in (TARGET_VIEW_ID_KEY, TARGET_LAYOUT_KEY, TARGET_SHEET_ID_KEY)
    )
    if not has_hint:
        return STATUS_UNBOUND
    resolved = _resolve_index_sheet(
        session, catalog, tag_id, cache, host_page_name
    )
    if resolved.ok:
        return STATUS_HEALTHY
    reason = (resolved.blocking or ("missing_sheet",))[0]
    if reason == "missing_source":
        return STATUS_UNBOUND
    if reason == "ambiguous_sheet":
        return STATUS_AMBIGUOUS
    return STATUS_ORPHANED


def _inspect_block(
    session: RhinoSession,
    object_id: str,
    page_name: str,
    catalog: TagTemplateSet,
    registered,
    objects: Mapping[str, dict],
    dupes: Sequence[str],
    types_by_id: Mapping[str, dict],
    cache: dict,
    registry_revision,
) -> Optional[dict]:
    if not session.is_block_instance(object_id):
        return None
    block_name = session.block_definition_name(object_id) or ""
    template = catalog.by_block_name(block_name)
    if template is None:
        if is_title_frame(session, object_id, catalog, registered):
            return {
                "kind": "title_frame",
                "tag_id": object_id,
                "page_name": page_name,
                "block_name": block_name,
            }
        return {
            "kind": "unchecked",
            "status": STATUS_UNCHECKED,
            "locked": False,
            "reason": "unknown_template",
            "tag_id": object_id,
            "page_name": page_name,
            "block_name": block_name,
        }
    if template.role == "title_frame":
        return {
            "kind": "title_frame",
            "tag_id": object_id,
            "page_name": page_name,
            "block_name": block_name,
        }

    locked = is_tag_locked(session, object_id)
    family = template.family
    reason = None
    if template.template_id == "TAG_DW" or "manual" in template.binding_modes:
        status = STATUS_HEALTHY
        reason = "manual"
    elif template.template_id == PAGE_TAG_TEMPLATE_ID:
        status = STATUS_HEALTHY
        reason = "elev_0"
    elif family in ("height", "finish"):
        status = _classify_object_tag(
            session, object_id, objects, dupes, types_by_id, cache
        )
        reason = status
    elif family == "item":
        status = _classify_item_tag(session, object_id, template)
        reason = status
    elif template.template_id in INDEX_TEMPLATE_IDS or family == "index":
        status = _classify_index_tag(
            session, object_id, catalog, cache, page_name
        )
        reason = status
    else:
        return {
            "kind": "unchecked",
            "status": STATUS_UNCHECKED,
            "locked": locked,
            "reason": "unknown_template",
            "tag_id": object_id,
            "page_name": page_name,
            "block_name": block_name,
        }

    if (
        status == STATUS_HEALTHY
        and reason not in ("manual", "elev_0")
        and _is_stale(
            session.get_object_user_text(object_id, LAST_SYNCED_REVISION_KEY),
            registry_revision,
        )
    ):
        status = STATUS_STALE
        reason = STATUS_STALE

    return {
        "kind": "tag",
        "status": status,
        "locked": locked,
        "reason": reason,
        "tag_id": object_id,
        "page_name": page_name,
        "block_name": block_name,
        "template_id": template.template_id,
        "family": family,
    }


def inspect_pages(
    session: RhinoSession,
    catalog: TagTemplateSet,
    payload: Optional[Mapping],
    revision,
) -> dict:
    objects, dupes = _object_index(payload)
    types_by_id = _types_by_id(payload)
    cache = {}
    counts = _empty_counts()
    issues: List[dict] = []
    objects_fn = getattr(session, "objects_on_layout_page", None)
    registered = registered_title_frame_names(session)
    page_names = _layout_page_names(session)

    for page_name in page_names:
        page_ids = tuple(objects_fn(page_name) or ()) if callable(objects_fn) else ()
        for object_id in page_ids:
            row = _inspect_block(
                session,
                object_id,
                page_name,
                catalog,
                registered,
                objects,
                dupes,
                types_by_id,
                cache,
                revision,
            )
            if row is None:
                continue
            if row["kind"] == "title_frame":
                counts["skipped_title_frame"] += 1
                continue
            if row["kind"] == "unchecked":
                counts["unchecked"] += 1
                issues.append(row)
                continue
            counts["scanned"] += 1
            status = row["status"]
            counts[status] = counts.get(status, 0) + 1
            if row.get("reason") == "manual":
                counts["skipped_manual"] += 1
            elif row.get("reason") == "elev_0":
                counts["skipped_elev_0"] += 1
            if row["locked"]:
                counts["locked"] += 1
                if status in PROBLEM_STATUSES:
                    counts["locked_disconnected"] += 1
            if status in PROBLEM_STATUSES or row["kind"] == "unchecked":
                issues.append(row)
    return {
        "counts": counts,
        "issues": tuple(issues),
        "page_names": page_names,
        "page_count": len(page_names),
        "registry_revision": revision,
    }


def _summary(counts: Mapping[str, int], revision, notes: Sequence[str]) -> str:
    lines = ["已檢查 %s 個 Tag。" % counts.get("scanned", 0)]
    if revision not in (None, ""):
        lines.append("Registry revision %s。" % revision)
    lines.append("活著 %s。" % counts.get("healthy", 0))
    problems = []
    labels = (
        ("unbound", "缺來源"),
        ("orphaned", "來源不在"),
        ("stale", "過期未同步"),
        ("ambiguous", "來源歧義"),
    )
    for key, label in labels:
        if counts.get(key):
            problems.append("%s %s" % (label, counts[key]))
    if problems:
        lines.append("斷連：%s。" % "、".join(problems))
    if counts.get("locked_disconnected"):
        lines.append("鎖定仍斷連 %s。" % counts["locked_disconnected"])
    if counts.get("unchecked"):
        lines.append("未檢查（未知圖塊）%s，不計入通過。" % counts["unchecked"])
    extra = []
    if counts.get("skipped_title_frame"):
        extra.append("圖框 %s" % counts["skipped_title_frame"])
    if counts.get("skipped_manual"):
        extra.append("門窗 %s" % counts["skipped_manual"])
    if counts.get("skipped_elev_0"):
        extra.append("TAG_ELEV_0 %s" % counts["skipped_elev_0"])
    if extra:
        lines.append("涵蓋但不判 unbound：%s。" % "、".join(extra))
    lines.append("只讀，不改 Tag、不改顏色。Repair 尚未實作。")
    for note in notes[:6]:
        lines.append(note)
    return "\n".join(lines)


def run_tag_o(
    session: RhinoSession,
    *,
    catalog: Optional[TagTemplateSet] = None,
    environ: Optional[Mapping[str, str]] = None,
    registry: Optional[Mapping] = None,
    show_message: Optional[ShowMessage] = None,
) -> results.Result:
    """全檔 Layout 頁只讀檢查。不寫入。"""
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
    page_names = _layout_page_names(session)
    if not page_names:
        return results.blocked(
            STAGE,
            "這份檔案沒有 Layout 頁，已停止，不寫入。",
            ("missing_layout_page",),
            command_id=COMMAND_ID,
        )
    loaded = catalog
    if loaded is None:
        templates = load_tag_templates()
        if not templates.ok:
            return templates
        loaded = templates.details["catalog"]

    payload = registry
    revision = None
    extra_warnings = {}
    notes: List[str] = []
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
            if warning == "missing_registry":
                notes.append("沒有 Registry，無法判斷過期，仍檢查來源是否還在。")
            elif warning == "used_last_good":
                notes.append("正式 Registry 不在，改用 last-good。")
            elif warning == "missing_project_id":
                notes.append("文件沒有合法 project_id，無法讀 Registry。")
    elif isinstance(payload, Mapping):
        revision = payload.get("registry_revision")

    def action(current: RhinoSession) -> results.Result:
        outcome = inspect_pages(current, loaded, payload, revision)
        counts = outcome["counts"]
        warnings = []
        for key in PROBLEM_STATUSES + (STATUS_UNCHECKED,):
            if counts.get(key):
                warnings.append(key)
        for key in extra_warnings:
            if key not in warnings:
                warnings.append(key)
        details = {
            "counts": dict(counts),
            "issues": outcome["issues"],
            "page_count": outcome["page_count"],
            "page_names": outcome["page_names"],
            "registry_revision": revision,
        }
        message = _summary(counts, revision, notes)
        if warnings:
            result = results.ok_with_warnings(
                STAGE,
                message,
                tuple(warnings),
                command_id=COMMAND_ID,
                details=details,
            )
        else:
            result = results.ok(
                STAGE, message, command_id=COMMAND_ID, details=details
            )
        if show_message and result.ok:
            show_message(result.message)
        return result

    return run_guarded(session, action, command_id=COMMAND_ID)
