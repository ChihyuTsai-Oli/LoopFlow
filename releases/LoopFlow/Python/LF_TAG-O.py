# -*- coding: utf-8 -*-
# Script: LF_TAG-O.py (Tag Block Broken-Link Audit Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LF_Registry.py, _LF_Debug.py, _LoopFlow_Config.py
# Usage: Run in 2D.3dm (run LF_Infuser_All first so colour flags are active).
#           Scans Tag Blocks across all Layouts and reports via a colour-coded Eto panel:
#           (1) unbound (orange) / broken-link (red) tag list;
#           (2) spaces in Space_Boundaries not covered by any FINISH tag.

# ==================================================================
# Imports
# ==================================================================
import os
import sys
import time
import Rhino
import Rhino.UI
import rhinoscriptsyntax as rs
import scriptcontext as sc
import Eto.Forms as forms
import Eto.Drawing as drawing

try:
    _script_dir = os.path.dirname(os.path.realpath(__file__))
except NameError:
    _script_dir = ""
if _script_dir and _script_dir not in sys.path:
    sys.path.append(_script_dir)

try:
    from _LoopFlow_Config import LAYER_SPACE_BOUNDARIES
except Exception:
    LAYER_SPACE_BOUNDARIES = "M3D::_Data::Space_Boundaries"

try:
    from _LF_Debug import log_exception
except Exception:
    log_exception = None

try:
    from _LF_Registry import RegistryCenter
except Exception:
    RegistryCenter = None

try:
    from LF_Infuser_Part import (
        WARNING_COLOR, BROKEN_COLOR,
        INDEX_BLOCKS, DATA_BLOCKS
    )
except Exception:
    from System.Drawing import Color as _SysColor
    WARNING_COLOR = _SysColor.FromArgb(255, 255, 130, 46)
    BROKEN_COLOR  = _SysColor.FromArgb(255, 255, 46, 97)
    INDEX_BLOCKS  = ["TAG_SECTION_DETAIL", "TAG_ELEV_1", "TAG_ELEV_2", "TAG_ELEV_3", "TAG_ELEV_4"]
    DATA_BLOCKS   = ["TAG_HEIGHT_GRAB", "TAG_HEIGHT_LASER", "TAG_FINISH_GRAB", "TAG_FINISH_LASER", "TAG_DW", "TAG_ITEM"]

# ==================================================================
# Constants & Eto Color Palette
# ==================================================================
FINISH_BLOCKS_SET = {"TAG_FINISH_GRAB", "TAG_FINISH_LASER"}
ALL_TAG_BLOCKS_SET = set(INDEX_BLOCKS) | set(DATA_BLOCKS)

_C_BG   = drawing.Color.FromArgb(30, 30, 30)
_C_TEXT = drawing.Color.FromArgb(220, 220, 220)
_C_DIM  = drawing.Color.FromArgb(120, 120, 120)
_C_HEAD = drawing.Color.FromArgb(140, 190, 240)
_C_OK   = drawing.Color.FromArgb(90, 200, 120)
_C_WARN = drawing.Color.FromArgb(255, 130, 46)
_C_BROK = drawing.Color.FromArgb(255, 46, 97)
_FONT   = drawing.Font("Consolas", 10)


# ==================================================================
# Color Match Utility
# ==================================================================
def _rgb_match(obj_color, sys_color):
    return (obj_color.R == sys_color.R and
            obj_color.G == sys_color.G and
            obj_color.B == sys_color.B)


