# -*- coding: utf-8 -*-
"""LF_Tagger_Grab：Layout 選 Tag，點進 Detail 再選來源。只寫 binding。不填 Infuser 顯示欄。"""
from __future__ import annotations

import re
import uuid
from typing import Callable, Optional

from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    GRAB_BLOCK_TEMPLATE_IDS,
    GRAB_OBJECT_TEMPLATE_IDS,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TEMPLATE_ID_KEY,
    TEMPLATE_VERSION_KEY,
    is_lock_true,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.foundation.usertext import OBJECT_ID_KEY, read_text
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Tagger_Grab"
UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
Pick = Callable[[RhinoSession], Optional[str]]


def _text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _new_id() -> str:
    return str(uuid.uuid4())


def _refuse_reason(template: TagTemplate) -> str:
    if template.template_id == "TAG_DW" or "manual" in template.binding_modes:
        return "「%s」是純手動標籤，不接受 Grab 綁定。" % template.template_id
    if template.template_id.endswith("_LASER"):
        return "「%s」請用 Laser 綁定，Grab 不寫入。" % template.template_id
    if template.family == "index":
        return "「%s」請用 Index 綁定，Grab 不寫入。" % template.template_id
    if template.role == "title_frame" or "none" in template.binding_modes:
        return "「%s」不綁模型來源，Grab 不寫入。" % template.template_id
    return "「%s」不是 Grab 可用的標籤，已停止，不寫入。" % template.template_id


def _ensure_identity(session: RhinoSession, tag_id: str, template: TagTemplate, binding_mode: str) -> None:
    block_name = session.block_definition_name(tag_id) or template.template_id
    if _text(session.get_object_user_text(tag_id, TAG_ID_KEY)) is None:
        session.set_object_user_text(tag_id, TAG_ID_KEY, _new_id())
    session.set_object_user_text(tag_id, TEMPLATE_ID_KEY, block_name)
    session.set_object_user_text(tag_id, TEMPLATE_VERSION_KEY, "1")
    session.set_object_user_text(tag_id, BINDING_MODE_KEY, binding_mode)


def _write_object_binding(session: RhinoSession, tag_id: str, template: TagTemplate, object_uuid: str) -> None:
    _ensure_identity(session, tag_id, template, "object")
    session.set_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY, object_uuid)
    session.set_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY, "")


def _write_block_binding(session: RhinoSession, tag_id: str, template: TagTemplate, block_name: str) -> None:
    _ensure_identity(session, tag_id, template, "block_name")
    session.set_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY, block_name)
    session.set_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY, "")


def _default_pick_tag(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_block_instance

    return pick_block_instance("選取要綁定的 Tag（Esc 取消）")


def _default_pick_object(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_source_through_detail

    return pick_source_through_detail("選取模型來源（Esc 取消）")


def _default_pick_block(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import GRAB_BLOCK_FILTER, pick_source_through_detail

    return pick_source_through_detail("選取家具圖塊來源（Esc 取消）", GRAB_BLOCK_FILTER)


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
            "請選 Tag 圖塊。已停止，不寫入。",
            ("not_a_block",),
            command_id=COMMAND_ID,
        )
    block_name = session.block_definition_name(tag_id)
    template = catalog.by_block_name(block_name or "")
    if template is None:
        return results.blocked(
            "bind_tag",
            "未知圖塊「%s」，已停止，不寫入。" % (block_name or "（未命名）"),
            ("unknown_block",),
            command_id=COMMAND_ID,
            details={"block_name": block_name},
        )
    if is_lock_true(session.get_object_user_text(tag_id, LOCK_STATE_KEY)):
        return results.blocked(
            "bind_tag",
            "此 Tag 已鎖定，請先解除鎖定再綁定。",
            ("tag_locked",),
            command_id=COMMAND_ID,
        )
    if template.template_id in GRAB_OBJECT_TEMPLATE_IDS:
        object_uuid = read_text(session, source_id, OBJECT_ID_KEY)
        if object_uuid is None or not UUID_V4_RE.match(object_uuid):
            return results.blocked(
                "bind_tag",
                "來源物件尚未寫入 UUID。請先跑 Nexus 寫入模型 Metadata。",
                ("missing_object_id",),
                command_id=COMMAND_ID,
            )
        _write_object_binding(session, tag_id, template, object_uuid)
        return results.ok(
            "bind_tag",
            "已綁定來源 UUID。",
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
                "家具 Tag 請選家具圖塊當來源。已停止，不寫入。",
                ("source_not_block",),
                command_id=COMMAND_ID,
            )
        source_name = session.block_definition_name(source_id) or ""
        pattern = template.source_block_name_pattern or r"^([A-Za-z]+)-([0-9]+)__(.+)$"
        if not re.match(pattern, source_name):
            return results.blocked(
                "bind_tag",
                "家具圖塊名稱格式不正確：%s。應為 FF-01__Chair-1。" % (source_name or "（未命名）"),
                ("invalid_block_name",),
                command_id=COMMAND_ID,
                details={"source_block_name": source_name},
            )
        _write_block_binding(session, tag_id, template, source_name)
        return results.ok(
            "bind_tag",
            "已綁定家具圖塊名稱。",
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
            "文件尚未寫入 schema，已停止，不寫入。",
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
                "已取消 Grab。",
                command_id=COMMAND_ID,
            )
        if current.get_view_state(tag_id) is None:
            return results.blocked(
                "bind_tag",
                "找不到選取的 Tag。",
                ("missing_tag",),
                command_id=COMMAND_ID,
            )
        if not current.is_block_instance(tag_id):
            return results.blocked(
                "bind_tag",
                "請選 Tag 圖塊。已停止，不寫入。",
                ("not_a_block",),
                command_id=COMMAND_ID,
            )
        block_name = current.block_definition_name(tag_id)
        template = loaded.by_block_name(block_name or "")
        if template is None:
            return results.blocked(
                "bind_tag",
                "未知圖塊「%s」，已停止，不寫入。" % (block_name or "（未命名）"),
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
        if is_lock_true(current.get_object_user_text(tag_id, LOCK_STATE_KEY)):
            return results.blocked(
                "bind_tag",
                "此 Tag 已鎖定，請先解除鎖定再綁定。",
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
                "已取消 Grab。",
                command_id=COMMAND_ID,
            )
        return bind_tag(current, tag_id, source_id, loaded)

    return run_guarded(session, action, command_id=COMMAND_ID)
