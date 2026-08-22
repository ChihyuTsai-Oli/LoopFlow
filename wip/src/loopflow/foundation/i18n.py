# -*- coding: utf-8 -*-
"""畫面句子：依這台電腦記住的語系取繁中或 English。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, Optional

from loopflow.foundation.locale import LOCALE_EN, LOCALE_ZH_TW, resolved_locale

CATALOG_PATH = Path(__file__).with_name("i18n_catalog.json")
_CACHE = None


def load_catalog() -> Mapping[str, Mapping[str, str]]:
    global _CACHE
    if _CACHE is None:
        _CACHE = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return _CACHE


def current_locale() -> str:
    """未記住時畫面用英文。"""
    return resolved_locale()


def t(key: str, *args, locale: Optional[str] = None) -> str:
    """取句子。缺 key 視為程式錯誤；%s 由呼叫端傳入，不翻譯。"""
    entry = load_catalog().get(key)
    if not entry:
        raise KeyError("未知句子 id：%s" % key)
    chosen = locale or current_locale()
    text = entry.get(chosen) or entry.get(LOCALE_ZH_TW)
    if text is None:
        raise KeyError("句子 id 沒有繁中：%s" % key)
    if args:
        return text % args
    return text


def is_english() -> bool:
    return current_locale() == LOCALE_EN
