# -*- coding: utf-8 -*-
"""這台電腦的介面語系偏好。不寫進 .3dm，也不猜 Rhino／Windows 語言。"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Optional

LOCALE_ZH_TW = "zh-TW"
LOCALE_EN = "en"
DEFAULT_LOCALE = LOCALE_EN
VALID_LOCALES = frozenset({LOCALE_ZH_TW, LOCALE_EN})
PREFS_ENV = "LOOPFLOW_PREFS_PATH"
PREFS_FILENAME = "preferences.json"


def _in_unittest() -> bool:
    return "unittest.case" in sys.modules or "unittest.loader" in sys.modules


def preferences_path() -> Path:
    """AppData\\LoopFlow\\preferences.json；測試可設 LOOPFLOW_PREFS_PATH。"""
    override = str(os.environ.get(PREFS_ENV) or "").strip().strip('"')
    if override:
        return Path(override)
    if _in_unittest():
        # 不讀這台電腦記住的語系，避免測試跟著 AppData 走。
        return Path(os.environ.get("TEMP") or ".") / "loopflow-unittest-prefs-absent.json"
    appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    return Path(appdata) / "LoopFlow" / PREFS_FILENAME


def read_locale() -> Optional[str]:
    path = preferences_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    locale = str(data.get("locale") or "").strip()
    if locale in VALID_LOCALES:
        return locale
    return None


def resolved_locale() -> str:
    """已記住用記住的；未記住時產品預設英文。測試未指定 LOOPFLOW_PREFS_PATH 時仍繁中。"""
    saved = read_locale()
    if saved:
        return saved
    if _in_unittest() and not str(os.environ.get(PREFS_ENV) or "").strip():
        return LOCALE_ZH_TW
    return DEFAULT_LOCALE


def write_locale(locale: str) -> Path:
    if locale not in VALID_LOCALES:
        raise ValueError("未知語系：%s" % locale)
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"locale": locale}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            existing = None
        if isinstance(existing, dict):
            existing["locale"] = locale
            payload = existing
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path
