# -*- coding: utf-8 -*-
"""Nexus Console 步驟選單。Esc／取消不執行後續步驟。"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from loopflow.features.project.console import COMMAND_ID, open_console
from loopflow.foundation import results
from loopflow.foundation.paths import normalize_dictionary_filename
from loopflow.platform.rhino.session import RhinoSession

MenuChoice = Tuple[str, str]
Chooser = Callable[[Sequence[str]], Optional[str]]

MENU_ITEMS: Tuple[Tuple[str, str, str], ...] = (
    ("open_check", "scan", "1  開案檢查"),
    ("sync_type_layers", "scan", "2  從字典同步 Type Layers"),
    ("level_boundary", "scan", "3  登記高程框（封閉曲線）"),
    ("space_boundary", "scan", "4  登記空間框（封閉曲線，須在高程框內）"),
    ("scan_apply_verify", "apply", "5  寫入模型 Metadata"),
    ("scan_apply_verify", "verify", "6  檢核模型 Metadata（不寫入）"),
)
MENU_LABELS: Tuple[str, ...] = tuple(item[2] for item in MENU_ITEMS)


def parse_menu_choice(text: Optional[str]) -> Optional[MenuChoice]:
    if text is None:
        return None
    stripped = str(text).strip()
    if stripped in ("", "0", "取消", "Esc", "ESC"):
        return None
    for step, action, label in MENU_ITEMS:
        if stripped == label or stripped == step:
            return step, action
        number = label.split()[0]
        if stripped == number:
            return step, action
    return None


def _rhino_listbox(labels: Sequence[str]) -> Optional[str]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    return rs.ListBox(
        list(labels),
        "開案檢查已完成。選一個步驟；Esc 取消。",
        "LoopFlow Nexus",
    )


def prompt_nexus_menu(chooser: Optional[Chooser] = None) -> Optional[MenuChoice]:
    picker = chooser or _rhino_listbox
    return parse_menu_choice(picker(MENU_LABELS))


def choose_dictionary_path(opener, root: Optional[Path], default, warn=None):
    """選到 .3dm 同層以外就說明並再問；取消回傳 None。"""
    while True:
        chosen = opener(default)
        if chosen is None:
            return None
        checked = normalize_dictionary_filename(chosen, root=root)
        if checked.ok:
            return chosen
        if callable(warn):
            warn(checked.message)


def _live_ask_dictionary(session):
    """選檔視窗開在 .3dm 所在資料夾。字典改名或搬走時先說明，再讓使用者選。"""
    from loopflow.features.dictionary.sync import dictionary_missing_hint
    from loopflow.foundation.paths import DICTIONARY_FILENAME, resolve_project_folder
    from loopflow.foundation.project_config import remembered_dictionary_filename
    from loopflow.platform.rhino.prompts import ask_open_filename, ask_popup_string, show_message

    def _ask(default):
        folder = None
        root = None
        located = resolve_project_folder(session)
        if located.ok:
            root = located.details["paths"].root.resolve()
            folder = str(root)
        remembered = remembered_dictionary_filename(session)
        if remembered and root is not None and not (root / remembered).is_file():
            show_message(dictionary_missing_hint(remembered))

        def _open(_default):
            try:
                return ask_open_filename(
                    "選這份專案的 Dictionary Excel（須與 .3dm 同資料夾）",
                    "Excel (*.xlsx)|*.xlsx||",
                    folder,
                    _default or DICTIONARY_FILENAME,
                )
            except ImportError:
                return ask_popup_string(
                    "Dictionary 檔名（.3dm 同資料夾內的 .xlsx）",
                    _default or DICTIONARY_FILENAME,
                    "LoopFlow",
                )

        return choose_dictionary_path(_open, root, default, warn=show_message)

    return _ask


def run_nexus_console(
    session: Optional[RhinoSession] = None,
    *,
    interactive: bool = False,
    chooser: Optional[Chooser] = None,
    **kwargs
) -> results.Result:
    """先開案檢查；interactive 時再選步驟。測試可注入 chooser。"""
    extra = dict(kwargs)
    presenter = extra.get("show_message")
    first = open_console(session, step="open_check", **extra)
    if not first.ok:
        from loopflow.platform.rhino.prompts import show_failure_popup

        show_failure_popup(first, presenter)
    if not first.ok or not interactive:
        return first
    picked = prompt_nexus_menu(chooser)
    if picked is None:
        return results.cancelled(
            "dispatch",
            "已完成開案檢查。使用者取消後續步驟。",
            command_id=COMMAND_ID,
            details=first.details,
        )
    step, identity_action = picked
    extra = dict(extra)
    if step == "open_check":
        return first
    if step == "sync_type_layers" and extra.get("ask_prefix") is None:
        from loopflow.platform.rhino.prompts import ask_popup_string

        def _ask_prefix(default):
            return ask_popup_string("請輸入專案名稱（圖層前綴）", default or "", "LoopFlow")

        extra["ask_prefix"] = _ask_prefix
    if step == "sync_type_layers" and extra.get("ask_dictionary") is None:
        try:
            import rhinoscriptsyntax  # type: ignore  # noqa: F401
        except ImportError:
            pass
        else:
            extra["ask_dictionary"] = _live_ask_dictionary(session)
    result = open_console(
        session,
        step=step,
        identity_action=identity_action,
        **extra
    )
    if not result.ok:
        from loopflow.platform.rhino.prompts import show_failure_popup

        show_failure_popup(result, extra.get("show_message"))
    return result
