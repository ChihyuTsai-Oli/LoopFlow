# -*- coding: utf-8 -*-
"""Registry schema_version 1 的根與陣列欄位。與 fixtures/schema/registry.json 對齊。"""
from __future__ import annotations

SCHEMA_ID = "loopflow.registry"
SCHEMA_VERSION = 1
REQUIRED_ROOT = (
    "schema_id",
    "schema_version",
    "project_id",
    "registry_revision",
    "published_at",
    "model_unit",
    "types",
    "spaces",
    "objects",
    "extension",
)
TYPE_KEYS = (
    "type_id",
    "type_category",
    "type_sequence",
    "type_display_name",
    "layer_path",
    "estimation_unit",
    "measurement_rule",
    "elevation_basis",
    "construction_default",
    "remarks_default",
)
SPACE_KEYS = (
    "space_id",
    "level_id",
    "space_display",
)
OBJECT_KEYS = (
    "object_id",
    "type_id",
    "type_category",
    "type_sequence",
    "type_display_name",
    "construction_status",
    "space_id",
    "space_display",
    "elevation_basis",
    "elevation_value",
    "elevation_display",
    "remarks",
    "data_revision",
)
FORBIDDEN_OBJECT_KEYS = (
    "dimension_w",
    "dimension_d",
    "dimension_h",
    "quantity",
    "local_frame",
)
RESERVED_SPACE_ID = "EXT"
COMMAND_ID = "LF_Publish_Exchange"
