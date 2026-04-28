# -*- coding: utf-8 -*-
# Script: LF_Infuser_Part.py (Single-Page Layout Attribute Infuser)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Registry.py, _LF_Debug.py, _LoopFlow_Config.py
# Usage: Run in 2D.3dm; injects attributes into all Tag Blocks on the current Layout page.
#           Reads Objects data from Project_Registry.json, matches by Source_UUID,
#           updates display fields of each tag; broken-link tags are coloured orange and filled with '?'.
#           Can also be called in batch by LF_Infuser_All.py.

# ==================================================================
# Imports
# ==================================================================
import os
import sys
import re
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
from System.Drawing import Color

try:
    from _LoopFlow_Config import (
        INDEX_BLOCKS, HEIGHT_BLOCKS, FINISH_BLOCKS, DW_BLOCKS, ITEM_BLOCKS,
        COLOR_WARNING, COLOR_BROKEN, LAYOUT_NAME_SEPARATOR
    )
except Exception:
    INDEX_BLOCKS         = ["TAG_SECTION_DETAIL", "TAG_ELEV_1", "TAG_ELEV_2", "TAG_ELEV_3", "TAG_ELEV_4"]
    HEIGHT_BLOCKS        = ["TAG_HEIGHT_GRAB", "TAG_HEIGHT_LASER"]
    FINISH_BLOCKS        = ["TAG_FINISH_GRAB", "TAG_FINISH_LASER"]
    DW_BLOCKS            = ["TAG_DW"]
    ITEM_BLOCKS          = ["TAG_ITEM"]
    COLOR_WARNING        = (255, 130, 46)
    COLOR_BROKEN         = (255,  46, 97)
    LAYOUT_NAME_SEPARATOR = "__"

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# Constants: Aggregated Tag Type Lists
# ==================================================================
DATA_BLOCKS = HEIGHT_BLOCKS + FINISH_BLOCKS + DW_BLOCKS + ITEM_BLOCKS

