# -*- coding: utf-8 -*-
"""專案環境設定：存在 `.3dm` 旁的 `_LoopFlow_Config/LoopFlow_Project.json`。

`.3dm` 會被複製到各個專案，所以不在文件 UserText 留專案名稱、字典檔名這類環境設定。
舊檔仍帶著 `lf_*` 五個鍵時，第一次讀取會搬進 JSON 並從文件清掉。
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Mapping, Optional

from . import results
from .paths import (
    DICTIONARY_FILENAME,
    normalize_dictionary_filename,
    normalize_project_id,
    resolve_project_folder,
)

CONFIG_FILENAME = "LoopFlow_Project.json"
PROJECT_SCHEMA_ID = "loopflow.project"
PROJECT_SCHEMA_VERSION = 1

SCHEMA_ID_FIELD = "schema_id"
SCHEMA_VERSION_FIELD = "schema_version"
PROJECT_ID_FIELD = "project_id"
LAYER_PREFIX_FIELD = "layer_prefix"
DICTIONARY_FILENAME_FIELD = "dictionary_filename"

FIELDS = (
    SCHEMA_ID_FIELD,
    SCHEMA_VERSION_FIELD,
    PROJECT_ID_FIELD,
    LAYER_PREFIX_FIELD,
    DICTIONARY_FILENAME_FIELD,
)

# 舊檔的文件 UserText → JSON 欄位。只在遷移時讀，之後不再寫回文件。
LEGACY_DOCUMENT_KEYS = (
    ("lf_schema_id", SCHEMA_ID_FIELD),
    ("lf_schema_version", SCHEMA_VERSION_FIELD),
    ("lf_project_id", PROJECT_ID_FIELD),
    ("lf_layer_prefix", LAYER_PREFIX_FIELD),
    ("lf_dictionary_filename", DICTIONARY_FILENAME_FIELD),
)

_cache: dict = {}


def _signature(path: Path):
    try:
        stat = os.stat(str(path))
    except OSError:
        return None
    return (stat.st_mtime_ns, stat.st_size)


def _read_json(path: Path) -> results.Result:
    signature = _signature(path)
    if signature is None:
        _cache.pop(str(path), None)
        return results.ok(
            "read_project_config",
            "尚無專案設定檔",
            details={"values": {}, "exists": False},
        )
    cached = _cache.get(str(path))
    if cached is not None and cached[0] == signature:
        return results.ok(
            "read_project_config",
            "已讀取專案設定",
            details={"values": dict(cached[1]), "exists": True},
        )
    try:
        with open(str(path), "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        return results.failed(
            "read_project_config",
            "%s 無法解析：%s。已停止，不猜測內容。" % (path.name, exc),
            details={"path": str(path)},
        )
    if not isinstance(data, dict):
        return results.failed(
            "read_project_config",
            "%s 內容不是設定物件。已停止，不猜測內容。" % path.name,
            details={"path": str(path)},
        )
    _cache[str(path)] = (signature, dict(data))
    return results.ok(
        "read_project_config",
        "已讀取專案設定",
        details={"values": dict(data), "exists": True},
    )


def _write_json(path: Path, values: Mapping) -> results.Result:
    payload = {key: values[key] for key in FIELDS if values.get(key) not in (None, "")}
    for key in values:
        if key not in FIELDS and values[key] not in (None, ""):
            payload[key] = values[key]
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
    except OSError as exc:
        return results.failed(
            "write_project_config",
            "無法寫入 %s：%s" % (path.name, exc),
            details={"path": str(path)},
        )
    _cache[str(path)] = (_signature(path), dict(payload))
    return results.ok(
        "write_project_config",
        "已更新專案設定",
        details={"values": dict(payload), "path": str(path)},
    )


def config_path_for_paths(paths) -> Path:
    return Path(paths.config_dir) / CONFIG_FILENAME


def _legacy_values(session) -> dict:
    getter = getattr(session, "document_user_text", None) if session is not None else None
    if not callable(getter):
        return {}
    values = {}
    for key, field in LEGACY_DOCUMENT_KEYS:
        raw = getter(key)
        text = str(raw or "").strip()
        if not text:
            continue
        if field == SCHEMA_VERSION_FIELD and text.isdigit():
            values[field] = int(text)
        else:
            values[field] = text
    return values


def _clear_legacy_keys(session) -> None:
    setter = getattr(session, "set_document_user_text", None) if session is not None else None
    getter = getattr(session, "document_user_text", None) if session is not None else None
    if not callable(setter) or not callable(getter):
        return
    for key, _field in LEGACY_DOCUMENT_KEYS:
        if str(getter(key) or "").strip():
            setter(key, "")


def read_config(session) -> results.Result:
    """讀專案設定。舊檔的文件 UserText 只在這裡搬一次，之後只認 JSON。"""
    resolved = resolve_project_folder(session)
    if not resolved.ok:
        return resolved
    paths = resolved.details["paths"]
    path = config_path_for_paths(paths)
    loaded = _read_json(path)
    if not loaded.ok:
        return loaded
    values = dict(loaded.details["values"])
    exists = bool(loaded.details["exists"])
    migrated = False
    if not exists:
        legacy = _legacy_values(session)
        if legacy:
            written = _write_json(path, legacy)
            if not written.ok:
                return written
            _clear_legacy_keys(session)
            values = dict(written.details["values"])
            exists = True
            migrated = True
    return results.ok(
        "read_project_config",
        "已讀取專案設定",
        details={
            "values": values,
            "exists": exists,
            "migrated": migrated,
            "path": path,
            "paths": paths,
        },
    )


def update_config(session, **fields) -> results.Result:
    """只覆寫指定欄位，保留其他設定。"""
    current = read_config(session)
    if not current.ok:
        return current
    values = dict(current.details["values"])
    values.update({key: value for key, value in fields.items() if value not in (None, "")})
    written = _write_json(Path(current.details["path"]), values)
    if not written.ok:
        return written
    return results.ok(
        "write_project_config",
        written.message,
        details={
            "values": written.details["values"],
            "path": Path(current.details["path"]),
            "paths": current.details["paths"],
        },
    )


def config_value(session, field: str) -> Optional[str]:
    """單一欄位；讀不到設定時回 None，不猜測。"""
    loaded = read_config(session)
    if not loaded.ok:
        return None
    value = loaded.details["values"].get(field)
    if value in (None, ""):
        return None
    return value


def ensure_schema(session) -> results.Result:
    """缺 schema 時順便補上 loopflow.project／1，不擋開案。"""
    loaded = read_config(session)
    if not loaded.ok:
        return loaded
    values = loaded.details["values"]
    fields = {}
    if str(values.get(SCHEMA_ID_FIELD) or "").strip() == "":
        fields[SCHEMA_ID_FIELD] = PROJECT_SCHEMA_ID
    if values.get(SCHEMA_VERSION_FIELD) in (None, ""):
        fields[SCHEMA_VERSION_FIELD] = PROJECT_SCHEMA_VERSION
    if not fields:
        return loaded
    return update_config(session, **fields)


def project_name(session) -> Optional[str]:
    """專案名稱；沒有 project_id 時才看 layer_prefix。"""
    loaded = read_config(session)
    if not loaded.ok:
        return None
    values = loaded.details["values"]
    for field in (PROJECT_ID_FIELD, LAYER_PREFIX_FIELD):
        name = normalize_project_id(values.get(field))
        if name:
            return name
    return None


def remember_project_name(session, name: str) -> results.Result:
    """專案名稱＝圖層前綴＝Registry 子資料夾名，兩個欄位同值。"""
    return update_config(session, project_id=name, layer_prefix=name)


def remembered_dictionary_filename(session) -> Optional[str]:
    """只回這份專案記住的 Dictionary 檔名。沒記住就不套預設檔名。"""
    raw = config_value(session, DICTIONARY_FILENAME_FIELD)
    if raw in (None, ""):
        return None
    normalized = normalize_dictionary_filename(raw)
    if normalized.ok:
        return str(normalized.details["filename"])
    return None


def dictionary_filename_from_session(session) -> str:
    return remembered_dictionary_filename(session) or DICTIONARY_FILENAME


def remember_dictionary_filename(session, filename: str) -> results.Result:
    return update_config(session, dictionary_filename=filename)


def clear_cache() -> None:
    """測試用：丟掉設定檔快取。"""
    _cache.clear()
