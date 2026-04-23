# -*- coding: utf-8 -*-
# Script: LF_Push_3D_to_JSON.py (3D Object Attribute Full-Push Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Registry.py, _LF_Debug.py, _LoopFlow_Config.py
# Usage: Scans all solid objects under M3D layers in 3D.3dm that have a _03_ attribute,
#           and full-pushes UUID + complete UserText snapshots to Project_Registry.json (Objects section).
#           Can be called automatically by LF_Nexus Tag Trigger, or run standalone in 3D.3dm.

# ==================================================================
# Imports
# ==================================================================
import os
import sys
import time
import importlib
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

# ==================================================================
# Config Reload & Aliases
# ==================================================================
import _LoopFlow_Config as _CFG
importlib.reload(_CFG)
LAYER_PREFIX_3D   = _CFG.LAYER_PREFIX_3D
LAYER_DATA_SUFFIX = _CFG.LAYER_DATA_SUFFIX
_PREFIX_WITH_SEP    = LAYER_PREFIX_3D + "::"
_DATA_PATH_FRAGMENT = "::" + LAYER_DATA_SUFFIX + "::"
_DATA_PATH_PREFIX   = LAYER_DATA_SUFFIX + "::"

# ==================================================================
# Layer Utilities
# ==================================================================
def _is_data_layer(layer_name):
    if not layer_name: return False
    if layer_name == LAYER_PREFIX_3D + "::" + LAYER_DATA_SUFFIX: return True
    return _DATA_PATH_FRAGMENT in layer_name or layer_name.startswith(_DATA_PATH_PREFIX)

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
    except NameError:
        return False
    if script_dir not in sys.path:
        sys.path.append(script_dir)
    return True

def get_project_dir():
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc or not doc.Path:
        rs.MessageBox(u"Please save the 3D file first!", 48, u"Warning")
        return None
    return os.path.dirname(doc.Path)

# ==================================================================
# Core Push Logic
# ==================================================================
def push_3d_data():
    try:
        print(u"\n" + "="*35)
        print(u"LF_Push_3D_to_JSON [Full Attribute Push] started...")
        print(u"="*35)

        if not setup_environment():
            return
        proj_dir = get_project_dir()
        if not proj_dir:
            return

        VALID_GEOMETRY_TYPES = [
            Rhino.DocObjects.ObjectType.Surface,
            Rhino.DocObjects.ObjectType.Brep,
            Rhino.DocObjects.ObjectType.Mesh,
            Rhino.DocObjects.ObjectType.InstanceReference,
            Rhino.DocObjects.ObjectType.Extrusion
        ]

        all_objects        = sc.doc.Objects
        objects_to_push    = {}
        missing_uuid_objs  = []
        count_in_prefix = count_success = total_attributes = 0

        _id_col_prefix = "_03_"

        print(u" Scanning all {} layers globally (including hidden and locked objects)...".format(LAYER_PREFIX_3D))

        for obj in all_objects:
            layer_index = obj.Attributes.LayerIndex
            if layer_index < 0: continue
            layer_name = sc.doc.Layers[layer_index].FullPath

            if not layer_name.startswith(_PREFIX_WITH_SEP): continue
            if _is_data_layer(layer_name): continue

            count_in_prefix += 1

            if obj.ObjectType not in VALID_GEOMETRY_TYPES: continue

            obj_id   = obj.Id
            all_keys = rs.GetUserText(obj_id) or []
            id_key   = next((k for k in all_keys if k.startswith(_id_col_prefix)), None)
            id_num   = rs.GetUserText(obj_id, id_key) if id_key else None
            uuid_raw = rs.GetUserText(obj_id, "_12_UUID")

            if id_num is not None and str(id_num).strip() == "-": continue
            if not uuid_raw or not uuid_raw.strip():
                missing_uuid_objs.append(obj_id)
                continue

            clean_uuid = uuid_raw.strip()
            obj_data   = {"Layer": layer_name, "Update_Time": time.time()}

            for k in all_keys:
                obj_data[k] = rs.GetUserText(obj_id, k)
                total_attributes += 1

            objects_to_push[clean_uuid] = obj_data
            count_success += 1

        print(u" --- Push Report ---")
        print(u"  └ {} qualifying objects total: {}".format(LAYER_PREFIX_3D, count_in_prefix))
        print(u"  └ Successfully inventoried: {}".format(count_success))
        print(u"  └ Total attribute records captured: {}".format(total_attributes))

        if missing_uuid_objs:
            rs.UnselectAllObjects()
            rs.SelectObjects(missing_uuid_objs)
            rs.MessageBox(u"Found {} objects with missing UUIDs! Run LF_Nexus to fix them.".format(len(missing_uuid_objs)), 48)
            return

        if not objects_to_push:
            rs.MessageBox(u"No valid objects found to push.\nPlease confirm:\n  1. Objects are under the {} layer\n  2. LF_Nexus \u2192 TagTrigger has been run to write _12_UUID".format(LAYER_PREFIX_3D), 48)
            return

        try:
            import _LF_Registry as _REG
            importlib.reload(_REG)
            registry = _REG.RegistryCenter(proj_dir)

            # Try once, then offer retry / force-unlock on failure. Typical cause
            # on Dropbox/OneDrive folders is a stale .lock file left by a crashed
            # session or a transient cloud-sync hold.
            success = registry.push_3d_objects(objects_to_push)
            if not success:
                for _attempt in range(3):
                    lock_path = registry.lock_path
                    prompt = (u"Failed to write JSON.\n\n"
                              u"The registry lock file is still present:\n  {}\n\n"
                              u"This often happens when the project sits in a cloud-sync folder\n"
                              u"(Dropbox / OneDrive) or a previous Rhino session crashed.\n\n"
                              u"[Yes]    Force unlock and retry\n"
                              u"[No]     Retry (wait for the lock to clear)\n"
                              u"[Cancel] Abort push").format(lock_path)
                    ans = rs.MessageBox(prompt, 3 | 48, u"Registry Locked")
                    if ans == 6:
                        registry.force_unlock()
                        success = registry.push_3d_objects(objects_to_push)
                    elif ans == 7:
                        success = registry.push_3d_objects(objects_to_push)
                    else:
                        break
                    if success:
                        break

            if success:
                rs.MessageBox(u"JSON Sync Successful!\n\nSuccessfully pushed {} solid objects to the project database.\nThe 2D Infuser can now access the latest data!".format(count_success), 64, u"Sync Complete")
            else:
                rs.MessageBox(u"Failed to write JSON after multiple retries.\n\nLock file: {}\n\nManually delete the .lock file after confirming no other Rhino instance is writing, then push again.".format(registry.lock_path), 16)
        except Exception as e:
            if log_exception: print(log_exception(u"LF_Push_3D_to_JSON.RegistryWrite", e))
            rs.MessageBox(u"Registry write failed:\n{}\n\nSee debug log: {}".format(str(e), _DEBUG_LOG_PATH), 16)

    except Exception as e:
        if log_exception: print(log_exception(u"LF_Push_3D_to_JSON.push_3d_data", e))
        rs.MessageBox(u"Push process encountered an unexpected error.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    push_3d_data()
