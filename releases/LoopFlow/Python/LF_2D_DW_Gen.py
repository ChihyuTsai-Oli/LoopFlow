# -*- coding: utf-8 -*-
# Script: LF_2D_DW_Gen.py (2D Door/Window Symbol Auto-Generator)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py
# Usage: In 2D.3dm, click points A and B of the door/window opening, then move the mouse to set direction;
#           automatically generates frame, leaf, and swing-arc 2D symbols.
#           Output layers are controlled by LAYER_2D_DW_* in _LoopFlow_Config.py.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino.Geometry as rg
import math
from System.Drawing import Color
import _LoopFlow_Config as _CFG

_L_FRAME     = _CFG.LAYER_2D_DW_FRAME
_L_PANEL     = _CFG.LAYER_2D_DW_PANEL
_L_ORBIT     = _CFG.LAYER_2D_DW_ORBIT
_L_DEFPOINTS = _CFG.LAYER_2D_DEFPOINTS

# ==============================================================================
#  A. Layer Setup & Helpers
# ==============================================================================
def setup_layers():
    """Set up standard layers and attributes"""
    layers = [
        {"name": _L_FRAME,     "color": tuple(_CFG.COLOR_2D_DW_FRAME),   "plot": True},
        {"name": _L_PANEL,     "color": tuple(_CFG.COLOR_2D_DW_PANEL),   "plot": True},
        {"name": _L_ORBIT,     "color": tuple(_CFG.COLOR_2D_DW_ORBIT),   "plot": True},
        {"name": _L_DEFPOINTS, "color": tuple(_CFG.COLOR_2D_DEFPOINTS),  "plot": False},
    ]
    
    for layer in layers:
        if not rs.IsLayer(layer["name"]):
            rs.AddLayer(layer["name"], layer["color"])
        
        layer_obj = sc.doc.Layers.FindName(layer["name"])
        if layer_obj is None:
            continue
        idx = layer_obj.Index
        if idx >= 0:
            sc.doc.Layers[idx].PlotWeight = 0.0 if layer["plot"] else -1.0

def bake_geometry(geo_list, layer_name, is_dashed=False):
    """Bake geometry objects into the Rhino document"""
    ids = []
    if not geo_list: return ids
    
    if not isinstance(geo_list, list):
        geo_list = [geo_list]

    for geo in geo_list:
        obj_id = None
        if isinstance(geo, rg.Point3d): 
            continue
        elif isinstance(geo, list): 
            if len(geo) > 1:
                obj_id = rs.AddPolyline(geo) 
        elif isinstance(geo, rg.Curve): 
            obj_id = sc.doc.Objects.AddCurve(geo)
        
        if obj_id:
            obj = sc.doc.Objects.FindId(obj_id)
            if obj:
                found_layer = sc.doc.Layers.FindName(layer_name)
                if found_layer is not None:
                    obj.Attributes.LayerIndex = found_layer.Index
                    if is_dashed:
                        lt_idx = sc.doc.Linetypes.Find("Hidden", True)
                        if lt_idx < 0: lt_idx = sc.doc.Linetypes.Find("Dashed", True)
                        if lt_idx >= 0:
                            obj.Attributes.LinetypeSource = Rhino.DocObjects.ObjectLinetypeSource.LinetypeFromObject
                            obj.Attributes.LinetypeIndex = lt_idx
                    obj.CommitChanges()
            ids.append(obj_id)
    return ids

