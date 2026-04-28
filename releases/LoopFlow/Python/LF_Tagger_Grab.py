# -*- coding: utf-8 -*-
# Script: LF_Tagger_Grab.py (Click-Mode Tag Block Binding Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Debug.py
# Usage: In 2D.3dm, first select the target Tag Block on the Layout,
#           then click the target object (2D block or 3D solid).
#           Door/window/furniture blocks: parses block name into shadow fields (.Auto_*) and sets Source_UUID = NAME_PARSED.
#           Regular 3D solids: reads _12_UUID and writes it directly to Source_UUID.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import re

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# Binding Runner
# ==================================================================
def run_tagger_grab():
    try:
        print(u"\n" + "="*35)
        print(u"LF_Tagger_Grab v3.0 started...")
        print(u"="*35)

        page_view = sc.doc.Views.ActiveView
        if not isinstance(page_view, Rhino.Display.RhinoPageView):
            rs.MessageBox(u"Please run this script in Layout space.", 48, u"Wrong Space")
            return

        tag_id = rs.GetObject(u"1. Select the 2D tag to bind (Tag Block)", rs.filter.instance)
        if not tag_id:
            return

        is_locked = False
        keys = rs.GetUserText(tag_id)
        if keys:
            for k in keys:
                if "LOCK" in k.upper() or u"\u4e0d\u66f4\u65b0" in k:
                    val = rs.GetUserText(tag_id, k)
                    if val and val.strip().upper() == "X":
                        is_locked = True; break
        if is_locked:
            rs.MessageBox(u" This tag is locked (NoUpdate=X)!\n\nTo re-bind, please clear that attribute value first.", 48)
            rs.UnselectAllObjects()
            return

        tag_bname = rs.BlockInstanceName(tag_id).upper()
        if "LASER" in tag_bname:
            rs.MessageBox(u"This tag ({}) is for Laser mode only!".format(rs.BlockInstanceName(tag_id)), 48)
            rs.UnselectAllObjects()
            return

        print(u"2. Click inside the target Detail View...")
        gp = Rhino.Input.Custom.GetPoint()
        gp.SetCommandPrompt(u"2. Click inside the target Detail View")
        gp.Get()
        if gp.CommandResult() != Rhino.Commands.Result.Success:
            rs.UnselectAllObjects(); return

        pt_2d = gp.Point()
        target_detail_id = None
        for detail in page_view.GetDetailViews():
            bbox = detail.Geometry.GetBoundingBox(True)
            if bbox.Min.X <= pt_2d.X <= bbox.Max.X and bbox.Min.Y <= pt_2d.Y <= bbox.Max.Y:
                target_detail_id = detail.Id; break

        if not target_detail_id:
            print(u" [!] Error: click position is outside all Detail Views.")
            rs.UnselectAllObjects(); return

        page_view.SetActiveDetail(target_detail_id)
        sc.doc.Views.Redraw()

        prompt    = u"3. Select target object (3D solid or 2D/3D Block)"
        target_id = rs.GetObject(prompt, rs.filter.instance | rs.filter.curve | rs.filter.hatch | rs.filter.polysurface | rs.filter.surface)

        page_view.SetPageAsActive()
        sc.doc.Views.Redraw()

        if not target_id:
            rs.UnselectAllObjects(); return

        for old_k in [".Auto_DW_ID", ".Auto_Item_Key", ".Auto_Item_Val", ".Auto_Item_Note"]:
            rs.SetUserText(tag_id, old_k, "")

        parsed_from_name = False

        if rs.IsBlockInstance(target_id):
            target_bname = rs.BlockInstanceName(target_id)

            if "TAG_DW" in tag_bname:
                match = re.match(r"^(2D|3D)_(.*)$", target_bname, re.IGNORECASE)
                if match:
                    dw_id = match.group(2).strip()
                    rs.SetUserText(tag_id, "attr_dw_id",  dw_id)
                    rs.SetUserText(tag_id, ".Auto_DW_ID", dw_id)
                    rs.SetUserText(tag_id, "Source_UUID", "NAME_PARSED")
                    parsed_from_name = True
                    print(u" Successfully parsed door/window ID from block name: {}".format(dw_id))

            elif "TAG_ITEM" in tag_bname:
                if "__" in target_bname:
                    prefix_part, note_part = target_bname.split("__", 1)
                    key, val = prefix_part.split("-", 1) if "-" in prefix_part else (prefix_part, "")

                    rs.SetUserText(tag_id, "attr_item_key",  key.strip())
                    rs.SetUserText(tag_id, "attr_item_val",  val.strip())
                    rs.SetUserText(tag_id, "attr_note",      note_part.strip())
                    rs.SetUserText(tag_id, ".Auto_Item_Key", key.strip())
                    rs.SetUserText(tag_id, ".Auto_Item_Val", val.strip())
                    rs.SetUserText(tag_id, ".Auto_Item_Note", note_part.strip())
                    rs.SetUserText(tag_id, "Source_UUID",    "NAME_PARSED")
                    parsed_from_name = True
                    print(u" Successfully parsed furniture from block name: KEY[{}] VAL[{}] NOTE[{}]".format(key, val, note_part))

        if not parsed_from_name:
            target_uuid = rs.GetUserText(target_id, "_12_UUID")
            if not target_uuid or not target_uuid.strip():
                rs.MessageBox(u" Target does not conform to 2D/3D standards and has no UUID.", 48)
                rs.UnselectAllObjects(); return

            clean_uuid = target_uuid.strip()
            rs.SetUserText(tag_id, "Source_UUID", clean_uuid)
            for k in [".Auto_DW_ID", ".Auto_Item_Key", ".Auto_Item_Val", ".Auto_Item_Note"]:
                rs.SetUserText(tag_id, k, "")
            print(u" UUID binding successful! UUID: {}".format(clean_uuid))

        rs.UnselectAllObjects()

    except Exception as e:
        if log_exception: print(log_exception(u"LF_Tagger_Grab.run_tagger_grab", e))
        rs.MessageBox(u" Grab binding encountered an unexpected error.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    run_tagger_grab()
