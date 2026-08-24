# -*- coding: utf-8 -*-
# Script: _LF_NamingRules.py (Layout Naming Rules Manager)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, LF_Tagger_Layout_ID.py, _LF_Debug.py
# Usage: Provides the NamingRulesManager class that encapsulates reading
#        and parsing of Layout naming rules. Prefers NamingRules_Config.json
#        in the project directory; if missing or malformed, falls back to
#        the defaults defined in _LoopFlow_Config.py.
#        Not intended to be executed directly.

# ==================================================================
# Imports
# ==================================================================
import os
import io
import json
import re

try:
    from _LoopFlow_Config import LAYOUT_NAME_SEPARATOR, LAYOUT_BASELINE_MARK
except Exception:
    LAYOUT_NAME_SEPARATOR = "__"
    LAYOUT_BASELINE_MARK  = ".01"

try:
    from _LF_Debug import log_exception
except Exception:
    log_exception = None

# ==================================================================
# Constants
# ==================================================================
NAMING_RULES_FILENAME = "NamingRules_Config.json"

DEFAULT_DWG_NO_FORMAT  = u"{prefix} {major:03d}.{minor:02d}"
DEFAULT_REF_ID_FORMAT  = u"{major:03d}.{minor:02d}"
DEFAULT_PREFIX_PATTERN = r"([A-Za-z\s]+?)[\s]*(\d+)$"

# ==================================================================
# NamingRulesManager Class
# ==================================================================
class NamingRulesManager(object):
    """Central manager for Layout naming rules.

    Attributes:
        separator       : separator between drawing number and drawing name
        baseline_mark   : token identifying a series baseline drawing
        dwg_no_format   : DWG_NO format template (supports prefix/major/minor)
        ref_id_format   : REF_ID format template (supports major/minor)
        prefix_pattern  : regex splitting "prefix + major number"
        source          : 'json' or 'default', indicates rule origin
        config_path     : actual JSON path loaded (if any)
        warnings        : list of warnings raised during initialization
    """

    def __init__(self, project_dir=None):
        self.separator       = LAYOUT_NAME_SEPARATOR
        self.baseline_mark   = LAYOUT_BASELINE_MARK
        self.dwg_no_format   = DEFAULT_DWG_NO_FORMAT
        self.ref_id_format   = DEFAULT_REF_ID_FORMAT
        self.prefix_pattern  = DEFAULT_PREFIX_PATTERN

        self.source      = "default"
        self.config_path = None
        self.warnings    = []

        self._prefix_regex = None
        if project_dir:
            self._load_from_project(project_dir)
        self._compile_regex()

# ==================================================================
#   Loader
# ==================================================================
    def _load_from_project(self, project_dir):
        config_path = os.path.join(project_dir, NAMING_RULES_FILENAME)
        if not os.path.exists(config_path):
            return

        self.config_path = config_path
        try:
            with io.open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except ValueError as e:
            # JSON parse error: ValueError covers json.JSONDecodeError (Python 3.5+)
            self.warnings.append(u"Malformed JSON; falling back to default rules: {}".format(e))
            if log_exception:
                print(log_exception(u"_LF_NamingRules._load_from_project.ValueError", e))
            return
        except Exception as e:
            self.warnings.append(u"Failed to read config; falling back to default rules: {}".format(e))
            if log_exception:
                print(log_exception(u"_LF_NamingRules._load_from_project", e))
            return

        if not isinstance(data, dict):
            self.warnings.append(u"Config root is not an object; falling back to default rules.")
            return

        self._apply_overrides(data)
        self.source = "json"

    def _apply_overrides(self, data):
        mapping = [
            ("separator",       "separator"),
            ("baseline_mark",   "baseline_mark"),
            ("dwg_no_format",   "dwg_no_format"),
            ("ref_id_format",   "ref_id_format"),
            ("prefix_pattern",  "prefix_pattern"),
        ]
        for key, attr in mapping:
            if key in data and isinstance(data[key], str) and data[key].strip() != "":
                setattr(self, attr, data[key])

    def _compile_regex(self):
        try:
            self._prefix_regex = re.compile(self.prefix_pattern)
        except re.error as e:
            self.warnings.append(
                u"Failed to compile prefix regex '{}'; using default: {}".format(self.prefix_pattern, e)
            )
            self.prefix_pattern = DEFAULT_PREFIX_PATTERN
            self._prefix_regex  = re.compile(DEFAULT_PREFIX_PATTERN)

