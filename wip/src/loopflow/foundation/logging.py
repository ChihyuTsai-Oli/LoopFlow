# -*- coding: utf-8 -*-
"""log 寫在 .3dm 旁的 `_LoopFlow_Config/logs/`，不把某台電腦的絕對路徑當成契約資料。"""
from __future__ import annotations
from loopflow.foundation.i18n import t

import datetime
import traceback
from pathlib import Path
from typing import Optional

from . import paths, results
from .config import AppConfig, DEFAULT_CONFIG


def _now() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def resolve_log_path(
    session=None,
    *,
    config: AppConfig = DEFAULT_CONFIG,
    log_path: Optional[Path] = None,
) -> results.Result:
    if log_path is not None:
        return results.ok("write_log", t("foundation.014"), details={"log_path": Path(log_path)})
    resolved = paths.resolve_project_folder(session)
    if not resolved.ok:
        return resolved
    project = resolved.details["paths"]
    return results.ok(
        "write_log",
        t("foundation.012"),
        details={"log_path": project.log_file(config)},
    )


def append_log(
    message: str,
    *,
    session=None,
    config: AppConfig = DEFAULT_CONFIG,
    log_path: Optional[Path] = None,
) -> results.Result:
    resolved = resolve_log_path(session, config=config, log_path=log_path)
    if not resolved.ok:
        return resolved
    target = Path(resolved.details["log_path"])
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write("[%s] %s\n" % (_now(), message))
    except OSError as exc:
        return results.failed("write_log", t("foundation.015") % exc)
    return results.ok("write_log", t("foundation.013"), details={"log_path": target})


def log_exception(
    context: str,
    exc: Optional[BaseException] = None,
    *,
    session=None,
    config: AppConfig = DEFAULT_CONFIG,
    log_path: Optional[Path] = None,
) -> results.Result:
    lines = ["[EXCEPTION] %s" % context]
    if exc is not None:
        lines.append("Exception: %r" % exc)
    lines.append(traceback.format_exc())
    return append_log("\n".join(lines), session=session, config=config, log_path=log_path)
