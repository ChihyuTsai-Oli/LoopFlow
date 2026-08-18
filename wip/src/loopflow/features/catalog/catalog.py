# -*- coding: utf-8 -*-
"""LF_Catalog：依定位點與 Sheet metadata 建立／更新圖目錄。

D04 寫 Sheet metadata；本模組只讀 `sheet_id` 與 Sheet metadata API，不解析
Layout 頁名、不讀圖框文字、不另存圖號／圖名副本。責任與零寫入條件見
`wip/docs/資料契約.md` 的 Catalog Anchor 章節。
"""
from __future__ import annotations

import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from loopflow.features.catalog.keys import (
    ALLOWED_FIELDS,
    CATALOG_ID_KEY,
    COLUMN_TOLERANCE,
    FIELD_DRAWING_NAME,
    FIELD_DRAWING_NO,
    FIELD_KEY,
    GENERATED_BY_KEY,
    GENERATED_BY_VALUE,
    HOME_LAYER_KEY,
    NAME_COLOR,
    NAME_LAYER,
    NUMBER_COLOR,
    NUMBER_LAYER,
    POINT_ID_KEY,
    ROW_TOLERANCE,
    SHEET_ID_KEY,
    TEXT_COLOR,
    TEXT_HEIGHT,
    TEXT_LAYER,
)
from loopflow.features.sheet.metadata import (
    get_sheet_metadata,
    list_active_sheets,
    stale_sheet_ids,
)
from loopflow.features.tagger.binding import UUID_V4_RE, text
from loopflow.features.tagger.templates import TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Catalog"
STAGE = "catalog"
PANEL_REMINDER = (
    "目錄定位點是持久控制物件，建立目錄後請勿刪除；"
    "移動目錄時請連同定位點一起移動。"
)

ConfirmPlan = Callable[[Sequence[str]], bool]
AskPath = Callable[[Optional[str]], Optional[str]]
PickPoints = Callable[[str], Optional[Sequence[str]]]
PickSheets = Callable[[RhinoSession], Optional[Sequence[str]]]


@dataclass(frozen=True)
class CatalogPoint:
    object_id: str
    page_name: str
    page_number: int
    x: float
    y: float
    catalog_id: Optional[str] = None
    field: Optional[str] = None
    sheet_id: Optional[str] = None


@dataclass(frozen=True)
class CatalogPair:
    number: CatalogPoint
    name: CatalogPoint


@dataclass(frozen=True)
class PairResult:
    ok: bool
    reason: Optional[str] = None
    pairs: Tuple[CatalogPair, ...] = ()


@dataclass(frozen=True)
class CatalogSlot:
    pair: CatalogPair
    sheet_id: Optional[str]


@dataclass(frozen=True)
class BindResult:
    ok: bool
    reason: Optional[str] = None
    slots: Tuple[CatalogSlot, ...] = ()


@dataclass(frozen=True)
class CatalogRow:
    number_point_id: str
    name_point_id: str
    sheet_id: Optional[str]
    drawing_no: Optional[str] = None
    drawing_name: Optional[str] = None
    skip_reason: Optional[str] = None


def _new_id() -> str:
    return str(uuid.uuid4())


def _cluster_columns(
    points: Sequence[CatalogPoint],
    tolerance: float,
) -> List[CatalogPoint]:
    ordered = sorted(points, key=lambda item: (item.x, -item.y, item.object_id))
    columns: List[List[CatalogPoint]] = []
    for point in ordered:
        if columns:
            mean_x = sum(item.x for item in columns[-1]) / float(len(columns[-1]))
            if abs(point.x - mean_x) <= tolerance:
                columns[-1].append(point)
                continue
        columns.append([point])
    columns.sort(key=lambda col: sum(item.x for item in col) / float(len(col)))
    result = []
    for column in columns:
        column.sort(key=lambda item: (-item.y, item.x, item.object_id))
        result.extend(column)
    return result


def sort_catalog_points(
    points: Sequence[CatalogPoint],
    *,
    column_tolerance: float = COLUMN_TOLERANCE,
) -> Tuple[CatalogPoint, ...]:
    """先依 Layout 頁序分組，再 X 分欄、Y 由上而下。"""
    by_page: Dict[int, List[CatalogPoint]] = {}
    for point in points:
        by_page.setdefault(int(point.page_number), []).append(point)
    ordered = []
    for page_number in sorted(by_page):
        ordered.extend(_cluster_columns(by_page[page_number], column_tolerance))
    return tuple(ordered)


def pair_catalog_anchors(
    number_points: Sequence[CatalogPoint],
    name_points: Sequence[CatalogPoint],
    *,
    row_tolerance: float = ROW_TOLERANCE,
    column_tolerance: float = COLUMN_TOLERANCE,
) -> PairResult:
    """逐頁數量必須相等；配對後 Y 必須在同列容差內。"""
    numbers = sort_catalog_points(number_points, column_tolerance=column_tolerance)
    names = sort_catalog_points(name_points, column_tolerance=column_tolerance)
    if not numbers or not names:
        return PairResult(ok=False, reason="missing_anchors")
    number_counts = Counter(point.page_number for point in numbers)
    name_counts = Counter(point.page_number for point in names)
    if number_counts != name_counts:
        return PairResult(ok=False, reason="page_count_mismatch")
    pairs = []
    for number, name in zip(numbers, names):
        if number.page_number != name.page_number:
            return PairResult(ok=False, reason="page_count_mismatch")
        if abs(number.y - name.y) > row_tolerance:
            return PairResult(ok=False, reason="row_mismatch")
        pairs.append(CatalogPair(number=number, name=name))
    return PairResult(ok=True, pairs=tuple(pairs))


