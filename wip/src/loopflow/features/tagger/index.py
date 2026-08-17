# -*- coding: utf-8 -*-
"""LF_Tagger_Index：選 Index Tag，再選已登記 View。只寫 binding。"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

from loopflow.features.tagger.binding import UUID_V4_RE, write_view_binding
from loopflow.features.tagger.keys import (
    INDEX_TEMPLATE_IDS,
    LOCK_STATE_KEY,
    is_lock_true,
)
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.view.keys import CLIPPING_PLANE_ID_KEY, SCHEMA_ID_KEY, VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Tagger_Index"
PickTag = Callable[[RhinoSession], Optional[str]]
ChooseView = Callable[[Sequence[dict]], Optional[dict]]


def _refuse_reason(template: TagTemplate) -> str:
    if template.template_id == "TAG_ELEV_0":
        return "「TAG_ELEV_0」請用 Layout ID 寫目前頁圖號，Index 不寫入。"
    if template.template_id.endswith("_LASER"):
        return "「%s」請用 Laser 綁定，Index 不寫入。" % template.template_id
    if template.template_id in ("TAG_HEIGHT_GRAB", "TAG_FINISH_GRAB") or "GRAB" in template.template_id:
        return "「%s」請用 Grab 綁定，Index 不寫入。" % template.template_id
    if template.template_id == "TAG_ITEM":
        return "家具 Tag 請用 Grab 綁定，Index 不寫入。"
    if template.template_id == "TAG_DW" or "manual" in template.binding_modes:
        return "「%s」是純手動標籤，不接受 Index 綁定。" % template.template_id
    if template.role == "title_frame" or "none" in template.binding_modes:
        return "「%s」不綁目標圖面，Index 不寫入。" % template.template_id
    return "「%s」不是 Index 可用的標籤，已停止，不寫入。" % template.template_id


def listed_views(session: RhinoSession):
    """已登記且有合法 lf_view_id 的 View 框。"""
    items = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        if session.get_object_user_text(object_id, SCHEMA_ID_KEY) != VIEW_SCHEMA_ID:
            continue
        view_id = session.get_object_user_text(object_id, VIEW_ID_KEY)
        if not view_id or not UUID_V4_RE.match(view_id):
            continue
        name = session.object_name(object_id) or ""
        if not name:
            cp_id = session.get_object_user_text(object_id, CLIPPING_PLANE_ID_KEY)
            if cp_id:
                name = session.object_name(cp_id) or ""
        items.append(
            {
                "frame_id": object_id,
                "view_id": view_id,
                "name": name,
            }
        )
    return tuple(sorted(items, key=lambda item: (item.get("name") or "").casefold()))


def view_choice_label(item: dict) -> str:
    """清單只顯示 View 名稱，不顯示 UUID。"""
    name = str(item.get("name") or "").strip()
    return name or "（未命名 View）"


def view_choice_labels(views: Sequence[dict]):
    base = [view_choice_label(item) for item in views]
    counts = {}
    for label in base:
        counts[label] = counts.get(label, 0) + 1
    seen = {}
    labels = []
    for label in base:
        if counts[label] == 1:
            labels.append(label)
            continue
        seen[label] = seen.get(label, 0) + 1
        labels.append("%s（%s）" % (label, seen[label]))
    return tuple(labels)


def _default_pick_tag(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_block_instance

    return pick_block_instance("選取要綁定的 Index Tag（Esc 取消）")


def _default_choose(views: Sequence[dict]):
    if not views:
        return None
    from loopflow.platform.rhino.prompts import ask_popup_choice

    labels = list(view_choice_labels(views))
    chosen = ask_popup_choice("請選目標 View", labels)
    if chosen is None:
        return None
    return views[labels.index(chosen)]


def bind_index_view(
    session: RhinoSession,
    tag_id: str,
    view_id: str,
    catalog: TagTemplateSet,
) -> results.Result:
    """把已登記 View 的 lf_view_id 寫進 Index Tag。測試可直接呼叫。"""
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
    if template.template_id not in INDEX_TEMPLATE_IDS:
        return results.blocked(
            "bind_tag",
            _refuse_reason(template),
            ("unsupported_template",),
            command_id=COMMAND_ID,
            details={"template_id": template.template_id},
        )
    if not view_id or not UUID_V4_RE.match(view_id):
        return results.blocked(
            "bind_tag",
            "目標 View 沒有合法的 lf_view_id。請先跑註冊 View。",
            ("missing_view",),
            command_id=COMMAND_ID,
        )
    write_view_binding(session, tag_id, template, view_id)
    return results.ok(
        "bind_tag",
        "已綁定目標 View。",
        command_id=COMMAND_ID,
        details={
            "tag_id": tag_id,
            "template_id": template.template_id,
            "binding_mode": "view",
            "target_view_id": view_id,
        },
    )


def run_tagger_index(
    session: RhinoSession,
    *,
    pick_tag: Optional[PickTag] = None,
    choose_view: Optional[ChooseView] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    """選 Index Tag，再選已登記 View。Esc 取消不寫入。"""
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
    chooser = choose_view or _default_choose

    def action(current: RhinoSession) -> results.Result:
        tag_id = tag_picker(current)
        if not tag_id:
            return results.cancelled(
                "bind_tag",
                "已取消 Index。",
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
        if template.template_id not in INDEX_TEMPLATE_IDS:
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
        views = listed_views(current)
        if not views:
            return results.blocked(
                "bind_tag",
                "沒有已登記的 View。請先跑註冊 View。",
                ("missing_view",),
                command_id=COMMAND_ID,
            )
        chosen = chooser(views)
        if not chosen:
            return results.cancelled(
                "bind_tag",
                "已取消 Index。",
                command_id=COMMAND_ID,
            )
        view_id = chosen.get("view_id") or ""
        bound = bind_index_view(current, tag_id, view_id, loaded)
        if bound.ok:
            details = dict(bound.details)
            details["frame_id"] = chosen.get("frame_id")
            return results.ok(bound.stage, bound.message, command_id=COMMAND_ID, details=details)
        return bound

    return run_guarded(session, action, command_id=COMMAND_ID)