# ==============================================================================
#  B. Door Core Logic
# ==============================================================================
def calculate_door_geometry(mode, pt_a, pt_b, thickness, flip, input_val=0.0):
    vec_ab = pt_b - pt_a
    width = vec_ab.Length
    half_thk = thickness / 2.0
    
    x_axis = vec_ab
    x_axis.Unitize()
    z_axis = rg.Vector3d.ZAxis
    y_axis = rg.Vector3d.CrossProduct(z_axis, x_axis)
    if flip: y_axis = -y_axis
        
    plane = rg.Plane(pt_a, x_axis, y_axis)
    xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)

    raw_frames = [] 
    raw_doors = []  
    raw_arcs = []   
    raw_threshold = [] 
    line_closed = True 
    
    y_front = half_thk + 1.0
    y_back = -(half_thk + 1.0)
    stop_depth = 3.0
    rebate_y = y_front - stop_depth 
    jamb_w = 6.0

    if mode == 3: # === Door 03: Concealed Door ===
        jamb_w_03, body_w_03 = 4.0, 3.0
        y_f_03, y_b_03 = -half_thk, half_thk
        y_notch = -half_thk + 1.0
        leaf_len = width - 6.0
        
        raw_frames.append([
            rg.Point3d(0, y_b_03, 0), rg.Point3d(body_w_03, y_b_03, 0),
            rg.Point3d(body_w_03, y_notch, 0), rg.Point3d(jamb_w_03, y_notch, 0),
            rg.Point3d(jamb_w_03, y_f_03, 0), rg.Point3d(0, y_f_03, 0), rg.Point3d(0, y_b_03, 0)
        ])
        raw_frames.append([
            rg.Point3d(width, y_b_03, 0), rg.Point3d(width-body_w_03, y_b_03, 0),
            rg.Point3d(width-body_w_03, y_notch, 0), rg.Point3d(width-jamb_w_03, y_notch, 0),
            rg.Point3d(width-jamb_w_03, y_f_03, 0), rg.Point3d(width, y_f_03, 0), rg.Point3d(width, y_b_03, 0)
        ])
        
        pivot_x = jamb_w_03
        base_leaf = [
            rg.Point3d(pivot_x-4.0, y_f_03, 0), rg.Point3d(pivot_x-4.0, y_f_03+leaf_len, 0),
            rg.Point3d(pivot_x-1.0, y_f_03+leaf_len, 0), rg.Point3d(pivot_x-1.0, y_f_03+leaf_len-1.0, 0),
            rg.Point3d(pivot_x, y_f_03+leaf_len-1.0, 0), rg.Point3d(pivot_x, y_f_03+1.0, 0),
            rg.Point3d(pivot_x-1.0, y_f_03+1.0, 0), rg.Point3d(pivot_x-1.0, y_f_03, 0),
            rg.Point3d(pivot_x-4.0, y_f_03, 0)
        ]
        move_vec = rg.Vector3d(3.0, 4.0, 0)
        raw_doors.append([p + move_vec for p in base_leaf])
        
        arc_c = rg.Point3d(3.0, -half_thk+4.0, 0)
        plane_arc = rg.Plane(arc_c, rg.Vector3d.YAxis, -rg.Vector3d.XAxis)
        raw_arcs.append(rg.Arc(plane_arc, leaf_len, math.radians(-90.0)).ToNurbsCurve())
        
        raw_threshold = [rg.Point3d(0, y_f_03, 0), rg.Point3d(width, y_f_03, 0)]
        line_closed = False

    elif mode == 8: # === Door 08: Shower Door ===
        raw_threshold = [
            rg.Point3d(0, -3.0, 0), rg.Point3d(width, -3.0, 0),
            rg.Point3d(width, 3.0, 0), rg.Point3d(0, 3.0, 0), rg.Point3d(0, -3.0, 0)
        ]
        line_closed = True
        
        gx_start, gx_end = input_val, width
        if gx_end > gx_start:
            raw_frames.append([
                rg.Point3d(gx_start, -1.0, 0), rg.Point3d(gx_end, -1.0, 0),
                rg.Point3d(gx_end, 1.0, 0), rg.Point3d(gx_start, 1.0, 0), rg.Point3d(gx_start, -1.0, 0)
            ])
            
        pivot_x = 5.0
        door_len = input_val
        door_tail, door_tip = -5.0, input_val - 5.0
        raw_doors.append([
            rg.Point3d(pivot_x-1, door_tail, 0), rg.Point3d(pivot_x+1, door_tail, 0),
            rg.Point3d(pivot_x+1, door_tip, 0), rg.Point3d(pivot_x-1, door_tip, 0),
            rg.Point3d(pivot_x-1, door_tail, 0)
        ])
        
        hy = 5.0
        handle = [
            rg.Point3d(pivot_x+1, hy, 0), rg.Point3d(pivot_x+6, hy, 0),
            rg.Point3d(pivot_x+6, hy+45, 0), rg.Point3d(pivot_x+1, hy+45, 0),
            rg.Point3d(pivot_x+1, hy, 0)
        ]
        raw_threshold = [raw_threshold, handle] 
        
        arc_c = rg.Point3d(pivot_x, 0, 0)
        if door_tip > 0.1:
            plane_arc = rg.Plane(arc_c, rg.Vector3d.YAxis, -rg.Vector3d.XAxis)
            raw_arcs.append(rg.Arc(plane_arc, door_tip, math.radians(-90.0)).ToNurbsCurve())

    else: # === Door 01, 02, 04, 05, 06, 07 ===
        raw_frames.append([
            rg.Point3d(0, y_back, 0), rg.Point3d(jamb_w, y_back, 0), rg.Point3d(jamb_w, rebate_y, 0),
            rg.Point3d(3.0, rebate_y, 0), rg.Point3d(3.0, y_front, 0), rg.Point3d(0, y_front, 0), rg.Point3d(0, y_back, 0)
        ])
        raw_frames.append([
            rg.Point3d(width, y_back, 0), rg.Point3d(width-jamb_w, y_back, 0), rg.Point3d(width-jamb_w, rebate_y, 0),
            rg.Point3d(width-3.0, rebate_y, 0), rg.Point3d(width-3.0, y_front, 0), rg.Point3d(width, y_front, 0), rg.Point3d(width, y_back, 0)
        ])
        
        total_leaf_space = width - 6.0
        is_double = mode in [4, 5, 6, 7]
        len_L, len_R = 0, 0
        
        if mode in [6, 7]: # Unequal
            len_L = input_val - 3.0
            if len_L >= total_leaf_space - 5.0: len_L = total_leaf_space - 10.0
            len_R = total_leaf_space - len_L
        elif mode in [4, 5]: # Double Equal
            len_L = total_leaf_space / 2.0
            len_R = len_L
        else: # Single
            len_L = total_leaf_space
            
        # Left Leaf
        raw_doors.append([
            rg.Point3d(3, y_front, 0), rg.Point3d(3, y_front+len_L, 0),
            rg.Point3d(6, y_front+len_L, 0), rg.Point3d(6, y_front, 0), rg.Point3d(3, y_front, 0)
        ])
        # Left Arc (-90)
        plane_L = rg.Plane(rg.Point3d(3, y_front, 0), rg.Vector3d.YAxis, -rg.Vector3d.XAxis)
        raw_arcs.append(rg.Arc(plane_L, len_L, math.radians(-90.0)).ToNurbsCurve())
        
        if is_double:
            p_Rx = width - 3.0
            raw_doors.append([
                rg.Point3d(p_Rx, y_front, 0), rg.Point3d(p_Rx, y_front+len_R, 0),
                rg.Point3d(p_Rx-3, y_front+len_R, 0), rg.Point3d(p_Rx-3, y_front, 0), rg.Point3d(p_Rx, y_front, 0)
            ])
            # Right Arc (90) - [Fix]: Plane Y-axis changed to -X so it sweeps inward
            plane_R = rg.Plane(rg.Point3d(p_Rx, y_front, 0), rg.Vector3d.YAxis, -rg.Vector3d.XAxis)
            raw_arcs.append(rg.Arc(plane_R, len_R, math.radians(90.0)).ToNurbsCurve())

        # Threshold
        if mode in [1, 4, 6]: # With Threshold
            raw_threshold = [
                rg.Point3d(6, y_back, 0), rg.Point3d(width-6, y_back, 0),
                rg.Point3d(width-6, rebate_y, 0), rg.Point3d(6, rebate_y, 0), rg.Point3d(6, y_back, 0)
            ]
            line_closed = True
        else: # No Threshold
            raw_threshold = [rg.Point3d(6, rebate_y, 0), rg.Point3d(width-6, rebate_y, 0)]
            line_closed = False

    # Transform
    def xform_pts(pts):
        if not pts: return []
        o  = plane.Origin
        xa = plane.XAxis
        ya = plane.YAxis
        za = plane.ZAxis
        result = []
        for p in pts:
            result.append(rg.Point3d(
                o.X + xa.X*p.X + ya.X*p.Y + za.X*p.Z,
                o.Y + xa.Y*p.X + ya.Y*p.Y + za.Y*p.Z,
                o.Z + xa.Z*p.X + ya.Z*p.Y + za.Z*p.Z
            ))
        return result

    def xform_crv(crv):
        c = crv.Duplicate()
        c.Transform(xform)
        return c

    fin_frames = [xform_pts(f) for f in raw_frames]
    fin_doors = [xform_pts(d) for d in raw_doors]
    fin_arcs = [xform_crv(a) for a in raw_arcs]
    
    fin_threshold = []
    if mode == 8:
        for poly in raw_threshold: 
            fin_threshold.append(xform_pts(poly))
    else:
        fin_threshold = [xform_pts(raw_threshold)]

    return (fin_frames, fin_doors, fin_threshold, fin_arcs, line_closed)

