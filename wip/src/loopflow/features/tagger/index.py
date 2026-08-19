# -*- coding: utf-8 -*-
"""LF_Tagger_Index：選 Index Tag，再選 Layout Detail，寫唯一對到的 View。"""
from __future__ import annotations

from typing import Callable, Optional, Sequence

from loopflow.features.tagger.binding import canonical_uuid, write_view_binding
from loopflow.features.tagger.keys import (
    INDEX_TEMPLATE_IDS,
    is_tag_locked,
)
from loopflow.features.tagger.laser import view_frames_containing
from loopflow.features.tagger.templates import TagTemplate, TagTemplateSet, load_tag_templates
from loopflow.features.view.keys import CLIPPING_PLANE_ID_KEY, SCHEMA_ID_KEY, VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Tagger_Index"
PickTag = Callable[[RhinoSession], Optional[str]]
ChooseDetail = Callable[[Sequence[dict]], Optional[dict]]


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
        view_id = canonical_uuid(session.get_object_user_text(object_id, VIEW_ID_KEY))
        if not view_id:
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


def listed_details(session: RhinoSession):
    """全檔 Layout 的 Detail，依頁碼、頁名、Detail 名排序。"""
    getter = getattr(session, "listed_layout_details", None)
    raw = getter() if callable(getter) else ()
    items = [dict(item) for item in raw or ()]
    return tuple(
        sorted(
            items,
            key=lambda item: (
                int(item.get("page_number") or 0),
                str(item.get("layout") or "").casefold(),
                str(item.get("dv_name") or "").casefold(),
            ),
        )
    )


def view_choice_label(item: dict) -> str:
    """清單只顯示 View 名稱，不顯示 UUID。"""
    name = str(item.get("name") or "").strip()
    return name or "（未命名 View）"


def view_choice_labels(views: Sequence[dict]):
    return _unique_labels([view_choice_label(item) for item in views])


def detail_choice_label(item: dict) -> str:
    """清單顯示頁名與 Detail 名，不顯示 GUID。"""
    layout = str(item.get("layout") or "").strip() or "（未命名頁）"
    name = str(item.get("dv_name") or "").strip() or "（未命名 Detail）"
    return "%s    %s" % (layout, name)


def detail_choice_labels(items: Sequence[dict]):
    return _unique_labels([detail_choice_label(item) for item in items])


def _unique_labels(base):
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


def with_detail_labels(items: Sequence[dict]):
    labels = detail_choice_labels(items)
    rows = []
    for item, label in zip(items, labels):
        row = dict(item)
        row["label"] = label
        rows.append(row)
    return tuple(rows)


def preview_detail(session: RhinoSession, item: dict) -> None:
    zoomer = getattr(session, "zoom_to_layout_detail", None)
    if not callable(zoomer):
        return
    zoomer(str(item.get("layout") or ""), str(item.get("detail_id") or ""))


def resolve_view_for_detail(session: RhinoSession, item: dict) -> results.Result:
    """用 Detail 模型空間中心對 View 框；恰好一個才回傳 view_id。"""
    detail_id = str(item.get("detail_id") or "")
    point_fn = getattr(session, "detail_model_point", None)
    point = point_fn(detail_id) if callable(point_fn) else None
    frames = view_frames_containing(session, point) if point is not None else ()
    if len(frames) == 0:
        return results.blocked(
            "bind_tag",
            "這個 Detail 對不到已登記 View。請先跑註冊 View。",
            ("missing_view",),
            command_id=COMMAND_ID,
        )
    if len(frames) > 1:
        return results.blocked(
            "bind_tag",
            "這個 Detail 對到兩個以上已登記 View，已停止，不猜測。",
            ("ambiguous_view",),
            command_id=COMMAND_ID,
        )
    view_id = canonical_uuid(session.get_object_user_text(frames[0], VIEW_ID_KEY))
    if not view_id:
        return results.blocked(
            "bind_tag",
            "目標 View 沒有合法的 lf_view_id。請先跑註冊 View。",
            ("missing_view",),
            command_id=COMMAND_ID,
        )
    return results.ok(
        "bind_tag",
        "已對到目標 View。",
        command_id=COMMAND_ID,
        details={"frame_id": frames[0], "view_id": view_id},
    )


def _default_pick_tag(_session: RhinoSession) -> Optional[str]:
    from loopflow.platform.rhino.prompts import pick_block_instance

    return pick_block_instance("選取要綁定的 Index Tag（Esc 取消）")


def _default_choose(session: RhinoSession, details: Sequence[dict]):
    if not details:
        return None
    from loopflow.platform.rhino.prompts import ask_layout_detail_choice

    rows = with_detail_labels(details)
    return ask_layout_detail_choice(
        rows,
        on_select=lambda item: preview_detail(session, item),
    )


def bind_index_view(
    session: RhinoSession,
    tag_id: str,
    view_id: str,
    catalog: TagTemplateSet,
    layout: Optional[str] = None,
) -> results.Result:
    """把已登記 View 的 lf_view_id 與所選 Layout 頁名寫進 Index Tag。測試可直接呼叫。"""
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
    if is_tag_locked(session, tag_id):
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
    bound_view = canonical_uuid(view_id)
    if not bound_view:
        return results.blocked(
            "bind_tag",
            "目標 View 沒有合法的 lf_view_id。請先跑註冊 View。",
            ("missing_view",),
            command_id=COMMAND_ID,
        )
    write_view_binding(session, tag_id, template, bound_view, layout=layout)
    return results.ok(
        "bind_tag",
        "已綁定目標 View。",
        command_id=COMMAND_ID,
        details={
            "tag_id": tag_id,
            "template_id": template.template_id,
            "binding_mode": "view",
            "target_view_id": bound_view,
            "target_layout": layout,
        },
    )


def run_tagger_index(
    session: RhinoSession,
    *,
    pick_tag: Optional[PickTag] = None,
    choose_detail: Optional[ChooseDetail] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    """選 Index Tag，再選 Layout Detail。Esc 取消不寫入。"""
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
        layout_fn = getattr(current, "is_layout_active", None)
        if not callable(layout_fn) or not layout_fn():
            return results.blocked(
                "bind_tag",
                "請在 Layout 執行 Index。",
                ("not_layout",),
                command_id=COMMAND_ID,
            )
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
        if is_tag_locked(current, tag_id):
            return results.blocked(
                "bind_tag",
                "此 Tag 已鎖定，請先解除鎖定再綁定。",
                ("tag_locked",),
                command_id=COMMAND_ID,
            )
        details = listed_details(current)
        if not details:
            return results.blocked(
                "bind_tag",
                "沒有 Detail View 可綁定。",
                ("missing_detail",),
                command_id=COMMAND_ID,
            )
        chooser = choose_detail or (lambda rows: _default_choose(current, rows))
        chosen = chooser(details)
        if not chosen:
            return results.cancelled(
                "bind_tag",
                "已取消 Index。",
                command_id=COMMAND_ID,
            )
        mapped = resolve_view_for_detail(current, chosen)
        if not mapped.ok:
            return mapped
        view_id = mapped.details["view_id"]
        bound = bind_index_view(
            current, tag_id, view_id, loaded, layout=chosen.get("layout")
        )
        if bound.ok:
            extra = dict(bound.details)
            extra["frame_id"] = mapped.details.get("frame_id")
            extra["detail_id"] = chosen.get("detail_id")
            extra["layout"] = chosen.get("layout")
            return results.ok(bound.stage, bound.message, command_id=COMMAND_ID, details=extra)
        return bound

    return run_guarded(session, action, command_id=COMMAND_ID)
