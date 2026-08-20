# -*- coding: utf-8 -*-
"""Extract／Drawing 的 UserText、圖層與顏色。"""
from __future__ import annotations

DRAWING_SCHEMA_ID = "loopflow.drawing"
DRAWING_SCHEMA_VERSION = "1"

DRAWING_ID_KEY = "lf_drawing_id"
DRAWING_ELEMENT_ID_KEY = "lf_drawing_element_id"
SOURCE_LAYER_ROOT_KEY = "lf_source_layer_root"
SOURCE_REVISION_KEY = "lf_source_revision"
SOURCE_OBJECT_IDS_KEY = "lf_source_object_ids"
PROVENANCE_METHOD_KEY = "lf_provenance_method"
PROVENANCE_STATE_KEY = "lf_provenance_state"
DRAWING_STATUS_KEY = "lf_drawing_status"
SCHEMA_ID_KEY = "lf_schema_id"
SCHEMA_VERSION_KEY = "lf_schema_version"

EXTRACT_LAYER_ROOT = "LoopFlow_Extract"
LAYER_VISIBLE = "LoopFlow_Extract::Visible"
LAYER_HATCH = "LoopFlow_Extract::Hatch"
CURVE_LAYER_PREFIX = "LoopFlow_Extract::Curve_"

COLOR_VISIBLE = (134, 160, 174)
COLOR_HATCH = (140, 151, 166)

KIND_VISIBLE = "visible"
KIND_HATCH = "hatch"
KIND_CURVE = "curve"

STATUS_GENERATED = "generated"
STATUS_MODIFIED = "modified"

STATE_CURRENT = "current"
STATE_MODIFIED = "modified"
STATE_STALE = "stale"
STATE_UNINDEXED = "unindexed"
STATE_AMBIGUOUS = "ambiguous"

METHOD_RHINO = "rhino_association"
METHOD_LOOPFLOW = "loopflow_geometry"
METHOD_MIGRATION = "migration"

MODE_REPLACE = "replace"
MODE_ADD = "add"
MODE_SKIP = "skip"

MODE_LABELS = (
    ("取代前次產出", MODE_REPLACE),
    ("新增一版（保留舊的）", MODE_ADD),
    ("略過", MODE_SKIP),
)
