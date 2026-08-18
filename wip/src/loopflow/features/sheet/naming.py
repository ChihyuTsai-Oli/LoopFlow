# -*- coding: utf-8 -*-
"""Sheet 圖號命名的純邏輯：頁名解析與依頁序推導圖號。

不碰 Rhino。命名格式來自文件 UserText，缺值用 `keys.NAMING_DEFAULTS`。
頁名：`**圖類別__圖編號__圖名`（寫入後起點頁保留 `**`）；圖框圖號：`圖類別 圖編號`（空格，不含星號）。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from loopflow.features.sheet.keys import NAMING_DEFAULTS, NAMING_KEYS

PARSE_BASELINE = "baseline"
PARSE_INHERIT = "inherit"
PARSE_SKIP = "skip"

STATUS_BASELINE = "baseline"
STATUS_NUMBERED = "numbered"
STATUS_DUPLICATE_BASELINE = "duplicate_baseline"
STATUS_UNNUMBERED = "unnumbered"
STATUS_SKIPPED = "skipped_blank_name"

NUMBER_RE = re.compile(r"^\d+(?:\.\d+)*$")


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
    return bool(value) and NUMBER_RE.match(value) is not None


def increment_number(token: str, steps: int = 1) -> str:
    """只加編號尾數。`201`→`202`；`201.02`→`201.03`。"""
    raw = (token or "").strip()
    if steps == 0:
        return raw
    if "." in raw:
        head, _, tail = raw.rpartition(".")
        if tail.isdigit():
            width = len(tail)
            return "%s.%0*d" % (head, width, int(tail) + steps)
    if raw.isdigit():
        next_value = int(raw) + steps
        if raw.startswith("0") and len(raw) > 1:
            return "%0*d" % (len(raw), next_value)
        return str(next_value)
    raise ValueError("無法遞增的圖編號：%s" % token)


def split_fields(page_name: str, rules: NamingRules) -> Tuple[str, ...]:
    raw = "" if page_name is None else str(page_name).strip()
    if not raw:
        return ()
    if not rules.separator:
        return (raw,)
    return tuple(part.strip() for part in raw.split(rules.separator))


def parse_page_name(page_name: str, rules: NamingRules) -> PageParse:
    """解析頁名。有 `**` 才當系列起點；三欄結構可更新圖名。"""
    raw = "" if page_name is None else str(page_name).strip()
    if not raw:
        return PageParse(kind=PARSE_SKIP)
    marked = bool(rules.baseline_mark) and raw.startswith(rules.baseline_mark)
    if marked:
        raw = raw[len(rules.baseline_mark) :].lstrip()
        if not raw:
            return PageParse(kind=PARSE_SKIP)
    parts = split_fields(raw, rules)
    if marked:
        if (
            len(parts) >= 2
            and parts[0]
            and is_number_token(parts[1])
        ):
            name = rules.separator.join(parts[2:]) if len(parts) > 2 else ""
            return PageParse(
                kind=PARSE_BASELINE,
                drawing_name=name,
                prefix=parts[0],
                number=parts[1],
                structured=True,
            )
        return PageParse(kind=PARSE_INHERIT, drawing_name=raw)
    if len(parts) >= 2 and parts[0] and is_number_token(parts[1]):
        name = rules.separator.join(parts[2:]) if len(parts) > 2 else ""
        return PageParse(
            kind=PARSE_INHERIT,
            drawing_name=name,
            prefix=parts[0],
            number=parts[1],
            structured=True,
        )
    return PageParse(kind=PARSE_INHERIT, drawing_name=raw)


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
) -> str:
    left = "%s%s%s" % (prefix, rules.separator, number)
    name = (drawing_name or "").strip()
    body = left if not name else "%s%s%s" % (left, rules.separator, name)
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
    （誤改頁名則恢復舊圖名）。`known_series` 是 `{page_name: (prefix, number)}`，
    在尚未碰到 `**` 起點時，讓已有 metadata 的第一頁接續原系列，並把 `**` 加回頁名。
    圖框圖號不含 `**`。
    """
    lookup = dict(known_names or {})
    series_lookup = dict(known_series or {})
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
            stored = series_lookup.get(page_name)
            if stored and stored[0] and stored[1]:
                prefix, number = stored[0], stored[1]
                status = STATUS_BASELINE
                seen_baselines.add((prefix, number))
            else:
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
