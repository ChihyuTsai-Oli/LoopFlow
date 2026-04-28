# -*- coding: utf-8 -*-
# Script: LF_2D_Shelf_Gap.py (2D Cabinet Shelf Auto-Layout Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: None
# Usage: In 2D.3dm, select the rectangle representing the cabinet interior;
#           enter board thickness and desired spacing, then auto-calculates optimal divisions and draws shelf lines.

import rhinoscriptsyntax as rs

# ==================================================================
# Core Logic
# ==================================================================
def create_auto_shelves():

    # 1. Direction selection menu
    options = ["X-axis (vertical dividers)", "Y-axis (horizontal shelves)"]
    direction = rs.ListBox(options, "Select arrangement direction:", "2D Shelf Gap Generator")
    if not direction: return

    # 2. Select rectangles (single or multi-select)
    rect_ids = rs.GetObjects("Select cabinet inner rectangles (multi-select allowed)", rs.filter.curve)
    if not rect_ids: return

    # 3. Parameter input
    thickness = rs.GetReal("Enter board thickness (cm)", 1.8, 0.1)
    if thickness is None: return
    
    target_spacing = rs.GetReal("Enter target spacing (cm)", 30.0, 1.0)
    if target_spacing is None: return

    rs.EnableRedraw(False)
    
    # Variables for final summary display
    final_n = 0
    final_spacing = 0.0

    for rect_id in rect_ids:
        # Get the local coordinate plane of the rectangle (supports rotated/angled cabinets)
        plane = rs.CurvePlane(rect_id)
        if not plane: continue
        
        # Get bounding box relative to the plane for accurate width/height
        bbox = rs.BoundingBox(rect_id, plane)
        pt0 = bbox[0]
        width = rs.Distance(bbox[0], bbox[1])
        height = rs.Distance(bbox[0], bbox[3])
        
        # Determine allocation axis based on direction
        is_x = "X-axis" in direction
        L, H = (width, height) if is_x else (height, width)
        u_vec, v_vec = (plane.XAxis, plane.YAxis) if is_x else (plane.YAxis, plane.XAxis)

        # Adaptive calculation
        n = int(round((L - target_spacing) / (thickness + target_spacing)))
        if n <= 0: continue
        actual_spacing = (L - (n * thickness)) / (n + 1)
        
        final_n, final_spacing = n, actual_spacing # Record data for summary

        new_shelves = []
        for i in range(1, n + 1):
            offset = (i * actual_spacing) + ((i - 1) * thickness)
            
            p1 = rs.PointAdd(pt0, u_vec * offset)
            p2 = rs.PointAdd(p1, u_vec * thickness)
            p3 = rs.PointAdd(p2, v_vec * H)
            p4 = rs.PointAdd(p1, v_vec * H)
            
            shelf_id = rs.AddPolyline([p1, p2, p3, p4, p1])
            new_shelves.append(shelf_id)

        # Create a separate group for shelves of each cabinet
        if new_shelves:
            group_name = rs.AddGroup()
            rs.AddObjectsToGroup(new_shelves, group_name)

    rs.EnableRedraw(True)
    
    # Format summary message
    summary = ">> Mode: {} | Shelves: {} | Actual spacing: {:.2f} cm (grouped)".format(
        direction.split(" ")[0], final_n, final_spacing
    )
    
    # Ensure message appears on the last command-line row
    print("\n" + summary)
    # Also show in Rhino's top prompt area
    rs.Prompt(summary)

if __name__ == "__main__":
    create_auto_shelves()