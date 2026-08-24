# -*- coding: utf-8 -*-
"""測試共用：在 .3dm 旁準備 `_LoopFlow_Config/LoopFlow_Project.json`。

工作資料夾就是 .3dm 所在資料夾，所以測試一律把 3dm、字典與設定放同一層。
"""
from __future__ import annotations

import atexit
import json
import shutil
import tempfile
from pathlib import Path

from loopflow.foundation.paths import CONFIG_DIR_NAME
from loopflow.foundation.project_config import CONFIG_FILENAME, clear_cache

DEFAULT_SCHEMA = {"schema_id": "loopflow.project", "schema_version": 1}
DOCUMENT_NAME = "project.3dm"

_TEMP_ROOTS = []


def config_path(root) -> Path:
    return Path(root) / CONFIG_DIR_NAME / CONFIG_FILENAME


def write_project_config(root, **values) -> Path:
    """寫入指定欄位；未指定 schema 時補上 loopflow.project／1。"""
    payload = dict(DEFAULT_SCHEMA)
    payload.update({key: value for key, value in values.items() if value is not None})
    target = config_path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    clear_cache()
    return target


def read_project_config(root) -> dict:
    """讀回設定檔內容；沒有檔案時回空 dict。"""
    clear_cache()
    target = config_path(root)
    if not target.is_file():
        return {}
    return json.loads(target.read_text(encoding="utf-8"))


def registry_dir(root, project_id) -> Path:
    """Registry 資料夾：`<3dm 資料夾>/_LoopFlow_Config/<專案名稱>/`。"""
    target = Path(root) / CONFIG_DIR_NAME / str(project_id)
    target.mkdir(parents=True, exist_ok=True)
    return target


def temp_project_root() -> Path:
    """建立一個只在本次測試程序存在的工作資料夾，程序結束時清掉。"""
    root = Path(tempfile.mkdtemp(prefix="loopflow-fixture-"))
    _TEMP_ROOTS.append(root)
    return root


def bind_project(session, root=None, *, write_config: bool = True, **values) -> Path:
    """把 session 當成已存檔的 .3dm，並在同層備好專案設定。

    多數指令要先解析工作資料夾才會動作，所以測試 session 一律綁一個臨時資料夾。
    """
    target = Path(root) if root is not None else temp_project_root()
    session.set_document_path(target / DOCUMENT_NAME)
    if write_config:
        write_project_config(target, **values)
    else:
        clear_cache()
    return target


@atexit.register
def _cleanup_temp_roots() -> None:
    for root in _TEMP_ROOTS:
        shutil.rmtree(str(root), ignore_errors=True)