# ==================================================================
#   Public API
# ==================================================================
    def parse_prefix(self, name):
        """Extract (prefix, major) from a baseline drawing name.

        Example: 'IN 101.01__Floor Plan' -> ('IN', 101).
        Returns (None, None) on failure.
        """
        if not name or self.baseline_mark not in name:
            return None, None
        prefix_part = name.split(self.baseline_mark, 1)[0].strip()
        match = self._prefix_regex.search(prefix_part)
        if match:
            try:
                return match.group(1).strip(), int(match.group(2))
            except (IndexError, ValueError):
                return None, None
        return None, None

    def is_new_baseline(self, name, current_prefix, current_major):
        """Return whether this Layout starts a new series."""
        if self.baseline_mark not in name:
            return False, None, None
        cat, major = self.parse_prefix(name)
        if cat is None or major is None:
            return False, None, None
        if cat != current_prefix or major > current_major:
            return True, cat, major
        return False, cat, major

    def extract_dwg_name(self, name):
        """Extract the drawing-name portion from 'DWG_NO__DWG_NAME'."""
        if self.separator in name:
            return name.split(self.separator, 1)[1].strip()
        return name.strip()

    def format_dwg_no(self, prefix, major, minor):
        """Assemble DWG_NO using dwg_no_format."""
        try:
            return self.dwg_no_format.format(prefix=prefix, major=major, minor=minor)
        except (KeyError, IndexError, ValueError) as e:
            if log_exception:
                print(log_exception(u"_LF_NamingRules.format_dwg_no", e))
            return DEFAULT_DWG_NO_FORMAT.format(prefix=prefix, major=major, minor=minor)

    def format_ref_id(self, major, minor):
        """Assemble REF_ID using ref_id_format."""
        try:
            return self.ref_id_format.format(major=major, minor=minor)
        except (KeyError, IndexError, ValueError) as e:
            if log_exception:
                print(log_exception(u"_LF_NamingRules.format_ref_id", e))
            return DEFAULT_REF_ID_FORMAT.format(major=major, minor=minor)

    def combine_full_name(self, dwg_no, dwg_name):
        """Combine the full Layout name: DWG_NO + separator + DWG_NAME."""
        if dwg_name:
            return u"{}{}{}".format(dwg_no, self.separator, dwg_name)
        return dwg_no

# ==================================================================
#   Template / Description
# ==================================================================
    def describe(self):
        """Return a human-readable summary of the active rules."""
        src = u"Project config file" if self.source == "json" else u"Built-in defaults"
        lines = [
            u"Rule source: {}".format(src),
        ]
        if self.config_path:
            lines.append(u"Config path: {}".format(self.config_path))
        lines.extend([
            u"",
            u"Separator: {}".format(self.separator),
            u"Baseline mark: {}".format(self.baseline_mark),
            u"DWG_NO format: {}".format(self.dwg_no_format),
            u"REF_ID format: {}".format(self.ref_id_format),
            u"Prefix regex: {}".format(self.prefix_pattern),
        ])
        if self.warnings:
            lines.append(u"")
            lines.append(u"[Notes]")
            for w in self.warnings:
                lines.append(u"  - {}".format(w))
        return u"\n".join(lines)


