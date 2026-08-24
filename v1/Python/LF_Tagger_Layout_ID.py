# -*- coding: utf-8 -*-
# Script: LF_Tagger_Layout_ID.py (Layout Drawing Auto-Numbering Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Registry.py, _LF_NamingRules.py, _LF_Debug.py, _LoopFlow_Config.py
# Usage: Run in 2D.3dm; follows the layout naming convention (format: DrawingNo__DrawingName)
#        to auto-calculate drawing numbers and write DWG_NO / DWG_NAME UserText into the title block,
#        and push Layout_Map to Project_Registry.json.
#        Naming rules are loaded from NamingRules_Config.json in the project directory;
#        falls back to _LoopFlow_Config.py defaults if the file is missing.

# ==================================================================
# Imports
# ==================================================================
import os
import sys
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

try:
    from _LoopFlow_Config import (
        INDEX_BLOCKS, HEIGHT_BLOCKS, FINISH_BLOCKS, DW_BLOCKS, ITEM_BLOCKS
    )
except Exception:
    INDEX_BLOCKS  = ["TAG_SECTION_DETAIL", "TAG_ELEV_1", "TAG_ELEV_2", "TAG_ELEV_3", "TAG_ELEV_4"]
    HEIGHT_BLOCKS = ["TAG_HEIGHT_GRAB", "TAG_HEIGHT_LASER"]
    FINISH_BLOCKS = ["TAG_FINISH_GRAB", "TAG_FINISH_LASER"]
    DW_BLOCKS     = ["TAG_DW"]
    ITEM_BLOCKS   = ["TAG_ITEM"]

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# Constants: Tag Type Aggregation
# ==================================================================
DATA_TAGS_ALL = HEIGHT_BLOCKS + FINISH_BLOCKS + DW_BLOCKS + ITEM_BLOCKS
INDEX_TAGS   = INDEX_BLOCKS
ELEV_0_TAGS  = ["TAG_ELEV_0"]

# ==================================================================
# Environment Helpers
# ==================================================================
def setup_environment():
    try:
        script_dir = os.path.dirname(os.path.realpath(__file__))
        if script_dir not in sys.path: sys.path.append(script_dir)
        return script_dir
    except: return None

def get_project_dir():
    doc = Rhino.RhinoDoc.ActiveDoc
    if not doc or not doc.Path:
        rs.MessageBox(u"[!] Please save the Rhino file first to locate the project path!", 48, u"Path Not Found")
        return None
    return os.path.dirname(doc.Path)

def load_naming_rules(project_dir):
    """Load the naming rules manager. Returns (rules, module) or (None, None) on failure."""
    try:
        import importlib
        import _LF_NamingRules as _NR
        importlib.reload(_NR)
        return _NR.NamingRulesManager(project_dir), _NR
    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_Tagger_Layout_ID.load_naming_rules", e))
        rs.MessageBox(
            u"[!] Failed to load _LF_NamingRules:\n{}".format(e),
            16, u"Module Error"
        )
        return None, None

# ==================================================================
# UI: Naming Rule Info
# ==================================================================
def show_naming_rules(rules):
    sep      = rules.separator
    baseline = rules.baseline_mark
    rule_text = (
        u"Active naming rules\n"
        u"--------------------------------\n"
        u"{detail}\n"
        u"--------------------------------\n\n"
        u"1. Separator\n"
        u"   Use '{sep}' to separate drawing number and name\n"
        u"   Format: DrawingNo{sep}DrawingName\n"
        u"   Example: IN 101.01{sep}Floor Plan\n\n"
        u"2. Baseline Layout ({bm})\n"
        u"   Layouts containing {bm} are 'Baseline Layouts', starting a new series\n\n"
        u"3. Pre-series Layouts\n"
        u"   Layouts before the first {bm} are not auto-numbered\n\n"
        u"4. No-{bm} mode\n"
        u"   If no {bm} baseline layouts exist, all pages switch to manual parsing mode\n\n"
        u"Tip: edit NamingRules_Config.json in the project directory to customize these rules."
    ).format(detail=rules.describe(), sep=sep, bm=baseline)
    rs.MessageBox(rule_text, 64, u"Naming Rules")

def create_config_template(proj_dir, module_ref):
    if module_ref is None:
        rs.MessageBox(u"[!] _LF_NamingRules module not loaded.", 16, u"Module Error")
        return
    ok, info = module_ref.write_template(proj_dir)
    if ok:
        rs.MessageBox(
            u"Naming rules template created:\n\n{}\n\nEdit it with any text editor, then rerun this tool.".format(info),
            64, u"Template Created"
        )
    else:
        rs.MessageBox(u"[!] {}".format(info), 48, u"Template Not Created")