# ==================================================================
# Tag Binding Status Check
# ==================================================================
def check_tag_status():
    results = []
    try:
        all_pages = sc.doc.Views.GetPageViews()
        if not all_pages:
            return results

        all_inst = sc.doc.Objects.FindByObjectType(
            Rhino.DocObjects.ObjectType.InstanceReference
        )
        if not all_inst:
            return results

        vp_to_name = {pg.MainViewport.Id: pg.PageName for pg in all_pages}

        for obj in all_inst:
            vp_id = obj.Attributes.ViewportId
            if vp_id not in vp_to_name:
                continue

            block_name = obj.InstanceDefinition.Name.upper()
            if block_name not in ALL_TAG_BLOCKS_SET:
                continue

            if (obj.Attributes.ColorSource !=
                    Rhino.DocObjects.ObjectColorSource.ColorFromObject):
                continue

            c = obj.Attributes.ObjectColor
            layout_name = vp_to_name[vp_id]

            if _rgb_match(c, WARNING_COLOR):
                results.append((u"Unbound", block_name, layout_name))
            elif _rgb_match(c, BROKEN_COLOR):
                results.append((u"Broken", block_name, layout_name))

    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_TAG-O.check_tag_status", e))
    return results


# ==================================================================
# Space Coverage Check
# ==================================================================
def check_space_coverage(project_dir):
    all_spaces = set()
    try:
        layer_idx = sc.doc.Layers.FindByFullPath(LAYER_SPACE_BOUNDARIES, -1)
        if layer_idx < 0:
            return [], u"Layer [{}] not found; skipping this check".format(LAYER_SPACE_BOUNDARIES)

        for obj in sc.doc.Objects:
            if obj.Attributes.LayerIndex == layer_idx:
                sname = rs.GetUserText(obj.Id, "Space_Name")
                if sname and sname.strip():
                    all_spaces.add(sname.strip())
    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_TAG-O.check_space_coverage.step1", e))
        return [], u"Error reading space boundaries"

    if not all_spaces:
        return [], u"No spaces defined on Space_Boundaries layer; skipping this check"

    if not project_dir or RegistryCenter is None:
        return sorted(all_spaces), u"Cannot read JSON; space coverage results may be inaccurate"

    src_objects = {}
    json_note = None
    try:
        reg = RegistryCenter(project_dir)
        jdata = reg.get_full_registry()
        src_objects = jdata.get("Objects", {})
        if not src_objects:
            json_note = u"JSON Objects is empty; please run Push to JSON first"
    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_TAG-O.check_space_coverage.json", e))
        json_note = u"JSON read failed; space coverage results may be inaccurate"

    if json_note:
        return sorted(all_spaces), json_note

    covered = set()
    try:
        all_pages = sc.doc.Views.GetPageViews()
        all_inst  = sc.doc.Objects.FindByObjectType(
            Rhino.DocObjects.ObjectType.InstanceReference
        )
        if all_pages and all_inst:
            layout_vp_ids = set(pg.MainViewport.Id for pg in all_pages)

            for obj in all_inst:
                if obj.Attributes.ViewportId not in layout_vp_ids:
                    continue

                if obj.InstanceDefinition.Name.upper() not in FINISH_BLOCKS_SET:
                    continue

                src_uuid = rs.GetUserText(obj.Id, "Source_UUID")
                if not src_uuid or not src_uuid.strip() or src_uuid.strip() == "NAME_PARSED":
                    continue

                obj_data = src_objects.get(src_uuid.strip())
                if not obj_data:
                    continue

                for key, val in obj_data.items():
                    if key.startswith("_01_") and val and val not in ("-", ""):
                        covered.add(val.strip())
                        break
    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_TAG-O.check_space_coverage.step3", e))

    missing = sorted(all_spaces - covered)
    return missing, None


