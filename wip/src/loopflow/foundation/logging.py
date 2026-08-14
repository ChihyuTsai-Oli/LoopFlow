# -*- coding: utf-8 -*-
"""寫入工作檔 logs，不把某台電腦的絕對路徑當成契約資料。"""
from __future__ import annotations

import datetime
import traceback
from pathlib import Path
from typing import Mapping, Optional

from . import paths, results
from .config import AppConfig, DEFAULT_CONFIG


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def resolve_log_path(
    environ: Optional[Mapping[str, str]] = None,
    *,
    config: AppConfig = DEFAULT_CONFIG,
    log_path: Optional[Path] = None,
) -> results.Result:
    if log_path is not None:
        return results.ok("write_log", "使用指定 log 路徑", details={"log_path": Path(log_path)})
    resolved = paths.resolve_workfiles(environ)
    if not resolved.ok:
        return resolved
    workfiles = resolved.details["paths"]
    return results.ok(
        "write_log",
        "使用工作檔 log 路徑",
        details={"log_path": workfiles.log_file(config)},
    )


def append_log(
    message: str,
    *,
    environ: Optional[Mapping[str, str]] = None,
    config: AppConfig = DEFAULT_CONFIG,
    log_path: Optional[Path] = None,
) -> results.Result:
    resolved = resolve_log_path(environ, config=config, log_path=log_path)
    if not resolved.ok:
        return resolved
    target = Path(resolved.details["log_path"])
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write("[%s] %s\n" % (_now(), message))
    except OSError as exc:
        return results.failed("write_log", "寫入 log 失敗：%s" % exc)
    return results.ok("write_log", "已寫入 log", details={"log_path": target})


def log_exception(
    context: str,
    exc: Optional[BaseException] = None,
    *,
    environ: Optional[Mapping[str, str]] = None,
    config: AppConfig = DEFAULT_CONFIG,
    log_path: Optional[Path] = None,
) -> results.Result:
    lines = ["[EXCEPTION] %s" % context]
    if exc is not None:
        lines.append("Exception: %r" % exc)
    lines.append(traceback.format_exc())
    return append_log("\n".join(lines), environ=environ, config=config, log_path=log_path)
