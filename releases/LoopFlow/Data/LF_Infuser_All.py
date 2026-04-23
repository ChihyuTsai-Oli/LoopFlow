# -*- coding: utf-8 -*-
# Script: LF_Infuser_All.py (All-Layout Attribute Batch Infuser)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: LF_Infuser_Part.py, _LF_Registry.py, _LF_Debug.py, _LoopFlow_Config.py
# Usage: Run in 2D.3dm; batch-calls LF_Infuser_Part.infuse_layout() for every Layout page,
#           injecting attributes from Project_Registry.json into all Tag Blocks.
#           Displays per-layout injection statistics (updated/skipped/broken/locked counts) when done.

# ==================================================================
# Imports
# ==================================================================
import os
import sys
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"


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
    if not doc or not doc.Path:
        rs.MessageBox(u"Please save the file first!", 48)
        return None
    return os.path.dirname(doc.Path)


# ==================================================================
# All-Layouts Runner
# ==================================================================
def run_infuser_all():
    try:
        print(u"\n" + "="*40)
        print(u"LF_Infuser_All [v2.1] started...")
        print(u"="*40)

        if not setup_environment():
            return
        proj_dir = get_project_dir()
        if not proj_dir:
            return

        page_views = sc.doc.Views.GetPageViews()
        if not page_views:
            rs.MessageBox(u"No Layouts found in this file!", 48)
            return

        print(u" Reading JSON registry...")
        try:
            import importlib
            import _LF_Registry as _REG
            importlib.reload(_REG)
            registry = _REG.RegistryCenter(proj_dir)
            json_data = registry.get_full_registry()
            db = json_data.get("Objects", {})
        except Exception as e:
            if log_exception:
                print(log_exception(u"LF_Infuser_All.ReadRegistry", e))
            rs.MessageBox(u"Failed to read database.", 16)
            return

        import importlib
        import LF_Infuser_Part as _bip_module
        importlib.reload(_bip_module)
        from LF_Infuser_Part import infuse_layout

        total_success = total_unbound = total_broken = total_locked = 0

        rs.EnableRedraw(False)
        all_blocks = sc.doc.Objects.FindByObjectType(Rhino.DocObjects.ObjectType.InstanceReference)

        print(u" Scanning all pages ({} layouts)...".format(len(page_views)))

        for page in page_views:
            vp_id = page.MainViewport.Id
            layout_objs = [b.Id for b in all_blocks if b.Attributes.ViewportId == vp_id]
            if not layout_objs:
                continue

            s, u_, b, l = infuse_layout(layout_objs, db, page_views)
            total_success += s
            total_unbound += u_
            total_broken += b
            total_locked += l

        rs.EnableRedraw(True)
        sc.doc.Views.Redraw()

        print(u" --- Processing complete ---")
        msg = u"Full-file Layout Update Complete!\n\nScanned {} Layouts\nSuccessfully synced: {} tags".format(len(page_views), total_success)
        if total_locked > 0:
            msg += u"\nLocked: {} tags (write-protect triggered)".format(total_locked)
        if total_unbound > 0:
            msg += u"\nUnbound: {} tags (orange – run Tagger to bind)".format(total_unbound)
        if total_broken > 0:
            msg += u"\nBroken: {} tags (red – source lost or JSON not re-pushed)".format(total_broken)
        if total_unbound > 0 or total_broken > 0:
            rs.MessageBox(msg, 48, u"Global Injection Report")
        else:
            rs.MessageBox(msg, 64, u"Update Complete")

    except Exception as e:
        try:
            rs.EnableRedraw(True)
        except Exception:
            pass
        if log_exception:
            print(log_exception(u"LF_Infuser_All.run_infuser_all", e))
        rs.MessageBox(u"Unexpected error in global injection.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)


if __name__ == "__main__":
    run_infuser_all()
