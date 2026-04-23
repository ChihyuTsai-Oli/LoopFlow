# -*- coding: utf-8 -*-
# Script: LF_Dictionary_Editor.py (LoopFlow Dictionary File Quick Opener)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: Run in 3D.3dm or 2D.3dm; auto-locates and opens
#           LoopFlow_Dictionary.xlsx (same folder as the .3dm) for direct editing in Excel.

# ==================================================================
# Imports
# ==================================================================
import rhinoscriptsyntax as rs
import os
import sys
import subprocess

try:
    from _LoopFlow_Config import DICTIONARY_FILENAME_XLSX
except Exception:
    DICTIONARY_FILENAME_XLSX = "LoopFlow_Dictionary.xlsx"

try:
    from _LF_Debug import log_exception
except Exception:
    log_exception = None

# ==================================================================
# Constants
# ==================================================================
TARGET_FILE = DICTIONARY_FILENAME_XLSX

def main():
    try:
        print(u"--- Opening {} ---".format(TARGET_FILE))

        doc_full_path = rs.DocumentPath()

        if not doc_full_path:
            rs.MessageBox(u"Please save the current Rhino file so the system can locate the dictionary folder!", 48, u"LoopFlow System Notice")
            return

        doc_dir = os.path.dirname(doc_full_path)
        full_path = os.path.join(doc_dir, TARGET_FILE)

        if not os.path.exists(full_path):
            error_msg = u"Dictionary file not found: {}\n\nPlease confirm the Excel file is in the following directory:\n{}".format(TARGET_FILE, doc_dir)
            rs.MessageBox(error_msg, 16, u"File Missing")
            return

        if sys.platform.startswith('win'):
            os.startfile(full_path)
        elif sys.platform.startswith('darwin'):
            subprocess.call(('open', full_path))
        else:
            subprocess.call(('xdg-open', full_path))

        print(u"Success! After editing in Excel, save and close it, then re-run the sync script.")

    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_Dictionary_Editor.main", e))
        rs.MessageBox(u"Cannot open file. Error:\n{}".format(e), 16, u"System Error")

if __name__ == "__main__":
    main()