# ==================================================================
# Color Utilities
# ==================================================================
def _to_sys_color(c):
    if isinstance(c, (list, tuple)):
        return Color.FromArgb(255, int(c[0]), int(c[1]), int(c[2]))
    h = str(c).lstrip('#')
    return Color.FromArgb(255, int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

WARNING_COLOR = _to_sys_color(COLOR_WARNING)
BROKEN_COLOR  = _to_sys_color(COLOR_BROKEN)

# ==================================================================
# Environment Helpers
# ==================================================================
def setup_environment():
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        if script_dir not in sys.path: sys.path.append(script_dir)
        return True
    except: return False

def get_project_dir():
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc or not doc.Path: return None
    return os.path.dirname(doc.Path)

# ==================================================================
# Object Attribute Helpers
# ==================================================================
def _apply_warning_color(obj_id, color):
    rh_obj = sc.doc.Objects.FindId(obj_id)
    if rh_obj:
        rh_obj.Attributes.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromObject
        rh_obj.Attributes.ObjectColor  = color
        rh_obj.CommitChanges()

def _clear_warning_color(obj_id):
    rh_obj = sc.doc.Objects.FindId(obj_id)
    if rh_obj:
        rh_obj.Attributes.ColorSource = Rhino.DocObjects.ObjectColorSource.ColorFromLayer
        rh_obj.CommitChanges()

def _get_by_prefix(data, prefix, default="-"):
    for k, v in data.items():
        if k.startswith(prefix):
            return str(v)
    return default

# ==================================================================
# Core Injection Logic (called by LF_Infuser_All)
# ==================================================================
def infuse_layout(layout_objs, db, page_views_all):
    count_success = count_unbound = count_broken = count_locked = 0

    for obj_id in layout_objs:
        block_name = rs.BlockInstanceName(obj_id).upper()

        is_locked = False
        all_keys  = rs.GetUserText(obj_id)
        if all_keys:
            for k in all_keys:
                if "LOCK" in k.upper() or u"\u4e0d\u66f4\u65b0" in k:
                    val = rs.GetUserText(obj_id, k)
                    if val and val.strip().upper() == "X":
                        is_locked = True; break
        if is_locked:
            count_locked += 1; continue

        if block_name in INDEX_BLOCKS:
            target_dv_id = rs.GetUserText(obj_id, ".Target_DV_ID")

            if not target_dv_id or not target_dv_id.strip():
                _apply_warning_color(obj_id, WARNING_COLOR)
                rs.SetUserText(obj_id, "Category", "?")
                rs.SetUserText(obj_id, "REF_ID", "?")
                count_unbound += 1
                continue

            target_dv_id = target_dv_id.strip()
            found_page   = None

            for page in page_views_all:
                for dv in page.GetDetailViews():
                    if str(dv.Id) == target_dv_id:
                        found_page = page; break
                if found_page: break

            if found_page:
                page_name = found_page.PageName
                if LAYOUT_NAME_SEPARATOR in page_name:
                    dwg_no = page_name.split(LAYOUT_NAME_SEPARATOR, 1)[0].strip()
                else:
                    dwg_no = page_name.strip()

                ref_match = re.search(r"\d+\.\d+", dwg_no)
                ref_id    = ref_match.group(0) if ref_match else dwg_no
                cat_match = re.match(r"^[A-Za-z\s]+", dwg_no)
                category  = cat_match.group(0).strip() if cat_match else ""

                _clear_warning_color(obj_id)
                rs.SetUserText(obj_id, "Category", category)
                rs.SetUserText(obj_id, "REF_ID",   ref_id)
                count_success += 1
            else:
                _apply_warning_color(obj_id, BROKEN_COLOR)
                rs.SetUserText(obj_id, "Category", "?")
                rs.SetUserText(obj_id, "REF_ID",   "?")
                count_broken += 1
            continue

        tag_uuid = rs.GetUserText(obj_id, "Source_UUID")
        if not tag_uuid or not tag_uuid.strip():
            if block_name in DATA_BLOCKS:
                _apply_warning_color(obj_id, WARNING_COLOR)
                if block_name in HEIGHT_BLOCKS:
                    for k in ["attr_ch_key", "attr_ch_val", "attr_mat_key", "attr_mat_val", "attr_note"]: rs.SetUserText(obj_id, k, "?")
                elif block_name in FINISH_BLOCKS:
                    for k in ["attr_mat_key", "attr_mat_val", "attr_note"]: rs.SetUserText(obj_id, k, "?")
                elif block_name in DW_BLOCKS:
                    rs.SetUserText(obj_id, "attr_dw_id", "?")
                elif block_name in ITEM_BLOCKS:
                    for k in ["attr_item_key", "attr_item_val", "attr_note"]: rs.SetUserText(obj_id, k, "?")
                count_unbound += 1
            continue
        tag_uuid = tag_uuid.strip()

        if tag_uuid == "NAME_PARSED":
            _clear_warning_color(obj_id)
            if block_name in DW_BLOCKS:
                auto_dw = rs.GetUserText(obj_id, ".Auto_DW_ID")
                if auto_dw is not None: rs.SetUserText(obj_id, "attr_dw_id", auto_dw)
            elif block_name in ITEM_BLOCKS:
                auto_key  = rs.GetUserText(obj_id, ".Auto_Item_Key")
                auto_val  = rs.GetUserText(obj_id, ".Auto_Item_Val")
                auto_note = rs.GetUserText(obj_id, ".Auto_Item_Note")
                if auto_key  is not None: rs.SetUserText(obj_id, "attr_item_key", auto_key)
                if auto_val  is not None: rs.SetUserText(obj_id, "attr_item_val", auto_val)
                if auto_note is not None: rs.SetUserText(obj_id, "attr_note",      auto_note)
            count_success += 1
            continue

        if tag_uuid in db:
            data    = db[tag_uuid]
            _clear_warning_color(obj_id)
            raw_id  = _get_by_prefix(data, "_03_")
            mat_key, mat_val = raw_id.split("-", 1) if "-" in raw_id else (raw_id, "")
            note    = _get_by_prefix(data, "_04_")
            raw_h   = _get_by_prefix(data, "_11_")
            clean_h = raw_h.split('.')[0] if '.' in raw_h and raw_h.split('.')[1] == '0' else raw_h
            h_basis = _get_by_prefix(data, "_10_")

            if block_name in HEIGHT_BLOCKS:
                rs.SetUserText(obj_id, "attr_ch_key",  h_basis)
                rs.SetUserText(obj_id, "attr_ch_val",  clean_h)
                rs.SetUserText(obj_id, "attr_mat_key", mat_key)
                rs.SetUserText(obj_id, "attr_mat_val", mat_val)
                rs.SetUserText(obj_id, "attr_note",    note)
            elif block_name in FINISH_BLOCKS:
                rs.SetUserText(obj_id, "attr_mat_key", mat_key)
                rs.SetUserText(obj_id, "attr_mat_val", mat_val)
                rs.SetUserText(obj_id, "attr_note",    note)
            elif block_name in DW_BLOCKS:
                rs.SetUserText(obj_id, "attr_dw_id", raw_id)
            elif block_name in ITEM_BLOCKS:
                rs.SetUserText(obj_id, "attr_item_key", mat_key)
                rs.SetUserText(obj_id, "attr_item_val", mat_val)
                rs.SetUserText(obj_id, "attr_note",     note)
            count_success += 1
        else:
            print(u"  [Broken] {} UUID=[{}] not in JSON -> marked red".format(block_name, tag_uuid))
            _apply_warning_color(obj_id, BROKEN_COLOR)
            if block_name in HEIGHT_BLOCKS:
                for k in ["attr_ch_key", "attr_ch_val", "attr_mat_key", "attr_mat_val", "attr_note"]: rs.SetUserText(obj_id, k, "?")
            elif block_name in FINISH_BLOCKS:
                for k in ["attr_mat_key", "attr_mat_val", "attr_note"]: rs.SetUserText(obj_id, k, "?")
            elif block_name in DW_BLOCKS:
                rs.SetUserText(obj_id, "attr_dw_id", "?")
            elif block_name in ITEM_BLOCKS:
                for k in ["attr_item_key", "attr_item_val", "attr_note"]: rs.SetUserText(obj_id, k, "?")
            count_broken += 1

    return count_success, count_unbound, count_broken, count_locked

# ==================================================================
# Single-Page Runner
# ==================================================================
def run_infuser_part():
    try:
        print(u"\n" + "="*40)
        print(u"LF_Infuser_Part [v3.1] started...")
        print(u"="*40)

        if not setup_environment(): return
        proj_dir = get_project_dir()
        if not proj_dir: return

        active_view = sc.doc.Views.ActiveView
        if not isinstance(active_view, Rhino.Display.RhinoPageView):
            rs.MessageBox(u"Please run in Layout space!", 48)
            return

        try:
            import importlib
            import _LF_Registry as _REG
            importlib.reload(_REG)
            registry  = _REG.RegistryCenter(proj_dir)
            json_data = registry.get_full_registry()
            db        = json_data.get("Objects", {})
        except Exception as e:
            if log_exception: print(log_exception(u"LF_Infuser_Part.ReadRegistry", e))
            rs.MessageBox(u"Failed to read database.", 16)
            return

        all_objs    = sc.doc.Objects.FindByObjectType(Rhino.DocObjects.ObjectType.InstanceReference)
        layout_objs = [obj.Id for obj in all_objs if obj.Attributes.ViewportId == active_view.MainViewport.Id]
        page_views_all = sc.doc.Views.GetPageViews()

        rs.EnableRedraw(False)
        count_success, count_unbound, count_broken, count_locked = infuse_layout(layout_objs, db, page_views_all)
        rs.EnableRedraw(True)
        sc.doc.Views.Redraw()

        msg = u"Partial Layout Update Complete!\nSuccessfully synced: {} tags".format(count_success)
        if count_locked  > 0: msg += u"\nLocked: {} tags (write-protected)".format(count_locked)
        if count_unbound > 0: msg += u"\nUnbound: {} tags (orange – run Tagger to bind)".format(count_unbound)
        if count_broken  > 0: msg += u"\nBroken: {} tags (red – source lost or JSON not re-pushed)".format(count_broken)

        if count_unbound > 0 or count_broken > 0:
            rs.MessageBox(msg, 48, u"Injection Report")
        elif count_success > 0:
            rs.MessageBox(msg, 64, u"Done")

    except Exception as e:
        try:
            rs.EnableRedraw(True)
        except Exception:
            pass
        if log_exception: print(log_exception(u"LF_Infuser_Part.run_infuser_part", e))
        rs.MessageBox(u"Unexpected error in single-page injection.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    run_infuser_part()
