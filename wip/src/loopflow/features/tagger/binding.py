# -*- coding: utf-8 -*-
"""Tag 身分與來源欄寫入。Grab／Laser／Index 共用；不寫 Infuser 顯示欄。"""
from __future__ import annotations

import re
import uuid
from typing import Optional

from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
    TEMPLATE_ID_KEY,
    TEMPLATE_VERSION_KEY,
)
from loopflow.features.tagger.templates import TagTemplate
from loopflow.platform.rhino.session import RhinoSession

UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    stripped = str(value).strip()
    return stripped or None


def new_id() -> str:
    return str(uuid.uuid4())


def ensure_identity(
    session: RhinoSession,
    tag_id: str,
    template: TagTemplate,
    binding_mode: str,
) -> None:
    block_name = session.block_definition_name(tag_id) or template.template_id
    if text(session.get_object_user_text(tag_id, TAG_ID_KEY)) is None:
        session.set_object_user_text(tag_id, TAG_ID_KEY, new_id())
    session.set_object_user_text(tag_id, TEMPLATE_ID_KEY, block_name)
    session.set_object_user_text(tag_id, TEMPLATE_VERSION_KEY, "1")
    session.set_object_user_text(tag_id, BINDING_MODE_KEY, binding_mode)


def write_object_binding(
    session: RhinoSession,
    tag_id: str,
    template: TagTemplate,
    object_uuid: str,
) -> None:
    ensure_identity(session, tag_id, template, "object")
    session.set_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY, object_uuid)
    session.set_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY, "")


def write_block_binding(
    session: RhinoSession,
    tag_id: str,
    template: TagTemplate,
    block_name: str,
) -> None:
    ensure_identity(session, tag_id, template, "block_name")
    session.set_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY, block_name)
    session.set_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY, "")


def write_view_binding(
    session: RhinoSession,
    tag_id: str,
    template: TagTemplate,
    view_id: str,
) -> None:
    ensure_identity(session, tag_id, template, "view")
    session.set_object_user_text(tag_id, TARGET_VIEW_ID_KEY, view_id)
    session.set_object_user_text(tag_id, TARGET_SHEET_ID_KEY, "")
    session.set_object_user_text(tag_id, SOURCE_OBJECT_ID_KEY, "")
    session.set_object_user_text(tag_id, SOURCE_BLOCK_NAME_KEY, "")
