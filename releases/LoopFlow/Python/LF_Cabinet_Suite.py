# -*- coding: utf-8 -*-
# Script: LF_Cabinet_Suite.py(3D Cabinet Suite: Geometry Generator)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: Select cabinet type via UI (Tall/Low/Wardrobe etc.),
#           auto-generate 3D panel geometry and write the corresponding _CB.* UserText attributes.
#           Run in 3D.3dm.

# ==================================================================
# Imports
# ==================================================================
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext as sc
import Rhino.UI
import Eto.Forms as forms
import Eto.Drawing as drawing
import os
import sys

try:
    from _LoopFlow_Config import LAYER_CABINET_PREFIX, LAYER_CABINET_NAME
except Exception:
    LAYER_CABINET_PREFIX = "04_CB"
    LAYER_CABINET_NAME   = u"\u6ac3\u9ad4"

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

_CABINET_LAYER_ID = LAYER_CABINET_PREFIX

# Environment bridge: ensure Rhino 8 CPython runs correctly
def bridge_rhino_env():
    user_prof = os.environ.get('USERPROFILE')
    if user_prof:
        py3_path = os.path.join(user_prof, r".rhinocode\py39-rh8\site-packages")
        if os.path.exists(py3_path) and py3_path not in sys.path:
            sys.path.append(py3_path)

bridge_rhino_env()

# ==========================================
#   0. Global canonical field names and cleanup definitions
# ==========================================
CB_KEYS = ["_CB.01_Panel_Type", "_CB.02_Length_L", "_CB.03_Width_W", "_CB.04_Thickness_T"]

JUNK_KEYS = [
    "B.01 Panel_Type", "B.02 Length_L", "B.03 Width_W", "B.04 Thickness_T", "A.06 Size_Desc", "R2A_Size",
    "B.01", "B.02", "B.03", "B.04", "B.04 Height_H", "ID", "Part_Name", "Material", 
    "Dim_L", "Dim_W", "Dim_T", "Dim_H", "Revit_Category", "Revit_Workset", "DeviceName", 
    "ElevationRef", "Elevation", "Space_Name", "BOM_DeviceName", "BOM_ElevationRef", 
    "BOM_Elevation", "BOM_Material", "BOM_Room_Name", "01.Space_Name", "02.Status", "03.Part", 
    "04.Mat_Device", "05.Size", "06.Elevation", "07.Elev_Base", "08.Revit_Category", 
    "09.Revit_Workset", "10.Mat_Notes", "11.UUID", "Ref_Length_L", "Ref_Width_W", "Ref_Height_H"
]

# ==========================================
#   1. Data write core (pure _CB attribute layer)
# ==========================================
# ==================================================================
# Attribute Write Helpers
# ==================================================================
def get_safe_val(x):
    if x is None: return "-"
    s = str(x).strip()
    return s if s else "-"

def write_cabinet_tags(obj_id, part_name, dims, is_update=False):
    layer_name = rs.ObjectLayer(obj_id)
    if is_update and _CABINET_LAYER_ID not in layer_name: return
        
    dims = sorted([abs(d) for d in dims])
    T, W, L = dims[0], dims[1], dims[2]
            
    for jk in JUNK_KEYS:
        if rs.GetUserText(obj_id, jk) is not None:
            rs.SetUserText(obj_id, jk, None)
        
    rs.SetUserText(obj_id, "_CB.01_Panel_Type", get_safe_val(part_name))
    rs.SetUserText(obj_id, "_CB.02_Length_L", "{:.1f}".format(L))
    rs.SetUserText(obj_id, "_CB.03_Width_W", "{:.1f}".format(W))
    rs.SetUserText(obj_id, "_CB.04_Thickness_T", "{:.1f}".format(T))

    if not is_update:
        short_id = str(obj_id).split('-')[0][:4].upper()
        vis_name = u"Panel-[{}]-{:.1f}x{:.1f}x{:.1f}-{}".format(part_name, T, W, L, short_id)
        rs.ObjectName(obj_id, vis_name)