def bind_sheets_to_anchors(
    pairs: Sequence[CatalogPair],
    sheet_ids: Sequence[str],
) -> BindResult:
    if not pairs:
        return BindResult(ok=False, reason="missing_anchors")
    if not sheet_ids:
        return BindResult(ok=False, reason="missing_sheets")
    if len(sheet_ids) > len(pairs):
        return BindResult(ok=False, reason="too_many_sheets")
    slots = []
    for index, pair in enumerate(pairs):
        sheet_id = sheet_ids[index] if index < len(sheet_ids) else None
        slots.append(CatalogSlot(pair=pair, sheet_id=sheet_id))
    return BindResult(ok=True, slots=tuple(slots))


def slots_from_bindings(pairs: Sequence[CatalogPair]) -> BindResult:
    """Refresh 用現有 `lf_catalog_sheet_id`，不改綁定。"""
    if not pairs:
        return BindResult(ok=False, reason="missing_anchors")
    slots = []
    for pair in pairs:
        number_id = text(pair.number.sheet_id)
        name_id = text(pair.name.sheet_id)
        if number_id != name_id:
            return BindResult(ok=False, reason="binding_mismatch")
        slots.append(CatalogSlot(pair=pair, sheet_id=number_id))
    return BindResult(ok=True, slots=tuple(slots))


def build_catalog_rows(
    slots: Sequence[CatalogSlot],
    *,
    metadata_by_id: Dict[str, dict],
    active_ids: Sequence[str],
) -> Tuple[CatalogRow, ...]:
    active = set(active_ids)
    rows = []
    for slot in slots:
        number_id = slot.pair.number.object_id
        name_id = slot.pair.name.object_id
        if not slot.sheet_id:
            rows.append(
                CatalogRow(
                    number_point_id=number_id,
                    name_point_id=name_id,
                    sheet_id=None,
                    skip_reason="empty_slot",
                )
            )
            continue
        if slot.sheet_id not in active:
            skip = "orphan" if slot.sheet_id in metadata_by_id else "missing_sheet"
            rows.append(
                CatalogRow(
                    number_point_id=number_id,
                    name_point_id=name_id,
                    sheet_id=slot.sheet_id,
                    skip_reason=skip,
                )
            )
            continue
        meta = metadata_by_id.get(slot.sheet_id) or {}
        drawing_no = text(meta.get("drawing_no"))
        drawing_name = text(meta.get("drawing_name"))
        skip = None
        if drawing_no is None:
            skip = "missing_drawing_no"
        elif drawing_name is None:
            skip = "missing_drawing_name"
        rows.append(
            CatalogRow(
                number_point_id=number_id,
                name_point_id=name_id,
                sheet_id=slot.sheet_id,
                drawing_no=drawing_no,
                drawing_name=drawing_name,
                skip_reason=skip,
            )
        )
    return tuple(rows)


def preview_lines(rows: Sequence[CatalogRow]) -> Tuple[str, ...]:
    lines = []
    for row in rows:
        if row.skip_reason == "empty_slot":
            lines.append("（空位）")
            continue
        drawing_no = row.drawing_no or "—"
        drawing_name = row.drawing_name or "—"
        if row.skip_reason:
            lines.append("%s　%s　[%s]" % (drawing_no, drawing_name, row.skip_reason))
        else:
            lines.append("%s　%s" % (drawing_no, drawing_name))
    return tuple(lines)


def format_catalog_txt(rows: Sequence[CatalogRow]) -> str:
    lines = ["圖名, 圖號"]
    for row in rows:
        if row.skip_reason:
            continue
        lines.append("%s, %s" % (row.drawing_name, row.drawing_no))
    return "\n".join(lines) + "\n"


def _require_schema(session: RhinoSession) -> Optional[results.Result]:
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
    return None


def _load_templates(catalog: Optional[TagTemplateSet]) -> results.Result:
    if catalog is not None:
        return results.ok(STAGE, "已載入 Tag templates", details={"catalog": catalog})
    loaded = load_tag_templates()
    if not loaded.ok:
        return loaded
    return loaded


def _page_index(session: RhinoSession) -> Dict[str, int]:
    pages = {}
    for page in session.listed_layout_pages() or ():
        name = str(page.get("name") or "")
        if name:
            pages[name] = int(page.get("page_number") or 0)
    return pages


