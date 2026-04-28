# -*- coding: utf-8 -*-
# Script: LF_2D_Cabinet_Gen.py (2D Cabinet Symbol Auto-Generator)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py
# Usage: In 2D.3dm, select the rectangle representing the cabinet extents;
#           choose cabinet type via UI, and auto-generate grouped 2D symbol lines.
#           Output layers are controlled by LAYER_2D_FURN_* in _LoopFlow_Config.py.

# ==================================================================
# Imports
# ==================================================================
import rhinoscriptsyntax as rs
import random
import math
import _LoopFlow_Config as _CFG


# ==================================================================
# Cabinet Generator
# ==================================================================
def cabinet_generator():
    # --- UI Menu ---
    opts = [
        "[ X ] Tall Cabinet", 
        "[ / ] Low Cabinet", 
        "[ ||/ ] Wardrobe. Full", 
        "[ | / ] Wardrobe. Lived-In"
    ]
    choice = rs.ListBox(opts, "Select cabinet type", "2D Cabinet Generator")
    if not choice: return

    # --- Parameters ---
    cfg_lays = {
        "Out": (_CFG.LAYER_2D_FURN_OUT,) + tuple(_CFG.COLOR_2D_FURN_OUT),
        "In":  (_CFG.LAYER_2D_FURN_IN,)  + tuple(_CFG.COLOR_2D_FURN_IN),
    }
    w_cfg = {
        "gap": 3.0, "pad": 3.0, "rots": [0, 10, -7],
        "sp_min": 8.0, "sp_max": 12.0, "h_h": 20.0
    }

    # --- Helper Functions ---
    def ensure_lay(n, r, g, b): 
        if not rs.IsLayer(n): rs.AddLayer(n, (r, g, b))
        return n

    def make_hanger():
        p_t, p_b = [0, 20, 0], [0, -20, 0]
        arcs = [rs.AddArc3Pt(p_t, p_b, [-1.8,0,0]), rs.AddArc3Pt(p_t, p_b, [0.7,0,0])]
        j = rs.JoinCurves(arcs, True)
        return j[0] if j else arcs[0]

    def get_rot_data(cx, ang):
        rad = math.radians(ang)
        off = w_cfg["h_h"] * math.sin(rad)
        return {"c": cx, "t": cx - off, "b": cx + off, "ang": ang}

    def check_dist(d1, cx2, ang2):
        d2 = get_rot_data(cx2, ang2)
        return min(abs(d2["c"]-d1["c"]), abs(d2["t"]-d1["t"]), abs(d2["b"]-d1["b"]))

    # --- Main Procedure ---
    r1 = rs.GetObject("Select rectangle (any angle supported)", rs.filter.curve)
    if not r1: return
    rs.EnableRedraw(False)

    # 1. Base geometry setup
    l_out = ensure_lay(*cfg_lays["Out"])
    l_in  = ensure_lay(*cfg_lays["In"])
    rs.ObjectLayer(r1, l_out)
    
    cen = rs.CurveAreaCentroid(r1)
    if not cen: return
    r2 = rs.OffsetCurve(r1, cen[0], 2.0)[0]
    rs.ObjectLayer(r2, l_in)
    
    new_objs = []

    # 2. Branch: tall/low cabinet
    if choice == opts[0] or choice == opts[1]:
        pts = rs.PolylineVertices(r2) if rs.IsPolyline(r2) else rs.CurvePoints(r2)
        if len(pts) >= 5: pts = pts[:-1]
        
        lines = []
        if choice == opts[0]: # [ X ]
            lines = [rs.AddLine(pts[0], pts[2]), rs.AddLine(pts[1], pts[3])]
        else: # [ / ]
            lines = [rs.AddLine(pts[0], pts[2])]
            
        for l in lines: 
            rs.ObjectLayer(l, l_in)
            new_objs.extend(lines)

    # 3. Branch: wardrobe
    else:
        # A. Analyse and build rectangular rod axis
        segs = rs.ExplodeCurves(r2, False)
        if not segs or len(segs) != 4:
            rs.EnableRedraw(True); print("Error: please use a standard rectangle"); return

        segs_s = sorted(segs, key=rs.CurveLength)
        p_s, p_e = rs.CurveMidPoint(segs_s[0]), rs.CurveMidPoint(segs_s[1])
        rs.DeleteObjects(segs)
        
        vec = rs.VectorUnitize(rs.VectorCreate(p_e, p_s))
        base_ang = math.degrees(math.atan2(vec.Y, vec.X))
        
        # Build 2 cm-wide rectangle (half-width 1.0)
        perp = rs.VectorRotate(vec, 90, [0,0,1])
        v_off = rs.VectorScale(perp, 1.0)
        v_neg = rs.VectorReverse(v_off)
        
        rec_pts = [
            rs.PointAdd(p_s, v_off),
            rs.PointAdd(p_e, v_off),
            rs.PointAdd(p_e, v_neg),
            rs.PointAdd(p_s, v_neg),
            rs.PointAdd(p_s, v_off)
        ]
        rod_axis = rs.AddPolyline(rec_pts)
        
        rs.ObjectLayer(rod_axis, l_in)
        new_objs.append(rod_axis)

        # B. Simulate hanger placement
        lim_len = rs.Distance(p_s, p_e) - (w_cfg["pad"] * 2)
        sims = []
        curr_x = 0.0
        
        a1 = random.choice(w_cfg["rots"])
        sims.append({"pos": 0.0, "ang": a1, "dat": get_rot_data(0.0, a1)})
        
        while True:
            opts_rot = list(w_cfg["rots"])
            if len(sims) >= 2 and sims[-1]["ang"] == sims[-2]["ang"]:
                if sims[-1]["ang"] in opts_rot: opts_rot.remove(sims[-1]["ang"])
            
            next_a = random.choice(opts_rot)
            step = random.uniform(w_cfg["sp_min"], w_cfg["sp_max"])
            valid = False
            
            while step < 30.0:
                try_pos = curr_x + step
                if try_pos > lim_len: break
                if check_dist(sims[-1]["dat"], try_pos, next_a) >= w_cfg["gap"]:
                    curr_x = try_pos
                    valid = True
                    break
                step += 0.5
            
            if not valid or curr_x > lim_len: break
            sims.append({"pos": curr_x, "ang": next_a, "dat": get_rot_data(curr_x, next_a)})
        
        if len(sims) > 1: sims.pop()
        
        # C. 'Lived-in' mode: removal logic
        keeps = [True] * len(sims)
        if choice == opts[3]:
            tgt_del = int(len(sims) * random.uniform(0.25, 0.33))
            cnt_del, try_n, dbl_used = 0, 0, False
            
            while cnt_del < tgt_del and try_n < 1000:
                try_n += 1
                idx = random.randint(0, len(sims)-1)
                pat = 2 if (not dbl_used and (tgt_del - cnt_del)>=2 and random.random()>0.5) else 1
                
                if idx + pat > len(sims): continue
                if not all(keeps[idx+k] for k in range(pat)): continue
                if idx > 0 and not keeps[idx-1]: continue
                if (idx + pat) < len(sims) and not keeps[idx+pat]: continue
                
                for k in range(pat): keeps[idx+k] = False
                cnt_del += pat
                if pat == 2: dbl_used = True

        # D. Generate geometry
        margin = (rs.Distance(p_s, p_e) - sims[-1]["pos"]) / 2.0
        
        for i, s in enumerate(sims):
            if not keeps[i]: continue
            h = make_hanger()
            rs.ObjectLayer(h, l_in)
            rs.RotateObject(h, [0,0,0], s["ang"])
            rs.RotateObject(h, [0,0,0], base_ang)
            
            vec_move = rs.VectorScale(vec, margin + s["pos"])
            rs.MoveObject(h, rs.PointAdd(p_s, vec_move))
            new_objs.append(h)

    # 4. Group
    rs.AddObjectsToGroup([r1, r2] + new_objs, rs.AddGroup())
    rs.EnableRedraw(True)
    print("Done: " + choice)

if __name__ == "__main__":
    cabinet_generator()