# ==========================================
#   2. UI class (final layout)
# ==========================================
class MasterDialog(forms.Dialog[bool]):
    def __init__(self, items):
        super(MasterDialog, self).__init__()
        self.Title = u"Cabinet Suite"
        self.Padding = drawing.Padding(20)
        self.Resizable = False
        self.ClientSize = drawing.Size(500, 280) # Final window size
        self.SelectedDoor, self.Action = None, None

        last_action = sc.sticky.get("LF_CABINET_LAST_ACTION", "Cabinet_Tall")

        # Cabinet radio buttons
        self.rb_tall = forms.RadioButton(); self.rb_tall.Text = u"Tall Cabinet (Standard)"
        self.rb_upper = forms.RadioButton(self.rb_tall); self.rb_upper.Text = u"Upper Cabinet (Wall-Mounted)"
        self.rb_lower = forms.RadioButton(self.rb_tall); self.rb_lower.Text = u"Base Cabinet"

        if last_action == "Cabinet_Upper": self.rb_upper.Checked = True
        elif last_action == "Cabinet_Lower": self.rb_lower.Checked = True
        else: self.rb_tall.Checked = True

        self.rb_tall.CheckedChanged += self.OnUIUpdate
        self.rb_upper.CheckedChanged += self.OnUIUpdate
        self.rb_lower.CheckedChanged += self.OnUIUpdate

        # Shelf standalone buttons
        self.btn_shelf_y = forms.Button()
        self.btn_shelf_y.Text = u"▤ Generate H-Shelf"
        self.btn_shelf_y.Click += self.OnShelfYClick

        self.btn_shelf_x = forms.Button()
        self.btn_shelf_x.Text = u"▥ Generate V-Divider"
        self.btn_shelf_x.Click += self.OnShelfXClick

        # BOM Updater large button
        self.btn_bom = forms.Button()
        self.btn_bom.Text = u"▪ BOM Updater"
        self.btn_bom.Height = 60 # Double height
        self.btn_bom.ToolTip = u"Update _CB values for {} only".format(_CABINET_LAYER_ID)
        self.btn_bom.Click += self.OnBOMClick

        # Right-side Door_Leaf style and OK button
        self.listbox = forms.ListBox()
        self.listbox.Height = 310
        self.listbox.DataStore = [str(i) for i in items if str(i).strip() != ""]
        self.listbox.SelectedIndexChanged += self.OnSelectionChanged
        self.listbox.MouseDoubleClick += self.OnDoubleClick

        self.btn_ok = forms.Button()
        self.btn_ok.Text = "OK"
        self.btn_ok.Enabled = False 
        self.btn_ok.Click += self.OnOk

        # Hide cancel button, bind ESC
        hidden_cancel = forms.Button()
        hidden_cancel.Click += (lambda s, e: self.Close(False))
        self.AbortButton = hidden_cancel 

        # Left layout
        layout_left = forms.DynamicLayout()
        layout_left.Spacing = drawing.Size(5, 10)
        lbl_1 = forms.Label(); lbl_1.Text = u"▫ Cabinet Gen"; lbl_1.Font = drawing.Font(drawing.SystemFont.Bold, 10)
        layout_left.AddRow(lbl_1)
        layout_left.AddRow(self.rb_tall)
        layout_left.AddRow(self.rb_upper)
        layout_left.AddRow(self.rb_lower)
        layout_left.AddRow(None)
        
        lbl_2 = forms.Label(); lbl_2.Text = u"▫ Data & Panel"; lbl_2.Font = drawing.Font(drawing.SystemFont.Bold, 10)
        layout_left.AddRow(lbl_2)
        layout_left.AddRow(self.btn_shelf_y)
        layout_left.AddRow(self.btn_shelf_x)
        layout_left.AddRow(self.btn_bom) # Place BOM button here

        # Right layout
        layout_right = forms.DynamicLayout()
        layout_right.Spacing = drawing.Size(5, 5)
        lbl_3 = forms.Label(); lbl_3.Text = u"▫ Door_Leaf Style:"; lbl_3.Font = drawing.Font(drawing.SystemFont.Bold, 10)
        layout_right.Add(lbl_3)
        layout_right.Add(self.listbox)
        layout_right.AddRow(None) # Align to bottom
        layout_right.Add(self.btn_ok)

        main_layout = forms.DynamicLayout()
        main_layout.Spacing = drawing.Size(20, 15)
        
        top_layout = forms.DynamicLayout()
        top_layout.Spacing = drawing.Size(25, 0)
        top_layout.BeginHorizontal()
        top_layout.Add(layout_left, xscale=False) 
        top_layout.Add(layout_right, xscale=True) 
        top_layout.EndHorizontal()
        
        main_layout.AddRow(top_layout)
        self.Content = main_layout
        self.OnUIUpdate(None, None)

    def OnUIUpdate(self, sender, e):
        self.listbox.Enabled = True
        self.btn_ok.Enabled = self.SelectedDoor is not None

    def OnSelectionChanged(self, sender, e):
        idx = self.listbox.SelectedIndex
        if idx >= 0:
            val = self.listbox.SelectedValue
            self.SelectedDoor = str(val) if val else None
        else:
            self.SelectedDoor = None
        self.OnUIUpdate(None, None)

    def OnDoubleClick(self, sender, e):
        if self.btn_ok.Enabled:
            self.OnOk(None, None)

    def OnShelfYClick(self, sender, e):
        self.Action = "Shelf_Y"
        self.Close(True)

    def OnShelfXClick(self, sender, e):
        self.Action = "Shelf_X"
        self.Close(True)

    def OnBOMClick(self, sender, e):
        self.Action = "BOM_Update"
        self.Close(True)

    def OnOk(self, sender, e):
        if self.rb_tall.Checked: self.Action = "Cabinet_Tall"
        elif self.rb_upper.Checked: self.Action = "Cabinet_Upper"
        elif self.rb_lower.Checked: self.Action = "Cabinet_Lower"
        sc.sticky["LF_CABINET_LAST_ACTION"] = self.Action
        self.Close(True)