# ==================================================================
# B-2. Door Direction Preview (Eto GetPoint)
# ==================================================================
class GetDoorDirection(Rhino.Input.Custom.GetPoint):
    def __init__(self, mode, pt_a, pt_b, thickness, input_val):
        super(GetDoorDirection, self).__init__()
        self.mode = mode
        self.pt_a = pt_a
        self.pt_b = pt_b
        self.thickness = thickness
        self.input_val = input_val
        self.flip = False
        self.current_geo = None
        self.vec_wall = pt_b - pt_a
        
    def OnMouseMove(self, e):
        curr_pt = e.Point
        vec_mouse = curr_pt - self.pt_a
        cross_z = (self.vec_wall.X * vec_mouse.Y) - (self.vec_wall.Y * vec_mouse.X)
        new_flip = True if cross_z < 0 else False
        self.flip = new_flip
        self.current_geo = calculate_door_geometry(self.mode, self.pt_a, self.pt_b, self.thickness, self.flip, self.input_val)
        Rhino.Input.Custom.GetPoint.OnMouseMove(self, e)

    def OnDynamicDraw(self, e):
        if not self.current_geo: return
        frames, doors, thresholds, arcs, closed = self.current_geo
        color = Color.Orange
        
        for f in frames: e.Display.DrawPolyline(f + [f[0]], color, 2)
        for d in doors: e.Display.DrawPolyline(d + [d[0]], color, 2)
        for t in thresholds:
            if closed: e.Display.DrawPolyline(t + [t[0]], color, 2)
            else: e.Display.DrawPolyline(t, color, 2)
        for a in arcs: e.Display.DrawCurve(a, color, 1)

