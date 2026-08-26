# -*- coding: utf-8 -*-
"""LF_Tagger_Grab：Layout 選 Tag，點進 Detail 再選來源。只寫 binding。不填 Infuser 顯示欄。"""
from __future__ import annotations

import re
from typing import Callable, Optional, Tuple

from loopflow.features.dictionary.layer_paths import is_structure_object
from loopflow.features.tagger.binding import (
    canonical_uuid,
    write_block_binding,
    write_object_binding,
)
from loopflow.features.tagger.keys import (
    GRAB_BLOCK_TEMPLATE_IDS,
    GRAB_OBJECT_TEMPLATE_IDS,
    is_tag_locked,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.foundation.usertext import OBJECT_ID_KEY, read_text
from loopflow.platform.rhino.session import RhinoSession, run_guarded
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Tagger_Grab"
Pick = Callable[[RhinoSession], Optional[str]]


def _refuse_reason(template: TagTemplate) -> str:
    if template.template_id == "TAG_DW" or "manual" in template.binding_modes:
        return t("grab.005") % template.template_id
    if template.template_id.endswith("_LASER"):
        return t("grab.006") % template.template_id
    if template.family == "index":
        return t("grab.007") % template.template_id
    if template.role == "title_frame" or "none" in template.binding_modes:
        return t("grab.008") % template.template_id
    return t("grab.001") % template.template_id


def _default_pick_tag(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_block_instance

    return pick_block_instance(t("grab.002"))


def _default_pick_object(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_source_through_detail

    return pick_source_through_detail(t("grab.003"))


def _default_pick_block(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import GRAB_BLOCK_FILTER, pick_source_through_detail

    return pick_source_through_detail(t("grab.004"), GRAB_BLOCK_FILTER)


def resolve_grab_object_uuid(session: RhinoSession, source_id: str) -> Tuple[Optional[str], Optional[str]]:
    """圖 A 讀 `_07_UUID`；圖 B 改從 `lf_source_object_ids` 解出唯一 UUID。"""
    from loopflow.features.drawing.extract import source_object_ids

    direct = canonical_uuid(read_text(session, source_id, OBJECT_ID_KEY))
    if direct:
        return direct, None
    found = []
    for item in source_object_ids(session, source_id):
        resolved = None
        if session.get_view_state(item) is not None:
            resolved = canonical_uuid(read_text(session, item, OBJECT_ID_KEY))
        if resolved is None:
            resolved = canonical_uuid(item)
        if resolved and resolved not in found:
            found.append(resolved)
    if len(found) == 1:
        return found[0], None
    if len(found) > 1:
        return None, "ambiguous_source"
    return None, "missing_object_id"


def bind_tag(
    session: RhinoSession,
    tag_id: str,
    source_id: str,
    catalog: TagTemplateSet,
) -> results.Result:
    """依 template 分流寫入。測試可直接呼叫，不經選取。"""
    if not session.is_block_instance(tag_id):
        return results.blocked(
            "bind_tag",
            t("grab.009"),
            ("not_a_block",),
            command_id=COMMAND_ID,
        )
    block_name = session.block_definition_name(tag_id)
    template = catalog.by_block_name(block_name or "")
    if template is None:
        return results.blocked(
            "bind_tag",
            t("grab.013") % (block_name or t("grab.019")),
            ("unknown_block",),
            command_id=COMMAND_ID,
            details={"block_name": block_name},
        )
    if is_tag_locked(session, tag_id):
        return results.blocked(
            "bind_tag",
            t("grab.010"),
            ("tag_locked",),
            command_id=COMMAND_ID,
        )
    if template.template_id in GRAB_OBJECT_TEMPLATE_IDS:
        if is_structure_object(session, source_id):
            return results.blocked(
                "bind_tag",
                t("grab.021"),
                ("structure_layer",),
                command_id=COMMAND_ID,
            )
        object_uuid, reason = resolve_grab_object_uuid(session, source_id)
        if reason == "ambiguous_source":
            return results.blocked(
                "bind_tag",
                t("grab.014"),
                ("ambiguous_source",),
                command_id=COMMAND_ID,
            )
        if object_uuid is None:
            return results.blocked(
                "bind_tag",
                t("grab.015"),
                ("missing_object_id",),
                command_id=COMMAND_ID,
            )
        write_object_binding(session, tag_id, template, object_uuid)
        return results.ok(
            "bind_tag",
            t("grab.011"),
            command_id=COMMAND_ID,
            details={
                "tag_id": tag_id,
                "template_id": template.template_id,
                "binding_mode": "object",
                "source_object_id": object_uuid,
            },
        )
    if template.template_id in GRAB_BLOCK_TEMPLATE_IDS:
        if not session.is_block_instance(source_id):
            return results.blocked(
                "bind_tag",
                t("grab.016"),
                ("source_not_block",),
                command_id=COMMAND_ID,
            )
        source_name = session.block_definition_name(source_id) or ""
        pattern = template.source_block_name_pattern or r"^([A-Za-z]+)-([0-9]+)__(.+)$"
        if not re.match(pattern, source_name):
            return results.blocked(
                "bind_tag",
                t("grab.020") % (source_name or t("grab.019")),
                ("invalid_block_name",),
                command_id=COMMAND_ID,
                details={"source_block_name": source_name},
            )
        write_block_binding(session, tag_id, template, source_name, source_id)
        return results.ok(
            "bind_tag",
            t("grab.012"),
            command_id=COMMAND_ID,
            details={
                "tag_id": tag_id,
                "template_id": template.template_id,
                "binding_mode": "block_name",
                "source_block_name": source_name,
            },
        )
    return results.blocked(
        "bind_tag",
        _refuse_reason(template),
        ("unsupported_template",),
        command_id=COMMAND_ID,
        details={"template_id": template.template_id},
    )


def run_tagger_grab(
    session: RhinoSession,
    *,
    pick_tag: Optional[Pick] = None,
    pick_source: Optional[Pick] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    """選 Tag、再選來源。Esc 取消不寫入。"""
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
    loaded = catalog
    if loaded is None:
        templates = load_tag_templates()
        if not templates.ok:
            return templates
        loaded = templates.details["catalog"]
    tag_picker = pick_tag or _default_pick_tag

    def action(current: RhinoSession) -> results.Result:
        tag_id = tag_picker(current)
        if not tag_id:
            return results.cancelled(
                "bind_tag",
                t("grab.017"),
                command_id=COMMAND_ID,
            )
        if current.get_view_state(tag_id) is None:
            return results.blocked(
                "bind_tag",
                t("grab.018"),
                ("missing_tag",),
                command_id=COMMAND_ID,
            )
        if not current.is_block_instance(tag_id):
            return results.blocked(
                "bind_tag",
                t("grab.009"),
                ("not_a_block",),
                command_id=COMMAND_ID,
            )
        block_name = current.block_definition_name(tag_id)
        template = loaded.by_block_name(block_name or "")
        if template is None:
            return results.blocked(
                "bind_tag",
                t("grab.013") % (block_name or t("grab.019")),
                ("unknown_block",),
                command_id=COMMAND_ID,
                details={"block_name": block_name},
            )
        if template.template_id not in (
            GRAB_OBJECT_TEMPLATE_IDS | GRAB_BLOCK_TEMPLATE_IDS
        ):
            return results.blocked(
                "bind_tag",
                _refuse_reason(template),
                ("unsupported_template",),
                command_id=COMMAND_ID,
                details={"template_id": template.template_id},
            )
        if is_tag_locked(current, tag_id):
            return results.blocked(
                "bind_tag",
                t("grab.010"),
                ("tag_locked",),
                command_id=COMMAND_ID,
            )
        source_picker = pick_source
        if source_picker is None:
            source_picker = (
                _default_pick_block
                if template.template_id in GRAB_BLOCK_TEMPLATE_IDS
                else _default_pick_object
            )
        source_id = source_picker(current)
        if not source_id:
            return results.cancelled(
                "bind_tag",
                t("grab.017"),
                command_id=COMMAND_ID,
            )
        return bind_tag(current, tag_id, source_id, loaded)

    return run_guarded(session, action, command_id=COMMAND_ID)
