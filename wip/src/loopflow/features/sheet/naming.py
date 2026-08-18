# -*- coding: utf-8 -*-
"""Sheet 圖號命名的純邏輯：頁名解析與依頁序推導圖號。

不碰 Rhino。命名格式來自文件 UserText，缺值用 `keys.NAMING_DEFAULTS`。
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from loopflow.features.sheet.keys import NAMING_DEFAULTS, NAMING_KEYS

# 解析狀態：頁名能否提供系列起點
PARSE_BASELINE = "baseline"
PARSE_INHERIT = "inherit"
PARSE_SKIP = "skip"

# 編號狀態：這一頁最後怎麼處理
STATUS_BASELINE = "baseline"
STATUS_NUMBERED = "numbered"
STATUS_DUPLICATE_BASELINE = "duplicate_baseline"
STATUS_UNNUMBERED = "unnumbered"
STATUS_SKIPPED = "skipped_blank_name"


@dataclass(frozen=True)
class NamingRules:
    separator: str = NAMING_DEFAULTS["separator"]
    baseline_mark: str = NAMING_DEFAULTS["baseline_mark"]
    drawing_no_format: str = NAMING_DEFAULTS["drawing_no_format"]
    sheet_ref_format: str = NAMING_DEFAULTS["sheet_ref_format"]
    prefix_pattern: str = NAMING_DEFAULTS["prefix_pattern"]


@dataclass(frozen=True)
class PageParse:
    kind: str
    drawing_name: Optional[str] = None
    prefix: Optional[str] = None
    major: Optional[int] = None


@dataclass(frozen=True)
class PagePlan:
    page_name: str
    page_number: int
    status: str
    series: Optional[str] = None
    prefix: Optional[str] = None
    major: Optional[int] = None
    sequence: Optional[int] = None
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


def split_page_name(page_name: str, rules: NamingRules) -> Tuple[str, Optional[str]]:
    """以第一個 separator 切開；其餘 separator 全部留在圖名。"""
    raw = "" if page_name is None else str(page_name)
    if rules.separator and rules.separator in raw:
        head, _, tail = raw.partition(rules.separator)
        return head.strip(), tail.strip()
    return raw.strip(), None


def parse_page_name(page_name: str, rules: NamingRules) -> PageParse:
    """只在首次匯入時使用；之後圖號一律以 metadata 為準。"""
    head, tail = split_page_name(page_name, rules)
    if not head and not tail:
        return PageParse(kind=PARSE_SKIP)
    drawing_name = tail if tail is not None else head
    if rules.baseline_mark and head.endswith(rules.baseline_mark):
        stem = head[: -len(rules.baseline_mark)].strip()
        match = re.search(rules.prefix_pattern, stem)
        if match:
            prefix = match.group(1).strip()
            return PageParse(
                kind=PARSE_BASELINE,
                drawing_name=drawing_name,
                prefix=prefix,
                major=int(match.group(2)),
            )
    return PageParse(kind=PARSE_INHERIT, drawing_name=drawing_name)


def parse_series_text(series: Optional[str], rules: NamingRules) -> Tuple[Optional[str], Optional[int]]:
    """從已存的 series 文字（例如 `IN 101`）取回前綴與主號。"""
    raw = (series or "").strip()
    if not raw:
        return None, None
    match = re.search(rules.prefix_pattern, raw)
    if not match:
        return None, None
    return match.group(1).strip(), int(match.group(2))


def format_series(prefix: str, major: int) -> str:
    return "%s %s" % (prefix, major)


def format_drawing_no(rules: NamingRules, prefix: str, major: int, minor: int) -> str:
    return rules.drawing_no_format.format(prefix=prefix, major=major, minor=minor)


def format_sheet_ref(rules: NamingRules, major: int, minor: int) -> str:
    """Tag 上引用他頁時的短碼，不含系列前綴。"""
    return rules.sheet_ref_format.format(major=major, minor=minor)


def compose_page_name(rules: NamingRules, drawing_no: str, drawing_name: Optional[str]) -> str:
    name = (drawing_name or "").strip()
    if not name:
        return drawing_no
    return "%s%s%s" % (drawing_no, rules.separator, name)


def assign_sheet_numbers(
    pages: Sequence[dict],
    rules: NamingRules,
    *,
    known_names: Optional[dict] = None,
    known_series: Optional[dict] = None,
) -> Tuple[PagePlan, ...]:
    """依 Layout 頁序推導每頁的系列、次號、圖號與應有頁名。

    `pages` 依頁序排列，每項至少有 `name` 與 `page_number`。`known_names` 是
    `{page_name: drawing_name}`，`known_series` 是 `{page_name: (prefix, major)}`，
    代表 metadata 已有的值：既有 Sheet 不再從頁名重解圖名或系列。
    """
    lookup = dict(known_names or {})
    series_lookup = dict(known_series or {})
    plans = []
    prefix: Optional[str] = None
    major: Optional[int] = None
    minor = 0
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
            key = (parse.prefix, parse.major)
            if key in seen_baselines:
                status = STATUS_DUPLICATE_BASELINE
                minor += 1
            else:
                seen_baselines.add(key)
                prefix, major = parse.prefix, parse.major
                minor = 1
                status = STATUS_BASELINE
        elif prefix is None:
            stored = series_lookup.get(page_name)
            if stored and stored[0] is not None and stored[1] is not None:
                prefix, major = stored
                minor = 1
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
            minor += 1
        if page_name in lookup:
            drawing_name = lookup[page_name]
        else:
            drawing_name = parse.drawing_name or ""
        drawing_no = format_drawing_no(rules, prefix, major, minor)
        plans.append(
            PagePlan(
                page_name=page_name,
                page_number=page_number,
                status=status,
                series=format_series(prefix, major),
                prefix=prefix,
                major=major,
                sequence=minor,
                drawing_no=drawing_no,
                drawing_name=drawing_name,
                new_page_name=compose_page_name(rules, drawing_no, drawing_name),
            )
        )
    return tuple(plans)
