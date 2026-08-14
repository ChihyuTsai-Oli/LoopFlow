# -*- coding: utf-8 -*-
"""Nexus Console 步驟選單。Esc／取消不執行後續步驟。"""
from __future__ import annotations

from typing import Callable, Mapping, Optional, Sequence, Tuple

from loopflow.features.project.console import COMMAND_ID, open_console
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession

MenuChoice = Tuple[str, str]
Chooser = Callable[[Sequence[str]], Optional[str]]

MENU_ITEMS: Tuple[Tuple[str, str, str], ...] = (
    ("open_check", "scan", "1  開案檢查（只看狀態，不寫入）"),
    ("sync_type_layers", "scan", "2  同步 Type Layers"),
    ("level_boundary", "scan", "3  登記樓層框"),
    ("space_boundary", "scan", "4  登記空間框"),
    ("scan_apply_verify", "scan", "5  Scan（不寫入）"),
    ("scan_apply_verify", "apply", "6  Apply（寫入 ID／Type／空間／高程）"),
    ("scan_apply_verify", "verify", "7  Verify（再 Scan，仍不可發布）"),
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
        "開案檢查已完成。選一個步驟；Esc 取消。發布尚未實作。",
        "LoopFlow Nexus",
    )


def prompt_nexus_menu(chooser: Optional[Chooser] = None) -> Optional[MenuChoice]:
    picker = chooser or _rhino_listbox
    return parse_menu_choice(picker(MENU_LABELS))


def run_nexus_console(
    session: Optional[RhinoSession] = None,
    *,
    environ: Optional[Mapping[str, str]] = None,
    interactive: bool = False,
    chooser: Optional[Chooser] = None,
    **kwargs
) -> results.Result:
    """先開案檢查；interactive 時再選步驟。測試可注入 chooser。"""
    first = open_console(session, environ=environ, step="open_check", **kwargs)
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
    extra = dict(kwargs)
    if step == "open_check":
        return first
    if step == "sync_type_layers" and extra.get("ask_prefix") is None:
        from loopflow.platform.rhino.prompts import ask_command_string

        def _ask_prefix(default):
            return ask_command_string("專案名稱（圖層前綴）", default or "M3D")

        extra["ask_prefix"] = _ask_prefix
    return open_console(
        session,
        environ=environ,
        step=step,
        identity_action=identity_action,
        **extra
    )
