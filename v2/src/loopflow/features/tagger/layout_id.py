# -*- coding: utf-8 -*-
"""LF_Tagger_Layout_ID：依 Layout 頁序建立與維護 Sheet metadata。

metadata 是圖號、圖名的真相；頁名與圖框顯示欄由 metadata 產生。責任、命名規則與
零寫入條件見 `v2/docs/資料契約.md` 的 Sheet 章節。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from loopflow.features.sheet.keys import (
    DRAWING_NAME_KEY,
    DRAWING_NO_KEY,
    SHEET_CODE_KEY,
    SHEET_ID_KEY,
)
from loopflow.features.sheet.metadata import (
    PageScan,
    get_sheet_field,
    register_title_frame_names,
    scan_layout_pages,
    write_sheet_metadata,
)
from loopflow.features.sheet.naming import (
    STATUS_BASELINE,
    STATUS_DUPLICATE_BASELINE,
    STATUS_MANUAL,
    STATUS_MANUAL_INVALID,
    STATUS_SKIPPED,
    STATUS_UNNUMBERED,
    NamingRules,
    PagePlan,
    assign_sheet_numbers,
    format_sheet_ref,
    load_naming_rules,
    parse_drawing_no,
)
from loopflow.features.tagger.binding import UUID_V4_RE, ensure_identity, new_id, text
from loopflow.features.tagger.keys import TARGET_LAYOUT_KEY, is_tag_locked
from loopflow.features.tagger.templates import TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.foundation.i18n import t
from loopflow.platform.rhino.session import RhinoSession, run_guarded

SKIP_MISSING_FRAME = "missing_title_frame"
SKIP_MISSING_START = "missing_series_start"
SKIP_BLANK_PAGE = "blank_page_name"
SKIP_MANUAL_INVALID = "manual_invalid"

COMMAND_ID = "LF_Tagger_Layout_ID"
STAGE = "write_sheet_id"
PAGE_TAG_TEMPLATE_ID = "TAG_ELEV_0"

ConfirmPlan = Callable[[Sequence[Sequence[str]]], bool]
AskRegister = Callable[[Sequence[str]], Sequence[str]]


@dataclass(frozen=True)
class SheetRow:
    """一頁的預定寫入內容。sheet_id 為 None 表示尚未建立身分。"""

    page_name: str
    page_number: int
    frame_id: str
    sheet_id: Optional[str]
    plan: PagePlan
    previous_drawing_no: Optional[str]
    previous_drawing_name: Optional[str]

    @property
    def is_new_sheet(self) -> bool:
        return self.sheet_id is None

    @property
    def renames_page(self) -> bool:
        return bool(self.plan.new_page_name) and self.plan.new_page_name != self.page_name


def _skip_reason(scan: PageScan) -> str:
    if scan.locked_frame_ids:
        return t("layout_id.005")
    if not scan.frame_ids:
        if scan.unregistered_blocks:
            return t("layout_id.016") % "、".join(scan.unregistered_blocks)
        return t("layout_id.006")
    return t("layout_id.007") % len(scan.frame_ids)


def _no_writable_pages_result(
    skipped: Sequence[dict],
    unknown: Sequence[str],
) -> results.Result:
    """沒有可寫入頁時，依實際原因說明；不要把「缺 ** 起點」說成缺圖框。"""
    codes = tuple(str(item.get("code") or "") for item in skipped)
    missing_start = SKIP_MISSING_START in codes
    frame_problem = any(code in (SKIP_MISSING_FRAME, SKIP_MANUAL_INVALID) for code in codes)
    details = {"skipped": skipped, "unregistered_blocks": unknown}
    if missing_start:
        return results.blocked(
            STAGE,
            t("layout_id.001"),
            ("missing_series_start",),
            command_id=COMMAND_ID,
            details=details,
        )
    lines = []
    blocking = []
    if frame_problem:
        blocking.append("missing_title_frame")
        lines.append(t("layout_id.008"))
    else:
        blocking.append("missing_title_frame")
        lines.append(t("layout_id.009"))
    if not skipped:
        lines.append(t("layout_id.010"))
    for item in skipped[:12]:
        lines.append(
            "%s：%s"
            % (item.get("page_name") or t("tag_o.032"), item.get("reason") or "")
        )
    if len(skipped) > 12:
        lines.append(t("layout_id.017") % (len(skipped) - 12))
    return results.blocked(
        STAGE,
        "\n".join(lines),
        tuple(blocking),
        command_id=COMMAND_ID,
        details=details,
    )


def unregistered_block_names(scans: Sequence[PageScan]) -> Tuple[str, ...]:
    """沒有可用圖框的頁面上出現的未登錄 Block 名，供詢問使用者是否登錄。"""
    names = []
    for scan in scans:
        if scan.usable_frame_id is not None:
            continue
        for name in scan.unregistered_blocks:
            if name not in names:
                names.append(name)
    return tuple(names)


def build_sheet_rows(
    session: RhinoSession,
    scans: Sequence[PageScan],
    rules: NamingRules,
) -> Tuple[Tuple[SheetRow, ...], Tuple[dict, ...]]:
    """可寫入的頁面產生 SheetRow；其餘回報為跳過項。"""
    writable = []
    skipped = []
    for scan in scans:
        frame_id = scan.usable_frame_id
        if frame_id is None:
            skipped.append(
                {
                    "page_name": scan.page_name,
                    "page_number": scan.page_number,
                    "code": SKIP_MISSING_FRAME,
                    "reason": _skip_reason(scan),
                }
            )
            continue
        writable.append((scan, frame_id))

    known_names = {}
    known_series = {}
    existing = {}
    seen_sheet_ids = set()
    for scan, frame_id in writable:
        sheet_id = text(session.get_object_user_text(frame_id, SHEET_ID_KEY))
        if sheet_id is not None and not UUID_V4_RE.match(sheet_id):
            sheet_id = None
        if sheet_id and sheet_id in seen_sheet_ids:
            sheet_id = None
        elif sheet_id:
            seen_sheet_ids.add(sheet_id)
        existing[scan.page_name] = sheet_id
        if sheet_id is None:
            continue
        name = get_sheet_field(session, sheet_id, "drawing_name")
        if name is not None:
            known_names[scan.page_name] = name
        series = get_sheet_field(session, sheet_id, "series")
        number = get_sheet_field(session, sheet_id, "sequence")
        if not number:
            _prefix, number = parse_drawing_no(get_sheet_field(session, sheet_id, "drawing_no"))
            series = series or _prefix
        if series and number:
            known_series[scan.page_name] = (series, number)

    pages = [
        {"name": scan.page_name, "page_number": scan.page_number}
        for scan, _frame_id in writable
    ]
    plans = assign_sheet_numbers(
        pages, rules, known_names=known_names, known_series=known_series
    )

    rows = []
    for (scan, frame_id), plan in zip(writable, plans):
        if plan.status in (STATUS_SKIPPED, STATUS_UNNUMBERED, STATUS_MANUAL_INVALID):
            if plan.status == STATUS_UNNUMBERED:
                reason = t("layout_id.018")
                code = SKIP_MISSING_START
            elif plan.status == STATUS_MANUAL_INVALID:
                reason = t("layout_id.026")
                code = SKIP_MANUAL_INVALID
            else:
                reason = t("layout_id.025")
                code = SKIP_BLANK_PAGE
            skipped.append(
                {
                    "page_name": scan.page_name,
                    "page_number": scan.page_number,
                    "code": code,
                    "reason": reason,
                }
            )
            continue
        sheet_id = existing.get(scan.page_name)
        rows.append(
            SheetRow(
                page_name=scan.page_name,
                page_number=scan.page_number,
                frame_id=frame_id,
                sheet_id=sheet_id,
                plan=plan,
                previous_drawing_no=(
                    get_sheet_field(session, sheet_id, "drawing_no") if sheet_id else None
                ),
                previous_drawing_name=(
                    get_sheet_field(session, sheet_id, "drawing_name") if sheet_id else None
                ),
            )
        )
    return tuple(rows), tuple(skipped)


def _preview_status(row: SheetRow) -> str:
    marks = []
    if row.plan.status == STATUS_BASELINE:
        marks.append(t("layout_id.011"))
    if row.plan.status == STATUS_MANUAL:
        marks.append(t("layout_id.012"))
    if row.plan.status == STATUS_DUPLICATE_BASELINE:
        marks.append(t("layout_id.013"))
    if row.previous_drawing_no and row.previous_drawing_no != row.plan.drawing_no:
        marks.append(t("layout_id.019") % (row.previous_drawing_no, row.plan.drawing_no))
    if (
        row.previous_drawing_name
        and row.previous_drawing_name != (row.plan.drawing_name or "")
    ):
        marks.append(
            t("layout_id.020") % (row.previous_drawing_name, row.plan.drawing_name or t("nexus_metadata.076"))
        )
    return "；".join(marks)


def preview_table_rows(
    rows: Sequence[SheetRow],
    skipped: Sequence[dict],
    page_order: Sequence[str] = (),
) -> Tuple[Tuple[str, str, str], ...]:
    """核對清單列，順序跟 Layout 列表相同。確認前不寫入。"""
    cells_by_name = {}
    for row in rows:
        name = row.page_name or t("tag_o.032")
        cells_by_name[name] = (
            name,
            row.plan.new_page_name or row.page_name or "",
            _preview_status(row),
        )
    for item in skipped:
        name = str(item.get("page_name") or t("tag_o.032"))
        cells_by_name[name] = (name, "", t("layout_id.021") % (item.get("reason") or ""))
    if page_order:
        table = []
        seen = set()
        for name in page_order:
            if name in cells_by_name and name not in seen:
                table.append(cells_by_name[name])
                seen.add(name)
        for name, cells in cells_by_name.items():
            if name not in seen:
                table.append(cells)
        return tuple(table)
    entries = []
    for row in rows:
        name = row.page_name or t("tag_o.032")
        number = row.page_number if row.page_number is not None else 0
        entries.append((int(number), cells_by_name[name]))
    for item in skipped:
        name = str(item.get("page_name") or t("tag_o.032"))
        raw = item.get("page_number")
        number = 0 if raw in (None, "") else int(raw)
        entries.append((number, cells_by_name[name]))
    entries.sort(key=lambda item: item[0])
    return tuple(cells for _number, cells in entries)


def preview_lines(rows: Sequence[SheetRow], skipped: Sequence[dict]) -> Tuple[str, ...]:
    """核對清單純文字（測試與無表格式介面）。"""
    lines = []
    for original, updated, status in preview_table_rows(rows, skipped):
        cells = [original, updated]
        if status:
            cells.append(status)
        lines.append("　".join(cells))
    return tuple(lines)


def _write_page_tags(
    session: RhinoSession,
    scan: PageScan,
    catalog: TagTemplateSet,
    sheet_code: str,
) -> int:
    """本頁圖號 Tag（TAG_ELEV_0）寫目前頁的 lf_sheet_code；鎖定的不覆寫。"""
    objects_fn = getattr(session, "objects_on_layout_page", None)
    if not callable(objects_fn):
        return 0
    written = 0
    for object_id in objects_fn(scan.page_name) or ():
        if not session.is_block_instance(object_id):
            continue
        template = catalog.by_block_name(session.block_definition_name(object_id) or "")
        if template is None or template.template_id != PAGE_TAG_TEMPLATE_ID:
            continue
        if is_tag_locked(session, object_id):
            continue
        session.set_object_user_text(object_id, SHEET_CODE_KEY, sheet_code)
        written += 1
    return written


def apply_sheet_rows(
    session: RhinoSession,
    rows: Sequence[SheetRow],
    scans: Sequence[PageScan],
    rules: NamingRules,
    catalog: TagTemplateSet,
) -> dict:
    """建立缺少的 sheet_id，寫 metadata、圖框顯示欄與頁名。"""
    scan_by_page = {scan.page_name: scan for scan in scans}
    created = 0
    renamed = 0
    tagged = 0
    rename_fn = getattr(session, "rename_layout_page", None)
    for row in rows:
        sheet_id = row.sheet_id
        if sheet_id is None:
            sheet_id = new_id()
            created += 1
        template = catalog.by_block_name(session.block_definition_name(row.frame_id) or "")
        if template is not None:
            ensure_identity(session, row.frame_id, template, "none")
        session.set_object_user_text(row.frame_id, SHEET_ID_KEY, sheet_id)
        write_sheet_metadata(
            session,
            sheet_id,
            {
                "drawing_no": row.plan.drawing_no,
                "drawing_name": row.plan.drawing_name or "",
                "series": row.plan.series,
                "sequence": row.plan.sequence,
                "page_position": row.page_number,
            },
        )
        session.set_object_user_text(row.frame_id, DRAWING_NO_KEY, row.plan.drawing_no or "")
        session.set_object_user_text(row.frame_id, DRAWING_NAME_KEY, row.plan.drawing_name or "")
        scan = scan_by_page.get(row.page_name)
        if scan is not None:
            sheet_code = format_sheet_ref(rules, row.plan.number or "")
            tagged += _write_page_tags(session, scan, catalog, sheet_code)
    if callable(rename_fn):
        for row in reversed(list(rows)):
            if row.renames_page and rename_fn(row.page_name, row.plan.new_page_name):
                renamed += 1
                _remap_index_target_layouts(
                    session, row.page_name, row.plan.new_page_name
                )
    redraw = getattr(session, "redraw", None)
    if callable(redraw):
        redraw()
    return {
        "sheets": len(rows),
        "created_sheet_ids": created,
        "renamed_pages": renamed,
        "page_tags": tagged,
    }


def _remap_index_target_layouts(session: RhinoSession, old_name: str, new_name: str) -> None:
    """Layout 改名後，把 Index Tag 上記住的目標頁名一併改掉。"""
    if not old_name or old_name == new_name:
        return
    objects_fn = getattr(session, "objects_on_layout_page", None)
    pages_fn = getattr(session, "listed_layout_pages", None)
    if not callable(objects_fn):
        return
    page_names = []
    if callable(pages_fn):
        page_names = [str(item.get("name") or "") for item in pages_fn() or ()]
    for extra in (old_name, new_name):
        if extra and extra not in page_names:
            page_names.append(extra)
    seen = set()
    for page_name in page_names:
        for object_id in objects_fn(page_name) or ():
            if object_id in seen:
                continue
            seen.add(object_id)
            stored = text(session.get_object_user_text(object_id, TARGET_LAYOUT_KEY))
            if stored == old_name:
                session.set_object_user_text(object_id, TARGET_LAYOUT_KEY, new_name)


def _default_confirm(table_rows: Sequence[Sequence[str]]) -> bool:
    from loopflow.platform.rhino.prompts import ask_confirm_table

    return ask_confirm_table(
        (t("layout_id.002"), t("layout_id.003"), t("layout_id.004")), table_rows, title=t("layout_id.014")
    )


def _default_ask_register(names: Sequence[str]) -> Sequence[str]:
    from loopflow.platform.rhino.prompts import ask_pick_title_frames

    return ask_pick_title_frames(names)


def _picked_title_frames(
    asker: AskRegister,
    unknown: Sequence[str],
) -> Tuple[str, ...]:
    """只接受清單裡的名稱；空選、取消或否都當沒登錄。"""
    if not unknown:
        return ()
    selected = asker(unknown)
    if selected is True:
        selected = unknown
    if not selected:
        return ()
    allowed = {name.casefold(): name for name in unknown}
    picked = []
    for item in selected:
        key = str(item or "").strip().casefold()
        name = allowed.get(key)
        if name is not None and name not in picked:
            picked.append(name)
    return tuple(picked)


def run_tagger_layout_id(
    session: RhinoSession,
    *,
    confirm: Optional[ConfirmPlan] = None,
    ask_register: Optional[AskRegister] = None,
    catalog: Optional[TagTemplateSet] = None,
) -> results.Result:
    """盤點 Layout 頁 → 核對清單 → 寫 Sheet metadata、顯示欄與頁名。取消不寫入。"""
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
    confirmer = confirm or _default_confirm
    register_asker = ask_register or _default_ask_register

    def action(current: RhinoSession) -> results.Result:
        scans = scan_layout_pages(current, loaded)
        if not scans:
            return results.blocked(
                STAGE,
                t("layout_id.022"),
                ("missing_layout",),
                command_id=COMMAND_ID,
            )
        rules = load_naming_rules(current)
        rows, skipped = build_sheet_rows(current, scans, rules)
        unknown = unregistered_block_names(scans)
        picked = _picked_title_frames(register_asker, unknown)
        if picked:
            register_title_frame_names(current, picked)
            scans = scan_layout_pages(current, loaded)
            rows, skipped = build_sheet_rows(current, scans, rules)
            unknown = unregistered_block_names(scans)
        if not rows:
            return _no_writable_pages_result(skipped, unknown)
        page_order = tuple(scan.page_name for scan in scans if scan.page_name)
        if not confirmer(preview_table_rows(rows, skipped, page_order=page_order)):
            return results.cancelled(
                STAGE,
                t("layout_id.023"),
                command_id=COMMAND_ID,
            )
        summary = apply_sheet_rows(current, rows, scans, rules, loaded)
        summary["skipped"] = skipped
        summary["unregistered_blocks"] = unknown
        message = t("layout_id.015") % (
            summary["sheets"],
            summary["created_sheet_ids"],
            summary["renamed_pages"],
        )
        if skipped:
            message += t("layout_id.024") % len(skipped)
        return results.ok(STAGE, message, command_id=COMMAND_ID, details=summary)

    return run_guarded(session, action, command_id=COMMAND_ID)
