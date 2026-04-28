# -*- coding: utf-8 -*-
# Script: LF_Data_Viewer.py (Object UserText Read-Only Viewer)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Debug.py
# Usage: Select any Rhino object and run; displays all UserText key-value pairs in a dark Eto window.
#           Read-only – no data is modified. Useful for verifying Tag Block binding status or 3D object attribute writes.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import Rhino.UI
import rhinoscriptsyntax as rs
import Eto.Forms as forms
import Eto.Drawing as drawing
import unicodedata

# ==================================================================
# Eto Dialog: Dark Inspector Window
# ==================================================================
class InspectorDialog(forms.Dialog[bool]):
    def __init__(self, title, message):
        super().__init__()

        self.Title = title
        self.ClientSize = drawing.Size(480, 360)
        self.Padding = drawing.Padding(10)
        self.Resizable = True

        dark_bg = drawing.Color.FromArgb(30, 30, 30)    
        dark_text = drawing.Color.FromArgb(220, 220, 220)
        
        self.BackgroundColor = dark_bg

        self.text_area = forms.TextArea()
        self.text_area.ReadOnly = True
        self.text_area.Text = message
        self.text_area.Wrap = False 
        self.text_area.Font = drawing.Font("Consolas", 10)
        
        self.text_area.BackgroundColor = dark_bg
        self.text_area.TextColor = dark_text

        layout = forms.DynamicLayout()
        layout.AddRow(self.text_area)
        self.Content = layout

        hidden_close_btn = forms.Button()
        hidden_close_btn.Click += self.OnCloseClick
        self.AbortButton = hidden_close_btn   
        self.DefaultButton = hidden_close_btn 

    def OnCloseClick(self, sender, e):
        self.Close(True)

# ==================================================================
# Dialog Launcher
# ==================================================================
def show_dark_message(title, message):
    dialog = InspectorDialog(title, message)
    dialog.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

# ==================================================================
# Text Width Utility (CJK-aware)
# ==================================================================
def get_display_width(text):
    width = 0
    for char in text:
        if unicodedata.east_asian_width(char) in ('W', 'F'):
            width += 2
        else:
            width += 1
    return width

# ==================================================================
# Interactive Query Loop
# ==================================================================
def main():
    print(u"--- LF Data Viewer started ---")
    
    while True:
        obj_id = rs.GetObject(u"Click an object to inspect (press Enter or Esc to exit)", preselect=False)
        
        if not obj_id:
            print(u"Inspection ended.")
            break

        obj_layer = rs.ObjectLayer(obj_id)
        obj_name = rs.ObjectName(obj_id) or u"Unnamed"
        
        if rs.IsBlockInstance(obj_id):
            obj_name = u"Block [{}]".format(rs.BlockInstanceName(obj_id))

        keys = rs.GetUserText(obj_id)

        if not keys:
            empty_msg = u"Layer: {}\nName: {}\n\nThis one's got nothing. Unlike my problems.".format(obj_layer, obj_name)
            show_dark_message("LF Data Viewer", empty_msg)
            continue

        data_lines = []
        data_lines.append(u"Layer: {}".format(obj_layer))
        data_lines.append(u"Name: {}".format(obj_name))
        data_lines.append("-" * 48)

        keys.sort()
        
        max_key_width = max([get_display_width(k) for k in keys] + [20])
        
        for k in keys:
            val = rs.GetUserText(obj_id, k)
            curr_width = get_display_width(k)
            pad_spaces = " " * (max_key_width - curr_width)
            data_lines.append(u"  {}{} : {}".format(k, pad_spaces, val))

        full_message = "\n".join(data_lines)
        show_dark_message("LF Data Viewer", full_message)

if __name__ == "__main__":
    main()
