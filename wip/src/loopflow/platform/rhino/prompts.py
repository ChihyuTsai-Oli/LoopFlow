# -*- coding: utf-8 -*-
"""Rhino 提示：指令列 Enter，或彈出視窗。"""
from __future__ import annotations

import time
from typing import Optional, Sequence, Tuple


def _ui_font(drawing, size: float = 11.0):
    """開發期繁中介面用微軟正黑體；找不到再退回系統無襯線。"""
    for name in ("微軟正黑體", "Microsoft JhengHei", "Microsoft JhengHei UI"):
        try:
            return drawing.Font(name, size)
        except Exception:
            continue
    return drawing.Font(drawing.Fonts.Sans, size)


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
    title: str = "Index 綁定",
) -> Optional[dict]:
    """可搜尋的 Layout Detail 清單；選取變更時可 zoom。取消回傳 None。"""
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
            self.Padding = drawing.Padding(10)
            self.Resizable = True
            self.Width = 450
            self.Height = 500
            self.selected_item = None
            self.all_data = list(items)
            self.filtered_data = list(items)

            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(5, 5)

            self.search_box = forms.TextBox()
            self.search_box.PlaceholderText = "輸入圖名或圖號搜尋"
            self.search_box.TextChanged += self._on_search_changed
            layout.AddRow(self.search_box)

            self.listbox = forms.ListBox()
            self.listbox.Height = 350
            self._update_listbox()
            self.listbox.SelectedIndexChanged += self._on_selection_changed
            self.listbox.MouseDoubleClick += self._on_ok
            layout.AddRow(self.listbox)
            layout.Add(None)

            btn_ok = forms.Button()
            btn_ok.Text = "綁定（Enter）"
            btn_ok.Click += self._on_ok
            btn_cancel = forms.Button()
            btn_cancel.Text = "取消（Esc）"
            btn_cancel.Click += self._on_cancel
            btn_layout = forms.DynamicLayout()
            btn_layout.DefaultSpacing = drawing.Size(10, 0)
            btn_layout.AddRow(None, btn_cancel, btn_ok)
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
                show_message("請先選一個 Detail。", title)
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
    ok_text: str = "確認寫入",
    cancel_text: str = "取消（Esc）",
) -> bool:
    """把核對清單完整列出，使用者按確認才回 True。無 Eto 時回 False，不寫入。"""
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
            self.Padding = drawing.Padding(12)
            self.Resizable = True
            self.Width = 760
            self.Height = 560
            font = _ui_font(drawing, 10)

            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(8, 8)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            scroll.Height = 430
            inner = forms.DynamicLayout()
            inner.Padding = drawing.Padding(10, 8, 10, 8)
            inner.Spacing = drawing.Size(0, 4)
            for line in lines:
                label = forms.Label()
                label.Text = str(line)
                label.Font = font
                inner.AddRow(label)
            inner.Add(None)
            scroll.Content = inner
            layout.AddRow(scroll)
            layout.Add(None)

            btn_ok = forms.Button()
            btn_ok.Text = ok_text
            btn_ok.Click += self._on_ok
            btn_cancel = forms.Button()
            btn_cancel.Text = cancel_text
            btn_cancel.Click += self._on_cancel
            btn_layout = forms.DynamicLayout()
            btn_layout.DefaultSpacing = drawing.Size(10, 0)
            btn_layout.AddRow(None, btn_cancel, btn_ok)
            layout.AddRow(btn_layout)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok

        def _on_ok(self, sender, e) -> None:
            self.Close(True)

        def _on_cancel(self, sender, e) -> None:
            self.Close(False)

    dialog = _ConfirmListDialog()
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
            self.Padding = drawing.Padding(10)
            self.Resizable = True
            self.Width = 480
            self.Height = 520
            self.boxes = []
            font = _ui_font(drawing, 11)

            layout = forms.DynamicLayout()
            layout.Spacing = drawing.Size(6, 6)
            note = forms.Label()
            note.Text = (
                "這些圖塊還沒登錄為圖框。請勾選真正的圖框；"
                "沒勾選的會略過，不會寫入圖號。"
            )
            note.Font = font
            layout.AddRow(note)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            scroll.Height = 360
            inner = forms.DynamicLayout()
            inner.Padding = drawing.Padding(6, 4, 6, 4)
            inner.Spacing = drawing.Size(0, 6)
            for name in names:
                box = forms.CheckBox()
                box.Text = str(name)
                box.Checked = False
                box.Font = font
                inner.AddRow(box)
                self.boxes.append(box)
            inner.Add(None)
            scroll.Content = inner
            layout.AddRow(scroll)
            layout.Add(None)

            btn_ok = forms.Button()
            btn_ok.Text = "登錄勾選項目"
            btn_ok.Click += self._on_ok
            btn_skip = forms.Button()
            btn_skip.Text = "都不登錄"
            btn_skip.Click += self._on_cancel
            btn_layout = forms.DynamicLayout()
            btn_layout.DefaultSpacing = drawing.Size(10, 0)
            btn_layout.AddRow(None, btn_skip, btn_ok)
            layout.AddRow(btn_layout)

            self.Content = layout
            self.AbortButton = btn_skip
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


