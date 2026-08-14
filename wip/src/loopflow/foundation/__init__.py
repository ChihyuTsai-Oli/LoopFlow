# -*- coding: utf-8 -*-
"""跨 feature 的小型共用能力。完整規則見 wip/docs/。"""
from loopflow.foundation.config import AppConfig, DEFAULT_CONFIG, load_config
from loopflow.foundation.paths import (
    WORKFILES_ROOT_ENV,
    resolve_workfiles,
    registry_paths,
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
    "registry_paths",
    "resolve_workfiles",
]