# ==================================================================
# Eto Dialog: Audit Results Panel
# ==================================================================
class AuditorDialog(forms.Dialog[bool]):
    def __init__(self, doc_name, tag_results, space_missing, space_note):
        super().__init__()

        self.Title = u"TAG-O ~ Holy Cargo ~~"
        self.ClientSize = drawing.Size(498, 625)
        self.Padding = drawing.Padding(0)
        self.Resizable = True
        self.BackgroundColor = _C_BG

        self._lines = []
        self._build_content(doc_name, tag_results, space_missing, space_note)

        stack = forms.StackLayout()
        stack.BackgroundColor = _C_BG
        stack.Orientation = forms.Orientation.Vertical
        stack.Padding = drawing.Padding(12)
        stack.Spacing = 1

        for text, color in self._lines:
            lbl = forms.Label()
            lbl.Text = text
            lbl.TextColor = color
            lbl.Font = _FONT
            lbl.BackgroundColor = _C_BG
            stack.Items.Add(forms.StackLayoutItem(lbl))

        scroll = forms.Scrollable()
        scroll.BackgroundColor = _C_BG
        scroll.Content = stack

        self.Content = scroll

        btn_close = forms.Button()
        btn_close.Click += self._on_close
        self.AbortButton = btn_close
        self.DefaultButton = btn_close

    def _line(self, text, color=None):
        self._lines.append((text, color if color is not None else _C_TEXT))

    def _build_content(self, doc_name, tag_results, space_missing, space_note):
        now_str = time.strftime(u"%Y-%m-%d  %H:%M:%S")

        self._line(u"TAG-O ~ Holy Cargo ~~", _C_HEAD)
        self._line(u"File: {}".format(doc_name), _C_DIM)
        self._line(u"Scanned: {}".format(now_str), _C_DIM)
        self._line(u"")

        cnt_w = sum(1 for s, _, _ in tag_results if s == u"Unbound")
        cnt_b = sum(1 for s, _, _ in tag_results if s == u"Broken")
        total_b = cnt_w + cnt_b

        if total_b > 0:
            self._line(u"── Tag Binding Status  ({} issues) ──".format(total_b), _C_HEAD)
        else:
            self._line(u"── Tag Binding Status ──", _C_HEAD)

        if not tag_results:
            self._line(u"  All tags bound correctly", _C_OK)
        else:
            sorted_tags = sorted(tag_results, key=lambda x: (x[2], x[0] != u"Broken"))
            col_w = max(len(b) for _, b, _ in sorted_tags)
            for status, bname, lname in sorted_tags:
                color = _C_BROK if status == u"Broken" else _C_WARN
                self._line(
                    u"  [{}]  {}  ->  {}".format(status, bname.ljust(col_w), lname),
                    color
                )

        self._line(u"")

        total_c = len(space_missing)

        if total_c > 0:
            self._line(u"── Uncovered Spaces  ({} spaces) ──".format(total_c), _C_HEAD)
        else:
            self._line(u"── Uncovered Spaces ──", _C_HEAD)

        if space_note:
            self._line(u"  [Note] {}".format(space_note), _C_DIM)

        if not space_missing:
            if not space_note:
                self._line(u"  All spaces are covered by finish tags", _C_OK)
        else:
            for sp in space_missing:
                self._line(u"  {}".format(sp), _C_TEXT)

    def _on_close(self, sender, e):
        self.Close(True)


def main():
    print(u"\n--- LF TAG-O ---")
    try:
        doc = Rhino.RhinoDoc.ActiveDoc
        if not doc or not doc.Path:
            rs.MessageBox(
                u"Please save the Rhino file before running.",
                48, u"LF TAG-O"
            )
            return

        doc_name    = os.path.basename(doc.Path)
        project_dir = os.path.dirname(doc.Path)

        print(u"  Scanning tag binding status...")
        tag_results = check_tag_status()

        print(u"  Scanning for uncovered spaces...")
        space_missing, space_note = check_space_coverage(project_dir)

        total = len(tag_results) + len(space_missing)
        print(u"  Done. Total issues: {}".format(total))

        dlg = AuditorDialog(doc_name, tag_results, space_missing, space_note)
        dlg.ShowModal(Rhino.UI.RhinoEtoApp.MainWindow)

    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_TAG-O.main", e))
        rs.MessageBox(
            u"Execution failed; see debug log.\n{}".format(str(e)),
            16, u"LF TAG-O"
        )


if __name__ == "__main__":
    main()
