# -*- coding: utf-8 -*-
"""跨 feature 的小型共用能力。完整規則見 wip/docs/。"""
from loopflow.foundation.config import AppConfig, DEFAULT_CONFIG, load_config
from loopflow.foundation.paths import (
    WORKFILES_ROOT_ENV,
    normalize_project_id,
    registry_paths,
    resolve_registry_for_document,
    resolve_workfiles,
)
from loopflow.foundation.results import Result
from loopflow.foundation.version import PACKAGE_VERSION, SCHEMA_VERSIONS, check_schema

__all__ = [
    "AppConfig",
    "DEFAULT_CONFIG",
    "PACKAGE_VERSION",
    "Result",
    "SCHEMA_VERSIONS",
    "WORKFILES_ROOT_ENV",
    "check_schema",
    "load_config",
    "normalize_project_id",
    "registry_paths",
    "resolve_registry_for_document",
    "resolve_workfiles",
]