# ==================================================================
# Main Runner
# ==================================================================
def run_tagger_layout_id():
    try:
        proj_dir = get_project_dir()
        if not proj_dir: return

        rules, nr_module = load_naming_rules(proj_dir)
        if rules is None: return

        action = rs.GetString(
            u"LF_Tagger_Layout_ID", "Run",
            ["Run", "Rule", "CreateTemplate"]
        )
        if action is None: return
        action_up = action.upper()
        if action_up == "RULE":
            show_naming_rules(rules)
            return
        if action_up == "CREATETEMPLATE":
            create_config_template(proj_dir, nr_module)
            return

        print(u"\n" + "="*40)
        print(u"LF_Tagger_Layout_ID [v1.0] started...")
        print(u"="*40)
        print(u" Rule source: {}".format(u"Project config file" if rules.source == "json" else u"Built-in defaults"))
        if rules.warnings:
            for w in rules.warnings:
                print(u" [Warning] {}".format(w))

        page_views_raw = sc.doc.Views.GetPageViews()
        if not page_views_raw:
            rs.MessageBox(u"[!] No Layout pages found!", 48, u"No Layouts")
            return

        page_views = sorted(page_views_raw, key=lambda v: v.PageNumber)
        start_idx  = next(
            (i for i, v in enumerate(page_views) if rules.baseline_mark in v.PageName),
            -1
        )

        if start_idx == -1:
            print(u" [Note] No baseline drawing containing '{}' found; switching to manual parsing mode.".format(rules.baseline_mark))
            start_idx = len(page_views)

        current_prefix = ""
        current_major  = 0
        current_minor  = 1
        layout_data_map = {}

        print(u" Processing layouts (pre-series/parsed: {}, auto-numbered: {})".format(start_idx, len(page_views) - start_idx))

        for idx, view in enumerate(page_views):
            old_name = view.PageName

            if idx < start_idx:
                if rules.separator in old_name:
                    dwg_no, dwg_name = old_name.split(rules.separator, 1)
                    dwg_no   = dwg_no.strip()
                    dwg_name = dwg_name.strip()
                else:
                    dwg_no   = " "
                    dwg_name = old_name.strip()
                new_full_name = old_name
                category = "-"
                ref_id   = "-"
                print(u"  [Parsed] {} -> writing to title block".format(new_full_name))
            else:
                baseline, parsed_cat, parsed_major = rules.is_new_baseline(
                    old_name, current_prefix, current_major
                )
                if baseline:
                    current_prefix = parsed_cat
                    current_major  = parsed_major
                    current_minor  = 1

                dwg_name      = rules.extract_dwg_name(old_name)
                dwg_no        = rules.format_dwg_no(current_prefix, current_major, current_minor)
                ref_id        = rules.format_ref_id(current_major, current_minor)
                category      = current_prefix
                new_full_name = rules.combine_full_name(dwg_no, dwg_name)

                tag = u"Baseline" if baseline else u"Numbered"
                print(u"  [{}] {} -> {}".format(tag, old_name, new_full_name))
                current_minor += 1

            if old_name != new_full_name:
                view.PageName = new_full_name

            layout_data_map[new_full_name] = {
                "Category": category,
                "DWG_NO":   dwg_no,
                "DWG_NAME": dwg_name,
                "REF_ID":   ref_id
            }

            layout_objs = [obj for obj in sc.doc.Objects if obj.Attributes.ViewportId == view.MainViewport.Id]

            for obj in layout_objs:
                if obj.ObjectType == Rhino.DocObjects.ObjectType.InstanceReference:
                    bname = rs.BlockInstanceName(obj).upper()

                    if bname in DATA_TAGS_ALL:
                        for k in ["DWG_NAME", "DWG_NO", "REF_ID", "Category"]:
                            rs.SetUserText(obj, k, None)
                    elif bname in INDEX_TAGS:
                        for k in ["DWG_NAME", "DWG_NO"]:
                            rs.SetUserText(obj, k, None)
                    elif bname in ELEV_0_TAGS:
                        for k in ["DWG_NAME", "DWG_NO", "REF_ID"]:
                            rs.SetUserText(obj, k, None)
                        rs.SetUserText(obj, "Category", category)
                    else:
                        rs.SetUserText(obj, "DWG_NO",   dwg_no)
                        rs.SetUserText(obj, "DWG_NAME", dwg_name)
                        for k in ["Category", "REF_ID"]:
                            rs.SetUserText(obj, k, None)

        try:
            import importlib
            import _LF_Registry as _REG
            importlib.reload(_REG)
            registry = _REG.RegistryCenter(proj_dir)
            success  = registry.push_layout_map(layout_data_map)

            if success:
                msg = u" Layout parsing and sync complete!\n\nProcessed {} Layouts; excess attributes cleaned up.".format(len(page_views))
                rs.MessageBox(msg, 64, u"Sync Successful")
            else:
                rs.MessageBox(u"[!] Failed to write JSON! The file may be locked.", 16, u"Write Error")

        except Exception as e:
            if log_exception: print(log_exception(u"LF_Tagger_Layout_ID.RegistryWrite", e))
            rs.MessageBox(u"[!] Execution exception:\n{}\n\nSee debug log: {}".format(e, _DEBUG_LOG_PATH), 16, u"Error")

    except Exception as e:
        if log_exception: print(log_exception(u"LF_Tagger_Layout_ID.run_tagger_layout_id", e))
        rs.MessageBox(u"[!] Unexpected error in drawing numbering workflow.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16, u"Error")

if __name__ == "__main__":
    run_tagger_layout_id()
