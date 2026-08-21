# -*- coding: utf-8 -*-
"""跨 feature 的小型共用能力。完整規則見 wip/docs/。"""
from loopflow.foundation.config import AppConfig, DEFAULT_CONFIG, load_config
from loopflow.foundation.paths import (
    CONFIG_DIR_NAME,
    normalize_project_id,
    registry_paths,
    resolve_project_folder,
    resolve_registry_for_document,
)
from loopflow.foundation.results import Result
from loopflow.foundation.version import PACKAGE_VERSION, SCHEMA_VERSIONS, check_schema

__all__ = [
    "AppConfig",
    "CONFIG_DIR_NAME",
    "DEFAULT_CONFIG",
    "PACKAGE_VERSION",
    "Result",
    "SCHEMA_VERSIONS",
    "check_schema",
    "load_config",
    "normalize_project_id",
    "registry_paths",
    "resolve_project_folder",
    "resolve_registry_for_document",
]
