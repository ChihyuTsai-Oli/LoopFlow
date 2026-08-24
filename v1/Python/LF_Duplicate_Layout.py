#! python3
# -*- coding: utf-8 -*-
# Script: LF_Duplicate_Layout.py (Layout Duplication Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Debug.py
# Usage: In 2D.3dm, select a source Layout from the list and enter a copy count;
#           automatically creates new layout pages with all objects (Detail Views, title blocks, tags, etc.),
#           named as 'SourceName_Copy_N', ready for renaming and binding.

# ==================================================================
# Imports
# ==================================================================
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino
import System

try:
    from _LoopFlow_Config import LAYOUT_NAME_SEPARATOR, LAYOUT_COPY_SUFFIX
except Exception:
    LAYOUT_NAME_SEPARATOR = "__"
    LAYOUT_COPY_SUFFIX    = "_Copy"


# ==================================================================
# Layout Query Helpers
# ==================================================================
def get_layout_names():
    views = sc.doc.Views.GetPageViews()
    if not views or len(views) == 0:
        return []
    return [v.PageName for v in views]


def find_page_view(name):
    views = sc.doc.Views.GetPageViews()
    if not views:
        return None
    for v in views:
        if v.PageName == name:
            return v
    return None


# ==================================================================
# Naming Helpers
# ==================================================================
def extract_copy_base_name(layout_name):
    if LAYOUT_NAME_SEPARATOR in layout_name:
        return layout_name.split(LAYOUT_NAME_SEPARATOR, 1)[1].strip()
    return layout_name.strip()


def generate_unique_name(base, index):
    new_name = "{}{}{}".format(base, LAYOUT_COPY_SUFFIX, index)
    existing = get_layout_names()
    suffix = 0
    original = new_name
    while new_name in existing:
        suffix += 1
        new_name = "{}_{}".format(original, suffix)
    return new_name


# ==================================================================
# Page Object Helpers
# ==================================================================
def get_page_object_ids(page_view):
    page_id = page_view.MainViewport.Id
    ids = []
    for obj in sc.doc.Objects:
        try:
            if obj.Attributes.ViewportId == page_id:
                ids.append(obj.Id)
        except:
            continue
    return ids


def delete_default_details(page_view):
    page_id = page_view.MainViewport.Id
    to_delete = []
    for obj in sc.doc.Objects:
        try:
            if obj.Attributes.ViewportId == page_id:
                if isinstance(obj, Rhino.DocObjects.DetailViewObject):
                    to_delete.append(obj.Id)
        except:
            continue
    for oid in to_delete:
        sc.doc.Objects.Delete(oid, True)


# ==================================================================
# Core Duplicate Logic
# ==================================================================
def duplicate_layout(source_name, count):
    source_view = find_page_view(source_name)
    if source_view is None:
        rs.MessageBox(
            "Layout '{}' not found.".format(source_name), 0, "Error"
        )
        return []

    page_width = source_view.PageWidth
    page_height = source_view.PageHeight

    source_obj_ids = get_page_object_ids(source_view)
    print("Source Layout has {} objects".format(len(source_obj_ids)))

    if len(source_obj_ids) == 0:
        rs.MessageBox("Source Layout has no objects.", 0, "Notice")
        return []

    # Use drawing name as copy naming base
    copy_base = extract_copy_base_name(source_name)

    # Switch to source Layout, select all objects, copy to clipboard (once)
    rs.CurrentView(source_name)
    sc.doc.Views.ActiveView = source_view
    rs.UnselectAllObjects()
    for oid in source_obj_ids:
        rs.SelectObject(oid)
    Rhino.RhinoApp.RunScript("_-CopyToClipboard 0,0,0", True)
    rs.UnselectAllObjects()

    created_names = []

    for i in range(1, count + 1):
        new_name = generate_unique_name(copy_base, i)

        new_page = sc.doc.Views.AddPageView(new_name, page_width, page_height)
        if new_page is None:
            print("  Warning: Could not create copy #{}.".format(i))
            continue

        # Delete auto-generated default Detail on new page
        delete_default_details(new_page)

        # Switch to new Layout and paste
        rs.CurrentView(new_name)
        sc.doc.Views.ActiveView = new_page
        Rhino.RhinoApp.RunScript("_-Paste 0,0,0", True)
        rs.UnselectAllObjects()

        new_objs = get_page_object_ids(new_page)
        obj_count = len(new_objs)

        created_names.append(new_name)
        print("  Created '{}' (objects: {})".format(new_name, obj_count))

    try:
        rs.CurrentView(source_name)
    except:
        pass

    sc.doc.Views.Redraw()
    return created_names


def main():
    layout_names = get_layout_names()

    if not layout_names:
        rs.MessageBox(
            "No Layouts found in the current document.\nPlease create at least one Layout first.",
            0,
            "Notice",
        )
        return

    selected = rs.ListBox(
        layout_names, "Select Layout to duplicate:", "LF_Duplicate_Layout"
    )
    if selected is None:
        print("User cancelled operation.")
        return

    count = rs.GetInteger("Enter number of copies", 1, 1, 100)
    if count is None:
        print("User cancelled operation.")
        return

    print("=" * 50)
    print("LF_Duplicate_Layout v1.4")
    print("Source: {}  Copies: {}".format(selected, count))
    print("=" * 50)

    result = duplicate_layout(selected, count)

    if result:
        msg = "Successfully duplicated {} Layouts:\n\n".format(len(result))
        for name in result:
            msg += "  • {}\n".format(name)
        rs.MessageBox(msg, 0, "LF_Duplicate_Layout Complete")
        print("\nDone! Duplicated {} Layouts.".format(len(result)))
    else:
        rs.MessageBox("No Layouts could be created during the copy process.", 0, "Notice")


if __name__ == "__main__":
    main()
