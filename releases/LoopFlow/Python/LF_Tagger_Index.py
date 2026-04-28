# -*- coding: utf-8 -*-
# Script: LF_Tagger_Index.py (Section/Elevation Index Tag Dynamic Binding Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: In 2D.3dm, select a TAG_SECTION_DETAIL or TAG_ELEV tag on the Layout;
#           choose the target Detail View from a list; writes its underlying GUID to .Target_DV_ID.
#           LF_Infuser resolves the latest drawing number of the target DV's layout page at runtime,
#           enabling automatic updates after page renaming/reordering without rebinding.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import Rhino.UI
import Eto.Forms as forms
import Eto.Drawing as drawing
import rhinoscriptsyntax as rs
import scriptcontext as sc
import re

try:
    from _LoopFlow_Config import LAYOUT_NAME_SEPARATOR
except Exception:
    LAYOUT_NAME_SEPARATOR = "__"

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# Eto Dialog: Detail View Selector
# ==================================================================
class DVSelectDialog(forms.Dialog[bool]):
    def __init__(self, dv_list, original_view):
        super().__init__()

        self.Title    = u"Section/Elevation Index Lock"
        self.Padding  = drawing.Padding(10)
        self.Resizable = True
        self.Width    = 450
        self.Height   = 500

        self.original_view = original_view
        self.selected_item = None

        layout = forms.DynamicLayout()
        layout.Spacing = drawing.Size(5, 5)

        self.search_box = forms.TextBox()
        self.search_box.PlaceholderText = u"Type drawing name or number to search..."
        self.search_box.TextChanged += self.on_search_changed
        layout.AddRow(self.search_box)

        self.listbox = forms.ListBox()
        self.listbox.Height = 350

        self.all_data      = dv_list
        self.filtered_data = list(self.all_data)
        self.update_listbox()

        self.listbox.SelectedIndexChanged += self.on_selection_changed
        self.listbox.MouseDoubleClick     += self.on_double_click

        layout.AddRow(self.listbox)
        layout.Add(None)

        btn_layout = forms.DynamicLayout()
        btn_layout.DefaultSpacing = drawing.Size(10, 0)

        self.btn_ok = forms.Button()
        self.btn_ok.Text = u"Lock & Bind (Enter)"
        self.btn_ok.Click += self.on_ok_click

        self.btn_cancel = forms.Button()
        self.btn_cancel.Text = u"Cancel (Esc)"
        self.btn_cancel.Click += self.on_cancel_click

        btn_layout.AddRow(None, self.btn_cancel, self.btn_ok)
        layout.AddRow(btn_layout)

        self.Content      = layout
        self.AbortButton  = self.btn_cancel
        self.DefaultButton = self.btn_ok

    def update_listbox(self):
        self.listbox.DataStore = [u"{}    {}".format(d['layout'], d['dv_name']) for d in self.filtered_data]

    def on_search_changed(self, sender, e):
        term = self.search_box.Text.lower()
        self.filtered_data = [d for d in self.all_data if term in d['layout'].lower() or term in d['dv_name'].lower()]
        self.update_listbox()

    def on_selection_changed(self, sender, e):
        idx = self.listbox.SelectedIndex
        if idx < 0: return
        selected  = self.filtered_data[idx]
        page_name = selected['layout']
        dv_id     = selected['dv_id']
        for page in sc.doc.Views.GetPageViews():
            if page.PageName == page_name:
                sc.doc.Views.ActiveView = page
                page.SetPageAsActive()
                rs.UnselectAllObjects()
                rs.SelectObject(dv_id)
                page.MainViewport.ZoomExtentsSelected()
                page.MainViewport.Magnify(0.8, False)
                sc.doc.Views.Redraw()
                break

    def on_double_click(self, sender, e):
        self.on_ok_click(sender, e)

    def on_ok_click(self, sender, e):
        idx = self.listbox.SelectedIndex
        if idx >= 0:
            self.selected_item = self.filtered_data[idx]
            self.Close(True)
        else:
            rs.MessageBox(u"Please select a view first!", 48)

    def on_cancel_click(self, sender, e):
        if self.original_view:
            sc.doc.Views.ActiveView = self.original_view
            rs.UnselectAllObjects()
            sc.doc.Views.Redraw()
        self.Close(False)

# ==================================================================
# Binding Runner
# ==================================================================
def run_tagger_index():
    try:
        print(u"\n" + "="*35)
        print(u"LF_Tagger_Index [v4.1 Dynamic Tracking] started...")
        print(u"="*35)

        active_view = sc.doc.Views.ActiveView
        if not isinstance(active_view, Rhino.Display.RhinoPageView):
            rs.MessageBox(u" Please run in Layout space!", 48, u"Wrong Space")
            return

        tag_id = rs.GetObject(u"1. Select the section/elevation tag (Tag Block) to bind", rs.filter.instance)
        if not tag_id:
            print(u" [!] Cancelled: no tag selected.")
            return

        is_locked = False
        all_keys  = rs.GetUserText(tag_id)
        if all_keys:
            for k in all_keys:
                if "LOCK" in k.upper() or u"\u4e0d\u66f4\u65b0" in k:
                    val = rs.GetUserText(tag_id, k)
                    if val and val.strip().upper() == "X":
                        is_locked = True; break

        if is_locked:
            rs.MessageBox(u" This tag has write-protect lock enabled.\nTo re-bind, please remove the lock first.", 48, u"Lock Protection")
            return

        dv_list      = []
        sorted_pages = sorted(sc.doc.Views.GetPageViews(), key=lambda p: p.PageNumber)
        for page in sorted_pages:
            details = page.GetDetailViews()
            if details:
                for dv in details:
                    dv_list.append({
                        'layout':  page.PageName,
                        'dv_name': dv.Name or u"Unnamed View",
                        'dv_id':   dv.Id
                    })

        if not dv_list:
            rs.MessageBox(u" No Detail Views found in this file for binding.", 48)
            return

        dialog = DVSelectDialog(dv_list, active_view)
        result = dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

        if result and dialog.selected_item:
            selected_layout = dialog.selected_item['layout']
            target_dv_id    = dialog.selected_item['dv_id']

            if LAYOUT_NAME_SEPARATOR in selected_layout:
                dwg_no, dwg_name = selected_layout.split(LAYOUT_NAME_SEPARATOR, 1)
            else:
                dwg_no   = selected_layout
                dwg_name = ""

            dwg_no   = dwg_no.strip()
            dwg_name = dwg_name.strip()

            ref_match = re.search(r"\d+\.\d+", dwg_no)
            ref_id    = ref_match.group(0) if ref_match else dwg_no
            cat_match = re.match(r"^[A-Za-z\s]+", dwg_no)
            category  = cat_match.group(0).strip() if cat_match else ""

            rs.SetUserText(tag_id, "Category",      category)
            rs.SetUserText(tag_id, "REF_ID",        ref_id)
            rs.SetUserText(tag_id, ".Target_DV_ID", str(target_dv_id))

            sc.doc.Views.ActiveView = active_view
            rs.UnselectAllObjects()
            sc.doc.Views.Redraw()

            print(u"   Successfully locked: {} (Category: {}, REF: {})".format(selected_layout, category, ref_id))
            print(u" Hidden link established: {}".format(str(target_dv_id)))
        else:
            print(u" [!] Binding cancelled.")

    except Exception as e:
        if log_exception: print(log_exception(u"LF_Tagger_Index.run_tagger_index", e))
        rs.MessageBox(u" Index binding encountered an unexpected error.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    run_tagger_index()