def _catalog_point(session: RhinoSession, object_id: str, pages: Dict[str, int]):
    if not session.is_point(object_id):
        return None
    xyz = session.point_xyz(object_id)
    if not xyz:
        return None
    page_name = session.layout_page_name_of(object_id)
    if not page_name:
        return None
    page_number = pages.get(page_name)
    if not page_number:
        return None
    return CatalogPoint(
        object_id=object_id,
        page_name=page_name,
        page_number=int(page_number),
        x=float(xyz[0]),
        y=float(xyz[1]),
        catalog_id=text(session.get_object_user_text(object_id, CATALOG_ID_KEY)),
        field=text(session.get_object_user_text(object_id, FIELD_KEY)),
        sheet_id=text(session.get_object_user_text(object_id, SHEET_ID_KEY)),
    )


def _layer_field_ids(session: RhinoSession, layer: str, field: str) -> Tuple[str, ...]:
    ids = []
    for object_id in session.objects_on_layer(layer) or ():
        if not session.is_point(object_id):
            continue
        if text(session.get_object_user_text(object_id, CATALOG_ID_KEY)) is None:
            continue
        actual = text(session.get_object_user_text(object_id, FIELD_KEY))
        if actual != field:
            continue
        ids.append(object_id)
    return tuple(ids)


def _unique_catalog_ids(session: RhinoSession, object_ids: Sequence[str]) -> Tuple[str, ...]:
    found = []
    for object_id in object_ids:
        catalog_id = text(session.get_object_user_text(object_id, CATALOG_ID_KEY))
        if catalog_id and catalog_id not in found:
            found.append(catalog_id)
    return tuple(found)


def _resolve_assign_catalog_id(
    session: RhinoSession,
    object_ids: Sequence[str],
    field: str,
) -> Tuple[Optional[str], Optional[str]]:
    """圖號與圖名分次選取、或分批加選，都沿用同一份目錄身分。"""
    selected = _unique_catalog_ids(session, object_ids)
    other_field = FIELD_DRAWING_NAME if field == FIELD_DRAWING_NO else FIELD_DRAWING_NO
    other_layer = NAME_LAYER if field == FIELD_DRAWING_NO else NUMBER_LAYER
    current_layer = NUMBER_LAYER if field == FIELD_DRAWING_NO else NAME_LAYER
    other_ids = _unique_catalog_ids(
        session, _layer_field_ids(session, other_layer, other_field)
    )
    current_ids = _unique_catalog_ids(
        session, _layer_field_ids(session, current_layer, field)
    )
    if len(other_ids) == 1:
        return other_ids[0], None
    if len(selected) > 1:
        return None, "mixed_catalog_id"
    if selected:
        return selected[0], None
    if len(current_ids) == 1:
        return current_ids[0], None
    return _new_id(), None


def collect_anchors(session: RhinoSession) -> results.Result:
    number_ids = _layer_field_ids(session, NUMBER_LAYER, FIELD_DRAWING_NO)
    name_ids = _layer_field_ids(session, NAME_LAYER, FIELD_DRAWING_NAME)
    if not number_ids or not name_ids:
        return results.blocked(
            STAGE,
            "找不到成對的圖號／圖名定位點，已停止，不寫入。",
            ("missing_anchors",),
            command_id=COMMAND_ID,
        )
    number_catalog_ids = _unique_catalog_ids(session, number_ids)
    name_catalog_ids = _unique_catalog_ids(session, name_ids)
    if len(number_catalog_ids) > 1 or len(name_catalog_ids) > 1:
        return results.blocked(
            STAGE,
            "定位點混入多個圖目錄身分，已停止，不寫入。",
            ("mixed_catalog_id",),
            command_id=COMMAND_ID,
        )
    if not number_catalog_ids or not name_catalog_ids:
        return results.blocked(
            STAGE,
            "找不到成對的圖號／圖名定位點，已停止，不寫入。",
            ("missing_anchors",),
            command_id=COMMAND_ID,
        )
    catalog_ids = (number_catalog_ids[0],)
    pages = _page_index(session)
    numbers = []
    names = []
    for object_id in number_ids:
        point = _catalog_point(session, object_id, pages)
        if point is None:
            return results.blocked(
                STAGE,
                "圖號定位點必須是 Layout 上的獨立 Point，已停止，不寫入。",
                ("damaged_anchor",),
                command_id=COMMAND_ID,
            )
        numbers.append(point)
    for object_id in name_ids:
        point = _catalog_point(session, object_id, pages)
        if point is None:
            return results.blocked(
                STAGE,
                "圖名定位點必須是 Layout 上的獨立 Point，已停止，不寫入。",
                ("damaged_anchor",),
                command_id=COMMAND_ID,
            )
        names.append(point)
    catalog_id = next(iter(catalog_ids))
    if not UUID_V4_RE.match(catalog_id):
        return results.blocked(
            STAGE,
            "圖目錄身分不是合法 UUID，已停止，不寫入。",
            ("invalid_catalog_id",),
            command_id=COMMAND_ID,
        )
    return results.ok(
        STAGE,
        "已讀取定位點。",
        command_id=COMMAND_ID,
        details={
            "catalog_id": catalog_id,
            "number_points": tuple(numbers),
            "name_points": tuple(names),
        },
    )