# ==========================================
#   [Module 1] Cabinet + Door_Leaf auto-gen logic (full engine)
# ==========================================
def run_cabinet_gen(mode, selected_menu):
    prefix = selected_menu.split("-")[0].strip()
    is_pure_carcass = (prefix == "0")
    config_type, style_code = "A", 1    
    
    if not is_pure_carcass:
        if "B" in prefix: config_type = "B"
        elif "C" in prefix: config_type = "C"
        if "2" in prefix: style_code = 2
        elif "3" in prefix: style_code = 3

    sc.doc.Objects.UnselectAll()
    go = Rhino.Input.Custom.GetObject()
    go.SetCommandPrompt(u"Step 1/2: Click the [front face] of the box")
    go.GeometryFilter = Rhino.DocObjects.ObjectType.Surface
    go.SubObjectSelect = True
    go.EnablePreSelect(False, True)
    if go.Get() != Rhino.Input.GetResult.Object: return
    
    obj_ref = go.Object(0)
    front_face = obj_ref.Face()
    box_id = obj_ref.ObjectId 
    if not rs.IsPolysurface(box_id) and not rs.IsSurface(box_id): return

    sc.doc.Objects.UnselectAll()
    pick_pt = rs.GetPoint(u"Step 2/2: Click [a point indicating the bottom]")
    if not pick_pt: return

    rs.EnableRedraw(False)

    box_center = rs.SurfaceAreaCentroid(box_id)[0]
    front_temp = front_face.DuplicateFace(False)
    front_center = Rhino.Geometry.AreaMassProperties.Compute(front_temp).Centroid
    depth_vec = box_center - front_center
    depth_vec.Unitize()

    user_dir = pick_pt - front_center
    brep = rs.coercebrep(box_id)
    best_dot = -1.0
    bottom_normal = None
    for face in brep.Faces:
        f_temp = face.DuplicateFace(False)
        f_center = Rhino.Geometry.AreaMassProperties.Compute(f_temp).Centroid
        f_normal = f_center - box_center
        f_normal.Unitize()
        if abs(f_normal * depth_vec) > 0.9: continue
        dot = user_dir * f_normal
        if dot > best_dot:
            best_dot = dot
            bottom_normal = f_normal
            
    up_vec = -bottom_normal if bottom_normal else Rhino.Geometry.Vector3d.ZAxis
    right_vec = Rhino.Geometry.Vector3d.CrossProduct(up_vec, depth_vec)
    plane = Rhino.Geometry.Plane(front_center, right_vec, up_vec)
    bbox = rs.BoundingBox(box_id, plane)
    pt0 = bbox[0] 

    W = rs.Distance(bbox[0], bbox[1])
    H = rs.Distance(bbox[0], bbox[3])
    D = rs.Distance(bbox[0], bbox[4])

    if not is_pure_carcass:
        retreat_dist = 2.0
        pt0 = pt0 + (depth_vec * retreat_dist)
        D = max(D - retreat_dist, 0.1)

    def make_part(p_start, w_v, h_v, d_v, part_name, true_w=None, true_h=None, true_d=None):
        p0 = p_start
        p1 = p_start + w_v
        p2 = p_start + w_v + h_v
        p3 = p_start + h_v
        p4 = p0 + d_v
        p5 = p1 + d_v
        p6 = p2 + d_v
        p7 = p3 + d_v
        
        bid = rs.AddBox([p0, p1, p2, p3, p4, p5, p6, p7])
        if bid:
            dim1 = true_w if true_w is not None else w_v.Length
            dim2 = true_h if true_h is not None else h_v.Length
            dim3 = true_d if true_d is not None else d_v.Length
            write_cabinet_tags(bid, part_name, [dim1, dim2, dim3], is_update=False)
        return bid

    t_top, t_side, t_bot, t_back = 6.0, 1.8, 12.0, 3.0
    gap_render, gap_top, gap_bot = 0.1, 2.0, 10.0
    
    if mode == "Upper": 
        t_bot = 1.8 
        gap_bot = 0.3 if config_type == "B" else 2.0 
    elif mode == "Lower": 
        t_top = 2.5 
        gap_top = 0.3 if config_type == "B" else 2.0 

    carcass_parts = []
    carcass_parts.append(make_part(pt0, right_vec * t_side, up_vec * H, depth_vec * D, u"Side_Panel")) 
    carcass_parts.append(make_part(pt0 + right_vec * (W - t_side), right_vec * t_side, up_vec * H, depth_vec * D, u"Side_Panel")) 
    
    t_top_board = t_top
    if mode in ["Tall", "Upper"]:
        t_top_board = 1.8 
        if t_top < t_top_board: t_top_board = t_top 
        
    true_mid_w = W - 2 * t_side
    w_mid_vec = right_vec * (true_mid_w - 2 * gap_render)
    p_top_start = pt0 + right_vec * (t_side + gap_render) + up_vec * (H - t_top)
    
    carcass_parts.append(make_part(p_top_start, w_mid_vec, up_vec * t_top_board, depth_vec * D, u"Top_Board", true_w=true_mid_w)) 
    
    if mode in ["Tall", "Upper"] and t_top > t_top_board:
        fascia_h = t_top - t_top_board
        carcass_parts.append(make_part(pt0 + right_vec * (t_side + gap_render) + up_vec * (H - t_top + t_top_board), w_mid_vec, up_vec * fascia_h, depth_vec * 1.8, u"Top_Fascia", true_w=true_mid_w))
    
    t_bot_board = 1.8
    if t_bot < t_bot_board: t_bot_board = t_bot
    carcass_parts.append(make_part(pt0 + right_vec * (t_side + gap_render) + up_vec * (t_bot - t_bot_board), w_mid_vec, up_vec * t_bot_board, depth_vec * D, u"Bottom_Board", true_w=true_mid_w)) 
    
    if t_bot > t_bot_board:
        carcass_parts.append(make_part(pt0 + right_vec * (t_side + gap_render), w_mid_vec, up_vec * (t_bot - t_bot_board), depth_vec * 1.8, u"Kick_Plate", true_w=true_mid_w))

    carcass_parts.append(make_part(pt0 + right_vec * t_side + up_vec * t_bot + depth_vec * (D - t_back), right_vec * (W - 2 * t_side), up_vec * (H - t_top - t_bot), depth_vec * 0.8, u"Back_Board")) 

    generated_frames, generated_glasses = [], []

    if not is_pure_carcass:
        d_thick, d_float, glass_thick, gap_side = 1.8, 0.2, 1.0, 0.3
        frame_w = 0.0
        if style_code == 2: frame_w = 0.6 
        elif style_code == 3: frame_w = 2.5 
        
        gap_mid, is_single = 0.3, False
        if config_type == "B": gap_mid = 2.0
        elif config_type == "C": is_single = True

        door_h = H - gap_top - gap_bot
        outward_vec = -depth_vec 
        start_offset_base = outward_vec * d_float 
        extrude_vec_door = outward_vec * d_thick  
        extrude_vec_glass = outward_vec * glass_thick

        def create_door_leaf(base_pt, width):
            if style_code == 1:
                return {"frame": make_part(base_pt, right_vec * width, up_vec * door_h, extrude_vec_door, u"Door_Leaf"), "glass": None}
            else:
                p1 = base_pt
                p2 = base_pt + right_vec * width
                p3 = base_pt + right_vec * width + up_vec * door_h
                p4 = base_pt + up_vec * door_h
                outer_crv = rs.AddPolyline([p1, p2, p3, p4, p1])
                
                pi1 = base_pt + right_vec * frame_w + up_vec * frame_w
                pi2 = base_pt + right_vec * (width - frame_w) + up_vec * frame_w
                pi3 = base_pt + right_vec * (width - frame_w) + up_vec * (door_h - frame_w)
                pi4 = base_pt + right_vec * frame_w + up_vec * (door_h - frame_w)
                inner_crv = rs.AddPolyline([pi1, pi2, pi3, pi4, pi1])
                
                srf = rs.AddPlanarSrf([outer_crv, inner_crv])[0]
                path_line = rs.AddLine(p1, p1 + extrude_vec_door)
                frame_obj = rs.ExtrudeSurface(srf, path_line)
                rs.CapPlanarHoles(frame_obj) 
                rs.DeleteObjects([outer_crv, inner_crv, srf, path_line])
                
                write_cabinet_tags(frame_obj, u"Door_Frame", [width, door_h, d_thick], is_update=False)
                
                glass_obj = make_part(pi1, right_vec * (width - 2 * frame_w), up_vec * (door_h - 2 * frame_w), extrude_vec_glass, u"Door_Leaf_Glass")
                return {"frame": frame_obj, "glass": glass_obj}

        if is_single:
            leaf = create_door_leaf(pt0 + (right_vec * gap_side) + (up_vec * gap_bot) + start_offset_base, W - gap_side * 2)
            generated_frames.append(leaf["frame"])
            if leaf["glass"]: generated_glasses.append(leaf["glass"])
        else:
            door_w = (W - gap_side * 2 - gap_mid) / 2
            p_L = pt0 + (right_vec * gap_side) + (up_vec * gap_bot) + start_offset_base
            leaf_L = create_door_leaf(p_L, door_w)
            generated_frames.append(leaf_L["frame"])
            if leaf_L["glass"]: generated_glasses.append(leaf_L["glass"])
            
            leaf_R = create_door_leaf(p_L + right_vec * (door_w + gap_mid), door_w)
            right_frame_id = leaf_R["frame"]
            
            if config_type == "B":
                baffle_id = make_part(p_L + right_vec * (door_w + gap_mid) - (right_vec * 1.7), right_vec * 2.0, up_vec * door_h, outward_vec * 0.3, u"Door_Leaf_Baffle")
                sc.doc.Objects.UnselectAll()
                rs.SelectObjects([right_frame_id, baffle_id])
                union_result = rs.BooleanUnion([right_frame_id, baffle_id])
                if union_result:
                    right_frame_id = union_result[0]
                    rs.SelectObject(right_frame_id)
                    rs.Command("_-MergeAllCoplanarFaces _Enter", False)
                    rs.UnselectAllObjects()
                    write_cabinet_tags(right_frame_id, u"Door_Leaf(w/Baffle)", [door_w + 1.7, door_h, d_thick], is_update=False)
                else: 
                    generated_frames.append(baffle_id)
            
            generated_frames.append(right_frame_id)
            if leaf_R["glass"]: generated_glasses.append(leaf_R["glass"])

    if carcass_parts: rs.AddObjectsToGroup(carcass_parts, rs.AddGroup())
    if generated_frames: rs.AddObjectsToGroup(generated_frames, rs.AddGroup())
    if generated_glasses: rs.AddObjectsToGroup(generated_glasses, rs.AddGroup())
    rs.DeleteObject(box_id)
    
    rs.UnselectAllObjects()
    rs.EnableRedraw(True)
    
    msg = u">> Done! Objects generated in the current layer.\n(Run LF Nexus → TagTrigger next to fill in remaining attributes)"
    print("\n" + msg); rs.Prompt(msg)

