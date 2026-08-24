# -*- coding: utf-8 -*-
# Script: LF_Extract_CP.py (Clipping Plane Section Line Extractor)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: In 2D.3dm, select the section parent layer; copies Visible / Hatch / Curve objects
#           into the corresponding Extract::* sub-layers, decoupling from the Clipping Plane,
#           so section lines can be edited independently without affecting the original CP display.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
from System.Drawing import Color

try:
    from _LoopFlow_Config import (
        LAYER_EXTRACT_ROOT, LAYER_EXTRACT_VISIBLE, LAYER_EXTRACT_HATCH,
        COLOR_EXTRACT_VISIBLE, COLOR_EXTRACT_HATCH
    )
except Exception:
    LAYER_EXTRACT_ROOT    = "Extract"
    LAYER_EXTRACT_VISIBLE = "Extract::Visible"
    LAYER_EXTRACT_HATCH   = "Extract::Hatch"
    COLOR_EXTRACT_VISIBLE = (134, 160, 174)
    COLOR_EXTRACT_HATCH   = (140, 151, 166)

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# Layer & Color Utilities
# ==================================================================
def reset_to_bylayer(obj_id):
    rs.ObjectColorSource(obj_id, 0)
    rs.ObjectLinetypeSource(obj_id, 0)
    rs.ObjectPrintColorSource(obj_id, 0)
    rs.ObjectPrintWidthSource(obj_id, 0)

def ensure_layer(full_path, layer_color=None):
    if not rs.IsLayer(full_path):
        rs.AddLayer(full_path)
    if layer_color:
        rs.LayerColor(full_path, layer_color)
    rs.LayerLocked(full_path, False)

def rgb_to_hex(r, g, b):
    return "#{:02X}{:02X}{:02X}".format(r, g, b)

def _to_sys_color(c):
    if isinstance(c, (list, tuple)):
        return Color.FromArgb(int(c[0]), int(c[1]), int(c[2]))
    h = str(c).lstrip('#')
    return Color.FromArgb(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))

# ==================================================================
# Core Logic
# ==================================================================
def run_kali_distiller():
    try:
        print(u"\n" + "="*40)
        print(u"LF_Extract_CP started...")
        print(u"="*40)

        target_roots = set()
        for layer in sc.doc.Layers:
            if layer.IsDeleted or not layer.Name or not layer.FullPath:
                continue
            lname     = layer.Name.upper()
            root_name = layer.FullPath.split("::")[0]
            if ("VISIBLE" in lname or "HATCH" in lname or "CURVE" in lname) \
                    and root_name.upper() != LAYER_EXTRACT_ROOT.upper():
                target_roots.add(root_name)

        if not target_roots:
            rs.MessageBox(u"[!] No section layers from Clipping Drawing found!\n(Looking for sub-layers containing Visible, Hatch, Curve)", 48, u"No Results")
            return

        items   = [(name, False) for name in sorted(list(target_roots))]
        results = rs.CheckListBox(items, u"Check '2D Section Layers' to decouple (multiple selection allowed):", u"Decouple CP Link")

        if not results:
            print(u" [!] Extract cancelled.")
            return

        selected_roots = [res[0] for res in results if res[1]]
        if not selected_roots:
            print(u" [!] No layers selected; Extract terminated.")
            return

        color_visible = _to_sys_color(COLOR_EXTRACT_VISIBLE)
        color_hatch   = _to_sys_color(COLOR_EXTRACT_HATCH)

        ensure_layer(LAYER_EXTRACT_ROOT)
        ensure_layer(LAYER_EXTRACT_VISIBLE, color_visible)
        ensure_layer(LAYER_EXTRACT_HATCH,   color_hatch)

        rs.EnableRedraw(False)
        count_vis = count_hat = count_crv = count_layers = 0
        hex_layers_created = set()

        print(u" Starting extraction...")

        for root in selected_roots:
            print(u"  └─ Extracting: {}".format(root))

            for layer in sc.doc.Layers:
                if layer.IsDeleted or not layer.FullPath or not layer.Name:
                    continue
                if layer.FullPath == root or layer.FullPath.startswith(root + "::"):
                    lname = layer.Name.upper()
                    objs  = sc.doc.Objects.FindByLayer(layer)
                    if not objs: continue

                    if "VISIBLE" in lname:
                        for obj in objs:
                            new_id = rs.CopyObject(obj.Id)
                            rs.ObjectLayer(new_id, LAYER_EXTRACT_VISIBLE)
                            reset_to_bylayer(new_id)
                            count_vis += 1

                    elif "HATCH" in lname:
                        for obj in objs:
                            new_id = rs.CopyObject(obj.Id)
                            rs.ObjectLayer(new_id, LAYER_EXTRACT_HATCH)
                            reset_to_bylayer(new_id)
                            count_hat += 1

                    elif "CURVE" in lname:
                        for obj in objs:
                            oc = obj.Attributes.ObjectColor
                            if obj.Attributes.ColorSource == Rhino.DocObjects.ObjectColorSource.ColorFromLayer:
                                oc = layer.Color

                            hex_str    = rgb_to_hex(oc.R, oc.G, oc.B)
                            target_lyr = LAYER_EXTRACT_ROOT + "::Curve_" + hex_str

                            if hex_str not in hex_layers_created:
                                ensure_layer(target_lyr, oc)
                                hex_layers_created.add(hex_str)
                                count_layers += 1

                            new_id = rs.CopyObject(obj.Id)
                            rs.ObjectLayer(new_id, target_lyr)
                            reset_to_bylayer(new_id)
                            count_crv += 1

        rs.EnableRedraw(True)

        total_objs = count_vis + count_hat + count_crv
        print(u" --- Extraction complete ---")
        msg  = u" Extraction complete!\n\n"
        msg += u"Copied {} objects and set ByLayer attributes:\n".format(total_objs)
        msg += u" - Visible (outlines): {}\n".format(count_vis)
        msg += u" - Hatch   (fills):    {}\n".format(count_hat)
        msg += u" - Curve   (details):  {}\n\n".format(count_crv)
        msg += u"Created {} hex-colour layers.".format(count_layers)
        rs.MessageBox(msg, 64, u"Result")

    except Exception as e:
        try:
            rs.EnableRedraw(True)
        except Exception:
            pass
        if log_exception:
            print(log_exception(u"LF_Extract_CP.run_kali_distiller", e))
        rs.MessageBox(u" Extract_CP encountered an unexpected error.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    run_kali_distiller()