def write_catalog_anchor_metadata(
    session: RhinoSession,
    slots: Sequence[CatalogSlot],
    catalog_id: str,
) -> None:
    for slot in slots:
        items = (
            (slot.pair.number.object_id, FIELD_DRAWING_NO),
            (slot.pair.name.object_id, FIELD_DRAWING_NAME),
        )
        for object_id, field in items:
            session.set_object_user_text(object_id, CATALOG_ID_KEY, catalog_id)
            session.set_object_user_text(object_id, FIELD_KEY, field)
            session.set_object_user_text(
                object_id,
                SHEET_ID_KEY,
                slot.sheet_id or "",
            )


def generated_text_ids(session: RhinoSession, catalog_id: str) -> Tuple[str, ...]:
    ids = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        if text(session.get_object_user_text(object_id, GENERATED_BY_KEY)) != GENERATED_BY_VALUE:
            continue
        if text(session.get_object_user_text(object_id, CATALOG_ID_KEY)) != catalog_id:
            continue
        ids.append(object_id)
    return tuple(ids)


def delete_generated_catalog_text(session: RhinoSession, catalog_id: str) -> int:
    removed = 0
    for object_id in generated_text_ids(session, catalog_id):
        session.delete_object(object_id)
        removed += 1
    return removed


def _ensure_text_layer(session: RhinoSession) -> None:
    session.ensure_layer(TEXT_LAYER)
    session.set_layer_appearance(TEXT_LAYER, TEXT_COLOR)


def _write_text_keys(
    session: RhinoSession,
    text_id: str,
    *,
    catalog_id: str,
    point_id: str,
    field: str,
) -> None:
    session.set_object_user_text(text_id, GENERATED_BY_KEY, GENERATED_BY_VALUE)
    session.set_object_user_text(text_id, CATALOG_ID_KEY, catalog_id)
    session.set_object_user_text(text_id, POINT_ID_KEY, point_id)
    session.set_object_user_text(text_id, FIELD_KEY, field)


def _create_catalog_text_object(
    session: RhinoSession,
    content: str,
    point_xyz,
    *,
    page_name: Optional[str],
    catalog_id: str,
    point_id: str,
    field: str,
    height: float,
) -> str:
    _ensure_text_layer(session)
    text_id = session.add_text(
        content,
        point_xyz,
        layer=TEXT_LAYER,
        page_name=page_name,
        height=height,
    )
    _write_text_keys(
        session,
        text_id,
        catalog_id=catalog_id,
        point_id=point_id,
        field=field,
    )
    return text_id


def sync_catalog_text(
    session: RhinoSession,
    rows: Sequence[CatalogRow],
    catalog_id: str,
    *,
    height: float = TEXT_HEIGHT,
) -> Tuple[str, ...]:
    """更新已有目錄文字的內容；字型、大小、圖層與位置維持原設定。缺件才在定位點新建。"""
    existing_by_point = {}
    for text_id in generated_text_ids(session, catalog_id):
        point_id = text(session.get_object_user_text(text_id, POINT_ID_KEY))
        if point_id:
            existing_by_point[point_id] = text_id
    keep = set()
    written = []
    updater = getattr(session, "update_text", None)
    for row in rows:
        placements = (
            (row.number_point_id, FIELD_DRAWING_NO, row.drawing_no),
            (row.name_point_id, FIELD_DRAWING_NAME, row.drawing_name),
        )
        for point_id, field, content in placements:
            if row.skip_reason:
                continue
            point_xyz = session.point_xyz(point_id)
            page_name = session.layout_page_name_of(point_id)
            existing = existing_by_point.get(point_id)
            if existing and callable(updater) and updater(existing, content or ""):
                _write_text_keys(
                    session,
                    existing,
                    catalog_id=catalog_id,
                    point_id=point_id,
                    field=field,
                )
                keep.add(existing)
                written.append(existing)
                continue
            text_id = _create_catalog_text_object(
                session,
                content or "",
                point_xyz,
                page_name=page_name,
                catalog_id=catalog_id,
                point_id=point_id,
                field=field,
                height=height,
            )
            keep.add(text_id)
            written.append(text_id)
    for text_id in generated_text_ids(session, catalog_id):
        if text_id not in keep:
            session.delete_object(text_id)
    return tuple(written)


def create_catalog_text(
    session: RhinoSession,
    rows: Sequence[CatalogRow],
    catalog_id: str,
    *,
    height: float = TEXT_HEIGHT,
) -> Tuple[str, ...]:
    return sync_catalog_text(session, rows, catalog_id, height=height)


