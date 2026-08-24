# -*- coding: utf-8 -*-
# Script: _LoopFlow_Config.py (LoopFlow Global Config Hub)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: Referenced by all LoopFlow scripts
# Usage: Centralises all customisable constants (layer prefixes, colours, filenames, 2D layers, etc.).
#           After editing, re-run the relevant script in Rhino to apply – no restart needed.
#           Not intended for direct execution.

# Dictionary filename (must be in the same folder as the .3dm); only .xlsx is supported
# ==================================================================
# Dictionary Settings
# ==================================================================
DICTIONARY_FILENAME_XLSX = "LoopFlow_Dictionary.xlsx"
# Column header used as the layer key in Excel (must match xlsx exactly)
DICTIONARY_KEY_COLUMN    = "__Rhino Layer"
# Rows to skip before data starts (row 1 is a version title, so always 1)
DICTIONARY_SKIPROWS      = 1

# Root prefix for 3D model layers; after changing, restart Rhino; existing layers are NOT renamed automatically
# ==================================================================
# Layer Naming
# ==================================================================
LAYER_PREFIX_3D    = "M3D"
# Suffix for system data layers, nested under LAYER_PREFIX_3D
LAYER_DATA_SUFFIX  = "_Data"

LAYER_SPACE_BOUNDARIES = "{}::{}::Space_Boundaries".format(LAYER_PREFIX_3D, LAYER_DATA_SUFFIX)
LAYER_LEVEL_FFL        = "{}::{}::Level_Boundaries_FFL".format(LAYER_PREFIX_3D, LAYER_DATA_SUFFIX)
LAYER_LEVEL_FL         = "{}::{}::Level_Boundaries_FL".format(LAYER_PREFIX_3D, LAYER_DATA_SUFFIX)
LAYER_DW_PLAN          = "{}::20_DW".format(LAYER_PREFIX_3D)

# Layer identification prefix for door/window/cabinet layers (maps to _CB.* dictionary fields)
LAYER_CABINET_PREFIX = "04_CB"
# Display name for cabinet layer (shown in the layer panel)
LAYER_CABINET_NAME   = u"\u6ac3\u9ad4"

# Root prefix for 2D drawing layers
LAYER_PREFIX_2D     = "M2D"
# Root layer name for LF_Extract_CP output
LAYER_EXTRACT_ROOT  = "Extract"
LAYER_EXTRACT_VISIBLE = "Extract::Visible"
LAYER_EXTRACT_HATCH   = "Extract::Hatch"
# 2D anchor layer name created by LF_Anchor_Frame
LAYER_ANCHOR_FRAME  = "Anchor_Frame"
LAYER_ANCHOR        = "{}::{}".format(LAYER_PREFIX_2D, LAYER_ANCHOR_FRAME)

# ==================================================================
# 2D Layer Constants (LF_2D_DW_Gen & LF_2D_Cabinet_Gen)
# ==================================================================
# ---- LF_2D_DW_Gen: Door/Window symbol output layers and colours ----
LAYER_2D_DW_FRAME  = "MP_5_DW"        # Door/window frame / members
COLOR_2D_DW_FRAME  = (  0,   0, 255)
LAYER_2D_DW_PANEL  = "MP_6_DW"        # Door leaf / track
COLOR_2D_DW_PANEL  = (255,   0, 255)
LAYER_2D_DW_ORBIT  = "MP_7_ORBIT_DW"  # Opening arc (dashed)
COLOR_2D_DW_ORBIT  = (255, 255,   0)
LAYER_2D_DEFPOINTS = "MP_Defpoints"   # Non-printable auxiliary layer
COLOR_2D_DEFPOINTS = (255, 255, 255)

# ---- LF_2D_Cabinet_Gen: Cabinet symbol output layers and colours ----
LAYER_2D_FURN_OUT  = "MP_4_FURN"      # Cabinet outer frame
COLOR_2D_FURN_OUT  = (  0, 255, 255)
LAYER_2D_FURN_IN   = "MP_7_ORBIT_CB"  # Cabinet interior lines
COLOR_2D_FURN_IN   = (100,   0, 255)

