# -*- coding: utf-8 -*-
"""同目錄暫存後 os.replace。失敗不先刪目標檔。"""
from __future__ import annotations
from loopflow.foundation.i18n import t

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
        return results.failed("replace_registry", t("foundation.002"))
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
        return results.failed("replace_registry", t("foundation.007") % exc)
    return results.ok("replace_registry", t("foundation.003") % target.name, details={"path": str(target)})


def write_json_atomic(path: Path, payload: JsonValue) -> results.Result:
    raw = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    return write_bytes_atomic(path, raw.encode("utf-8"))


def read_json(path: Path) -> results.Result:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return results.failed("read_registry", t("foundation.006") % target.name)
    try:
        text = target.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return results.failed(
            "read_registry",
            t("foundation.008") % exc,
            details={"filename": target.name},
        )
    if not isinstance(data, dict):
        return results.failed("read_registry", t("foundation.004"))
    return results.ok("read_registry", t("foundation.001"), details={"payload": data})


def copy_file(source: Path, dest: Path) -> results.Result:
    src = Path(source)
    if not src.exists() or not src.is_file():
        return results.failed("replace_registry", t("foundation.005"))
    try:
        data = src.read_bytes()
    except OSError as exc:
        return results.failed("replace_registry", t("foundation.009") % exc)
    return write_bytes_atomic(dest, data)