def assign_catalog_points(
    session: RhinoSession,
    object_ids: Sequence[str],
    field: str,
) -> results.Result:
    """選取定位點：歸位圖層並寫 `lf_catalog_id`／`lf_catalog_field`。不寫 sheet_id。"""
    blocked = _require_schema(session)
    if blocked is not None:
        return blocked
    if field not in ALLOWED_FIELDS:
        return results.failed(
            STAGE,
            "未知的目錄欄位：%s。" % field,
            command_id=COMMAND_ID,
        )
    if not object_ids:
        return results.cancelled(
            STAGE,
            "已取消選取定位點，未寫入。",
            command_id=COMMAND_ID,
        )

    def action(current: RhinoSession) -> results.Result:
        for object_id in object_ids:
            if current.is_block_instance(object_id):
                return results.blocked(
                    STAGE,
                    "選到 Block 或其子物件，已停止，不寫入。定位點必須是獨立 Point。",
                    ("block_instance",),
                    command_id=COMMAND_ID,
                )
            if not current.is_point(object_id):
                return results.blocked(
                    STAGE,
                    "選到的不是獨立 Point，已停止，不寫入。",
                    ("not_point",),
                    command_id=COMMAND_ID,
                )
        catalog_id, reason = _resolve_assign_catalog_id(current, object_ids, field)
        if catalog_id is None:
            return results.blocked(
                STAGE,
                "選取的定位點屬於不同圖目錄，已停止，不寫入。",
                (reason or "mixed_catalog_id",),
                command_id=COMMAND_ID,
            )
        layer = NUMBER_LAYER if field == FIELD_DRAWING_NO else NAME_LAYER
        color = NUMBER_COLOR if field == FIELD_DRAWING_NO else NAME_COLOR
        current.ensure_layer(layer)
        current.set_layer_appearance(layer, color)
        for object_id in object_ids:
            _remember_home_layer(current, object_id)
            current.set_object_layer(object_id, layer)
            current.set_object_user_text(object_id, CATALOG_ID_KEY, catalog_id)
            current.set_object_user_text(object_id, FIELD_KEY, field)
        return results.ok(
            STAGE,
            "已歸位 %s 個%s定位點。"
            % (len(object_ids), "圖號" if field == FIELD_DRAWING_NO else "圖名"),
            command_id=COMMAND_ID,
            details={
                "catalog_id": catalog_id,
                "field": field,
                "count": len(object_ids),
                "layer": layer,
            },
        )

    return run_guarded(session, action, command_id=COMMAND_ID)


def _remember_home_layer(session: RhinoSession, object_id: str) -> None:
    if text(session.get_object_user_text(object_id, HOME_LAYER_KEY)):
        return
    current = session.object_layer(object_id) or ""
    if current in (NUMBER_LAYER, NAME_LAYER, TEXT_LAYER):
        return
    session.set_object_user_text(object_id, HOME_LAYER_KEY, current or "Default")


def _catalog_point_ids(session: RhinoSession) -> Tuple[str, ...]:
    ids = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        if not session.is_point(object_id):
            continue
        if text(session.get_object_user_text(object_id, CATALOG_ID_KEY)) is None:
            continue
        ids.append(object_id)
    return tuple(ids)


def reset_catalog_points(
    session: RhinoSession,
    *,
    confirm: Optional[Callable[[], bool]] = None,
) -> results.Result:
    """清除定位點目錄資料、還原原圖層，並刪除產生的目錄文字。"""
    blocked = _require_schema(session)
    if blocked is not None:
        return blocked
    point_ids = _catalog_point_ids(session)
    if not point_ids:
        return results.blocked(
            STAGE,
            "沒有圖目錄定位點可清除。",
            ("missing_anchors",),
            command_id=COMMAND_ID,
        )
    confirmer = confirm
    if confirmer is None:
        from loopflow.platform.rhino.prompts import ask_yes_no

        def _ask() -> bool:
            return ask_yes_no(
                "將清除所有圖目錄定位點上的資料，把點放回原來的圖層，並刪除目錄文字。確定？",
                "清除定位點",
            )

        confirmer = _ask
    if not confirmer():
        return results.cancelled(
            STAGE,
            "已取消清除定位點，未寫入。",
            command_id=COMMAND_ID,
        )

    def action(current: RhinoSession) -> results.Result:
        catalog_ids = []
        restored = 0
        for object_id in _catalog_point_ids(current):
            catalog_id = text(current.get_object_user_text(object_id, CATALOG_ID_KEY))
            if catalog_id and catalog_id not in catalog_ids:
                catalog_ids.append(catalog_id)
            home = text(current.get_object_user_text(object_id, HOME_LAYER_KEY)) or "Default"
            current.ensure_layer(home)
            current.set_object_layer(object_id, home)
            current.set_object_user_text(object_id, CATALOG_ID_KEY, "")
            current.set_object_user_text(object_id, FIELD_KEY, "")
            current.set_object_user_text(object_id, SHEET_ID_KEY, "")
            current.set_object_user_text(object_id, HOME_LAYER_KEY, "")
            restored += 1
        removed = 0
        for catalog_id in catalog_ids:
            removed += delete_generated_catalog_text(current, catalog_id)
        return results.ok(
            STAGE,
            "已還原 %s 個定位點，刪除 %s 個目錄文字。" % (restored, removed),
            command_id=COMMAND_ID,
            details={"points": restored, "texts": removed},
        )

    return run_guarded(session, action, command_id=COMMAND_ID)