# ==================================================================
# Template Writer
# ==================================================================
def write_template(project_dir):
    """Write a NamingRules_Config.json template into the project directory.

    Returns (success, path_or_message). Does not overwrite existing files;
    returns (False, message) if the target already exists.
    """
    if not project_dir or not os.path.isdir(project_dir):
        return False, u"Project directory not found: {}".format(project_dir)

    target = os.path.join(project_dir, NAMING_RULES_FILENAME)
    if os.path.exists(target):
        return False, u"Config file already exists; not overwritten: {}".format(target)

    template = {
        "__README__": [
            u"==========================================================",
            u"  NamingRules_Config.json - User Guide",
            u"==========================================================",
            u"",
            u"This file controls how LF_Tagger_Layout_ID auto-numbers Layouts.",
            u"Save this file after editing; the new rules take effect the next",
            u"time you run LF_Tagger_Layout_ID (no need to restart Rhino).",
            u"",
            u"[What the three variables mean]",
            u"  Given a Layout named 'IN 101.01__Floor Plan':",
            u"    {prefix} = series prefix   -> 'IN'  (letters, e.g. IN/EL/DT/RCP)",
            u"    {major}  = major number    -> 101   (integer, set on each baseline layout)",
            u"    {minor}  = minor number    -> 1     (integer, auto-incremented from 1)",
            u"",
            u"[Zero-padding syntax]",
            u"  {major}        -> '101'",
            u"  {major:03d}    -> '101' (pads to 3 digits; e.g. 5 becomes '005')",
            u"  {major:02d}    -> pads to 2 digits",
            u"  {minor:02d}    -> '01', '02', '03', ...",
            u"",
            u"[Field-by-field description]",
            u"  -- separator --",
            u"    Meaning: separator between drawing number and drawing name",
            u"    Default: '__' (double underscore)",
            u"    Examples:",
            u"      '__'   -> IN 101.01__Floor Plan",
            u"      ' - '  -> IN 101.01 - Floor Plan",
            u"      ' | '  -> IN 101.01 | Floor Plan",
            u"",
            u"  -- baseline_mark --",
            u"    Meaning: marker that identifies the first drawing of a new series",
            u"    Default: '.01'",
            u"    Examples:",
            u"      '.01'  -> baseline name 'IN 101.01__Plan'",
            u"      '-01'  -> baseline name 'IN 101-01__Plan'",
            u"",
            u"  -- dwg_no_format --",
            u"    Meaning: format used to assemble DWG_NO (written into title block)",
            u"    Default: '{prefix} {major:03d}.{minor:02d}'",
            u"    Examples (with prefix=IN, major=101, minor=2):",
            u"      '{prefix} {major:03d}.{minor:02d}' -> 'IN 101.02'",
            u"      '{prefix}-{major:02d}-{minor:02d}' -> 'IN-101-02' (dash style)",
            u"      '{prefix}{major}.{minor}'          -> 'IN101.2'  (no padding)",
            u"      'A-{major:03d}-{minor:02d}'        -> 'A-101-02' (fixed prefix A)",
            u"",
            u"  -- ref_id_format --",
            u"    Meaning: format for REF_ID (used by section/elevation index tags; no prefix)",
            u"    Default: '{major:03d}.{minor:02d}'",
            u"    Examples (with major=101, minor=2):",
            u"      '{major:03d}.{minor:02d}' -> '101.02'",
            u"      '{major}-{minor}'         -> '101-2'",
            u"",
            u"  -- prefix_pattern --",
            u"    Meaning: regex used to extract (prefix, major) from a baseline layout name",
            u"    Default: '([A-Za-z\\s]+?)[\\s]*(\\d+)$'",
            u"         => 'letters+spaces followed by digits'",
            u"    Tip: if you are not familiar with regex, keep the default.",
            u"         The default already handles 'IN 101', 'EL 205', 'DT 99', 'RCP 301', etc.",
            u"",
            u"==========================================================",
            u"  Worked example:",
            u"==========================================================",
            u"  Suppose the Layouts appear in this order:",
            u"    IN 101.01__Floor Plan       <- baseline (new series)",
            u"    IN__Ceiling Detail          <- 2nd page of same series",
            u"    IN__Floor Detail            <- 3rd page of same series",
            u"    EL 201.01__East Elevation   <- baseline (starts EL series)",
            u"    EL__West Elevation          <- 2nd page of EL series",
            u"",
            u"  With the default rules, they are numbered as:",
            u"    IN 101.01__Floor Plan       (DWG_NO=IN 101.01, REF_ID=101.01)",
            u"    IN 101.02__Ceiling Detail   (DWG_NO=IN 101.02, REF_ID=101.02)",
            u"    IN 101.03__Floor Detail     (DWG_NO=IN 101.03, REF_ID=101.03)",
            u"    EL 201.01__East Elevation   (DWG_NO=EL 201.01, REF_ID=201.01)",
            u"    EL 201.02__West Elevation   (DWG_NO=EL 201.02, REF_ID=201.02)",
            u"",
            u"==========================================================",
            u"  Common customizations:",
            u"==========================================================",
            u"  Q1. Change the separator from '__' to ' - ' (space-dash-space)",
            u"     -> Set \"separator\" below to \" - \"",
            u"",
            u"  Q2. Want drawing numbers like 'IN-101-02'",
            u"     -> Set \"dwg_no_format\" to \"{prefix}-{major:03d}-{minor:02d}\"",
            u"",
            u"  Q3. Use '-01' instead of '.01' as the baseline mark",
            u"     -> Adjust all three together:",
            u"       \"baseline_mark\"  : \"-01\"",
            u"       \"dwg_no_format\"  : \"{prefix} {major:03d}-{minor:02d}\"",
            u"       \"ref_id_format\"  : \"{major:03d}-{minor:02d}\"",
            u"",
            u"==========================================================",
            u"  Notes:",
            u"==========================================================",
            u"  1. Keep the JSON syntax valid (commas, quotes). If unsure,",
            u"     validate with an online JSON validator before saving.",
            u"  2. On invalid JSON the script falls back to the built-in defaults",
            u"     and prints a warning in the Rhino command line.",
            u"  3. Fields starting with '__README__' or '_help_' are for reading",
            u"     only and are ignored by the script; feel free to keep or trim.",
            u"=========================================================="
        ],
        "separator":      LAYOUT_NAME_SEPARATOR,
        "_help_separator": u"Separator between drawing number and name. E.g. '__' -> IN 101.01__Plan; ' - ' -> IN 101.01 - Plan",

        "baseline_mark":  LAYOUT_BASELINE_MARK,
        "_help_baseline_mark": u"Marker for a new series. E.g. '.01' -> 'IN 101.01__Plan' is treated as the first page of IN-101",

        "dwg_no_format":  DEFAULT_DWG_NO_FORMAT,
        "_help_dwg_no_format": u"DWG_NO format. Variables: {prefix} {major} {minor}. E.g. '{prefix} {major:03d}.{minor:02d}' -> IN 101.02",

        "ref_id_format":  DEFAULT_REF_ID_FORMAT,
        "_help_ref_id_format": u"REF_ID format. Variables: {major} {minor}. E.g. '{major:03d}.{minor:02d}' -> 101.02",

        "prefix_pattern": DEFAULT_PREFIX_PATTERN,
        "_help_prefix_pattern": u"Advanced: regex extracting (prefix, major). Keep default if unsure."
    }

    try:
        with io.open(target, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=4, ensure_ascii=False)
        return True, target
    except Exception as e:
        if log_exception:
            print(log_exception(u"_LF_NamingRules.write_template", e))
        return False, u"Failed to write template: {}".format(e)
