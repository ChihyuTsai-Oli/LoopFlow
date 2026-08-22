# -*- coding: utf-8 -*-
"""LF_TAG-O：檢查全檔 Layout 頁的 Tag 是否活著或斷連。

過期把自動欄改成「!」並塗橘；斷連改成「?」並塗紅。未綁定不列入面板。
鎖定 Tag 不改文字與顏色。只檢查與上色，不實作 Repair。
只檢查 D08 Tag 圖塊；未知圖塊不列入。
`TAG_DW` 與 `TAG_ELEV_0` 無來源屬正常。家具跟綁定實例：改名要更新，刪除為斷連。
"""
from __future__ import annotations

import os
import time
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.health.appearance import (
    MODE_BROKEN,
    MODE_CLEAR,
    MODE_STALE,
    apply_tag_health,
)
from loopflow.features.infuser.part import (
    PAGE_TAG_TEMPLATE_ID,
    _as_uuid,
    _item_fields,
    _item_source_name,
    _iter_live_source_ids,
    _lookup_object_row,
    _object_index,
    _resolve_index_sheet,
    _types_by_id,
)
from loopflow.features.dictionary.layer_paths import project_id_from_session
from loopflow.features.infuser import keys as infuser_keys
from loopflow.features.infuser.reader import load_published_registry
from loopflow.features.sheet.metadata import is_title_frame, registered_title_frame_names
from loopflow.features.tagger.binding import text
from loopflow.features.tagger.keys import (
    HEALTH_STATE_BROKEN,
    HEALTH_STATE_KEY,
    HEALTH_STATE_STALE,
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
from loopflow.features.viewer.inspect import check_document_schema, ensure_project_schema
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    OBJECT_ID_KEY,
    SPACE_DISPLAY_KEY,
    SPACE_FRAME_DISPLAY_KEY,
    read_text,
)
from loopflow.platform.rhino.session import RhinoSession, run_guarded
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_TAG-O"
STAGE = "health_check"
ShowMessage = Callable[[str], None]
ShowPanel = Callable[[Sequence[tuple]], None]

COLOR_HEAD = "head"
COLOR_DIM = "dim"
COLOR_TEXT = "text"
COLOR_OK = "ok"
COLOR_WARN = "warn"
COLOR_BROK = "brok"
COLOR_RULE = "rule"
EXT_SPACE = "EXT"
PANEL_TITLE = "TAG-O ~ Holy Cargo ~~"


def unassigned_page() -> str:
    return t("tag_o.001")


STATUS_HEALTHY = "healthy"
STATUS_UNBOUND = "unbound"
STATUS_ORPHANED = "orphaned"
STATUS_STALE = "stale"
STATUS_MISSING_TARGET = "missing_target"
STATUS_AMBIGUOUS = "ambiguous"
STATUS_UNCHECKED = "unchecked"

PROBLEM_STATUSES = (
    STATUS_UNBOUND,
    STATUS_ORPHANED,
    STATUS_STALE,
    STATUS_MISSING_TARGET,
    STATUS_AMBIGUOUS,
)
BROKEN_STATUSES = (STATUS_ORPHANED, STATUS_MISSING_TARGET)
STALE_STATUSES = (STATUS_STALE, STATUS_AMBIGUOUS)

def status_line():
    return {
        STATUS_HEALTHY: (t("tag_o.002"), COLOR_OK),
        STATUS_UNBOUND: (t("tag_o.003"), COLOR_WARN),
        STATUS_ORPHANED: (t("tag_o.004"), COLOR_BROK),
        STATUS_STALE: (t("tag_o.005"), COLOR_WARN),
        STATUS_MISSING_TARGET: (t("tag_o.004"), COLOR_BROK),
        STATUS_AMBIGUOUS: (t("tag_o.005"), COLOR_WARN),
        STATUS_UNCHECKED: (t("tag_o.006"), COLOR_DIM),
    }


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


def _binding_text(value) -> Optional[str]:
    """來源／顯示欄：空值與 Infuser 寫的 '-' 都算沒有。"""
    raw = text(value)
    if raw is None or raw == infuser_keys.MISSING_DISPLAY:
        return None
    return raw


