# -*- coding: utf-8 -*-
"""LF_Language：記住這台電腦的介面語系。不寫 .3dm。"""
from __future__ import annotations

from typing import Callable, Optional

from loopflow.foundation import locale as locale_store
from loopflow.foundation import results
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Language"
STAGE = "choose_locale"
LOCALE_ZH_TW = locale_store.LOCALE_ZH_TW
LOCALE_EN = locale_store.LOCALE_EN
LABEL_ZH = "正體中文"
LABEL_EN = "English"

AskLocale = Callable[[], Optional[str]]


def _live_ask() -> Optional[str]:
    from loopflow.platform.rhino.prompts import ask_ui_locale

    return ask_ui_locale()


def parse_locale_choice(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    stripped = str(text).strip()
    if stripped in (LOCALE_ZH_TW, LABEL_ZH, "繁中", "zh", "zh_TW", "Traditional Chinese"):
        return LOCALE_ZH_TW
    if stripped in (LOCALE_EN, LABEL_EN, "en-US", "en_US"):
        return LOCALE_EN
    return None


def saved_message(locale: str) -> str:
    if locale == LOCALE_EN:
        return t("locale.saved.en")
    return t("locale.saved.zh")


def ensure_locale(*, ask: Optional[AskLocale] = None) -> Optional[results.Result]:
    """已記住或沒有 Rhino 介面時繼續指令；取消則停止且下次再問。"""
    if locale_store.read_locale():
        return None
    picker = ask or _live_ask
    try:
        choice = picker()
    except ImportError:
        return None
    locale = parse_locale_choice(choice)
    if locale is None:
        return results.cancelled(
            STAGE,
            t("locale.cancelled.first"),
            command_id=COMMAND_ID,
        )
    locale_store.write_locale(locale)
    return None


def run_language(*, ask: Optional[AskLocale] = None) -> results.Result:
    """Document 右鍵／LFLanguage：每次都問，記住後回報。"""
    picker = ask or _live_ask
    try:
        choice = picker()
    except ImportError:
        return results.failed(
            STAGE,
            t("document.006"),
            command_id=COMMAND_ID,
        )
    locale = parse_locale_choice(choice)
    if locale is None:
        return results.cancelled(
            STAGE,
            t("locale.cancelled.switch"),
            command_id=COMMAND_ID,
        )
    path = locale_store.write_locale(locale)
    return results.ok(
        STAGE,
        saved_message(locale),
        command_id=COMMAND_ID,
        details={"locale": locale, "preferences_path": str(path)},
    )