# ==============================================================================
#  C. Window Core Logic
# ==============================================================================
def draw_single_window_unit(mode, pt_start, pt_end):
    vec_ab = pt_end - pt_start
    width = vec_ab.Length
    frame_w = 5.0
    depth = 12.0
    half_depth = 6.0
    
    if width < (frame_w * 2 + 1.0): return ([], [])

    x_axis = vec_ab
    x_axis.Unitize()
    z_axis = rg.Vector3d.ZAxis
    y_axis = rg.Vector3d.CrossProduct(z_axis, x_axis)
    
    plane = rg.Plane(pt_start, x_axis, y_axis)
    xform = rg.Transform.PlaneToPlane(rg.Plane.WorldXY, plane)
    y_min, y_max = -half_depth, half_depth
    
    geo_blue = []  # Frames, Sill
    geo_pink = []  # Sash, Glass, Rail
    geo_yellow = []  # Orbit
    
    geo_blue.append([rg.Point3d(0, y_min, 0), rg.Point3d(frame_w, y_min, 0), rg.Point3d(frame_w, y_max, 0), rg.Point3d(0, y_max, 0), rg.Point3d(0, y_min, 0)])
    geo_blue.append([rg.Point3d(width-frame_w, y_min, 0), rg.Point3d(width, y_min, 0), rg.Point3d(width, y_max, 0), rg.Point3d(width-frame_w, y_max, 0), rg.Point3d(width-frame_w, y_min, 0)])
    geo_blue.append([rg.Point3d(frame_w, y_min, 0), rg.Point3d(width-frame_w, y_min, 0), rg.Point3d(width-frame_w, y_max, 0), rg.Point3d(frame_w, y_max, 0), rg.Point3d(frame_w, y_min, 0)])

    if mode == 9: # Sliding
        overlap = 4.0
        mid = width / 2.0
        geo_pink.append([rg.Point3d(frame_w, 2, 0), rg.Point3d(mid+overlap, 2, 0)])
        geo_pink.append([rg.Point3d(width-frame_w, -2, 0), rg.Point3d(mid-overlap, -2, 0)])
        geo_pink.append([rg.Point3d(mid, y_min, 0), rg.Point3d(mid, y_max, 0)])
        
    elif mode == 10: # Fixed
        geo_pink.append([
            rg.Point3d(frame_w, -1, 0), rg.Point3d(width-frame_w, -1, 0),
            rg.Point3d(width-frame_w, 1, 0), rg.Point3d(frame_w, 1, 0), rg.Point3d(frame_w, -1, 0)
        ])
        
    elif mode == 11: # Casement
        geo_pink.append([
            rg.Point3d(frame_w, -1, 0), rg.Point3d(width-frame_w, -1, 0),
            rg.Point3d(width-frame_w, 1, 0), rg.Point3d(frame_w, 1, 0), rg.Point3d(frame_w, -1, 0)
        ])
        pivot = rg.Point3d(frame_w, 0, 0)
        sash_len = width - (frame_w*2)
        rot_ang = math.radians(30.0)
        
        base_rect = [
            rg.Point3d(frame_w, -1, 0), rg.Point3d(width-frame_w, -1, 0),
            rg.Point3d(width-frame_w, 1, 0), rg.Point3d(frame_w, 1, 0), rg.Point3d(frame_w, -1, 0)
        ]
        poly = rg.Polyline(base_rect).ToNurbsCurve()
        poly.Rotate(rot_ang, rg.Vector3d.ZAxis, pivot)
        geo_yellow.append(poly)
        
        p_arc = rg.Plane(pivot, rg.Vector3d.XAxis, rg.Vector3d.YAxis)
        arc = rg.Arc(p_arc, sash_len, rot_ang).ToNurbsCurve()
        geo_yellow.append(arc)

    ids = []
    def do_bake(geos, layer, dashed=False):
        for g in geos:
            final_obj = None
            if isinstance(g, list):
                o  = plane.Origin
                xa = plane.XAxis
                ya = plane.YAxis
                za = plane.ZAxis
                pts = []
                for p in g:
                    pts.append(rg.Point3d(
                        o.X + xa.X*p.X + ya.X*p.Y + za.X*p.Z,
                        o.Y + xa.Y*p.X + ya.Y*p.Y + za.Y*p.Z,
                        o.Z + xa.Z*p.X + ya.Z*p.Y + za.Z*p.Z
                    ))
                if len(pts)>2: final_obj = rs.AddPolyline(pts)
                else: final_obj = rs.AddLine(pts[0], pts[1])
            elif isinstance(g, rg.Curve):
                c = g.Duplicate()
                c.Transform(xform)
                final_obj = sc.doc.Objects.AddCurve(c)
            
            if final_obj:
                rs.ObjectLayer(final_obj, layer)
                if dashed:
                    o = sc.doc.Objects.FindId(final_obj)
                    lt = sc.doc.Linetypes.Find("Hidden", True)
                    if lt < 0: lt = sc.doc.Linetypes.Find("Dashed", True)
                    if lt >= 0:
                        o.Attributes.LinetypeSource = Rhino.DocObjects.ObjectLinetypeSource.LinetypeFromObject
                        o.Attributes.LinetypeIndex = lt
                        o.CommitChanges()
                ids.append(final_obj)

    do_bake(geo_blue,   _L_FRAME)
    do_bake(geo_pink,   _L_PANEL)
    do_bake(geo_yellow, _L_ORBIT, True)
    
    return ids

