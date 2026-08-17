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


def ask_open_filename(
    message: str,
    file_filter: str,
    folder: Optional[str] = None,
    filename: Optional[str] = None,
) -> Optional[str]:
    """選檔；沒有 Rhino 時丟 ImportError，取消時回傳 None。"""
    import rhinoscriptsyntax as rs  # type: ignore

    value = rs.OpenFileName(message, file_filter, folder, filename)
    if not value:
        return None
    return str(value)


def ask_popup_choice(
    message: str,
    items: Sequence[str],
    title: str = "LoopFlow",
) -> Optional[str]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    value = rs.ListBox(list(items), message, title)
    if value is None:
        return None
    return str(value)


def format_result_popup(result) -> str:
    """失敗／阻擋時列出訊息與 Dictionary issues 全文。"""
    lines = [getattr(result, "message", "") or ""]
    details = getattr(result, "details", None) or {}
    for issue in details.get("issues") or ():
        text = str(issue).strip()
        if text and text not in lines:
            lines.append(text)
    return "\n".join(item for item in lines if item)


def show_failure_popup(result, presenter=None, title: str = "LoopFlow") -> None:
    if getattr(result, "ok", False) or getattr(result, "status", "") == "cancelled":
        return
    text = format_result_popup(result)
    if callable(presenter):
        presenter(text)
        return
    show_message(text, title)


def show_message(message: str, title: str = "LoopFlow") -> None:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        print(message)
        return
    rs.MessageBox(message, 64, title)


def split_hint_message(message: str, hint: str) -> Tuple[str, Optional[str]]:
    """把提醒句從本文拆出。沒有提醒句時第二個回傳值為 None。"""
    text = (message or "").replace("\r\n", "\n").strip()
    hint_text = (hint or "").strip()
    if not hint_text or hint_text not in text:
        return text, None
    body = text.replace(hint_text, "").strip()
    return body, hint_text


def show_message_with_red_hint(message: str, hint: str, title: str = "LoopFlow") -> None:
    """本文維持預設色；提醒句紅字。Eto 不可用時退回單色 MessageBox。"""
    body, hint_text = split_hint_message(message, hint)
    if hint_text is None:
        show_message(body or message, title)
        return
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        show_message(message, title)
        return

    class _HintDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = drawing.Padding(12)
            self.Resizable = True
            self.ClientSize = drawing.Size(480, 280)
            body_area = forms.TextArea()
            body_area.ReadOnly = True
            body_area.Text = body
            body_area.Wrap = True
            hint_area = forms.TextArea()
            hint_area.ReadOnly = True
            hint_area.Text = hint_text
            hint_area.Wrap = True
            hint_area.BackgroundColor = drawing.Colors.White
            hint_area.TextColor = drawing.Color.FromArgb(196, 32, 32)
            try:
                hint_area.Font = drawing.Font(body_area.Font.FamilyName, 11)
            except Exception:
                pass
            ok = forms.Button()
            ok.Text = "確定"
            ok.Click += self._on_close
            self.DefaultButton = ok
            self.AbortButton = ok
            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(0, 10)
            layout.Add(body_area, xscale=True, yscale=True)
            layout.Add(hint_area, xscale=True)
            try:
                hint_area.Height = 56
            except Exception:
                pass
            layout.AddRow(None, ok)
            self.Content = layout

        def _on_close(self, sender, e) -> None:
            self.Close(True)

    dialog = _HintDialog()
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)


def pick_curves() -> Optional[Tuple[str, ...]]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    ids = rs.GetObjects("選取封閉曲線，按 Enter 完成", 4, True, True)
    if not ids:
        return None
    return tuple(str(item) for item in ids)


def pick_object(message: str = "點選要查看的物件（Enter／Esc 結束）") -> Optional[str]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    object_id = rs.GetObject(message, preselect=True)
    if not object_id:
        return None
    return str(object_id)


def show_readonly_text(message: str, title: str = "LF Data Viewer") -> None:
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        show_message(message, title)
        return

    class _ReadonlyDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.ClientSize = drawing.Size(520, 420)
            self.Padding = drawing.Padding(10)
            self.Resizable = True
            dark_bg = drawing.Color.FromArgb(30, 30, 30)
            dark_text = drawing.Color.FromArgb(220, 220, 220)
            self.BackgroundColor = dark_bg
            text_area = forms.TextArea()
            text_area.ReadOnly = True
            text_area.Text = message
            text_area.Wrap = False
            text_area.Font = drawing.Font("Consolas", 10)
            text_area.BackgroundColor = dark_bg
            text_area.TextColor = dark_text
            layout = forms.DynamicLayout()
            layout.AddRow(text_area)
            self.Content = layout
            close_btn = forms.Button()
            close_btn.Click += self._on_close
            self.AbortButton = close_btn
            self.DefaultButton = close_btn

        def _on_close(self, sender, e) -> None:
            self.Close(True)

    dialog = _ReadonlyDialog()
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
