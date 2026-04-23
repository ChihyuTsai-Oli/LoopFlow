# -*- coding: utf-8 -*-
# Script: LF_Anchor_Frame.py (2D Section Anchor Frame Generator)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: In 2D.3dm, window-select section lines and the corresponding Text Dot (name must match the Clipping Plane),
#           to auto-generate an Anchor Frame rectangle and write Target_CP / Role UserText,
#           serving as the spatial reference for the LF_Tagger_Laser ray probe.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
from System.Drawing import Color

try:
    from _LoopFlow_Config import LAYER_ANCHOR
except Exception:
    LAYER_ANCHOR = "M2D::Anchor_Frame"

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# Core Logic
# ==================================================================
def run_anchor_frame():
    try:
        print(u"\n" + "="*30)
        print(u" LF_Anchor_Frame [Anchor Frame Generator] started...")
        print(u"="*30)

        filter_code  = rs.filter.curve | rs.filter.instance | rs.filter.hatch | rs.filter.textdot
        selected_ids = rs.GetObjects(u"1. Window-select section objects and the Text Dot (name label)", filter_code, preselect=True)

        if not selected_ids:
            print(u" [!] Operation cancelled.")
            return

        text_dots = [obj for obj in selected_ids if rs.ObjectType(obj) == rs.filter.textdot]
        geom_ids  = [obj for obj in selected_ids if rs.ObjectType(obj) != rs.filter.textdot]

        if not text_dots:
            rs.MessageBox(u" Error: The selection contains no Text Dot!\n\nThe script needs a Text Dot to determine the anchor name.", 48, u"Missing Name")
            return
        if len(text_dots) > 1:
            rs.MessageBox(u" Warning: Multiple Text Dots selected!\n\nThe first one found will be used automatically.", 48)

        sec_name = rs.TextDotText(text_dots[0]).strip()
        print(u"  Anchor name extracted: [{}]".format(sec_name))

        OFFSET_VAL = rs.GetReal(u"2. Enter frame offset distance", 50.0, 0.0)
        if OFFSET_VAL is None:
            print(u" [!] User cancelled generation.")
            rs.UnselectAllObjects()
            return

        cp_exists = False
        for obj in sc.doc.Objects:
            if isinstance(obj.Geometry, Rhino.Geometry.ClippingPlaneSurface):
                if rs.ObjectName(obj.Id) and sec_name.upper() in rs.ObjectName(obj.Id).upper():
                    cp_exists = True
                    break

        if not cp_exists:
            res = rs.MessageBox(u" Warning: No 3D Clipping Plane with name containing '{}'  found!\n\nForce-generate this 2D anchor frame anyway?".format(sec_name), 4+32, u"Clipping Plane Not Found")
            if res != 6:
                print(u" [!] User cancelled generation.")
                rs.UnselectAllObjects()
                return
        else:
            print(u"  3D Clipping Plane matched successfully!")

        if not geom_ids:
            rs.MessageBox(u" Error: No valid geometry selected to generate the frame.", 48)
            return

        bbox = rs.BoundingBox(geom_ids)
        if not bbox: return

        min_pt, max_pt = bbox[0], bbox[2]

        p1 = Rhino.Geometry.Point3d(min_pt.X - OFFSET_VAL, min_pt.Y - OFFSET_VAL, min_pt.Z)
        p2 = Rhino.Geometry.Point3d(max_pt.X + OFFSET_VAL, min_pt.Y - OFFSET_VAL, min_pt.Z)
        p3 = Rhino.Geometry.Point3d(max_pt.X + OFFSET_VAL, max_pt.Y + OFFSET_VAL, min_pt.Z)
        p4 = Rhino.Geometry.Point3d(min_pt.X - OFFSET_VAL, max_pt.Y + OFFSET_VAL, min_pt.Z)

        frame_id = rs.AddPolyline([p1, p2, p3, p4, p1])

        if frame_id:
            rs.ObjectName(frame_id, sec_name)

            target_layer = LAYER_ANCHOR
            layer_parts  = target_layer.split("::")
            current_layer_path = ""

            for part in layer_parts:
                current_layer_path = part if not current_layer_path else current_layer_path + "::" + part
                if not rs.IsLayer(current_layer_path):
                    rs.AddLayer(current_layer_path)

            rs.LayerColor(target_layer, Color.FromArgb(155, 140, 205))

            layer_index = sc.doc.Layers.FindByFullPath(target_layer, -1)
            if layer_index >= 0:
                rh_layer = sc.doc.Layers[layer_index]
                rh_layer.PlotWeight = 0.0
                rh_layer.PlotColor  = Color.White
                rh_layer.CommitChanges()

            rs.ObjectLayer(frame_id, target_layer)
            rs.ObjectColorSource(frame_id, 0)
            rs.ObjectPrintWidthSource(frame_id, 0)
            rs.ObjectPrintColorSource(frame_id, 0)

            rs.SetUserText(frame_id, "Role",     "Anchor_Frame")
            rs.SetUserText(frame_id, "Target_CP", sec_name)

            print(u"  Anchor frame generated! (Name: {}, Offset: {})".format(sec_name, OFFSET_VAL))

        rs.UnselectAllObjects()

    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_Anchor_Frame.run_anchor_frame", e))
        rs.MessageBox(u" Anchor_Frame encountered an unexpected error.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    run_anchor_frame()
