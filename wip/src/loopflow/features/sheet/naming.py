# -*- coding: utf-8 -*-
"""Sheet 圖號命名的純邏輯：頁名解析與依頁序推導圖號。

不碰 Rhino。命名格式來自文件 UserText，缺值用 `keys.NAMING_DEFAULTS`。
頁名：`**圖類別__圖編號__圖名`（寫入後起點頁保留 `**`）；`//` 手動頁不編號但寫入圖框。
圖框圖號：`圖類別 圖編號`（空格，不含 `**`／`//`）。圖編號只要尾端是數字即可。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from loopflow.features.sheet.keys import NAMING_DEFAULTS, NAMING_KEYS
from loopflow.foundation.i18n import t

PARSE_BASELINE = "baseline"
PARSE_INHERIT = "inherit"
PARSE_MANUAL = "manual"
PARSE_MANUAL_INVALID = "manual_invalid"
PARSE_SKIP = "skip"

STATUS_BASELINE = "baseline"
STATUS_NUMBERED = "numbered"
STATUS_DUPLICATE_BASELINE = "duplicate_baseline"
STATUS_MANUAL = "manual"
STATUS_MANUAL_INVALID = "manual_invalid"
STATUS_UNNUMBERED = "unnumbered"
STATUS_SKIPPED = "skipped_blank_name"

MANUAL_MARK = "//"
TRAILING_DIGITS_RE = re.compile(r"^(.*?)(\d+)$")


@dataclass(frozen=True)
class NamingRules:
    separator: str = NAMING_DEFAULTS["separator"]
    baseline_mark: str = NAMING_DEFAULTS["baseline_mark"]
    drawing_no_format: str = NAMING_DEFAULTS["drawing_no_format"]
    sheet_ref_format: str = NAMING_DEFAULTS["sheet_ref_format"]


@dataclass(frozen=True)
class PageParse:
    kind: str
    drawing_name: Optional[str] = None
    prefix: Optional[str] = None
    number: Optional[str] = None
    structured: bool = False


@dataclass(frozen=True)
class PagePlan:
    page_name: str
    page_number: int
    status: str
    series: Optional[str] = None
    prefix: Optional[str] = None
    number: Optional[str] = None
    sequence: Optional[str] = None
    drawing_no: Optional[str] = None
    drawing_name: Optional[str] = None
    new_page_name: Optional[str] = None


def load_naming_rules(session) -> NamingRules:
    """讀文件 UserText 的命名設定；不寫死單機路徑的 config 檔。"""
    values = {}
    for field, key in NAMING_KEYS.items():
        raw = session.document_user_text(key)
        text = None if raw in (None, "") else str(raw)
        if text:
            values[field] = text
    return NamingRules(**values)


def is_number_token(value: str) -> bool:
    """圖號只要尾端是數字就放行，允許前面英數（`201`、`101.1`、`A01`）。"""
    raw = (value or "").strip()
    return bool(raw) and TRAILING_DIGITS_RE.match(raw) is not None


def increment_number(token: str, steps: int = 1) -> str:
    """只加編號尾端數字。`201`→`202`；`A09`→`A10`；`101.1`→`101.2`；`101.9`→`101.10`。"""
    raw = (token or "").strip()
    if steps == 0:
        return raw
    match = TRAILING_DIGITS_RE.match(raw)
    if match is None:
        raise ValueError(t("duplicate_layout.015") % token)
    head, tail = match.group(1), match.group(2)
    next_value = int(tail) + steps
    width = len(tail)
    if width == 1:
        return "%s%s" % (head, next_value)
    return "%s%0*d" % (head, width, next_value)


def split_fields(page_name: str, rules: NamingRules) -> Tuple[str, ...]:
    raw = "" if page_name is None else str(page_name).strip()
    if not raw:
        return ()
    if not rules.separator:
        return (raw,)
    return tuple(part.strip() for part in raw.split(rules.separator))


def _three_part(parts: Tuple[str, ...], rules: NamingRules):
    if len(parts) >= 2 and parts[0] and is_number_token(parts[1]):
        name = rules.separator.join(parts[2:]) if len(parts) > 2 else ""
        return parts[0], parts[1], name
    return None


def parse_page_name(page_name: str, rules: NamingRules) -> PageParse:
    """解析頁名。`//` 為手動頁；`**` 才當系列起點；三欄結構可更新圖名。"""
    raw = "" if page_name is None else str(page_name).strip()
    if not raw:
        return PageParse(kind=PARSE_SKIP)
    if raw.startswith(MANUAL_MARK):
        body = raw[len(MANUAL_MARK) :].lstrip()
        if not body:
            return PageParse(kind=PARSE_MANUAL_INVALID, drawing_name="")
        parsed = _three_part(split_fields(body, rules), rules)
        if parsed is None:
            return PageParse(kind=PARSE_MANUAL_INVALID, drawing_name=body)
        prefix, number, name = parsed
        return PageParse(
            kind=PARSE_MANUAL,
            drawing_name=name,
            prefix=prefix,
            number=number,
            structured=True,
        )
    marked = bool(rules.baseline_mark) and raw.startswith(rules.baseline_mark)
    if marked:
        raw = raw[len(rules.baseline_mark) :].lstrip()
        if not raw:
            return PageParse(kind=PARSE_SKIP)
    parts = split_fields(raw, rules)
    parsed = _three_part(parts, rules)
    if marked:
        if parsed is None:
            return PageParse(kind=PARSE_INHERIT, drawing_name=raw)
        prefix, number, name = parsed
        return PageParse(
            kind=PARSE_BASELINE,
            drawing_name=name,
            prefix=prefix,
            number=number,
            structured=True,
        )
    if parsed is None:
        return PageParse(kind=PARSE_INHERIT, drawing_name=raw)
    prefix, number, name = parsed
    return PageParse(
        kind=PARSE_INHERIT,
        drawing_name=name,
        prefix=prefix,
        number=number,
        structured=True,
    )


def parse_drawing_no(drawing_no: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """從圖框圖號 `IN 201` 取回圖類別與編號。"""
    raw = (drawing_no or "").strip()
    if not raw or " " not in raw:
        return None, None
    prefix, _, number = raw.partition(" ")
    prefix = prefix.strip()
    number = number.strip()
    if not prefix or not is_number_token(number):
        return None, None
    return prefix, number


def parse_series_text(series: Optional[str]) -> Optional[str]:
    """已存的 series 就是圖類別（`IN`、`A`）。"""
    raw = (series or "").strip()
    return raw or None


def format_drawing_no(rules: NamingRules, prefix: str, number: str) -> str:
    return rules.drawing_no_format.format(prefix=prefix, number=number)


def format_sheet_ref(rules: NamingRules, number: str) -> str:
    """Tag 上引用他頁時的短碼，只寫圖編號。"""
    return rules.sheet_ref_format.format(number=number)


def compose_page_name(
    rules: NamingRules,
    prefix: str,
    number: str,
    drawing_name: Optional[str],
    *,
    marked: bool = False,
    manual: bool = False,
) -> str:
    left = "%s%s%s" % (prefix, rules.separator, number)
    name = (drawing_name or "").strip()
    body = left if not name else "%s%s%s" % (left, rules.separator, name)
    if manual:
        return "%s%s" % (MANUAL_MARK, body)
    if marked and rules.baseline_mark:
        return "%s%s" % (rules.baseline_mark, body)
    return body


def assign_sheet_numbers(
    pages: Sequence[dict],
    rules: NamingRules,
    *,
    known_names: Optional[dict] = None,
    known_series: Optional[dict] = None,
) -> Tuple[PagePlan, ...]:
    """依 Layout 頁序推導每頁的系列、編號、圖號與應有頁名。

    `known_names` 是 `{page_name: drawing_name}`，僅在頁名不是三欄結構時使用
    （誤改頁名則恢復舊圖名）。沒有 `**` 時不得用舊 metadata 當起點。
    `//` 手動頁不改系列尾數。圖框圖號不含 `**`／`//`。
    """
    lookup = dict(known_names or {})
    plans = []
    prefix: Optional[str] = None
    number: Optional[str] = None
    seen_baselines = set()
    for item in pages:
        page_name = str(item.get("name") or "")
        page_number = int(item.get("page_number") or (len(plans) + 1))
        parse = parse_page_name(page_name, rules)
        if parse.kind == PARSE_SKIP:
            plans.append(
                PagePlan(
                    page_name=page_name,
                    page_number=page_number,
                    status=STATUS_SKIPPED,
                )
            )
            continue
        if parse.kind == PARSE_MANUAL_INVALID:
            plans.append(
                PagePlan(
                    page_name=page_name,
                    page_number=page_number,
                    status=STATUS_MANUAL_INVALID,
                    drawing_name=parse.drawing_name,
                )
            )
            continue
        if parse.kind == PARSE_MANUAL:
            drawing_no = format_drawing_no(rules, parse.prefix or "", parse.number or "")
            plans.append(
                PagePlan(
                    page_name=page_name,
                    page_number=page_number,
                    status=STATUS_MANUAL,
                    series=parse.prefix,
                    prefix=parse.prefix,
                    number=parse.number,
                    sequence=parse.number,
                    drawing_no=drawing_no,
                    drawing_name=parse.drawing_name or "",
                    new_page_name=compose_page_name(
                        rules,
                        parse.prefix or "",
                        parse.number or "",
                        parse.drawing_name,
                        manual=True,
                    ),
                )
            )
            continue
        status = STATUS_NUMBERED
        if parse.kind == PARSE_BASELINE:
            key = (parse.prefix, parse.number)
            if key in seen_baselines:
                status = STATUS_DUPLICATE_BASELINE
                number = increment_number(number or parse.number)
            else:
                seen_baselines.add(key)
                prefix, number = parse.prefix, parse.number
                status = STATUS_BASELINE
        elif prefix is None:
            plans.append(
                PagePlan(
                    page_name=page_name,
                    page_number=page_number,
                    status=STATUS_UNNUMBERED,
                    drawing_name=lookup.get(page_name) or parse.drawing_name,
                )
            )
            continue
        else:
            number = increment_number(number)
        if parse.structured:
            drawing_name = parse.drawing_name or ""
        elif page_name in lookup:
            drawing_name = lookup[page_name]
        else:
            drawing_name = parse.drawing_name or ""
        drawing_no = format_drawing_no(rules, prefix, number)
        plans.append(
            PagePlan(
                page_name=page_name,
                page_number=page_number,
                status=status,
                series=prefix,
                prefix=prefix,
                number=number,
                sequence=number,
                drawing_no=drawing_no,
                drawing_name=drawing_name,
                new_page_name=compose_page_name(
                    rules,
                    prefix,
                    number,
                    drawing_name,
                    marked=(status == STATUS_BASELINE),
                ),
            )
        )
    return tuple(plans)