def _pair_or_block(session: RhinoSession) -> results.Result:
    collected = collect_anchors(session)
    if not collected.ok:
        return collected
    paired = pair_catalog_anchors(
        collected.details["number_points"],
        collected.details["name_points"],
    )
    if not paired.ok:
        messages = {
            "page_count_mismatch": "圖號與圖名定位點的逐頁數量不一致，已停止，不寫入。",
            "row_mismatch": "圖名定位點不在對應圖號的同一列，已停止，不寫入。",
            "missing_anchors": "找不到成對的圖號／圖名定位點，已停止，不寫入。",
        }
        return results.blocked(
            STAGE,
            messages.get(paired.reason or "", "定位點無法配對，已停止，不寫入。"),
            (paired.reason or "pair_failed",),
            command_id=COMMAND_ID,
        )
    return results.ok(
        STAGE,
        "定位點已配對。",
        command_id=COMMAND_ID,
        details={
            "catalog_id": collected.details["catalog_id"],
            "pairs": paired.pairs,
        },
    )


def _sheet_context(
    session: RhinoSession,
    catalog: TagTemplateSet,
    sheet_ids: Sequence[str],
) -> Tuple[Dict[str, dict], Tuple[str, ...], Tuple[str, ...]]:
    active = list_active_sheets(session, catalog)
    active_ids = tuple(sheet.sheet_id for sheet in active)
    metadata_by_id = {sheet.sheet_id: dict(sheet.metadata) for sheet in active}
    for sheet_id in sheet_ids:
        if sheet_id not in metadata_by_id:
            extra = get_sheet_metadata(session, sheet_id)
            if extra:
                metadata_by_id[sheet_id] = extra
    stale = tuple(
        sheet_id
        for sheet_id in stale_sheet_ids(session, catalog)
        if sheet_id in set(sheet_ids)
    )
    return metadata_by_id, active_ids, stale


def _apply_rows(
    session: RhinoSession,
    slots: Sequence[CatalogSlot],
    rows: Sequence[CatalogRow],
    catalog_id: str,
    *,
    write_bindings: bool,
) -> Tuple[int, Tuple[str, ...]]:
    if write_bindings:
        write_catalog_anchor_metadata(session, slots, catalog_id)
    created = sync_catalog_text(session, rows, catalog_id)
    skipped = tuple(
        row.skip_reason
        for row in rows
        if row.skip_reason and row.skip_reason != "empty_slot"
    )
    return len(created), skipped