# ==========================================
#   [Module 2] Shelf / divider generation logic
# ==========================================
def run_shelf_gap(direction):
    sc.doc.Objects.UnselectAll() 
    go_back = Rhino.Input.Custom.GetObject()
    go_back.SetCommandPrompt(u"Step 1/4: Click the [Back_Board face] inside the cabinet")
    go_back.GeometryFilter = Rhino.DocObjects.ObjectType.Surface
    go_back.SubObjectSelect = True 
    go_back.EnablePreSelect(False, True) 
    if go_back.Get() != Rhino.Input.GetResult.Object: return
    back_face = go_back.Object(0).Face()
    
    sc.doc.Objects.UnselectAll()
    go_bottom = Rhino.Input.Custom.GetObject()
    go_bottom.SetCommandPrompt(u"Step 2/4: Click the [Bottom_Board face] inside the cabinet")
    go_bottom.GeometryFilter = Rhino.DocObjects.ObjectType.Surface
    go_bottom.SubObjectSelect = True 
    go_bottom.EnablePreSelect(False, True) 
    if go_bottom.Get() != Rhino.Input.GetResult.Object: return
    bottom_face = go_bottom.Object(0).Face()

    thickness = rs.GetReal(u"Step 3/4: Enter board thickness (cm)", 1.8, 0.1)
    if thickness is None: return
    target_spacing = rs.GetReal(u"Step 4/4: Enter target spacing (cm)", 30.0, 1.0)
    if target_spacing is None: return

    rs.EnableRedraw(False)
    cabinet_plane = Rhino.Geometry.Plane(
        Rhino.Geometry.AreaMassProperties.Compute(back_face.OuterLoop.To3dCurve()).Centroid, 
        Rhino.Geometry.Vector3d.CrossProduct(bottom_face.NormalAt(bottom_face.Domain(0).Mid, bottom_face.Domain(1).Mid), back_face.NormalAt(back_face.Domain(0).Mid, back_face.Domain(1).Mid)), 
        bottom_face.NormalAt(bottom_face.Domain(0).Mid, bottom_face.Domain(1).Mid)
    )
    
    temp_id = sc.doc.Objects.AddCurve(back_face.OuterLoop.To3dCurve())
    bbox = rs.BoundingBox(temp_id, cabinet_plane)
    rs.DeleteObject(temp_id)
    
    bottom_brep = bottom_face.DuplicateFace(False)
    bottom_bbox = bottom_brep.GetBoundingBox(cabinet_plane)
    auto_depth = max(abs(bottom_bbox.Max.Z - bottom_bbox.Min.Z) - 4.0, 0.1)
    
    L = rs.Distance(bbox[0], bbox[3]) if u"Y-axis" in direction else rs.Distance(bbox[0], bbox[1])
    H = rs.Distance(bbox[0], bbox[1]) if u"Y-axis" in direction else rs.Distance(bbox[0], bbox[3])
    
    u_vec = cabinet_plane.YAxis if u"Y-axis" in direction else cabinet_plane.XAxis
    v_vec = cabinet_plane.XAxis if u"Y-axis" in direction else cabinet_plane.YAxis
    part_name = u"Shelf" if u"Y-axis" in direction else u"Divider_Panel"

    n = int(round((L - target_spacing) / (thickness + target_spacing)))
    new_solids = []
    
    if n > 0:
        actual_spacing = (L - (n * thickness)) / (n + 1)
        for i in range(1, n + 1):
            b1 = rs.PointAdd(bbox[0], u_vec * ((i * actual_spacing) + ((i - 1) * thickness)))
            
            p0 = b1
            p1 = rs.PointAdd(b1, u_vec * thickness)
            p2 = rs.PointAdd(b1, u_vec * thickness + v_vec * H)
            p3 = rs.PointAdd(b1, v_vec * H)
            p4 = rs.PointAdd(p0, cabinet_plane.ZAxis * auto_depth)
            p5 = rs.PointAdd(p1, cabinet_plane.ZAxis * auto_depth)
            p6 = rs.PointAdd(p2, cabinet_plane.ZAxis * auto_depth)
            p7 = rs.PointAdd(p3, cabinet_plane.ZAxis * auto_depth)
            
            box_id = rs.AddBox([p0, p1, p2, p3, p4, p5, p6, p7])
            if box_id:
                write_cabinet_tags(box_id, part_name, [thickness, H, auto_depth], is_update=False)
                new_solids.append(box_id)
                
        if new_solids: rs.AddObjectsToGroup(new_solids, rs.AddGroup())

    sc.doc.Objects.UnselectAll() 
    rs.EnableRedraw(True)
    
    msg = u">> Shelf / Divider panels generated in current layer! Total: {} pcs".format(len(new_solids))
    print("\n" + msg); rs.Prompt(msg)

