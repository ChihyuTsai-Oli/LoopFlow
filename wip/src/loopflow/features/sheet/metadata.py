# -*- coding: utf-8 -*-
"""Sheet metadata 的唯一存取點。

Layout ID 寫、其他功能（Index、Catalog、Infuser）讀。任何人都不得自行組
`lf_sheet.<sheet_id>.*` 字串、解析 Layout 頁名或從圖框文字反推圖號。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

from loopflow.features.sheet.keys import (
    DOCUMENT_NAMESPACE,
    METADATA_FIELDS,
    SHEET_ID_KEY,
    TITLE_FRAME_REGISTRY_KEY,
    TITLE_FRAME_REGISTRY_SEPARATOR,
)
from loopflow.features.tagger.binding import canonical_uuid, text
from loopflow.features.tagger.keys import LOCK_STATE_KEY, is_lock_true
from loopflow.features.tagger.templates import TagTemplateSet
from loopflow.platform.rhino.session import RhinoSession

STATE_CURRENT = "current"
STATE_STALE = "stale"


@dataclass(frozen=True)
class PageScan:
    """一個 Layout 頁的圖框盤點結果。"""

    page_name: str
    page_number: int
    frame_ids: Tuple[str, ...]
    locked_frame_ids: Tuple[str, ...]
    unregistered_blocks: Tuple[str, ...]

    @property
    def usable_frame_id(self) -> Optional[str]:
        if len(self.frame_ids) != 1 or self.locked_frame_ids:
            return None
        return self.frame_ids[0]


@dataclass(frozen=True)
class ActiveSheet:
    """目前存在的 Layout 頁 + 該頁圖框上的 lf_sheet_id。"""

    sheet_id: str
    page_name: str
    page_number: int
    frame_id: str
    metadata: Dict[str, str]


def document_key(sheet_id: str, field: str) -> str:
    if field not in METADATA_FIELDS:
        raise ValueError("未定義的 Sheet 欄位：%s" % field)
    cid = canonical_uuid(sheet_id) or str(sheet_id).strip()
    return "%s.%s.%s" % (DOCUMENT_NAMESPACE, cid, field)


def get_sheet_field(session: RhinoSession, sheet_id: str, field: str) -> Optional[str]:
    return text(session.document_user_text(document_key(sheet_id, field)))


def get_sheet_metadata(session: RhinoSession, sheet_id: str) -> Dict[str, str]:
    """只回傳實際有值的欄位；缺欄不補預設值。"""
    values = {}
    for field in METADATA_FIELDS:
        value = get_sheet_field(session, sheet_id, field)
        if value is not None:
            values[field] = value
    return values


def write_sheet_metadata(session: RhinoSession, sheet_id: str, values: dict) -> None:
    for field, value in values.items():
        session.set_document_user_text(
            document_key(sheet_id, field),
            "" if value is None else str(value),
        )


def sheet_state(session: RhinoSession, sheet_id: str, current_page_position: int) -> str:
    """比對 metadata 記錄的頁序與目前頁序；不一致即 stale。"""
    recorded = get_sheet_field(session, sheet_id, "page_position")
    if recorded is None:
        return STATE_STALE
    try:
        return STATE_CURRENT if int(recorded) == int(current_page_position) else STATE_STALE
    except (TypeError, ValueError):
        return STATE_STALE


def registered_title_frame_names(session: RhinoSession) -> Tuple[str, ...]:
    """本份 .3dm 額外認可的圖框 Block 名。"""
    raw = text(session.document_user_text(TITLE_FRAME_REGISTRY_KEY))
    if raw is None:
        return ()
    names = [part.strip() for part in raw.split(TITLE_FRAME_REGISTRY_SEPARATOR)]
    return tuple(name for name in names if name)


def register_title_frame_names(session: RhinoSession, names: Sequence[str]) -> Tuple[str, ...]:
    """把使用者確認過的 Block 名加入登錄；不分大小寫去重。"""
    merged = list(registered_title_frame_names(session))
    folded = {name.casefold() for name in merged}
    for name in names:
        clean = (name or "").strip()
        if clean and clean.casefold() not in folded:
            merged.append(clean)
            folded.add(clean.casefold())
    session.set_document_user_text(
        TITLE_FRAME_REGISTRY_KEY,
        TITLE_FRAME_REGISTRY_SEPARATOR.join(merged),
    )
    return tuple(merged)


def is_title_frame(
    session: RhinoSession,
    object_id: str,
    catalog: TagTemplateSet,
    registered: Sequence[str] = (),
) -> bool:
    """manifest 宣告的 title_frame，或本專案登錄的 Block，才算圖框。"""
    if not session.is_block_instance(object_id):
        return False
    block_name = session.block_definition_name(object_id) or ""
    if not block_name:
        return False
    template = catalog.by_block_name(block_name)
    if template is not None:
        return template.role == "title_frame"
    folded = block_name.casefold()
    return any(name.casefold() == folded for name in registered)


def scan_layout_pages(
    session: RhinoSession,
    catalog: TagTemplateSet,
) -> Tuple[PageScan, ...]:
    """依頁序盤點每一頁的圖框；未登錄的 Block 名一併回報供使用者決定。"""
    pages_fn = getattr(session, "listed_layout_pages", None)
    objects_fn = getattr(session, "objects_on_layout_page", None)
    if not callable(pages_fn) or not callable(objects_fn):
        return ()
    registered = registered_title_frame_names(session)
    scans = []
    for index, page in enumerate(pages_fn() or ()):
        page_name = str(page.get("name") or "")
        frame_ids = []
        locked_ids = []
        unknown = []
        for object_id in objects_fn(page_name) or ():
            if not session.is_block_instance(object_id):
                continue
            if is_title_frame(session, object_id, catalog, registered):
                frame_ids.append(object_id)
                if is_lock_true(session.get_object_user_text(object_id, LOCK_STATE_KEY)):
                    locked_ids.append(object_id)
                continue
            block_name = session.block_definition_name(object_id) or ""
            if block_name and catalog.by_block_name(block_name) is None:
                if block_name not in unknown:
                    unknown.append(block_name)
        raw_number = page.get("page_number")
        if raw_number in (None, ""):
            page_number = index + 1
        else:
            try:
                page_number = int(raw_number)
            except (TypeError, ValueError):
                page_number = index + 1
        scans.append(
            PageScan(
                page_name=page_name,
                page_number=page_number,
                frame_ids=tuple(frame_ids),
                locked_frame_ids=tuple(locked_ids),
                unregistered_blocks=tuple(unknown),
            )
        )
    return tuple(scans)


def list_active_sheets(
    session: RhinoSession,
    catalog: TagTemplateSet,
) -> Tuple[ActiveSheet, ...]:
    """active Sheet 依 Layout 頁序回傳。metadata 存在不代表 Sheet 仍 active。"""
    sheets = []
    for scan in scan_layout_pages(session, catalog):
        frame_id = scan.usable_frame_id
        if frame_id is None:
            continue
        sheet_id = canonical_uuid(session.get_object_user_text(frame_id, SHEET_ID_KEY))
        if sheet_id is None:
            continue
        sheets.append(
            ActiveSheet(
                sheet_id=sheet_id,
                page_name=scan.page_name,
                page_number=scan.page_number,
                frame_id=frame_id,
                metadata=get_sheet_metadata(session, sheet_id),
            )
        )
    return tuple(sheets)


def stale_sheet_ids(session: RhinoSession, catalog: TagTemplateSet) -> Tuple[str, ...]:
    """頁序與 metadata 不一致的 Sheet；consumer 應先要求重跑 Layout ID。"""
    stale = []
    for sheet in list_active_sheets(session, catalog):
        if sheet_state(session, sheet.sheet_id, sheet.page_number) == STATE_STALE:
            stale.append(sheet.sheet_id)
    return tuple(stale)


def stale_among_sheet_ids(
    session: RhinoSession,
    catalog: TagTemplateSet,
    sheet_ids: Sequence[str],
) -> Tuple[str, ...]:
    """被選中的 sheet_id 是否過期。

    同一 id 若有任一頁的 page_position 對得上，來源頁就不被複本連坐。
    全新複製、尚未跑 Layout ID 的 id（沒有對得上的頁）仍算過期。
    """
    wanted = tuple(sid for sid in sheet_ids if sid)
    if not wanted:
        return ()
    wanted_set = set(wanted)
    current = set()
    present = set()
    for sheet in list_active_sheets(session, catalog):
        if sheet.sheet_id not in wanted_set:
            continue
        present.add(sheet.sheet_id)
        if sheet_state(session, sheet.sheet_id, sheet.page_number) == STATE_CURRENT:
            current.add(sheet.sheet_id)
    return tuple(sid for sid in wanted if sid in present and sid not in current)