def _read_binding(session: RhinoSession, object_id: str, key: str) -> Optional[str]:
    return _binding_text(session.get_object_user_text(object_id, key))


def _display_keys(template: TagTemplate):
    family = template.family
    if family == "height":
        return infuser_keys.HEIGHT_RENDER_KEYS
    if family == "finish":
        return infuser_keys.FINISH_RENDER_KEYS
    if family == "item":
        return infuser_keys.ITEM_RENDER_KEYS
    if template.template_id in INDEX_TEMPLATE_IDS or family == "index":
        return infuser_keys.INDEX_RENDER_KEYS
    return ()


def _has_display_mark(session: RhinoSession, tag_id: str, template: TagTemplate, mark: str) -> bool:
    for key in _display_keys(template):
        if text(session.get_object_user_text(tag_id, key)) == mark:
            return True
    return False


def _display_is_empty(session: RhinoSession, tag_id: str, template: TagTemplate) -> bool:
    keys = _display_keys(template)
    if not keys:
        return False
    return all(_read_binding(session, tag_id, key) is None for key in keys)


def _issue_sort_key(issue: Mapping, page_names: Sequence[str]):
    page = str(issue.get("page_name") or "")
    try:
        page_index = list(page_names).index(page)
    except ValueError:
        page_index = len(page_names) + (0 if page == unassigned_page() else 1)
    orphaned = 0 if issue.get("status") in BROKEN_STATUSES else 1
    return (
        page_index,
        orphaned,
        str(issue.get("block_name") or ""),
        str(issue.get("tag_id") or ""),
    )


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
        "missing_target": 0,
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
    source_id = _read_binding(session, tag_id, SOURCE_OBJECT_ID_KEY)
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
    source_name, source_status = _item_source_name(session, tag_id)
    if source_status == "orphaned":
        return STATUS_ORPHANED
    parsed = _item_fields(source_name, template.source_block_name_pattern)
    if not parsed.ok:
        return STATUS_UNBOUND
    fields = (parsed.details or {}).get("fields") or {}
    for key, value in fields.items():
        if _read_binding(session, tag_id, key) != text(value):
            return STATUS_STALE
    return STATUS_HEALTHY


