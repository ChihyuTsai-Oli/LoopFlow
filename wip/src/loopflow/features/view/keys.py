# -*- coding: utf-8 -*-
"""View 登記的 UserText key 與圖層。"""
from __future__ import annotations

VIEW_SCHEMA_ID = "loopflow.view"
VIEW_SCHEMA_VERSION = "1"
TRANSFORM_SCHEMA_ID = "loopflow.view_transform"
TRANSFORM_SCHEMA_VERSION = 1

VIEW_ID_KEY = "lf_view_id"
SCHEMA_ID_KEY = "lf_schema_id"
SCHEMA_VERSION_KEY = "lf_schema_version"
CLIPPING_PLANE_ID_KEY = "lf_clipping_plane_id"
VIEW_TRANSFORM_KEY = "lf_view_transform"
DETAIL_ID_KEY = "lf_detail_id"

LEGACY_ROLE_KEY = "Role"
LEGACY_TARGET_CP_KEY = "Target_CP"
LEGACY_ROLE_VALUE = "Anchor_Frame"

ANCHOR_LAYER = "M2D::Anchor_Frame"
ANCHOR_COLOR = (155, 140, 205)
DEFAULT_OFFSET = 50.0
INVERT_Y = True
MIRROR_KEYWORDS = ("CEILING", "天花", "RCP")
