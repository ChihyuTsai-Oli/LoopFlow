# -*- coding: utf-8 -*-
"""Rhino 提示：指令列 Enter，或彈出視窗。"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple


def ask_command_string(
    message: str,
    default: str = "",
    options: Optional[Sequence[str]] = None,
) -> Optional[str]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    strings = list(options) if options else None
    value = rs.GetString(message, default or None, strings)
    if value is None:
        return None
    return str(value)


def ask_popup_string(
    message: str,
    default: str = "",
    title: str = "LoopFlow",
) -> Optional[str]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    value = rs.StringBox(message, default, title)
    if value is None:
        return None
    return str(value)


def show_message(message: str, title: str = "LoopFlow") -> None:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        print(message)
        return
    rs.MessageBox(message, 64, title)


def pick_curves() -> Optional[Tuple[str, ...]]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    ids = rs.GetObjects("選取封閉曲線，按 Enter 完成", 4, True, True)
    if not ids:
        return None
    return tuple(str(item) for item in ids)
