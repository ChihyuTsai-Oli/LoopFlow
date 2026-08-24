# -*- coding: utf-8 -*-
# Script: _LF_Debug.py (LoopFlow Exception Logger)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: None (referenced by all other LoopFlow scripts)
# Usage: For all LoopFlow scripts to call log_exception() after import,
#           which writes exceptions and tracebacks to cursor_LF_debug_log.txt.
#           Not intended for direct execution.
# ==================================================================
# Imports
# ==================================================================
from __future__ import absolute_import

import datetime
import io
import os
import traceback

try:
    from _LoopFlow_Config import DEBUG_LOG_FILENAME as _LOG_FILENAME
except Exception:
    _LOG_FILENAME = "cursor_LF_debug_log.txt"

# ==================================================================
# Constants: Log Path
# ==================================================================
_SCRIPT_DIR   = os.path.dirname(os.path.realpath(__file__))
_TOOLS_DIR    = os.path.dirname(_SCRIPT_DIR)
DEBUG_LOG_PATH = os.path.join(_TOOLS_DIR, _LOG_FILENAME)


# ==================================================================
# Internal Helpers
# ==================================================================
def _now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ==================================================================
# Public API
# ==================================================================
def log_exception(context, exc=None):
    try:
        header = u"[{}] [LF_EXCEPTION] {}\n".format(_now_str(), context)
        if exc is not None:
            detail = u"Exception: {}\n".format(repr(exc))
        else:
            detail = u"Exception: (no exception object)\n"
        tb = traceback.format_exc()
        body = header + detail + tb + u"\n" + (u"-" * 70) + u"\n"

        parent = os.path.dirname(DEBUG_LOG_PATH)
        if parent and not os.path.exists(parent):
            os.makedirs(parent)

        with io.open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(body)

        return body
    except Exception:
        return u"[{}] [LF_EXCEPTION] {} (log write failed)\n".format(_now_str(), context)