def _classify_index_tag(
    session: RhinoSession,
    tag_id: str,
    catalog: TagTemplateSet,
    cache: dict,
    host_page_name: Optional[str],
) -> str:
    has_hint = any(
        _read_binding(session, tag_id, key)
        for key in (TARGET_VIEW_ID_KEY, TARGET_LAYOUT_KEY, TARGET_SHEET_ID_KEY)
    )
    if not has_hint:
        return STATUS_UNBOUND
    resolved = _resolve_index_sheet(
        session, catalog, tag_id, cache, host_page_name
    )
    if not resolved.ok:
        reason = (resolved.blocking or ("missing_sheet",))[0]
        if reason == "missing_source":
            return STATUS_UNBOUND
        if reason == "ambiguous_sheet":
            return STATUS_AMBIGUOUS
        return STATUS_MISSING_TARGET
    fields = (resolved.details or {}).get("fields") or {}
    for key in infuser_keys.INDEX_RENDER_KEYS:
        expected = text(fields.get(key))
        actual = text(session.get_object_user_text(tag_id, key))
        if actual != expected:
            return STATUS_STALE
    return STATUS_HEALTHY


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
        return None
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
        and _display_is_empty(session, object_id, template)
    ):
        status = STATUS_STALE
        reason = STATUS_STALE
    elif (
        status == STATUS_HEALTHY
        and reason not in ("manual", "elev_0")
        and _is_stale(
            session.get_object_user_text(object_id, LAST_SYNCED_REVISION_KEY),
            registry_revision,
        )
    ):
        status = STATUS_STALE
        reason = STATUS_STALE

    if reason not in ("manual", "elev_0"):
        health = text(session.get_object_user_text(object_id, HEALTH_STATE_KEY))
        if health == HEALTH_STATE_BROKEN and status != STATUS_UNBOUND:
            status = STATUS_MISSING_TARGET
            reason = STATUS_MISSING_TARGET
        elif status == STATUS_HEALTHY and (
            health == HEALTH_STATE_STALE
            or _has_display_mark(session, object_id, template, infuser_keys.STALE_DISPLAY)
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
        "source_object_id": _read_binding(session, object_id, SOURCE_OBJECT_ID_KEY),
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
    tags: List[dict] = []
    objects_fn = getattr(session, "objects_on_layout_page", None)
    extra_fn = getattr(session, "paper_space_object_ids", None)
    page_of = getattr(session, "layout_page_name_of", None)
    registered = registered_title_frame_names(session)
    page_names = _layout_page_names(session)
    seen = set()
    targets: List[Tuple[str, str]] = []

    for page_name in page_names:
        page_ids = tuple(objects_fn(page_name) or ()) if callable(objects_fn) else ()
        for object_id in page_ids:
            if object_id in seen:
                continue
            seen.add(object_id)
            targets.append((page_name, object_id))
    extra_ids = tuple(extra_fn() or ()) if callable(extra_fn) else ()
    for object_id in extra_ids:
        if object_id in seen:
            continue
        seen.add(object_id)
        host = page_of(object_id) if callable(page_of) else None
        targets.append((str(host or unassigned_page()), object_id))

    for page_name, object_id in targets:
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
        tags.append(row)
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
        if status in PROBLEM_STATUSES:
            issues.append(row)
    return {
        "counts": counts,
        "issues": tuple(issues),
        "tags": tuple(tags),
        "page_names": page_names,
        "page_count": len(page_names),
        "registry_revision": revision,
    }


def _listed_spaces(session: RhinoSession) -> Tuple[str, ...]:
    found = []
    for object_id in _iter_live_source_ids(session):
        name = read_text(session, object_id, SPACE_FRAME_DISPLAY_KEY)
        if name is None:
            continue
        if name == EXT_SPACE:
            continue
        if name not in found:
            found.append(name)
    return tuple(found)


def inspect_space_coverage(
    session: RhinoSession,
    payload: Optional[Mapping],
    tags: Sequence[Mapping],
) -> Tuple[Tuple[str, ...], Optional[str]]:
    spaces = _listed_spaces(session)
    if not spaces:
        return (), t("tag_o.009")
    objects, _dupes = _object_index(payload)
    types_by_id = _types_by_id(payload)
    cache = {}
    covered = []
    for row in tags:
        if row.get("family") != "finish":
            continue
        if row.get("status") in (STATUS_UNBOUND, STATUS_ORPHANED, STATUS_UNCHECKED):
            continue
        source_id = text(row.get("source_object_id"))
        if source_id is None:
            continue
        obj_row, _from_live = _lookup_object_row(
            session, source_id, objects, types_by_id, cache
        )
        space = text((obj_row or {}).get("space_display"))
        if space is None:
            space = _space_from_live(session, source_id)
        if space and space != EXT_SPACE and space not in covered:
            covered.append(space)
    missing = tuple(name for name in spaces if name not in covered)
    return missing, None


def _space_from_live(session: RhinoSession, source_id: str) -> Optional[str]:
    wanted = _as_uuid(source_id) or (str(source_id).strip("{}").casefold() or None)
    if wanted is None:
        return None
    for object_id in _iter_live_source_ids(session):
        uid = _as_uuid(read_text(session, object_id, OBJECT_ID_KEY))
        if uid == wanted:
            return read_text(session, object_id, SPACE_DISPLAY_KEY)
    return None


def _doc_label(session: RhinoSession) -> str:
    getter = getattr(session, "document_path", None)
    raw = getter() if callable(getter) else getattr(session, "_document_path", None)
    if not raw:
        return t("tag_o.007")
    return os.path.basename(str(raw))


def _panel_visible(row: Mapping) -> bool:
    if row.get("kind") != "tag":
        return False
    if row.get("reason") in ("manual", "elev_0"):
        return False
    return row.get("status") != STATUS_UNBOUND


def _apply_health_rows(session: RhinoSession, catalog: TagTemplateSet, tags) -> None:
    for row in tags:
        if row.get("kind") != "tag":
            continue
        if row.get("locked") or row.get("reason") in ("manual", "elev_0"):
            continue
        status = row.get("status")
        if status == STATUS_UNBOUND:
            continue
        template = catalog.by_block_name(str(row.get("block_name") or ""))
        keys = _display_keys(template) if template else ()
        tag_id = str(row.get("tag_id") or "")
        if not tag_id:
            continue
        if status in STALE_STATUSES:
            apply_tag_health(session, tag_id, keys, MODE_STALE)
        elif status in BROKEN_STATUSES:
            apply_tag_health(session, tag_id, keys, MODE_BROKEN)
        elif status == STATUS_HEALTHY:
            apply_tag_health(session, tag_id, keys, MODE_CLEAR)


def build_panel_lines(
    outcome: Mapping,
    *,
    doc_name: str,
    notes: Sequence[str] = (),
    now: Optional[str] = None,
) -> Tuple[tuple, ...]:
    """色碼列表：已綁定 Tag 依頁序，頁與頁之間灰線。點選可跳頁。"""
    stamp = now or time.strftime("%Y-%m-%d  %H:%M:%S")
    revision = outcome.get("registry_revision")
    counts = outcome.get("counts") or {}
    scanned = counts.get("scanned", 0)
    page_names = tuple(outcome.get("page_names") or ())
    rows = [row for row in (outcome.get("tags") or ()) if _panel_visible(row)]
    lines: List[tuple] = [
        (PANEL_TITLE, COLOR_HEAD),
        (t("tag_o.016") % doc_name, COLOR_DIM),
        (t("tag_o.017") % stamp, COLOR_DIM),
        (t("tag_o.018") % scanned, COLOR_DIM),
    ]
    if revision not in (None, ""):
        lines.append(("Registry revision %s" % revision, COLOR_DIM))
    for note in notes:
        lines.append((str(note), COLOR_DIM))
    lines.append(("", COLOR_TEXT))

    lines.append((t("tag_o.019") % len(rows), COLOR_HEAD))
    if not rows:
        if scanned == 0:
            lines.append(("  " + t("tag_o.030"), COLOR_DIM))
        else:
            lines.append(("  " + t("tag_o.031"), COLOR_DIM))
    else:
        ranked = sorted(rows, key=lambda row: _issue_sort_key(row, page_names))
        names = [str(row.get("block_name") or "") for row in ranked]
        width = max((len(name) for name in names), default=0)
        last_page = None
        for row in ranked:
            page = str(row.get("page_name") or t("tag_o.032"))
            if last_page is not None and page != last_page:
                lines.append(("", COLOR_RULE))
            last_page = page
            status = row.get("status")
            label, color = status_line().get(status, (str(status or ""), COLOR_TEXT))
            lock = "  " + t("tag_o.020") if row.get("locked") else ""
            name = str(row.get("block_name") or "").ljust(width)
            lines.append(
                (
                    "  [%s]  %s  ->  %s%s" % (label, name, page, lock),
                    color,
                    str(row.get("tag_id") or ""),
                    page,
                )
            )
        lines.append((t("tag_o.021"), COLOR_DIM))

    lines.append(("", COLOR_TEXT))
    missing = tuple(outcome.get("space_missing") or ())
    space_note = outcome.get("space_note")
    if missing:
        lines.append(
            (t("tag_o.033") % len(missing), COLOR_HEAD)
        )
    else:
        lines.append((t("tag_o.022"), COLOR_HEAD))
    if space_note:
        lines.append(("  ［說明］%s" % space_note, COLOR_DIM))
    if not missing and not space_note:
        lines.append(("  所有空間都有 Finish Tag", COLOR_OK))
    for space in missing:
        lines.append(("  %s" % space, COLOR_TEXT))

    lines.append(("", COLOR_TEXT))
    lines.append((t("tag_o.010"), COLOR_DIM))
    return tuple(lines)


def _summary(counts: Mapping[str, int], revision, notes: Sequence[str]) -> str:
    lines = [t("tag_o.011") % counts.get("scanned", 0)]
    if revision not in (None, ""):
        lines.append("Registry revision %s。" % revision)
    lines.append(t("tag_o.012") % counts.get("healthy", 0))
    problems = []
    labels = (
        ("unbound", t("tag_o.003")),
        ("orphaned", t("tag_o.004")),
        ("missing_target", t("tag_o.004")),
        ("stale", t("tag_o.013")),
        ("ambiguous", t("tag_o.014")),
    )
    for key, label in labels:
        if counts.get(key):
            problems.append("%s %s" % (label, counts[key]))
    if problems:
        lines.append(t("tag_o.024") % "、".join(problems))
    if counts.get("locked_disconnected"):
        lines.append(t("tag_o.025") % counts["locked_disconnected"])
    if counts.get("unchecked"):
        lines.append(t("tag_o.026") % counts["unchecked"])
    extra = []
    if counts.get("skipped_title_frame"):
        extra.append(t("tag_o.027") % counts["skipped_title_frame"])
    if counts.get("skipped_manual"):
        extra.append(t("tag_o.028") % counts["skipped_manual"])
    if counts.get("skipped_elev_0"):
        extra.append("TAG_ELEV_0 %s" % counts["skipped_elev_0"])
    if extra:
        lines.append(t("tag_o.029") % "、".join(extra))
    lines.append(t("tag_o.008"))
    for note in notes[:6]:
        lines.append(note)
    return "\n".join(lines)


def run_tag_o(
    session: RhinoSession,
    *,
    catalog: Optional[TagTemplateSet] = None,
    registry: Optional[Mapping] = None,
    show_message: Optional[ShowMessage] = None,
    show_panel: Optional[ShowPanel] = None,
) -> results.Result:
    """全檔 Layout 頁檢查。過期／斷連會改 Tag 外觀。"""
    ensure_project_schema(session)
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
            t("catalog.008"),
            ("missing_document_schema",),
            command_id=COMMAND_ID,
        )
    page_names = _layout_page_names(session)
    if not page_names:
        return results.blocked(
            STAGE,
            t("tag_o.015"),
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
            project_id_from_session(session),
            document_path=session.document_path() if hasattr(session, "document_path") else None,
            command_id=COMMAND_ID,
        )
        if not registry_result.ok:
            return registry_result
        payload = registry_result.details.get("payload")
        revision = registry_result.details.get("registry_revision")
        for warning in registry_result.warnings or ():
            extra_warnings[warning] = True
            if warning == "missing_registry":
                notes.append(t("tag_o.035"))
            elif warning == "used_last_good":
                notes.append(t("tag_o.036"))
            elif warning == "missing_project_id":
                notes.append(t("tag_o.037"))
    elif isinstance(payload, Mapping):
        revision = payload.get("registry_revision")

    def action(current: RhinoSession) -> results.Result:
        outcome = inspect_pages(current, loaded, payload, revision)
        missing, space_note = inspect_space_coverage(
            current, payload, outcome.get("tags") or ()
        )
        counts = outcome["counts"]
        warnings = []
        for key in PROBLEM_STATUSES + (STATUS_UNCHECKED,):
            if counts.get(key):
                warnings.append(key)
        if missing:
            warnings.append("uncovered_space")
        for key in extra_warnings:
            if key not in warnings:
                warnings.append(key)
        panel_lines = build_panel_lines(
            {
                **outcome,
                "space_missing": missing,
                "space_note": space_note,
            },
            doc_name=_doc_label(current),
            notes=notes,
        )
        details = {
            "counts": dict(counts),
            "issues": outcome["issues"],
            "tags": outcome.get("tags") or (),
            "page_count": outcome["page_count"],
            "page_names": outcome["page_names"],
            "registry_revision": revision,
            "space_missing": missing,
            "space_note": space_note,
            "panel_lines": panel_lines,
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
        return result

    guarded = run_guarded(session, action, command_id=COMMAND_ID)
    if guarded.ok:
        _apply_health_rows(session, loaded, (guarded.details or {}).get("tags") or ())
        panel_lines = (guarded.details or {}).get("panel_lines")
        if show_panel and panel_lines is not None:
            show_panel(panel_lines)
        elif show_message:
            show_message(guarded.message)
    return guarded