def build_catalog(
    session: RhinoSession,
    sheet_ids: Sequence[str],
    *,
    confirm: Optional[ConfirmPlan] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    blocked = _require_schema(session)
    if blocked is not None:
        return blocked
    loaded = _load_templates(catalog)
    if not loaded.ok:
        return loaded
    templates = loaded.details["catalog"]
    confirmer = confirm or _default_confirm

    def action(current: RhinoSession) -> results.Result:
        if not sheet_ids:
            return results.blocked(
                STAGE,
                "尚未選取 Sheet，已停止，不寫入。",
                ("missing_sheets",),
                command_id=COMMAND_ID,
            )
        paired = _pair_or_block(current)
        if not paired.ok:
            return paired
        bound = bind_sheets_to_anchors(paired.details["pairs"], sheet_ids)
        if not bound.ok:
            messages = {
                "too_many_sheets": "選取的 Sheet 多於可用定位點，已停止，不寫入。",
                "missing_sheets": "尚未選取 Sheet，已停止，不寫入。",
                "missing_anchors": "找不到成對的圖號／圖名定位點，已停止，不寫入。",
            }
            return results.blocked(
                STAGE,
                messages.get(bound.reason or "", "無法綁定 Sheet，已停止，不寫入。"),
                (bound.reason or "bind_failed",),
                command_id=COMMAND_ID,
            )
        metadata_by_id, active_ids, stale = _sheet_context(
            current, templates, sheet_ids
        )
        if stale:
            return results.blocked(
                STAGE,
                "Sheet metadata 已過期，請先執行 Layout ID，已停止，不寫入。",
                ("stale",),
                command_id=COMMAND_ID,
                details={"stale_sheet_ids": stale},
            )
        rows = build_catalog_rows(
            bound.slots,
            metadata_by_id=metadata_by_id,
            active_ids=active_ids,
        )
        if not confirmer(preview_lines(rows)):
            return results.cancelled(
                STAGE,
                "已取消圖目錄寫入。",
                command_id=COMMAND_ID,
            )
        catalog_id = paired.details["catalog_id"]
        created, skipped = _apply_rows(
            current, bound.slots, rows, catalog_id, write_bindings=True
        )
        message = "已建立圖目錄，寫入 %s 個文字。" % created
        if skipped:
            message += " 略過 %s 列。" % len(skipped)
        return results.ok(
            STAGE,
            message,
            command_id=COMMAND_ID,
            warnings=skipped,
            details={
                "catalog_id": catalog_id,
                "created": created,
                "rows": rows,
                "skipped": skipped,
            },
        )

    return run_guarded(session, action, command_id=COMMAND_ID)


def refresh_catalog(
    session: RhinoSession,
    *,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    blocked = _require_schema(session)
    if blocked is not None:
        return blocked
    loaded = _load_templates(catalog)
    if not loaded.ok:
        return loaded
    templates = loaded.details["catalog"]

    def action(current: RhinoSession) -> results.Result:
        paired = _pair_or_block(current)
        if not paired.ok:
            return paired
        bound = slots_from_bindings(paired.details["pairs"])
        if not bound.ok:
            return results.blocked(
                STAGE,
                "圖號與圖名定位點的綁定不一致，已停止，不寫入。",
                (bound.reason or "binding_mismatch",),
                command_id=COMMAND_ID,
            )
        sheet_ids = tuple(slot.sheet_id for slot in bound.slots if slot.sheet_id)
        metadata_by_id, active_ids, stale = _sheet_context(
            current, templates, sheet_ids
        )
        if stale:
            return results.blocked(
                STAGE,
                "Sheet metadata 已過期，請先執行 Layout ID，已停止，不寫入。",
                ("stale",),
                command_id=COMMAND_ID,
                details={"stale_sheet_ids": stale},
            )
        rows = build_catalog_rows(
            bound.slots,
            metadata_by_id=metadata_by_id,
            active_ids=active_ids,
        )
        catalog_id = paired.details["catalog_id"]
        created, skipped = _apply_rows(
            current, bound.slots, rows, catalog_id, write_bindings=False
        )
        message = "已更新圖目錄文字 %s 個。" % created
        if skipped:
            message += " 略過 %s 列。" % len(skipped)
        return results.ok(
            STAGE,
            message,
            command_id=COMMAND_ID,
            warnings=skipped,
            details={
                "catalog_id": catalog_id,
                "created": created,
                "rows": rows,
                "skipped": skipped,
            },
        )

    return run_guarded(session, action, command_id=COMMAND_ID)


def default_txt_path(session: RhinoSession) -> Optional[str]:
    getter = getattr(session, "document_path", None)
    path = getter() if callable(getter) else None
    if not path:
        return None
    source = Path(str(path))
    if not source.name:
        return None
    return str(source.with_name(source.stem + "_catalog.txt"))


def export_catalog_txt(
    session: RhinoSession,
    path: Optional[str] = None,
    *,
    ask_path: Optional[AskPath] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    blocked = _require_schema(session)
    if blocked is not None:
        return blocked
    loaded = _load_templates(catalog)
    if not loaded.ok:
        return loaded
    templates = loaded.details["catalog"]
    paired = _pair_or_block(session)
    if not paired.ok:
        return paired
    bound = slots_from_bindings(paired.details["pairs"])
    if not bound.ok:
        return results.blocked(
            STAGE,
            "圖號與圖名定位點的綁定不一致，已停止，不匯出。",
            (bound.reason or "binding_mismatch",),
            command_id=COMMAND_ID,
        )
    sheet_ids = tuple(slot.sheet_id for slot in bound.slots if slot.sheet_id)
    metadata_by_id, active_ids, stale = _sheet_context(session, templates, sheet_ids)
    if stale:
        return results.blocked(
            STAGE,
            "Sheet metadata 已過期，請先執行 Layout ID，已停止，不匯出。",
            ("stale",),
            command_id=COMMAND_ID,
            details={"stale_sheet_ids": stale},
        )
    rows = build_catalog_rows(
        bound.slots,
        metadata_by_id=metadata_by_id,
        active_ids=active_ids,
    )
    target = path
    if not target:
        default = default_txt_path(session)
        if ask_path is not None:
            target = ask_path(default)
        else:
            target = default
    if not target:
        return results.blocked(
            STAGE,
            "Rhino 檔尚未儲存，請選擇圖目錄 TXT 的儲存位置。",
            ("missing_path",),
            command_id=COMMAND_ID,
        )
    Path(target).write_text(format_catalog_txt(rows), encoding="utf-8")
    return results.ok(
        STAGE,
        "已匯出圖目錄 TXT。",
        command_id=COMMAND_ID,
        details={"path": str(target), "rows": rows},
    )


def _default_confirm(lines: Sequence[str]) -> bool:
    from loopflow.platform.rhino.prompts import ask_confirm_list

    return ask_confirm_list(lines, title="圖目錄核對清單")


def _default_pick_points(message: str) -> Optional[Sequence[str]]:
    from loopflow.platform.rhino.prompts import pick_catalog_points

    return pick_catalog_points(message)


def _default_pick_sheets(
    session: RhinoSession,
    selected: Sequence[str] = (),
) -> Optional[Sequence[str]]:
    from loopflow.platform.rhino.prompts import ask_pick_catalog_sheets

    loaded = load_tag_templates()
    if not loaded.ok:
        return None
    sheets = list_active_sheets(session, loaded.details["catalog"])
    items = []
    for sheet in sheets:
        meta = sheet.metadata
        items.append(
            {
                "sheet_id": sheet.sheet_id,
                "page_number": sheet.page_number,
                "drawing_no": meta.get("drawing_no") or "—",
                "drawing_name": meta.get("drawing_name") or "—",
                "page_name": sheet.page_name or "",
            }
        )
    if not items:
        from loopflow.platform.rhino.prompts import show_message

        show_message("沒有可列入目錄的 Sheet。請先執行 Layout ID。")
        return None
    return ask_pick_catalog_sheets(items, selected_ids=selected)


def _default_ask_path(default: Optional[str]) -> Optional[str]:
    from loopflow.platform.rhino.prompts import ask_save_filename

    folder = None
    filename = "catalog.txt"
    if default:
        path = Path(default)
        folder = str(path.parent)
        filename = path.name
    return ask_save_filename(
        "匯出圖目錄 TXT",
        "Text Files (*.txt)|*.txt",
        folder=folder,
        filename=filename,
    )


def _show_catalog_panel(session: RhinoSession) -> results.Result:
    from loopflow.platform.rhino.prompts import show_failure_popup

    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        return results.failed(
            STAGE,
            "找不到 Eto 介面，無法開啟圖目錄面板。",
            command_id=COMMAND_ID,
        )

    selected_sheets: List[str] = []
    session.ensure_layer(NUMBER_LAYER)
    session.set_layer_appearance(NUMBER_LAYER, NUMBER_COLOR)
    session.ensure_layer(NAME_LAYER)
    session.set_layer_appearance(NAME_LAYER, NAME_COLOR)
    session.ensure_layer(TEXT_LAYER)
    session.set_layer_appearance(TEXT_LAYER, TEXT_COLOR)

    class _CatalogDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = "LF_Catalog 圖目錄"
            self.Padding = drawing.Padding(12)
            self.Resizable = True
            self.Width = 420
            self.Height = 460
            font = None
            try:
                from loopflow.platform.rhino.prompts import _ui_font

                font = _ui_font(drawing, 11)
            except Exception:
                font = drawing.Font(drawing.Fonts.Sans, 11)

            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(8, 8)

            reminder = forms.Label()
            reminder.Text = PANEL_REMINDER
            reminder.Font = font
            layout.AddRow(reminder)

            self.count_label = forms.Label()
            self.count_label.Font = font
            layout.AddRow(self.count_label)

            buttons = (
                ("選取圖號定位點", self._on_pick_number),
                ("選取圖名定位點", self._on_pick_name),
                ("選取 Sheet", self._on_pick_sheets),
                ("Build／Rebind", self._on_build),
                ("Refresh", self._on_refresh),
                ("清除定位點並還原圖層", self._on_reset_points),
                ("匯出 TXT", self._on_export),
            )
            for caption, handler in buttons:
                button = forms.Button()
                button.Text = caption
                button.Height = 28
                button.Click += handler
                layout.AddRow(button)

            close_btn = forms.Button()
            close_btn.Text = "關閉"
            close_btn.Height = 28
            close_btn.Click += self._on_close
            layout.AddRow(close_btn)
            layout.Add(None)
            self.Content = layout
            self.AbortButton = close_btn
            self._refresh_counts()

        def _refresh_counts(self) -> None:
            numbers = _layer_field_ids(session, NUMBER_LAYER, FIELD_DRAWING_NO)
            names = _layer_field_ids(session, NAME_LAYER, FIELD_DRAWING_NAME)
            self.count_label.Text = "圖號定位點 %s　圖名定位點 %s　已選 Sheet %s" % (
                len(numbers),
                len(names),
                len(selected_sheets),
            )

        def _present(self, result: results.Result) -> None:
            if not result.ok:
                show_failure_popup(result)
            self._refresh_counts()

        def _on_pick_number(self, sender, e) -> None:
            self.Visible = False
            ids = _default_pick_points("選取圖號定位點（獨立 Point，Esc 取消）")
            self.Visible = True
            if ids is None:
                return
            self._present(assign_catalog_points(session, ids, FIELD_DRAWING_NO))

        def _on_pick_name(self, sender, e) -> None:
            self.Visible = False
            ids = _default_pick_points("選取圖名定位點（獨立 Point，Esc 取消）")
            self.Visible = True
            if ids is None:
                return
            self._present(assign_catalog_points(session, ids, FIELD_DRAWING_NAME))

        def _on_pick_sheets(self, sender, e) -> None:
            self.Visible = False
            try:
                picked = _default_pick_sheets(session, selected_sheets)
            finally:
                self.Visible = True
            if picked is None:
                return
            selected_sheets[:] = list(picked)
            self._refresh_counts()

        def _on_build(self, sender, e) -> None:
            if not selected_sheets:
                self.Visible = False
                try:
                    picked = _default_pick_sheets(session, selected_sheets)
                finally:
                    self.Visible = True
                if picked is None:
                    return
                selected_sheets[:] = list(picked)
                self._refresh_counts()
            self._present(build_catalog(session, tuple(selected_sheets)))

        def _on_refresh(self, sender, e) -> None:
            self._present(refresh_catalog(session))

        def _on_reset_points(self, sender, e) -> None:
            self._present(reset_catalog_points(session))

        def _on_export(self, sender, e) -> None:
            self._present(export_catalog_txt(session, ask_path=_default_ask_path))

        def _on_close(self, sender, e) -> None:
            self.Close(True)

    dialog = _CatalogDialog()
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    return results.ok(STAGE, "已關閉圖目錄面板。", command_id=COMMAND_ID)


def run_catalog(
    session: RhinoSession,
    *,
    show_panel: Optional[Callable[[RhinoSession], results.Result]] = None,
) -> results.Result:
    blocked = _require_schema(session)
    if blocked is not None:
        return blocked
    presenter = show_panel or _show_catalog_panel
    return presenter(session)