def ask_pick_catalog_sheets(
    items: Sequence[dict],
    selected_ids: Sequence[str] = (),
    title: str = "選取 Sheet",
) -> Optional[Tuple[str, ...]]:
    """以反白多選 Sheet。Shift 連選、Ctrl 加選或取消。取消回 None。"""
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
    preselected = {str(item) for item in selected_ids if item}

    class _PickSheetsDialog(forms.Dialog[bool]):
        def __init__(self) -> None:
            super().__init__()
            self.Title = title
            self.Padding = drawing.Padding(10)
            self.Resizable = True
            self.Width = 780
            self.Height = 560
            self.font = _ui_font(drawing, 11)
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
            layout.Spacing = drawing.Size(6, 6)
            note = forms.Label()
            note.Text = (
                "Shift 連選、Ctrl 加選或取消選取。選取列會反白。"
                "未選的不納入；新增頁不會自動加入既有目錄。"
            )
            note.Font = self.font
            layout.AddRow(note)

            scroll = forms.Scrollable()
            scroll.Border = forms.BorderType.Line
            scroll.Height = 380
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
            layout.AddRow(scroll)

            btn_all = forms.Button()
            btn_all.Text = "全選"
            btn_all.Click += self._on_select_all
            btn_clear = forms.Button()
            btn_clear.Text = "清除選取"
            btn_clear.Click += self._on_clear
            extra = forms.DynamicLayout()
            extra.DefaultSpacing = drawing.Size(10, 0)
            extra.AddRow(btn_all, btn_clear, None)
            layout.AddRow(extra)

            btn_ok = forms.Button()
            btn_ok.Text = "採用選取項目"
            btn_ok.Click += self._on_ok
            btn_cancel = forms.Button()
            btn_cancel.Text = "取消（Esc）"
            btn_cancel.Click += self._on_cancel
            btn_layout = forms.DynamicLayout()
            btn_layout.DefaultSpacing = drawing.Size(10, 0)
            btn_layout.AddRow(None, btn_cancel, btn_ok)
            layout.AddRow(btn_layout)

            self.Content = layout
            self.AbortButton = btn_cancel
            self.DefaultButton = btn_ok
            for index, row in enumerate(self.rows):
                if row[4] in preselected:
                    self.selected.add(index)
            self._refresh_rows()

        def _make_header_row(self):
            row = forms.TableRow()
            row.ScaleHeight = False
            for index, caption in enumerate(("頁序", "圖號", "圖名", "頁名")):
                label = forms.Label()
                label.Text = caption
                label.Font = self.font
                label.TextColor = self._header_fg
                header_panel = forms.Panel()
                header_panel.Padding = drawing.Padding(8, 5, 8, 5)
                header_panel.Content = label
                row.Cells.Add(forms.TableCell(header_panel, index >= 2))
            return row

        def _make_data_row(self, index: int, row: Tuple[str, str, str, str, str]):
            table_row = forms.TableRow()
            table_row.ScaleHeight = False
            labels = []
            handler = self._make_click(index)
            for col, text in enumerate(row[:4]):
                label = forms.Label()
                label.Text = text
                label.Font = self.font
                try:
                    label.Wrap = getattr(forms.WrapMode, "None")
                except Exception:
                    pass
                panel = forms.Panel()
                panel.Padding = drawing.Padding(8, 5, 8, 5)
                panel.Content = label
                panel.MouseDown += handler
                label.MouseDown += handler
                labels.append((panel, label))
                table_row.Cells.Add(forms.TableCell(panel, col >= 2))
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
            picked = set()
            for index in self.selected:
                if 0 <= index < len(self.rows) and self.rows[index][4]:
                    picked.add(self.rows[index][4])
            return tuple(row[4] for row in self.rows if row[4] in picked)

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
        text = "%s：%s" % (item.get("page_name") or "（未命名頁）", item.get("reason") or "")
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
    ids = rs.GetObjects("選取封閉曲線，按 Enter 完成", FILTER_CURVE, True, True)
    if not ids:
        return None
    return tuple(str(item) for item in ids)


def pick_object(message: str = "點選要查看的物件（Enter／Esc 結束）") -> Optional[str]:
    try:
        import rhinoscriptsyntax as rs  # type: ignore
    except ImportError:
        return None
    object_id = rs.GetObject(message, 0, preselect=True)
    if not object_id:
        return None
    return str(object_id)


def pick_block_instance(message: str = "選取圖塊（Esc 取消）") -> Optional[str]:
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
        show_message("請在 Layout 執行 Grab。")
        return None
    page_view.SetPageAsActive()
    sc.doc.Views.Redraw()
    getter = Rhino.Input.Custom.GetPoint()
    getter.SetCommandPrompt("在目標 Detail 內點一下（Esc 取消）")
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
        show_message("點擊位置不在任何 Detail 內。")
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


def pick_layout_detail_model_point(
    message: str = "在目標 Detail 內點一下（Esc 取消）",
):
    """Layout 點 Detail，回傳 2D 模型空間座標。Esc／點在 Detail 外為 None。"""
    try:
        import Rhino  # type: ignore
        import scriptcontext as sc  # type: ignore
    except ImportError:
        return None
    page_view = sc.doc.Views.ActiveView
    if not isinstance(page_view, Rhino.Display.RhinoPageView):
        show_message("請在 Layout 執行 Laser。")
        return None
    page_view.SetPageAsActive()
    sc.doc.Views.Redraw()
    getter = Rhino.Input.Custom.GetPoint()
    getter.SetCommandPrompt(message)
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
        show_message("點擊位置不在任何 Detail 內。")
        return None
    model_pt = Rhino.Geometry.Point3d(point)
    model_pt.Transform(detail_obj.PageToWorldTransform)
    return (float(model_pt.X), float(model_pt.Y), float(model_pt.Z))


def pick_anchor_selection(
    message: str = "框選剖面物件與對應的 Text Dot（Esc 取消）",
) -> Optional[Tuple[str, ...]]:
    """2D 模型空間框選。第三參數是 group，不可把 True 當 filter。"""
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
    message: str = "選取目錄定位點（獨立 Point，Esc 取消）",
) -> Optional[Tuple[str, ...]]:
    """只選 Point。第三參數是 group，不可把 True 當 filter。"""
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