# ==========================================
#   [Module 3] BOM Update dimension write-back logic (full engine)
# ==========================================
def run_bom_updater():
    objs = rs.GetObjects(u"Window-select the entire cabinet (or the panel solids to update)", rs.filter.polysurface)
    if not objs: return

    valid_objs = [obj for obj in objs if _CABINET_LAYER_ID in rs.ObjectLayer(obj)]
    if not valid_objs:
        rs.MessageBox(u"No objects belonging to {} found in the selection.".format(_CABINET_LAYER_ID))
        return

    g_bbox = rs.BoundingBox(valid_objs)
    g_center_z = (g_bbox[0].Z + g_bbox[6].Z) / 2.0
    comp_parts = [u"Top_Board", u"Bottom_Board", u"Kick_Plate", u"Top_Fascia"]
    standard_names = [u"Top_Board", u"Bottom_Board", u"Shelf", u"Side_Panel", u"Divider_Panel", u"Back_Board", u"Kick_Plate", u"Top_Fascia", u"Door_Leaf", u"Custom_Panel", u"Door_Frame", u"Door_Leaf_Glass", u"Door_Leaf(w/Baffle)", u"Door_Leaf_Baffle"]
    
    frames_y_centers = []
    horiz_z_list = []
    vert_x_list = []
    
    for obj_id in valid_objs:
        brep = rs.coercebrep(obj_id)
        if not brep: continue
        
        vol_prop = Rhino.Geometry.VolumeMassProperties.Compute(brep)
        bbox = brep.GetBoundingBox(True)
        v_bbox = (bbox.Max.X - bbox.Min.X) * (bbox.Max.Y - bbox.Min.Y) * (bbox.Max.Z - bbox.Min.Z)
        v_actual = vol_prop.Volume if vol_prop else v_bbox
        vol_ratio = v_actual / v_bbox if v_bbox > 0 else 1.0
        
        if vol_ratio < 0.75:
            c_y = (bbox.Max.Y + bbox.Min.Y) / 2.0
            c_x = (bbox.Max.X + bbox.Min.X) / 2.0
            frames_y_centers.append((c_x, c_y))
            
        max_area = -1.0
        for face in brep.Faces:
            if face.IsPlanar() and Rhino.Geometry.AreaMassProperties.Compute(face):
                if Rhino.Geometry.AreaMassProperties.Compute(face).Area > max_area:
                    max_area = Rhino.Geometry.AreaMassProperties.Compute(face).Area
                    rc, best_plane = face.TryGetPlane()
                    
        if best_plane:
            if abs(best_plane.Normal.Z) > 0.8: 
                horiz_z_list.append((bbox.Max.Z + bbox.Min.Z) / 2.0)
            elif abs(best_plane.Normal.X) > abs(best_plane.Normal.Y): 
                vert_x_list.append((bbox.Max.X + bbox.Min.X) / 2.0)

    max_horiz_z = max(horiz_z_list) if horiz_z_list else -9999
    min_horiz_z = min(horiz_z_list) if horiz_z_list else 9999
    max_vert_x = max(vert_x_list) if vert_x_list else -9999
    min_vert_x = min(vert_x_list) if vert_x_list else 9999

    count = 0
    
    for obj_id in objs:
        layer_name = rs.ObjectLayer(obj_id)
        if _CABINET_LAYER_ID not in layer_name:
            continue

        brep = rs.coercebrep(obj_id)
        if not brep: continue
        
        best_plane = None
        max_area = -1.0
        for face in brep.Faces:
            if face.IsPlanar() and Rhino.Geometry.AreaMassProperties.Compute(face) and Rhino.Geometry.AreaMassProperties.Compute(face).Area > max_area:
                max_area = Rhino.Geometry.AreaMassProperties.Compute(face).Area
                rc, plane = face.TryGetPlane()
                if rc: best_plane = plane

        if best_plane:
            bbox_local = brep.GetBoundingBox(best_plane)
            dims = sorted([abs(bbox_local.Max.X - bbox_local.Min.X), abs(bbox_local.Max.Y - bbox_local.Min.Y), abs(bbox_local.Max.Z - bbox_local.Min.Z)])
            
            part_name = rs.GetUserText(obj_id, "_CB.01_Panel_Type") or rs.GetUserText(obj_id, "B.01 Panel_Type") or rs.GetUserText(obj_id, "B.01")
            if part_name == "-": part_name = None
            
            old_l_str = rs.GetUserText(obj_id, "_CB.02_Length_L") or rs.GetUserText(obj_id, "B.02 Length_L") or rs.GetUserText(obj_id, "B.02")
            old_w_str = rs.GetUserText(obj_id, "_CB.03_Width_W") or rs.GetUserText(obj_id, "B.03 Width_W") or rs.GetUserText(obj_id, "B.03")
            
            guessed_name = u"Custom_Panel"
            board_bbox = rs.BoundingBox(obj_id)
            c_z = (board_bbox[0].Z + board_bbox[6].Z) / 2.0
            c_x = (board_bbox[0].X + board_bbox[6].X) / 2.0
            c_y = (board_bbox[0].Y + board_bbox[6].Y) / 2.0
            h = board_bbox[6].Z - board_bbox[0].Z
            
            vol_prop = Rhino.Geometry.VolumeMassProperties.Compute(brep)
            v_bbox = dims[0]*dims[1]*dims[2]
            v_actual = vol_prop.Volume if vol_prop else v_bbox
            vol_ratio = v_actual / v_bbox if v_bbox > 0 else 1.0
            
            if abs(best_plane.Normal.Z) > 0.8: 
                if abs(c_z - max_horiz_z) < 2.0: guessed_name = u"Top_Board"
                elif abs(c_z - min_horiz_z) < 2.0: guessed_name = u"Bottom_Board"
                else: guessed_name = u"Shelf"
            else:
                if vol_ratio < 0.75:
                    guessed_name = u"Door_Frame"
                else:
                    if abs(best_plane.Normal.X) > abs(best_plane.Normal.Y): 
                        if abs(c_x - min_vert_x) < 2.0 or abs(c_x - max_vert_x) < 2.0:
                            guessed_name = u"Side_Panel"
                        else:
                            guessed_name = u"Divider_Panel"
                    else:
                        if h < 25.0 and dims[0] >= 1.2: 
                            if c_z > g_center_z: guessed_name = u"Top_Fascia"
                            else: guessed_name = u"Kick_Plate"
                        elif dims[0] <= 1.2:
                            is_glass = False
                            for fx, fy in frames_y_centers:
                                if abs(c_y - fy) < 10.0:
                                    is_glass = True
                                    break
                            guessed_name = u"Door_Leaf_Glass" if is_glass else u"Back_Board"
                        else:
                            guessed_name = u"Door_Leaf"

            if (not part_name) or (part_name in standard_names): 
                part_name = guessed_name

            if part_name in comp_parts:
                if old_l_str and old_w_str and old_l_str != "-" and old_w_str != "-":
                    try:
                        old_l, old_w = float(old_l_str), float(old_w_str)
                        d1, d2 = dims[1], dims[2]
                        tol = 0.05 
                        if ((abs(d1 - old_l) < tol) or (abs(d1 - old_w) < tol)) and not ((abs(d2 - old_l) < tol) or (abs(d2 - old_w) < tol)):
                            d2 += 0.2 
                        elif ((abs(d2 - old_l) < tol) or (abs(d2 - old_w) < tol)) and not ((abs(d1 - old_l) < tol) or (abs(d1 - old_w) < tol)):
                            d1 += 0.2
                        elif ((abs(d1 + 0.2 - old_l) < tol) or (abs(d1 + 0.2 - old_w) < tol)) and not ((abs(d2 + 0.2 - old_l) < tol) or (abs(d2 + 0.2 - old_w) < tol)):
                            d1 += 0.2 
                        elif ((abs(d2 + 0.2 - old_l) < tol) or (abs(d2 + 0.2 - old_w) < tol)) and not ((abs(d1 + 0.2 - old_l) < tol) or (abs(d1 + 0.2 - old_w) < tol)):
                            d2 += 0.2
                        else:
                            d2 += 0.2 
                        dims[1], dims[2] = d1, d2
                    except ValueError:
                        dims[2] += 0.2
                else: 
                    dims[2] += 0.2
                dims = sorted(dims)

            write_cabinet_tags(obj_id, part_name, dims, is_update=True)
            count += 1

    msg = u">> Done! Updated _CB fields for {} cabinet panels.\n(Run LF Nexus → TagTrigger next to sync elevation and space)".format(count)
    rs.MessageBox(msg, 0, u"BOM Update Complete")

