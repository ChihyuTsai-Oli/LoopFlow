# -*- coding: utf-8 -*-
"""指令結果與錯誤階段。

取消、失敗、阻擋與尚未實作都必須可區分；顏色或對話框不是真相來源。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Tuple

STATUSES = (
    "ok",
    "ok_with_warnings",
    "cancelled",
    "blocked",
    "failed",
    "not_implemented",
    "unknown_command",
)

STAGES = (
    "dispatch",
    "resolve_workfiles",
    "resolve_dictionary",
    "resolve_exchange",
    "resolve_registry",
    "check_schema",
    "write_log",
    "load_config",
    "read_excel",
    "load_dictionary",
    "validate_dictionary",
    "rhino_session",
    "snapshot",
    "restore",
    "guarded_run",
    "open_check",
    "sync_type_layers",
    "register_spaces",
    "scan_identity",
    "apply_identity",
    "verify_identity",
    "rollback_identity",
)


@dataclass(frozen=True)
class Result:
    ok: bool
    status: str
    stage: str
    message: str
    command_id: Optional[str] = None
    warnings: Tuple[str, ...] = ()
    blocking: Tuple[str, ...] = ()
    details: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "status": self.status,
            "stage": self.stage,
            "message": self.message,
            "command_id": self.command_id,
            "warnings": list(self.warnings),
            "blocking": list(self.blocking),
            "details": dict(self.details),
        }


def _result(
    status: str,
    stage: str,
    message: str,
    *,
    ok: bool,
    command_id: Optional[str] = None,
    warnings: Tuple[str, ...] = (),
    blocking: Tuple[str, ...] = (),
    details: Optional[Mapping[str, Any]] = None,
) -> Result:
    if status not in STATUSES:
        raise ValueError("未知結果狀態：%s" % status)
    return Result(
        ok=ok,
        status=status,
        stage=stage,
        message=message,
        command_id=command_id,
        warnings=warnings,
        blocking=blocking,
        details=dict(details or {}),
    )


def ok(stage: str, message: str, **kwargs) -> Result:
    return _result("ok", stage, message, ok=True, **kwargs)


def ok_with_warnings(stage: str, message: str, warnings: Tuple[str, ...], **kwargs) -> Result:
    return _result(
        "ok_with_warnings",
        stage,
        message,
        ok=True,
        warnings=warnings,
        **kwargs,
    )


def cancelled(stage: str, message: str, **kwargs) -> Result:
    return _result("cancelled", stage, message, ok=False, **kwargs)


def blocked(stage: str, message: str, blocking: Tuple[str, ...], **kwargs) -> Result:
    return _result("blocked", stage, message, ok=False, blocking=blocking, **kwargs)


def failed(stage: str, message: str, **kwargs) -> Result:
    return _result("failed", stage, message, ok=False, **kwargs)


def not_implemented(stage: str, message: str, **kwargs) -> Result:
    return _result("not_implemented", stage, message, ok=False, **kwargs)


def unknown_command(stage: str, message: str, **kwargs) -> Result:
    return _result("unknown_command", stage, message, ok=False, **kwargs)
