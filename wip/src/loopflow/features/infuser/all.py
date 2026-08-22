# -*- coding: utf-8 -*-
"""LF_Infuser_All：全檔 Layout 頁把 Registry／Sheet 資料注入 Tag 顯示欄。

與 Part 同一套注入規則；一次處理所有頁。取消／失敗不寫入。
"""
from __future__ import annotations

from typing import Callable, Mapping, Optional

from loopflow.features.dictionary.layer_paths import project_id_from_session
from loopflow.features.infuser.part import infuse_page, _result_from_counts
from loopflow.features.health.appearance import apply_queued_appearances
from loopflow.features.infuser.reader import load_published_registry
from loopflow.features.tagger.templates import TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema, ensure_project_schema
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Infuser_All"
STAGE = "infuse_tags"
ShowMessage = Callable[[str], None]


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


def _merge_counts(total: dict, page_counts: Mapping[str, int]) -> None:
    for key, value in page_counts.items():
        total[key] = total.get(key, 0) + int(value or 0)


def run_infuser_all(
    session: RhinoSession,
    *,
    catalog: Optional[TagTemplateSet] = None,
    registry: Optional[Mapping] = None,
    show_message: Optional[ShowMessage] = None,
) -> results.Result:
    """全檔 Layout 頁注入。取消／失敗不寫入。"""
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
    elif isinstance(payload, Mapping):
        revision = payload.get("registry_revision")

    def action(current: RhinoSession) -> results.Result:
        totals = {}
        notes = []
        used_live = False
        appearances = []
        for page_name in page_names:
            outcome = infuse_page(
                current, page_name, loaded, payload, revision, redraw=False
            )
            _merge_counts(totals, outcome["counts"])
            appearances.extend(outcome.get("appearances") or ())
            for note in outcome.get("notes") or ():
                if t("infuser.003") in str(note):
                    used_live = True
                    continue
                notes.append("%s：%s" % (page_name, note))
            if outcome.get("used_live_object"):
                used_live = True
        if used_live:
            notes.append(t("infuser.002"))
        extra = dict(extra_warnings)
        if used_live:
            extra["used_live_object"] = True
        extra["page_count"] = len(page_names)
        extra["page_names"] = tuple(page_names)
        extra["appearances"] = tuple(appearances)
        redraw = getattr(current, "redraw", None)
        if callable(redraw):
            redraw()
        result = _result_from_counts(
            t("infuser.001"),
            revision,
            totals,
            notes,
            extra=extra,
            command_id=COMMAND_ID,
            headline=t("infuser.004") % len(page_names),
        )
        if show_message and result.ok:
            show_message(result.message)
        return result

    guarded = run_guarded(session, action, command_id=COMMAND_ID)
    if guarded.ok:
        apply_queued_appearances(session, (guarded.details or {}).get("appearances"))
    return guarded