# ==============================================================================
#  D. Main Logic
# ==============================================================================
def main_generator():
    setup_layers()
    
    options = [
        "Door 01 | Single-leaf, with threshold", 
        "Door 02 | Single-leaf, no threshold",
        "Door 03 | Concealed door",
        "Door 04 | Double-leaf, with threshold",
        "Door 05 | Double-leaf, no threshold",
        "Door 06 | Asymmetric door, with threshold",
        "Door 07 | Asymmetric door, no threshold",
        "Door 08 | Shower door",
        "Window 01 | Sliding window",
        "Window 02 | Fixed window",
        "Window 03 | Casement window"
    ]
    
    selected = rs.ListBox(options, "Select door/window style", "2D DW Generator")
    if not selected: return
    mode = options.index(selected) + 1 

    # --- Common Points ---
    pt_a = rs.GetPoint("Click start point (Point A)")
    if not pt_a: return
    pt_b = rs.GetPoint("Click end point (Point B)", pt_a)
    if not pt_b: return
    
    dist = pt_a.DistanceTo(pt_b)
    if dist < 5.0: return

    # === Branch ===
    if mode <= 8:
        # === DOOR FLOW ===
        if mode == 8: thk = 6.0
        else:
            thk = rs.GetReal("Enter wall thickness", 12.0, 1.0, 100.0)
            if thk is None: return
            
        input_val = 90.0
        if mode in [6, 7]:
            val = rs.GetReal("Enter large-leaf width", 90.0, 10.0, dist)
            if val: input_val = val
        elif mode == 8:
            val = rs.GetReal("Enter shower door width (opening width)", 65.0, 10.0, dist)
            if val: input_val = val
            
        gp = GetDoorDirection(mode, pt_a, pt_b, thk, input_val)
        gp.SetCommandPrompt("Move mouse to set door direction, click to confirm")
        gp.AcceptNothing(True)
        res = gp.Get()
        
        if res == Rhino.Input.GetResult.Point or res == Rhino.Input.GetResult.Nothing:
            final_flip = gp.flip
            frames, doors, thres, arcs, closed = calculate_door_geometry(mode, pt_a, pt_b, thk, final_flip, input_val)
            
            rs.EnableRedraw(False)
            all_ids = []
            
            layer_t = _L_PANEL if mode in [1, 4, 6, 8] else _L_DEFPOINTS
            all_ids.extend(bake_geometry(frames, _L_FRAME))
            all_ids.extend(bake_geometry(doors,  _L_FRAME))
            all_ids.extend(bake_geometry(arcs,   _L_ORBIT, True))
            all_ids.extend(bake_geometry(thres,  layer_t))
            
            if all_ids:
                group = rs.AddGroup()
                rs.AddObjectsToGroup(all_ids, group)
            rs.EnableRedraw(True)
            print("Door created: {}".format(options[mode-1]))

    else:
        # === WINDOW FLOW ===
        prompt_msg = "Total length {:.1f} cm. Enter number of splits (Split Count)".format(dist)
        count = rs.GetInteger(prompt_msg, 1, 1)
        if not count: return
        
        rs.EnableRedraw(False)
        vec_unit = (pt_b - pt_a) / count
        all_ids = []
        
        for i in range(count):
            p1 = pt_a + (vec_unit * i)
            p2 = pt_a + (vec_unit * (i+1))
            new_ids = draw_single_window_unit(mode, p1, p2)
            all_ids.extend(new_ids)
            
        if all_ids:
            group = rs.AddGroup()
            rs.AddObjectsToGroup(all_ids, group)
        rs.EnableRedraw(True)
        print("Window created: {} ({} units)".format(options[mode-1], count))

if __name__ == "__main__":
    main_generator()