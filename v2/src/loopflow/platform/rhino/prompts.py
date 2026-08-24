# -*- coding: utf-8 -*-
"""Rhino 提示：指令列 Enter，或彈出視窗。"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Callable, Optional, Sequence, Tuple

from loopflow.foundation.i18n import t


def _ui_font(drawing, size: float = 11.0):
    """開發期繁中介面用微軟正黑體；找不到再退回系統無襯線。"""
    for name in ("微軟正黑體", "Microsoft JhengHei", "Microsoft JhengHei UI"):
        try:
            return drawing.Font(name, size)
        except Exception:
            continue
    return drawing.Font(drawing.Fonts.Sans, size)


# 對齊 Nexus／rs.ListBox 的 Windows 系統鈕。
DIALOG_BUTTON_WIDTH = 75
DIALOG_BUTTON_HEIGHT = 23
LOCALE_CHOICE_BUTTON_HEIGHT = 59
LOCALE_HINT_BUTTON_GAP = 18
# 對齊 Index 綁定：系統預設字、外框 10、區塊間距 5。
DIALOG_PADDING = 10
DIALOG_SPACING = 5
DIALOG_ROW_PAD_X = 8
DIALOG_ROW_PAD_Y = 2
# 約一個中文字寬；選 Sheet 圖名 +2、頁名 -4。
CJK_EM = 16
SHEET_NAME_EXTRA = 2 * CJK_EM
SHEET_PAGE_SHRINK = 4 * CJK_EM
CATALOG_BUTTON_HEIGHT = 28


def _dialog_padding(drawing):
    return drawing.Padding(DIALOG_PADDING)


def _dialog_spacing(drawing):
    return drawing.Size(DIALOG_SPACING, DIALOG_SPACING)


def _dialog_row_padding(drawing):
    return drawing.Padding(
        DIALOG_ROW_PAD_X, DIALOG_ROW_PAD_Y, DIALOG_ROW_PAD_X, DIALOG_ROW_PAD_Y
    )


def _sheet_col_padding(drawing, col: int):
    """圖名欄右側多兩個中文字寬。"""
    extra = SHEET_NAME_EXTRA if col == 2 else 0
    return drawing.Padding(
        DIALOG_ROW_PAD_X,
        DIALOG_ROW_PAD_Y,
        DIALOG_ROW_PAD_X + extra,
        DIALOG_ROW_PAD_Y,
    )


def _lock_control_height(control, drawing, height: int) -> None:
    """鎖定列高，避免 DynamicLayout 把最後一顆鈕拉高。"""
    control.Height = height
    try:
        control.MinimumSize = drawing.Size(0, height)
        control.MaximumSize = drawing.Size(10000, height)
    except Exception:
        pass


def _center_dialog_on_screen(dialog, drawing) -> None:
    """放到螢幕工作區正中。Shown 後再呼叫，避免 ShowModal 依主窗重算。"""
    try:
        import Eto.Forms as forms  # type: ignore
        area = forms.Screen.PrimaryScreen.WorkingArea
    except Exception:
        return
    width = int(getattr(dialog, "Width", 0) or 0)
    height = int(getattr(dialog, "Height", 0) or 0)
    size = getattr(dialog, "Size", None)
    if size is not None:
        width = int(getattr(size, "Width", 0) or width)
        height = int(getattr(size, "Height", 0) or height)
    if width <= 0 or height <= 0:
        return
    x = int(area.X + (area.Width - width) / 2)
    y = int(area.Y + (area.Height - height) / 2)
    dialog.Location = drawing.Point(x, y)


def _apply_dialog_button_size(button, drawing, width: int = DIALOG_BUTTON_WIDTH) -> None:
    size = drawing.Size(width, DIALOG_BUTTON_HEIGHT)
    button.Width = width
    button.Height = DIALOG_BUTTON_HEIGHT
    button.Size = size
    try:
        button.MinimumSize = size
        button.MaximumSize = size
    except Exception:
        pass


def _ok_cancel_buttons(forms, drawing, on_ok, on_cancel):
    """固定大小的 OK／Cancel。"""
    btn_ok = forms.Button()
    btn_ok.Text = "OK"
    _apply_dialog_button_size(btn_ok, drawing)
    btn_ok.Click += on_ok
    btn_cancel = forms.Button()
    btn_cancel.Text = "Cancel"
    _apply_dialog_button_size(btn_cancel, drawing)
    btn_cancel.Click += on_cancel
    return btn_ok, btn_cancel


def _ok_cancel_row(forms, drawing, on_ok, on_cancel):
    """右下：左 OK、右 Cancel，固定系統鈕大小。回傳 (列, OK, Cancel)。"""
    btn_ok, btn_cancel = _ok_cancel_buttons(forms, drawing, on_ok, on_cancel)
    row = forms.DynamicLayout()
    row.DefaultSpacing = drawing.Size(10, 0)
    row.AddRow(None, btn_ok, btn_cancel)
    return row, btn_ok, btn_cancel


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


def dialog_file_name(folder: Optional[str], filename: Optional[str]) -> Optional[str]:
    """選檔對話框要用的檔名。有資料夾時組成完整路徑，避免落到剛存檔的 .3dm 目錄。"""
    name = str(filename or "").strip()
    root = str(folder or "").strip()
    if not name:
        return None
    if root and (len(name) < 2 or name[1] != ":"):
        return str(Path(root) / Path(name).name)
    return name


def winforms_file_filter(file_filter: str) -> str:
    """Rhino `A|*.xlsx||` 轉成 WinForms `A|*.xlsx`。"""
    text = str(file_filter or "").strip()
    while text.endswith("|"):
        text = text[:-1]
    return text or "All files (*.*)|*.*"


def _show_winforms_open(message: str, file_filter: str, folder: str, basename: str) -> Optional[str]:
    """舊式 Windows 選檔，較會遵守 InitialDirectory。"""
    import System.Windows.Forms as winforms  # type: ignore

    dialog = winforms.OpenFileDialog()
    dialog.Title = message
    dialog.Filter = winforms_file_filter(file_filter)
    dialog.RestoreDirectory = True
    dialog.CheckFileExists = True
    try:
        dialog.AutoUpgradeEnabled = False
    except Exception:
        pass
    if folder:
        dialog.InitialDirectory = folder
    if basename:
        dialog.FileName = basename
    result = dialog.ShowDialog()
    if int(result) == int(winforms.DialogResult.OK):
        return str(dialog.FileName or "") or None
    return None


def ask_open_filename(
    message: str,
    file_filter: str,
    folder: Optional[str] = None,
    filename: Optional[str] = None,
) -> Optional[str]:
    """選檔。先把工作目錄切到指定資料夾，避免沿用剛存檔的 .3dm 目錄。取消時回傳 None。"""
    start_folder = str(folder).strip() if folder else ""
    suggested = dialog_file_name(start_folder or None, filename)
    basename = Path(suggested).name if suggested else ""
    previous = None
    try:
        if start_folder and os.path.isdir(start_folder):
            previous = os.getcwd()
            os.chdir(start_folder)
        try:
            return _show_winforms_open(message, file_filter, start_folder, basename)
        except Exception:
            pass
        try:
            import Rhino.UI  # type: ignore

            dialog = Rhino.UI.OpenFileDialog()
            dialog.Title = message
            if file_filter:
                dialog.Filter = file_filter
            if start_folder:
                dialog.InitialDirectory = start_folder
            if suggested:
                dialog.FileName = suggested
            show = getattr(dialog, "ShowOpenDialog", None) or getattr(dialog, "ShowDialog", None)
            if show is None:
                raise AttributeError("OpenFileDialog has no show method")
            if show():
                return str(dialog.FileName or "") or None
            return None
        except Exception:
            import rhinoscriptsyntax as rs  # type: ignore

            value = rs.OpenFileName(message, file_filter, start_folder or None, suggested)
            if not value:
                return None
            return str(value)
    finally:
        if previous:
            try:
                os.chdir(previous)
            except OSError:
                pass


def ask_save_filename(
    message: str,
    file_filter: str,
    folder: Optional[str] = None,
    filename: Optional[str] = None,
) -> Optional[str]:
    """存檔路徑；沒有 Rhino 時丟 ImportError，取消時回傳 None。"""
    import rhinoscriptsyntax as rs  # type: ignore

    value = rs.SaveFileName(message, file_filter, folder, filename)
    if not value:
        return None
    return str(value)


def ask_checklist(
    items: Sequence[str],
    message: str,
    title: str = "LoopFlow",
) -> Optional[Tuple[str, ...]]:
    """多選清單。取消回傳 None；確定但一項都沒勾回傳空 tuple。"""
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    rows = [(str(item), False) for item in items]
    result = rs.CheckListBox(rows, message, title)
    if result is None:
        return None
    return tuple(str(name) for name, checked in result if checked)


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


LOCALE_PROMPT_TITLE = "LoopFlow"
# 定稿仍有「選擇介面語言」；此窗與 ListBox 後備都不顯示該行。
LOCALE_PROMPT_HEADING = "選擇介面語言 / Choose interface language"
LOCALE_PROMPT_HINT = (
    "Document 按鈕右鍵切換語言介面 (LFLanguage)\n"
    "Right-click Document to switch the UI (LFLanguage)"
)
LOCALE_LABEL_ZH = "正體中文"
LOCALE_LABEL_EN = "English"


def _fit_locale_choice_buttons(dialog, btn_en, btn_zh, drawing) -> None:
    """兩顆選擇鈕各佔一半寬、高度固定。"""
    try:
        inner = int(dialog.ClientSize.Width) - (2 * DIALOG_PADDING)
    except Exception:
        inner = 0
    if inner <= 0:
        inner = int(getattr(dialog, "Width", 0) or 0) - (2 * DIALOG_PADDING)
    width = max(80, (inner - DIALOG_SPACING) // 2)
    size = drawing.Size(width, LOCALE_CHOICE_BUTTON_HEIGHT)
    for button in (btn_en, btn_zh):
        button.Width = width
        button.Height = LOCALE_CHOICE_BUTTON_HEIGHT
        button.Size = size
        try:
            button.MinimumSize = size
            button.MaximumSize = size
        except Exception:
            pass


def ask_ui_locale() -> Optional[str]:
    """第一次或切換語系。回傳「正體中文」／「English」；Esc／關閉鈕 None；沒有介面 ImportError。"""
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        import rhinoscriptsyntax as rs  # type: ignore

        value = rs.ListBox(
            [LOCALE_LABEL_EN, LOCALE_LABEL_ZH],
            LOCALE_PROMPT_HINT,
            LOCALE_PROMPT_TITLE,
        )
        if value is None:
            return None
        return str(value)

    class _LocaleDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = LOCALE_PROMPT_TITLE
            self.Padding = _dialog_padding(drawing)
            self.Resizable = False
            self.choice = None
            hint = forms.Label()
            hint.Text = LOCALE_PROMPT_HINT
            hint.Font = _ui_font(drawing, 10)
            self._btn_en = forms.Button()
            self._btn_en.Text = LOCALE_LABEL_EN
            _lock_control_height(self._btn_en, drawing, LOCALE_CHOICE_BUTTON_HEIGHT)
            self._btn_en.Click += self._pick_en
            self._btn_zh = forms.Button()
            self._btn_zh.Text = LOCALE_LABEL_ZH
            _lock_control_height(self._btn_zh, drawing, LOCALE_CHOICE_BUTTON_HEIGHT)
            self._btn_zh.Click += self._pick_zh
            row = forms.TableLayout()
            row.Spacing = drawing.Size(DIALOG_SPACING, 0)
            table_row = forms.TableRow()
            table_row.ScaleHeight = False
            table_row.Cells.Add(forms.TableCell(self._btn_en, True))
            table_row.Cells.Add(forms.TableCell(self._btn_zh, True))
            row.Rows.Add(table_row)
            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(DIALOG_SPACING, LOCALE_HINT_BUTTON_GAP)
            layout.AddRow(hint)
            layout.AddRow(row)
            self.Content = layout
            self.DefaultButton = self._btn_en
            btn_abort = forms.Button()
            btn_abort.Visible = False
            btn_abort.Click += self._on_cancel
            self.AbortButton = btn_abort
            try:
                self.KeyDown += self._on_key_down
            except Exception:
                pass

        def _on_key_down(self, sender, e) -> None:
            try:
                if e.Key == forms.Keys.Escape:
                    e.Handled = True
                    self._on_cancel(sender, e)
            except Exception:
                pass

        def _pick_zh(self, sender, e) -> None:
            self.choice = LOCALE_LABEL_ZH
            self.Close(True)

        def _pick_en(self, sender, e) -> None:
            self.choice = LOCALE_LABEL_EN
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.choice = None
            self.Close(False)

    dialog = _LocaleDialog()

    def _on_shown(sender, e) -> None:
        _fit_locale_choice_buttons(dialog, dialog._btn_en, dialog._btn_zh, drawing)

    try:
        dialog.Shown += _on_shown
    except Exception:
        _fit_locale_choice_buttons(dialog, dialog._btn_en, dialog._btn_zh, drawing)
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    if not dialog.choice:
        return None
    return str(dialog.choice)


def ask_layout_pages_choice(
    items: Sequence[str],
    title: Optional[str] = None,
) -> Optional[Tuple[str, ...]]:
    """加高可捲動反白列，Ctrl／Shift 複選 Layout。不用 GridView（會空白並閃退）。

    取消或確定但沒選＝None。
    """
    if title is None:
        title = t("prompts.003")
    names = [str(item).strip() for item in items if str(item).strip()]
    if not names:
        return None
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        return None

    class _PageSelectDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = _dialog_padding(drawing)
            self.Resizable = True
            self.Width = 320
            self.Height = 600
            self.names = names
            self.selected = set()
            self.last_index = None
            self.row_labels = []
            self._last_click = None
            self._selected_bg = drawing.Color.FromArgb(61, 124, 198)
            self._selected_fg = drawing.Colors.White
            self._normal_bg = drawing.Colors.White
            self._normal_fg = drawing.Colors.Black

            layout = forms.DynamicLayout()
            layout.Spacing = _dialog_spacing(drawing)
            hint = forms.Label()
            hint.Text = t("prompts.011")
            layout.AddRow(hint)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            try:
                scroll.ExpandContentWidth = True
                scroll.ExpandContentHeight = False
            except Exception:
                pass
            table = forms.TableLayout()
            table.Spacing = drawing.Size(0, 0)
            table.Padding = drawing.Padding(0, 2, 0, 2)
            for index, name in enumerate(self.names):
                table.Rows.Add(self._make_data_row(index, name))
            spacer = forms.TableRow()
            spacer.ScaleHeight = True
            table.Rows.Add(spacer)
            scroll.Content = table
            layout.Add(scroll, True, True)

            btn_layout, btn_ok, btn_cancel = _ok_cancel_row(
                forms, drawing, self._on_ok, self._on_cancel
            )
            layout.Add(btn_layout, True, False)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok
            self._refresh_rows()

        def _make_data_row(self, index: int, name: str):
            table_row = forms.TableRow()
            table_row.ScaleHeight = False
            handler = self._make_click(index)
            label = forms.Label()
            label.Text = name
            try:
                label.Wrap = getattr(forms.WrapMode, "None")
            except Exception:
                pass
            panel = forms.Panel()
            panel.Padding = _dialog_row_padding(drawing)
            panel.Content = label
            panel.MouseDown += handler
            label.MouseDown += handler
            self.row_labels.append((panel, label))
            table_row.Cells.Add(forms.TableCell(panel, True))
            return table_row

        def _refresh_rows(self) -> None:
            for index, (panel, label) in enumerate(self.row_labels):
                selected = index in self.selected
                bg = self._selected_bg if selected else self._normal_bg
                fg = self._selected_fg if selected else self._normal_fg
                panel.BackgroundColor = bg
                label.BackgroundColor = bg
                label.TextColor = fg

        def _make_click(self, index: int):
            def _on_click(sender, e) -> None:
                now = time.monotonic()
                last = self._last_click
                if last is not None and last[0] == index and (now - last[1]) < 0.08:
                    return
                self._last_click = (index, now)
                shift, ctrl = _mouse_modifiers(e)
                if shift and self.last_index is not None:
                    start = min(self.last_index, index)
                    end = max(self.last_index, index)
                    if ctrl:
                        for item in range(start, end + 1):
                            self.selected.add(item)
                    else:
                        self.selected = set(range(start, end + 1))
                    self.last_index = index
                elif ctrl:
                    if index in self.selected:
                        self.selected.discard(index)
                    else:
                        self.selected.add(index)
                    self.last_index = index
                else:
                    self.selected = {index}
                    self.last_index = index
                self._refresh_rows()

            return _on_click

        def _chosen_names(self):
            return tuple(
                self.names[index]
                for index in sorted(self.selected)
                if 0 <= index < len(self.names)
            )

        def _on_ok(self, sender, e) -> None:
            if not self.selected:
                self.Close(False)
                return
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.Close(False)

    dialog = _PageSelectDialog()

    def _on_shown(sender, e) -> None:
        _center_dialog_on_screen(dialog, drawing)

    try:
        dialog.Shown += _on_shown
    except Exception:
        _center_dialog_on_screen(dialog, drawing)
    result = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    if result:
        chosen = dialog._chosen_names()
        if chosen:
            return chosen
    return None


def ask_integer(
    message: str,
    default: int = 1,
    minimum: int = 1,
    maximum: int = 100,
) -> Optional[int]:
    """指令列整數。取消回傳 None。"""
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    value = rs.GetInteger(message, int(default), int(minimum), int(maximum))
    if value is None:
        return None
    return int(value)


def _restore_page_view(original_view) -> None:
    if original_view is None:
        return
    try:
        import Rhino  # type: ignore
        import rhinoscriptsyntax as rs  # type: ignore
        import scriptcontext as sc  # type: ignore
    except ImportError:
        return
    try:
        sc.doc.Views.ActiveView = original_view
        if isinstance(original_view, Rhino.Display.RhinoPageView):
            original_view.SetPageAsActive()
        rs.UnselectAllObjects()
        sc.doc.Views.Redraw()
    except Exception:
        pass


def ask_layout_detail_choice(
    items: Sequence[dict],
    on_select=None,
    title: Optional[str] = None,
) -> Optional[dict]:
    """可搜尋的 Layout Detail 清單；選取變更時可 zoom。取消回傳 None。"""
    if title is None:
        title = t("prompts.004")
    if not items:
        return None
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
        import scriptcontext as sc  # type: ignore
    except ImportError:
        return None

    original_view = sc.doc.Views.ActiveView

    class _DetailSelectDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = _dialog_padding(drawing)
            self.Resizable = True
            self.Width = 450
            self.Height = 500
            self.selected_item = None
            self.all_data = list(items)
            self.filtered_data = list(items)

            layout = forms.DynamicLayout()
            layout.Spacing = _dialog_spacing(drawing)

            self.search_box = forms.TextBox()
            self.search_box.PlaceholderText = t("prompts.012")
            self.search_box.TextChanged += self._on_search_changed
            layout.AddRow(self.search_box)

            self.listbox = forms.ListBox()
            self.listbox.Height = 350
            self._update_listbox()
            self.listbox.SelectedIndexChanged += self._on_selection_changed
            self.listbox.MouseDoubleClick += self._on_ok
            layout.AddRow(self.listbox)
            layout.Add(None)

            btn_layout, btn_ok, btn_cancel = _ok_cancel_row(
                forms, drawing, self._on_ok, self._on_cancel
            )
            layout.AddRow(btn_layout)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok

        def _label(self, item: dict) -> str:
            return str(item.get("label") or "")

        def _update_listbox(self) -> None:
            self.listbox.DataStore = [self._label(item) for item in self.filtered_data]

        def _on_search_changed(self, sender, e) -> None:
            term = (self.search_box.Text or "").casefold()
            if not term:
                self.filtered_data = list(self.all_data)
            else:
                self.filtered_data = [
                    item
                    for item in self.all_data
                    if term in str(item.get("layout") or "").casefold()
                    or term in str(item.get("dv_name") or "").casefold()
                    or term in self._label(item).casefold()
                ]
            self._update_listbox()

        def _on_selection_changed(self, sender, e) -> None:
            idx = self.listbox.SelectedIndex
            if idx < 0 or idx >= len(self.filtered_data):
                return
            item = self.filtered_data[idx]
            if callable(on_select):
                on_select(item)

        def _on_ok(self, sender, e) -> None:
            idx = self.listbox.SelectedIndex
            if idx < 0 or idx >= len(self.filtered_data):
                show_message(t("prompts.022"), title)
                return
            self.selected_item = self.filtered_data[idx]
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            _restore_page_view(original_view)
            self.Close(False)

    dialog = _DetailSelectDialog()
    result = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
    _restore_page_view(original_view)
    if result and dialog.selected_item:
        return dialog.selected_item
    return None


def ask_confirm_list(
    lines: Sequence[str],
    title: str = "LoopFlow",
) -> bool:
    """把核對清單完整列出，使用者按 OK 才回 True。無 Eto 時回 False，不寫入。"""
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        return False

    class _ConfirmListDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = _dialog_padding(drawing)
            self.Resizable = True
            self.Width = 510
            self.Height = 560

            layout = forms.DynamicLayout()
            layout.Spacing = _dialog_spacing(drawing)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            scroll.Height = 430
            inner = forms.DynamicLayout()
            inner.Padding = _dialog_row_padding(drawing)
            inner.Spacing = drawing.Size(0, DIALOG_ROW_PAD_Y)
            for line in lines:
                label = forms.Label()
                label.Text = str(line)
                inner.AddRow(label)
            inner.Add(None)
            scroll.Content = inner
            layout.Add(scroll, True, True)

            btn_layout, btn_ok, btn_cancel = _ok_cancel_row(
                forms, drawing, self._on_ok, self._on_cancel
            )
            layout.Add(btn_layout, True, False)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok

        def _on_ok(self, sender, e) -> None:
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.Close(False)

    dialog = _ConfirmListDialog()
    return bool(dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow))


def ask_confirm_table(
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    title: str = "LoopFlow",
) -> bool:
    """欄位對齊的核對表，版面比照選取 Sheet。無 Eto 時回 False，不寫入。"""
    captions = [str(item) for item in headers]
    table_rows = [tuple(str(cell) for cell in row) for row in rows]
    if not captions:
        return False
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        return False

    class _ConfirmTableDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = _dialog_padding(drawing)
            self.Resizable = True
            self.Width = 520
            self.Height = 560
            self._header_fg = drawing.Color.FromArgb(90, 90, 90)

            layout = forms.DynamicLayout()
            layout.Spacing = _dialog_spacing(drawing)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            try:
                scroll.ExpandContentWidth = True
                scroll.ExpandContentHeight = False
            except Exception:
                pass
            table = forms.TableLayout()
            table.Spacing = drawing.Size(0, 0)
            table.Padding = drawing.Padding(0, 2, 0, 2)
            table.Rows.Add(self._make_header_row())
            for row in table_rows:
                table.Rows.Add(self._make_data_row(row))
            spacer = forms.TableRow()
            spacer.ScaleHeight = True
            table.Rows.Add(spacer)
            scroll.Content = table
            layout.Add(scroll, True, True)

            btn_layout, btn_ok, btn_cancel = _ok_cancel_row(
                forms, drawing, self._on_ok, self._on_cancel
            )
            layout.Add(btn_layout, True, False)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok

        def _cell_padding(self, col: int):
            return _dialog_row_padding(drawing)

        def _make_header_row(self):
            row = forms.TableRow()
            row.ScaleHeight = False
            for index, caption in enumerate(captions):
                label = forms.Label()
                label.Text = caption
                label.TextColor = self._header_fg
                header_panel = forms.Panel()
                header_panel.Padding = self._cell_padding(index)
                header_panel.Content = label
                row.Cells.Add(forms.TableCell(header_panel, index == 1))
            return row

        def _make_data_row(self, cells: Sequence[str]):
            table_row = forms.TableRow()
            table_row.ScaleHeight = False
            padded = list(cells) + [""] * max(0, len(captions) - len(cells))
            for col, text in enumerate(padded[: len(captions)]):
                label = forms.Label()
                label.Text = text
                try:
                    label.Wrap = getattr(forms.WrapMode, "None")
                except Exception:
                    pass
                panel = forms.Panel()
                panel.Padding = self._cell_padding(col)
                panel.Content = label
                table_row.Cells.Add(forms.TableCell(panel, col == 1))
            return table_row

        def _on_ok(self, sender, e) -> None:
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.Close(False)

    dialog = _ConfirmTableDialog()
    return bool(dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow))


def ask_pick_title_frames(
    names: Sequence[str],
    title: str = "Layout ID",
) -> Tuple[str, ...]:
    """勾選哪些未登錄 Block 是圖框。預設全不勾；取消或全不選回空 tuple。"""
    if not names:
        return ()
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        return ()

    class _PickFramesDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = _dialog_padding(drawing)
            self.Resizable = True
            self.Width = 320
            self.Height = 520
            self.boxes = []

            layout = forms.DynamicLayout()
            layout.Spacing = _dialog_spacing(drawing)
            note = forms.Label()
            note.Text = t("prompts.013")
            layout.AddRow(note)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            scroll.Height = 360
            inner = forms.DynamicLayout()
            inner.Padding = _dialog_row_padding(drawing)
            inner.Spacing = drawing.Size(0, DIALOG_ROW_PAD_Y)
            for name in names:
                box = forms.CheckBox()
                box.Text = str(name)
                box.Checked = False
                inner.AddRow(box)
                self.boxes.append(box)
            inner.Add(None)
            scroll.Content = inner
            layout.AddRow(scroll)
            layout.Add(None)

            btn_layout, btn_ok, btn_cancel = _ok_cancel_row(
                forms, drawing, self._on_ok, self._on_cancel
            )
            layout.AddRow(btn_layout)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok

        def selected_names(self):
            picked = []
            for box in self.boxes:
                if box.Checked:
                    picked.append(str(box.Text or ""))
            return tuple(name for name in picked if name)

        def _on_ok(self, sender, e) -> None:
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.Close(False)

    dialog = _PickFramesDialog()
    accepted = bool(dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow))
    if not accepted:
        return ()
    return dialog.selected_names()


def sheet_picker_cells(item: dict) -> Tuple[str, str, str, str, str]:
    """Sheet 選單列：頁序、圖號、圖名、頁名、sheet_id。"""
    sheet_id = str(item.get("sheet_id") or "")
    page_number = item.get("page_number")
    drawing_no = item.get("drawing_no")
    drawing_name = item.get("drawing_name")
    page_name = item.get("page_name")
    if page_number is None and drawing_no is None and item.get("label"):
        return str(item.get("label") or ""), "", "", "", sheet_id
    return (
        "" if page_number is None else str(page_number),
        str(drawing_no or "—"),
        str(drawing_name or "—"),
        str(page_name or ""),
        sheet_id,
    )


def sheet_picker_selected_ids(
    rows: Sequence[Tuple[str, str, str, str, str]],
    selected_indices: Sequence[int],
) -> Tuple[str, ...]:
    """只回被點到的列，不把同 id 的其他列一併算進去。"""
    picked = []
    seen = set()
    for index in sorted(selected_indices):
        if index < 0 or index >= len(rows):
            continue
        sheet_id = rows[index][4]
        if not sheet_id or sheet_id in seen:
            continue
        seen.add(sheet_id)
        picked.append(sheet_id)
    return tuple(picked)


def sheet_picker_preselected_indices(
    rows: Sequence[Tuple[str, str, str, str, str]],
    selected_ids: Sequence[str],
) -> set:
    """每個 sheet_id 只預選第一次出現的列，複本不連亮。"""
    remaining = []
    seen = set()
    for item in selected_ids:
        sheet_id = str(item or "")
        if not sheet_id or sheet_id in seen:
            continue
        seen.add(sheet_id)
        remaining.append(sheet_id)
    chosen = set()
    leftover = list(remaining)
    for index, row in enumerate(rows):
        sheet_id = row[4]
        if sheet_id and sheet_id in leftover:
            chosen.add(index)
            leftover.remove(sheet_id)
            if not leftover:
                break
    return chosen


def ask_pick_catalog_sheets(
    items: Sequence[dict],
    selected_ids: Sequence[str] = (),
    title: Optional[str] = None,
) -> Optional[Tuple[str, ...]]:
    """以反白多選 Layout。Shift 連選、Ctrl 加選或取消。取消回 None。"""
    if title is None:
        title = t("catalog.051")
    if not items:
        return ()
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        return None

    rows = [sheet_picker_cells(item) for item in items]

    class _PickSheetsDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = _dialog_padding(drawing)
            self.Resizable = True
            self.Width = 560 + SHEET_NAME_EXTRA - SHEET_PAGE_SHRINK
            self.Height = 500
            self.rows = rows
            self.selected = set()
            self.last_index = None
            self.row_labels = []
            self._last_click = None
            self._selected_bg = drawing.Color.FromArgb(61, 124, 198)
            self._selected_fg = drawing.Colors.White
            self._normal_bg = drawing.Colors.White
            self._normal_fg = drawing.Colors.Black
            self._header_fg = drawing.Color.FromArgb(90, 90, 90)

            layout = forms.DynamicLayout()
            layout.Spacing = _dialog_spacing(drawing)
            note = forms.Label()
            note.Text = t("prompts.014")
            layout.AddRow(note)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            try:
                scroll.ExpandContentWidth = True
                scroll.ExpandContentHeight = False
            except Exception:
                pass
            table = forms.TableLayout()
            table.Spacing = drawing.Size(0, 0)
            table.Padding = drawing.Padding(0, 2, 0, 2)
            table.Rows.Add(self._make_header_row())
            for index, row in enumerate(self.rows):
                table.Rows.Add(self._make_data_row(index, row))
            spacer = forms.TableRow()
            spacer.ScaleHeight = True
            table.Rows.Add(spacer)
            scroll.Content = table
            layout.Add(scroll, True, True)

            btn_all = forms.Button()
            btn_all.Text = t("prompts.015")
            btn_all.Height = DIALOG_BUTTON_HEIGHT
            btn_all.Click += self._on_select_all
            btn_clear = forms.Button()
            btn_clear.Text = t("prompts.016")
            btn_clear.Height = DIALOG_BUTTON_HEIGHT
            btn_clear.Click += self._on_clear
            btn_ok, btn_cancel = _ok_cancel_buttons(
                forms, drawing, self._on_ok, self._on_cancel
            )
            bottom = forms.DynamicLayout()
            bottom.DefaultSpacing = drawing.Size(10, 0)
            bottom.AddRow(btn_all, btn_clear, None, btn_ok, btn_cancel)
            layout.Add(bottom, True, False)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok
            self.selected = sheet_picker_preselected_indices(self.rows, selected_ids)
            self._refresh_rows()

        def _make_header_row(self):
            row = forms.TableRow()
            row.ScaleHeight = False
            for index, caption in enumerate((t("prompts.023"), t("catalog.055"), t("catalog.056"), t("prompts.024"))):
                label = forms.Label()
                label.Text = caption
                label.TextColor = self._header_fg
                header_panel = forms.Panel()
                header_panel.Padding = _sheet_col_padding(drawing, index)
                header_panel.Content = label
                row.Cells.Add(forms.TableCell(header_panel, index == 3))
            return row

        def _make_data_row(self, index: int, row: Tuple[str, str, str, str, str]):
            table_row = forms.TableRow()
            table_row.ScaleHeight = False
            labels = []
            handler = self._make_click(index)
            for col, text in enumerate(row[:4]):
                label = forms.Label()
                label.Text = text
                try:
                    label.Wrap = getattr(forms.WrapMode, "None")
                except Exception:
                    pass
                panel = forms.Panel()
                panel.Padding = _sheet_col_padding(drawing, col)
                panel.Content = label
                panel.MouseDown += handler
                label.MouseDown += handler
                labels.append((panel, label))
                table_row.Cells.Add(forms.TableCell(panel, col == 3))
            self.row_labels.append(labels)
            return table_row

        def _refresh_rows(self) -> None:
            for index, cells in enumerate(self.row_labels):
                selected = index in self.selected
                bg = self._selected_bg if selected else self._normal_bg
                fg = self._selected_fg if selected else self._normal_fg
                for panel, label in cells:
                    panel.BackgroundColor = bg
                    label.BackgroundColor = bg
                    label.TextColor = fg

        def _make_click(self, index: int):
            def _on_click(sender, e) -> None:
                now = time.monotonic()
                last = self._last_click
                if last is not None and last[0] == index and (now - last[1]) < 0.08:
                    return
                self._last_click = (index, now)
                shift, ctrl = _mouse_modifiers(e)
                if shift and self.last_index is not None:
                    start = min(self.last_index, index)
                    end = max(self.last_index, index)
                    if ctrl:
                        for item in range(start, end + 1):
                            self.selected.add(item)
                    else:
                        self.selected = set(range(start, end + 1))
                    self.last_index = index
                elif ctrl:
                    if index in self.selected:
                        self.selected.discard(index)
                    else:
                        self.selected.add(index)
                    self.last_index = index
                else:
                    self.selected = {index}
                    self.last_index = index
                self._refresh_rows()

            return _on_click

        def _on_select_all(self, sender, e) -> None:
            self.selected = set(range(len(self.rows)))
            self.last_index = 0 if self.rows else None
            self._refresh_rows()

        def _on_clear(self, sender, e) -> None:
            self.selected = set()
            self.last_index = None
            self._refresh_rows()

        def selected_ids(self):
            return sheet_picker_selected_ids(self.rows, self.selected)

        def _on_ok(self, sender, e) -> None:
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.Close(False)

    dialog = _PickSheetsDialog()
    accepted = bool(dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow))
    if not accepted:
        return None
    return dialog.selected_ids()


def _enum_has_flag(modifiers, *names: str) -> bool:
    """判斷修飾鍵。Python.NET enum 的 `&` 結果不能直接當 bool。"""
    if modifiers is None:
        return False
    text = str(modifiers)
    keys = type(modifiers)
    for name in names:
        flag = getattr(keys, name, None)
        if flag is not None:
            try:
                if (int(modifiers) & int(flag)) != 0:
                    return True
            except Exception:
                try:
                    if int(modifiers & flag) != 0:
                        return True
                except Exception:
                    pass
        if name in text:
            return True
    return False


def _mouse_modifiers(event) -> Tuple[bool, bool]:
    """回傳 (shift, ctrl)。優先讀 Keyboard／WinForms，避免點到文字時吃不到 Ctrl。"""
    shift = False
    ctrl = False
    try:
        import Eto.Forms as forms  # type: ignore

        keyboard = getattr(forms, "Keyboard", None)
        keys = getattr(forms, "Keys", None)
        if keyboard is not None and keys is not None:
            mods = getattr(keyboard, "Modifiers", None)
            shift = _enum_has_flag(mods, "Shift")
            ctrl = _enum_has_flag(mods, "Control", "Application", "Command")
    except Exception:
        pass
    if not (shift and ctrl):
        event_mods = getattr(event, "Modifiers", None)
        shift = shift or _enum_has_flag(event_mods, "Shift")
        ctrl = ctrl or _enum_has_flag(event_mods, "Control", "Application", "Command")
    if not (shift and ctrl):
        try:
            import System.Windows.Forms as winforms  # type: ignore

            km = winforms.Control.ModifierKeys
            shift = shift or _enum_has_flag(km, "Shift")
            ctrl = ctrl or _enum_has_flag(km, "Control")
        except Exception:
            pass
    return bool(shift), bool(ctrl)


def ask_yes_no(message: str, title: str = "LoopFlow") -> bool:
    """是／否詢問。無 Rhino 時回 False，維持零寫入。"""
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return False
    answer = rs.MessageBox(message, 4 | 32, title)
    return answer == 6


def format_result_popup(result) -> str:
    """失敗／阻擋時列出訊息與 Dictionary issues 全文。"""
    message = getattr(result, "message", "") or ""
    blocking = getattr(result, "blocking", None) or ()
    if "missing_series_start" in blocking:
        return message
    lines = [message]
    details = getattr(result, "details", None) or {}
    for issue in details.get("issues") or ():
        text = str(issue).strip()
        if text and text not in lines:
            lines.append(text)
    for item in details.get("skipped") or ():
        if not isinstance(item, dict):
            continue
        text = "%s：%s" % (item.get("page_name") or t("tag_o.032"), item.get("reason") or "")
        if text.strip("：") and text not in lines:
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


# 與 Rhino ObjectType／rs.filter 對齊。第二個 GetObject 參數是 filter，不可傳 True。
FILTER_POINT = 1
FILTER_CURVE = 4
FILTER_SURFACE = 8
FILTER_POLYSURFACE = 16
FILTER_MESH = 32
FILTER_INSTANCE = 4096
FILTER_TEXTDOT = 8192
FILTER_HATCH = 65536
FILTER_SUBD = 262144
FILTER_EXTRUSION = 1073741824
GRAB_BLOCK_FILTER = FILTER_INSTANCE
GRAB_SOURCE_FILTER = (
    FILTER_CURVE
    | FILTER_SURFACE
    | FILTER_POLYSURFACE
    | FILTER_MESH
    | FILTER_INSTANCE
    | FILTER_HATCH
    | FILTER_SUBD
    | FILTER_EXTRUSION
)


def pick_curves() -> Optional[Tuple[str, ...]]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    ids = rs.GetObjects(t("prompts.010"), FILTER_CURVE, True, True)
    if not ids:
        return None
    return tuple(str(item) for item in ids)


def pick_object(message: Optional[str] = None) -> Optional[str]:
    if message is None:
        message = t("prompts.005")
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    object_id = rs.GetObject(message, 0, preselect=True)
    if not object_id:
        return None
    return str(object_id)


def pick_block_instance(
    message: Optional[str] = None,
    *,
    debug_ray_option: bool = False,
) -> Optional[str]:
    if message is None:
        message = t("prompts.006")
    if debug_ray_option:
        try:
            import Rhino  # type: ignore
        except ImportError:
            return None
        getter = Rhino.Input.Custom.GetObject()
        getter.SetCommandPrompt(message)
        getter.GeometryFilter = Rhino.DocObjects.ObjectType.InstanceReference
        getter.SubObjectSelect = False
        try:
            getter.EnablePreSelect(True, True)
        except Exception:
            pass
        _run_getter_with_debug_ray(getter, Rhino)
        if getter.CommandResult() != Rhino.Commands.Result.Success:
            return None
        objref = getter.Object(0)
        if objref is None:
            return None
        return str(objref.ObjectId)
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    object_id = rs.GetObject(message, FILTER_INSTANCE, preselect=True)
    if not object_id:
        return None
    return str(object_id)


def pick_source_through_detail(
    message: str,
    filter_value: int = GRAB_SOURCE_FILTER,
) -> Optional[str]:
    """Layout 點進 Detail 再選來源。Esc／點在 Detail 外不寫入；結束必回紙空間。"""
    try:
        import Rhino  # type: ignore
        import rhinoscriptsyntax as rs  # type: ignore
        import scriptcontext as sc  # type: ignore
    except ImportError:
        return None
    page_view = sc.doc.Views.ActiveView
    if not isinstance(page_view, Rhino.Display.RhinoPageView):
        show_message(t("prompts.017"))
        return None
    page_view.SetPageAsActive()
    sc.doc.Views.Redraw()
    getter = Rhino.Input.Custom.GetPoint()
    getter.SetCommandPrompt(t("prompts.007"))
    getter.Get()
    if getter.CommandResult() != Rhino.Commands.Result.Success:
        return None
    point = getter.Point()
    target_detail_id = None
    for detail in page_view.GetDetailViews():
        box = detail.Geometry.GetBoundingBox(True)
        if box.Min.X <= point.X <= box.Max.X and box.Min.Y <= point.Y <= box.Max.Y:
            target_detail_id = detail.Id
            break
    if target_detail_id is None:
        show_message(t("prompts.018"))
        return None
    object_id = None
    try:
        page_view.SetActiveDetail(target_detail_id)
        sc.doc.Views.Redraw()
        object_id = rs.GetObject(message, filter_value, preselect=False)
    finally:
        page_view.SetPageAsActive()
        sc.doc.Views.Redraw()
    if not object_id:
        return None
    return str(object_id)


DEBUG_RAY_STICKY_KEY = "loopflow.laser.debug_ray"


def debug_ray_sticky():
    """本次 Rhino 工作階段是否開過 Laser DebugRay。沒設過則 None。"""
    try:
        import scriptcontext as sc  # type: ignore
    except ImportError:
        return None
    sticky = getattr(sc, "sticky", None)
    if sticky is None:
        return None
    try:
        if DEBUG_RAY_STICKY_KEY not in sticky:
            return None
        return bool(sticky[DEBUG_RAY_STICKY_KEY])
    except Exception:
        return None


def _debug_ray_initial() -> bool:
    value = debug_ray_sticky()
    return bool(value) if value is not None else False


def _save_debug_ray(opt_debug) -> None:
    try:
        import scriptcontext as sc  # type: ignore

        sc.sticky[DEBUG_RAY_STICKY_KEY] = bool(opt_debug.CurrentValue)
    except Exception:
        return


def _run_getter_with_debug_ray(getter, Rhino):
    """命令列加上 DebugRay=No／Yes，點選項後繼續等選取。"""
    opt_debug = Rhino.Input.Custom.OptionToggle(_debug_ray_initial(), "No", "Yes")
    getter.AddOptionToggle("DebugRay", opt_debug)
    while True:
        get_result = getter.Get()
        if get_result == Rhino.Input.GetResult.Option:
            continue
        break
    _save_debug_ray(opt_debug)
    return getter


def pick_layout_detail_model_point(
    message: Optional[str] = None,
    *,
    debug_ray_option: bool = False,
):
    """Layout 點 Detail，回傳 2D 模型空間座標。Esc／點在 Detail 外為 None。

    Laser 傳 debug_ray_option=True，命令列出現 DebugRay=No／Yes，記住到關 Rhino。
    """
    if message is None:
        message = t("prompts.007")
    try:
        import Rhino  # type: ignore
        import scriptcontext as sc  # type: ignore
    except ImportError:
        return None
    page_view = sc.doc.Views.ActiveView
    if not isinstance(page_view, Rhino.Display.RhinoPageView):
        show_message(t("prompts.019"))
        return None
    page_view.SetPageAsActive()
    sc.doc.Views.Redraw()
    getter = Rhino.Input.Custom.GetPoint()
    getter.SetCommandPrompt(message)
    if debug_ray_option:
        _run_getter_with_debug_ray(getter, Rhino)
    else:
        getter.Get()
    if getter.CommandResult() != Rhino.Commands.Result.Success:
        return None
    point = getter.Point()
    detail_obj = None
    for detail in page_view.GetDetailViews():
        box = detail.Geometry.GetBoundingBox(True)
        if box.Min.X <= point.X <= box.Max.X and box.Min.Y <= point.Y <= box.Max.Y:
            detail_obj = detail
            break
    if detail_obj is None:
        show_message(t("prompts.018"))
        return None
    model_pt = Rhino.Geometry.Point3d(point)
    model_pt.Transform(detail_obj.PageToWorldTransform)
    return (float(model_pt.X), float(model_pt.Y), float(model_pt.Z))


def pick_anchor_selection(
    message: Optional[str] = None,
) -> Optional[Tuple[str, ...]]:
    """2D 模型空間框選。第三參數是 group，不可把 True 當 filter。"""
    if message is None:
        message = t("prompts.008")
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    filter_code = FILTER_CURVE | FILTER_INSTANCE | FILTER_HATCH | FILTER_TEXTDOT
    ids = rs.GetObjects(message, filter_code, preselect=True)
    if not ids:
        return None
    return tuple(str(item) for item in ids)


def pick_catalog_points(
    message: Optional[str] = None,
) -> Optional[Tuple[str, ...]]:
    """只選 Point。第三參數是 group，不可把 True 當 filter。"""
    if message is None:
        message = t("prompts.009")
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    ids = rs.GetObjects(message, FILTER_POINT, preselect=True)
    if not ids:
        return None
    return tuple(str(item) for item in ids)


def ask_real(
    message: str,
    default: float = 50.0,
    minimum: float = 0.0,
) -> Optional[float]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    value = rs.GetReal(message, default, minimum)
    if value is None:
        return None
    return float(value)


def ask_popup_real(
    message: str,
    default: float = 50.0,
    minimum: float = 0.0,
    title: str = "LoopFlow",
) -> Optional[float]:
    """彈窗輸入數字；取消或小於下限回傳 None。"""
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    value = rs.RealBox(message, default, title)
    if value is None:
        return None
    number = float(value)
    if number < minimum:
        show_message(t("prompts.021") % minimum, title)
        return None
    return number


def ask_popup_integer(
    message: str,
    default: int = 1,
    minimum: int = 1,
    maximum: int = 100,
    title: str = "LoopFlow",
) -> Optional[int]:
    """彈窗輸入整數；取消回傳 None。超出範圍會說明並視為取消。"""
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    value = rs.RealBox(message, float(default), title)
    if value is None:
        return None
    number = int(round(float(value)))
    if number < minimum or number > maximum:
        show_message(t("duplicate_layout.011") % (minimum, maximum), title)
        return None
    return number


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


_PANEL_COLORS = {
    "head": (140, 190, 240),
    "dim": (120, 120, 120),
    "text": (220, 220, 220),
    "ok": (0xAA, 0xDC, 0x78),
    "warn": (0xEA, 0x93, 0x28),
    "brok": (0xD8, 0x1C, 0x1C),
}


def show_colored_log_panel(
    lines: Sequence[tuple],
    title: str = "TAG-O ~ Holy Cargo ~~",
    on_select: Optional[Callable[[str, str], None]] = None,
) -> None:
    """1.0 風格深色色碼列表。點選斷連列可跳到該 Tag。無 Eto 時改成純文字訊息框。"""
    try:
        import Eto.Drawing as drawing  # type: ignore
        import Eto.Forms as forms  # type: ignore
        import Rhino  # type: ignore
        import Rhino.UI  # type: ignore
    except ImportError:
        text = "\n".join(str(item[0]) for item in lines)
        show_message(text, title)
        return

    bg = drawing.Color.FromArgb(30, 30, 30)
    try:
        log_font = drawing.Font("Consolas", 10)
    except Exception:
        log_font = _ui_font(drawing, 10)
    ui_font = _ui_font(drawing, 11)
    palette = {
        key: drawing.Color.FromArgb(rgb[0], rgb[1], rgb[2])
        for key, rgb in _PANEL_COLORS.items()
    }

    class _LogPanel(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.ClientSize = drawing.Size(520, 625)
            self.Padding = drawing.Padding(0)
            self.Resizable = True
            self.BackgroundColor = bg

            stack = forms.StackLayout()
            stack.BackgroundColor = bg
            stack.Orientation = forms.Orientation.Vertical
            stack.Padding = drawing.Padding(12)
            stack.Spacing = 1
            self._row_panels = []
            self._selected_index = None
            self._row_bg = bg
            self._selected_bg = drawing.Color.FromArgb(45, 85, 145)
            for index, row in enumerate(lines):
                text = str(row[0]) if row else ""
                color_key = str(row[1]) if len(row) > 1 else "text"
                tag_id = str(row[2]) if len(row) > 2 else ""
                page_name = str(row[3]) if len(row) > 3 else ""
                if color_key == "rule":
                    bar = forms.Panel()
                    bar.BackgroundColor = drawing.Color.FromArgb(90, 90, 90)
                    bar.Height = 1
                    wrap = forms.Panel()
                    wrap.BackgroundColor = bg
                    wrap.Padding = drawing.Padding(4, 6, 4, 6)
                    wrap.Content = bar
                    stack.Items.Add(forms.StackLayoutItem(wrap))
                    self._row_panels.append((wrap, wrap, False))
                    continue
                label = forms.Label()
                label.Text = text
                label.TextColor = palette.get(color_key, palette["text"])
                label.Font = log_font
                label.BackgroundColor = bg
                panel = forms.Panel()
                panel.BackgroundColor = bg
                panel.Padding = drawing.Padding(4, 1, 4, 1)
                panel.Content = label
                clickable = bool(on_select and tag_id)
                if clickable:
                    try:
                        label.Cursor = forms.Cursors.Pointer
                    except Exception:
                        pass

                    def _clicked(
                        sender,
                        e,
                        selected_id=tag_id,
                        selected_page=page_name,
                        selected_index=index,
                    ) -> None:
                        self._highlight_row(selected_index)
                        try:
                            on_select(selected_id, selected_page)
                        except Exception:
                            pass

                    panel.MouseDown += _clicked
                    label.MouseDown += _clicked
                stack.Items.Add(forms.StackLayoutItem(panel))
                self._row_panels.append((panel, label, clickable))

            scroll = forms.Scrollable()
            scroll.BackgroundColor = bg
            scroll.Content = stack
            # 內容變高時出現捲軸，而不是把對話框撐開、捲不動。
            scroll.ExpandContentWidth = True
            scroll.ExpandContentHeight = False

            close_btn = forms.Button()
            close_btn.Text = t("prompts.020")
            close_btn.Font = ui_font
            close_btn.Click += self._on_close

            btn_row = forms.DynamicLayout()
            btn_row.DefaultSpacing = drawing.Size(10, 0)
            btn_row.AddRow(None, close_btn)

            layout = forms.DynamicLayout()
            layout.BackgroundColor = bg
            layout.Padding = drawing.Padding(0, 0, 0, 10)
            layout.Spacing = drawing.Size(0, 8)
            layout.Add(scroll, True, True)
            layout.Add(btn_row, True, False)

            self.Content = layout
            self.AbortButton = close_btn
            self.DefaultButton = close_btn

        def _highlight_row(self, selected_index: int) -> None:
            self._selected_index = selected_index
            for index, (panel, label, clickable) in enumerate(self._row_panels):
                color = (
                    self._selected_bg
                    if clickable and index == selected_index
                    else self._row_bg
                )
                panel.BackgroundColor = color
                label.BackgroundColor = color

        def _on_close(self, sender, e) -> None:
            self.Close(True)

    dialog = _LogPanel()
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)
