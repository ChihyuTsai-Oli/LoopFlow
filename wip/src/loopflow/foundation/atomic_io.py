# -*- coding: utf-8 -*-
"""同目錄暫存後 os.replace。失敗不先刪目標檔。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Union

from . import results

JsonValue = Union[dict, list]


def write_bytes_atomic(path: Path, data: bytes) -> results.Result:
    """寫入後 fsync，再以 os.replace 換成目標。不先刪正式檔。"""
    target = Path(path)
    if not target.parent.exists():
        return results.failed("replace_registry", "輸出目錄不存在，不建立正式檔。")
    tmp = target.with_name(target.name + ".tmp")
    try:
        with open(tmp, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(tmp), str(target))
    except OSError as exc:
        try:
            if tmp.exists():
                tmp.unlink()
        except OSError:
            pass
        return results.failed("replace_registry", "無法寫入檔案：%s" % exc)
    return results.ok("replace_registry", "已寫入 %s" % target.name, details={"path": str(target)})


def write_json_atomic(path: Path, payload: JsonValue) -> results.Result:
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return write_bytes_atomic(path, raw.encode("utf-8"))


def read_json(path: Path) -> results.Result:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return results.failed("read_registry", "找不到 JSON：%s" % target.name)
    try:
        text = target.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return results.failed(
            "read_registry",
            "無法讀取 JSON：%s" % exc,
            details={"filename": target.name},
        )
    if not isinstance(data, dict):
        return results.failed("read_registry", "JSON 根物件必須是 object。")
    return results.ok("read_registry", "已讀取 JSON", details={"payload": data})


def copy_file(source: Path, dest: Path) -> results.Result:
    src = Path(source)
    if not src.exists() or not src.is_file():
        return results.failed("replace_registry", "找不到要複製的檔案。")
    try:
        data = src.read_bytes()
    except OSError as exc:
        return results.failed("replace_registry", "無法讀取來源：%s" % exc)
    return write_bytes_atomic(dest, data)
