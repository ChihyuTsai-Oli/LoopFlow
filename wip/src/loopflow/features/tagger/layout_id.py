# -*- coding: utf-8 -*-
"""LF_Tagger_Layout_ID：依 Layout 頁序建立與維護 Sheet metadata。

metadata 是圖號、圖名的真相；頁名與圖框顯示欄由 metadata 產生。責任、命名規則與
零寫入條件見 `wip/docs/資料契約.md` 的 Sheet 章節。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence, Tuple

from loopflow.features.sheet.keys import (
    DRAWING_NAME_KEY,
    DRAWING_NO_KEY,
    LEGACY_DRAWING_NAME_KEY,
    LEGACY_DRAWING_NO_KEY,
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
from loopflow.features.tagger.keys import LOCK_STATE_KEY, is_lock_true
from loopflow.features.tagger.templates import TagTemplateSet, load_tag_templates
from loopflow.features.viewer.inspect import check_document_schema
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Tagger_Layout_ID"
STAGE = "write_sheet_id"
PAGE_TAG_TEMPLATE_ID = "TAG_ELEV_0"
SERIES_START_HELP = (
    "圖框已就緒，但尚未設定系列起點，因此未執行。\n"
    "請將每個系列的第一頁按照下列規則命名：\n"
    "**圖類別__圖號__圖名\n"
    "**IN__101.01__一樓平面圖\n"
    "**A__101__一樓平面圖\n"
    "---\n"
    "1. ** 作為自動編號起點，勿刪\n"
    "2. ** 之間的頁面為同一系列\n"
    "3. ** 頁面之外的Layout名稱，只需要填寫圖名\n"
    "4. // 頁面不參與自動編號，但仍需使用相同命名格式規範\n"
    "5. 圖號 / 圖名 的編號與命名可以從Layout列表手動調整\n"
    "　經由自動編號寫入圖框中，不可直接修改圖框內容\n"
    "---\n"
    "\n"
    "Sample\n"
    "\n"
    "**IN__101.01__一樓平面圖\n"
    "二樓平面圖\n"
    "三樓平面圖\n"
    "**IN__201.01__立面圖1\n"
    "立面圖2\n"
    "//S__901__結構平面圖\n"
    "--------Layout自動編號如下--------\n"
    "**IN__101.01__一樓平面圖\n"
    "IN__101.02__二樓平面圖\n"
    "IN__101.03__三樓平面圖\n"
    "**IN__201.01__立面圖1\n"
    "IN__201.02__立面圖2\n"
    "//S__901__結構平面圖"
)

ConfirmPlan = Callable[[Sequence[str]], bool]
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
        return "圖框已鎖定"
    if not scan.frame_ids:
        if scan.unregistered_blocks:
            return "沒有登錄的圖框（未登錄圖塊：%s）" % "、".join(scan.unregistered_blocks)
        return "這一頁沒有圖框"
    return "這一頁有 %s 個圖框，無法決定身分" % len(scan.frame_ids)


def _no_writable_pages_result(
    skipped: Sequence[dict],
    unknown: Sequence[str],
) -> results.Result:
    """沒有可寫入頁時，依實際原因說明；不要把「缺 ** 起點」說成缺圖框。"""
    reasons = tuple(str(item.get("reason") or "") for item in skipped)
    missing_start = any("系列起點" in reason for reason in reasons)
    frame_problem = any(
        reason and "系列起點" not in reason and "頁名是空的" not in reason
        for reason in reasons
    )
    details = {"skipped": skipped, "unregistered_blocks": unknown}
    if missing_start:
        return results.blocked(
            STAGE,
            SERIES_START_HELP,
            ("missing_series_start",),
            command_id=COMMAND_ID,
            details=details,
        )
    lines = []
    blocking = []
    if frame_problem:
        blocking.append("missing_title_frame")
        lines.append("沒有可寫入的 Layout 頁。請確認每一頁只有一個已登錄的圖框。")
    else:
        blocking.append("missing_title_frame")
        lines.append("沒有可寫入的 Layout 頁。")
    if not skipped:
        lines.append("這份檔案沒有可編號的 Layout 頁。")
    for item in skipped[:12]:
        lines.append(
            "%s：%s"
            % (item.get("page_name") or "（未命名頁）", item.get("reason") or "")
        )
    if len(skipped) > 12:
        lines.append("…另有 %s 頁。" % (len(skipped) - 12))
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
                    "reason": _skip_reason(scan),
                }
            )
            continue
        writable.append((scan, frame_id))

    known_names = {}
    known_series = {}
    existing = {}
    for scan, frame_id in writable:
        sheet_id = text(session.get_object_user_text(frame_id, SHEET_ID_KEY))
        if sheet_id is not None and not UUID_V4_RE.match(sheet_id):
            sheet_id = None
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
                reason = "頁序中還沒有系列起點，未編號"
            elif plan.status == STATUS_MANUAL_INVALID:
                reason = "手動頁格式不正確，需 //圖類別__圖號__圖名"
            else:
                reason = "頁名是空的"
            skipped.append(
                {
                    "page_name": scan.page_name,
                    "page_number": scan.page_number,
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


def preview_lines(rows: Sequence[SheetRow], skipped: Sequence[dict]) -> Tuple[str, ...]:
    """核對清單。使用者確認前不寫入任何資料。"""
    lines = []
    for row in rows:
        marks = []
        if row.is_new_sheet:
            marks.append("新頁")
        if row.plan.status == STATUS_BASELINE:
            marks.append("系列起點")
        if row.plan.status == STATUS_MANUAL:
            marks.append("手動頁，不編號")
        if row.plan.status == STATUS_DUPLICATE_BASELINE:
            marks.append("重複的系列起點，已接續目前系列")
        if row.previous_drawing_no and row.previous_drawing_no != row.plan.drawing_no:
            marks.append("圖號 %s → %s" % (row.previous_drawing_no, row.plan.drawing_no))
        if (
            row.previous_drawing_name
            and row.previous_drawing_name != (row.plan.drawing_name or "")
        ):
            marks.append(
                "圖名 %s → %s" % (row.previous_drawing_name, row.plan.drawing_name or "（空）")
            )
        if row.renames_page:
            marks.append("頁名 → %s" % row.plan.new_page_name)
        suffix = "　［%s］" % "；".join(marks) if marks else ""
        lines.append(
            "%02d　%s　%s%s"
            % (
                row.page_number,
                row.plan.drawing_no or "",
                row.plan.drawing_name or "（未命名）",
                suffix,
            )
        )
    for item in skipped:
        lines.append(
            "--　%s　跳過：%s" % (item.get("page_name") or "（未命名頁）", item.get("reason") or "")
        )
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
        if is_lock_true(session.get_object_user_text(object_id, LOCK_STATE_KEY)):
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
        session.set_object_user_text(row.frame_id, LEGACY_DRAWING_NO_KEY, row.plan.drawing_no or "")
        session.set_object_user_text(row.frame_id, LEGACY_DRAWING_NAME_KEY, row.plan.drawing_name or "")
        scan = scan_by_page.get(row.page_name)
        if scan is not None:
            sheet_code = format_sheet_ref(rules, row.plan.number or "")
            tagged += _write_page_tags(session, scan, catalog, sheet_code)
    if callable(rename_fn):
        for row in reversed(list(rows)):
            if row.renames_page and rename_fn(row.page_name, row.plan.new_page_name):
                renamed += 1
    redraw = getattr(session, "redraw", None)
    if callable(redraw):
        redraw()
    return {
        "sheets": len(rows),
        "created_sheet_ids": created,
        "renamed_pages": renamed,
        "page_tags": tagged,
    }


def _default_confirm(lines: Sequence[str]) -> bool:
    from loopflow.platform.rhino.prompts import ask_confirm_list

    return ask_confirm_list(lines, title="Layout ID 核對清單")


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
    confirmer = confirm or _default_confirm
    register_asker = ask_register or _default_ask_register

    def action(current: RhinoSession) -> results.Result:
        scans = scan_layout_pages(current, loaded)
        if not scans:
            return results.blocked(
                STAGE,
                "這份檔案沒有 Layout 分頁，已停止，不寫入。",
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
        if not confirmer(preview_lines(rows, skipped)):
            return results.cancelled(
                STAGE,
                "已取消 Layout ID，未寫入。",
                command_id=COMMAND_ID,
            )
        summary = apply_sheet_rows(current, rows, scans, rules, loaded)
        summary["skipped"] = skipped
        summary["unregistered_blocks"] = unknown
        message = "已寫入 %s 頁圖號；新建 %s 個 Sheet 身分，改名 %s 頁。" % (
            summary["sheets"],
            summary["created_sheet_ids"],
            summary["renamed_pages"],
        )
        if skipped:
            message += "跳過 %s 頁，詳見報告。" % len(skipped)
        return results.ok(STAGE, message, command_id=COMMAND_ID, details=summary)

    return run_guarded(session, action, command_id=COMMAND_ID)