# ==========================================
#   Main entry point
# ==========================================
def main():
    try:
        type_opts = [
            u"0 - Carcass only (no Door_Leaf)",
            u"A1 - Double-door standard (gap 0.3)", u"A2 - Double-door slim glass (gap 0.3)", u"A3 - Double-door alum glass (gap 0.3)",
            u"B1 - Double-door standard (gap 2.0)", u"B2 - Double-door slim glass (gap 2.0)", u"B3 - Double-door alum glass (gap 2.0)",
            u"C1 - Single-door standard", u"C2 - Single-door slim glass", u"C3 - Single-door alum glass"
        ]

        dlg = MasterDialog(type_opts)
        rc = dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

        if rc and dlg.Action:
            if dlg.Action.startswith("Cabinet"):
                mode = dlg.Action.split("_")[1]
                door = dlg.SelectedDoor
                run_cabinet_gen(mode, door)
            elif dlg.Action == "Shelf_Y":
                run_shelf_gap(u"Y-axis")
            elif dlg.Action == "Shelf_X":
                run_shelf_gap(u"X-axis")
            elif dlg.Action == "BOM_Update":
                run_bom_updater()
    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_Cabinet_Suite.main", e))
        rs.MessageBox(u"Cabinet Suite encountered an unexpected error.\n\nSee debug log: C:\\_RH_Tools\\cursor_LF_debug_log.txt", 16)

if __name__ == "__main__":
    main()