# List of protected UserText attribute prefixes that TagTrigger/Checker will NOT overwrite
# ==================================================================
# Write-Protection List (WHITE_LIST)
# ==================================================================
WHITE_LIST = [u"_02_\u5efa\u69cb\u72c0\u614b", u"_09_\u5be6\u4f5c\u6578\u91cf", "_12_UUID", u"_13_\u5099\u8a3b"]

# ==================================================================
# System File Names
# ==================================================================
REGISTRY_FILENAME      = "Project_Registry.json"
REGISTRY_LOCK_FILENAME = "Project_Registry.lock"
DEBUG_LOG_FILENAME     = "cursor_LF_debug_log.txt"

# Block names for index tags (section/elevation index)
# ==================================================================
# Tag Block Definitions
# ==================================================================
INDEX_BLOCKS  = ["TAG_SECTION_DETAIL", "TAG_ELEV_1", "TAG_ELEV_2", "TAG_ELEV_3", "TAG_ELEV_4"]
# Block names for height tags
HEIGHT_BLOCKS = ["TAG_HEIGHT_GRAB", "TAG_HEIGHT_LASER"]
# Block names for finish-surface tags
FINISH_BLOCKS = ["TAG_FINISH_GRAB", "TAG_FINISH_LASER"]
# Block names for door/window tags
DW_BLOCKS     = ["TAG_DW"]
# Block names for item tags
ITEM_BLOCKS   = ["TAG_ITEM"]

# Layer colour map; keys are numeric prefix codes (e.g. "04" matches layers starting with 04_)
# ==================================================================
# Color Maps
# ==================================================================
COLOR_LAYER_MAP = {
    "furniture": (190, 190, 190),
    "00": (202,  16,  16),
    "01": (119, 219, 225),
    "02": (219, 179, 120),
    "03": (116, 219, 153),
    "04": (187, 153, 244),
    "05": (236, 216, 110),
    "06": (233, 137, 229),
    "07": (215,  76, 110),
    "08": ( 62,  97, 255),
    "09": (210, 105,  30),
    "10": (228,  80,  72),
    "20": (206, 255,   0),
}
# Colour for system data layers (_Data)
COLOR_DATA_LAYER      = (  0,   0,   0)
# Colours for LF_Extract_CP output layers
COLOR_EXTRACT_VISIBLE = (134, 160, 174)
COLOR_EXTRACT_HATCH   = (140, 151, 166)
# Colours for LF_TAG-O warning/broken-link markers
COLOR_WARNING         = (255, 130,  46)
COLOR_BROKEN          = (255,  46,  97)

# Separator between drawing number and drawing name in Layout names
# ==================================================================
# Layout Conventions
# ==================================================================
LAYOUT_NAME_SEPARATOR = "__"
# Suffix appended when LF_Duplicate_Layout copies a Layout
LAYOUT_COPY_SUFFIX    = "_Copy"
# Marker in Layout names that identifies a 'series baseline drawing'
LAYOUT_BASELINE_MARK  = ".01"
# Keywords for ceiling plans, used by LF_2D_DW_Gen to detect ceiling orientation
CEILING_KEYWORDS      = ["CEILING", u"\u5929\u82b1", "RCP"]
# Keywords for mirrored section direction, used by LF_Tagger_Laser to invert X offset
MIRROR_KEYWORDS       = ["CEILING", u"\u5929\u82b1", "RCP"]
# Whether to invert Y-axis offset during ray-probe positioning in LF_Tagger_Laser (True for section DVs)
INVERT_Y              = True

# Delay in seconds before LF_Sync_Worksession refreshes after detecting a .3dm change
# ==================================================================
# Timing & Concurrency
# ==================================================================
SYNC_INTERVAL       = 0.5
# Maximum seconds to wait for Project_Registry.json to be unlocked
# (Cloud-sync folders such as Dropbox/OneDrive may need a longer window)
LOCK_TIMEOUT        = 20.0
# Lock files older than this many seconds are treated as stale and forcibly removed
STALE_LOCK_SECONDS  = 30.0
