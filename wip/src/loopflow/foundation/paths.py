# -*- coding: utf-8 -*-
"""以 LOOPFLOW_WORKFILES_ROOT 解析工作檔，不寫死磁碟機、不猜路徑。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from . import results
from .config import AppConfig, DEFAULT_CONFIG

WORKFILES_ROOT_ENV = "LOOPFLOW_WORKFILES_ROOT"
DICTIONARY_FILENAME = "LoopFlow_Dictionary.xlsx"
EXCHANGE_DIR_NAME = "exchange"
REGISTRY_FILENAME = "Project_Registry.json"
REGISTRY_LOCK_FILENAME = "Project_Registry.lock"
REGISTRY_PENDING_FILENAME = "Project_Registry.pending.json"
REGISTRY_LAST_GOOD_FILENAME = "Project_Registry.last-good.json"

_MISSING_ROOT_HINT = (
    "缺少或無效的 %s。請在本機設定該環境變數，指向既有的工作檔資料夾"
    "（見工作區根目錄的工作檔路徑說明），然後重開程式。不得猜測磁碟機，也不建立正式資料。"
    % WORKFILES_ROOT_ENV
)


@dataclass(frozen=True)
class WorkfilesPaths:
    root: Path
    dictionary: Path
    exchange_root: Path

    def registry(self, project_id: str) -> results.Result:
        return registry_paths(self.exchange_root, project_id)

    def log_file(self, config: AppConfig = DEFAULT_CONFIG) -> Path:
        return self.root / config.log_dir_name / config.log_filename


def _environ(environ: Optional[Mapping[str, str]] = None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def resolve_workfiles(
    environ: Optional[Mapping[str, str]] = None,
) -> results.Result:
    """解析工作檔根目錄。目錄必須已存在；不建立、不搜尋 .3dm 旁路徑。"""
    raw = (_environ(environ).get(WORKFILES_ROOT_ENV) or "").strip()
    if not raw:
        return results.failed(
            "resolve_workfiles",
            _MISSING_ROOT_HINT,
            details={"env": WORKFILES_ROOT_ENV},
        )
    root = Path(raw)
    if not root.exists() or not root.is_dir():
        return results.failed(
            "resolve_workfiles",
            _MISSING_ROOT_HINT,
            details={"env": WORKFILES_ROOT_ENV, "exists": root.exists()},
        )
    paths = WorkfilesPaths(
        root=root,
        dictionary=root / DICTIONARY_FILENAME,
        exchange_root=root / EXCHANGE_DIR_NAME,
    )
    return results.ok(
        "resolve_workfiles",
        "已解析工作檔根目錄",
        details={"paths": paths},
    )


def dictionary_path(root: Path) -> Path:
    return Path(root) / DICTIONARY_FILENAME


def registry_paths(exchange_root: Path, project_id: str) -> results.Result:
    pid = (project_id or "").strip()
    if not pid:
        return results.failed(
            "resolve_registry",
            "缺少 project_id，停止解析 Registry。不從檔名猜測。",
        )
    if any(sep in pid for sep in ("/", "\\", "..")):
        return results.blocked(
            "resolve_registry",
            "project_id 不可當作資料夾路徑。",
            blocking=("invalid_project_id",),
            details={"project_id": pid},
        )
    folder = Path(exchange_root) / pid
    return results.ok(
        "resolve_registry",
        "已解析 Registry 路徑",
        details={
            "project_id": pid,
            "folder": folder,
            "registry": folder / REGISTRY_FILENAME,
            "lock": folder / REGISTRY_LOCK_FILENAME,
            "pending": folder / REGISTRY_PENDING_FILENAME,
            "last_good": folder / REGISTRY_LAST_GOOD_FILENAME,
        },
    )
