# -*- coding: utf-8 -*-
"""Registry 安全發布：lock → 重讀 → pending → validate → atomic replace。"""
from __future__ import annotations

import copy
import errno
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence

from loopflow.features.registry import schema
from loopflow.features.registry.lock import acquire_lock, release_lock
from loopflow.features.registry.validate import validate_payload
from loopflow.foundation import atomic_io, results
from loopflow.foundation.paths import normalize_project_id, resolve_registry_for_document
from loopflow.foundation.i18n import t

COMMAND_ID = schema.COMMAND_ID
REPLACE_WAITS = (0.2, 0.4, 0.8, 1.6)


def _stamp_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _prepare_payload(payload: Mapping, current: Optional[Mapping]) -> dict:
    body = copy.deepcopy(dict(payload))
    current_rev = 0
    if isinstance(current, dict):
        try:
            current_rev = int(current.get("registry_revision") or 0)
        except (TypeError, ValueError):
            current_rev = 0
    body["schema_id"] = schema.SCHEMA_ID
    if "schema_version" not in body:
        body["schema_version"] = schema.SCHEMA_VERSION
    body["registry_revision"] = current_rev + 1
    if not str(body.get("published_at") or "").strip():
        body["published_at"] = _stamp_now()
    if not isinstance(body.get("extension"), dict):
        body["extension"] = {}
    return body


def _is_sharing_violation(exc: OSError) -> bool:
    if getattr(exc, "winerror", None) == 32:
        return True
    return getattr(exc, "errno", None) in (errno.EACCES, errno.EPERM, errno.EBUSY)


def _replace_with_retry(
    pending: Path,
    official: Path,
    replace: Optional[Callable[[Path, Path], None]],
    sleep: Callable[[float], None],
    waits: Sequence[float],
) -> None:
    last = None
    for index, wait in enumerate((0.0,) + tuple(waits)):
        if wait:
            sleep(wait)
        try:
            if callable(replace):
                replace(pending, official)
            else:
                os.replace(str(pending), str(official))
            return
        except OSError as exc:
            last = exc
            if not _is_sharing_violation(exc):
                raise
            if index >= len(waits):
                raise
    if last is not None:
        raise last


def publish_registry(
    payload: Mapping,
    *,
    document_path: Optional[str] = None,
    command_id: str = COMMAND_ID,
    after_pending: Optional[Callable[[Path], None]] = None,
    replace: Optional[Callable[[Path, Path], None]] = None,
    pid: Optional[int] = None,
    host: Optional[str] = None,
    pid_alive: Optional[Callable[[int], bool]] = None,
    now=None,
    sleep: Optional[Callable[[float], None]] = None,
    replace_waits: Optional[Sequence[float]] = None,
) -> results.Result:
    """寫入 <3dm 資料夾>/_LoopFlow_Config/<專案名稱>/ 的正式 Registry。失敗不刪正式檔，保留 last-good。"""
    if not isinstance(payload, Mapping):
        return results.blocked(
            "validate_registry",
            t("registry.013"),
            blocking=("invalid_payload",),
            command_id=command_id,
        )
    project_id = normalize_project_id(payload.get("project_id"))
    if not project_id:
        return results.blocked(
            "validate_registry",
            t("registry.014"),
            blocking=("invalid_project_id",),
            command_id=command_id,
        )
    resolved = resolve_registry_for_document(document_path, project_id)
    if not resolved.ok:
        return resolved
    folder = Path(resolved.details["folder"])
    official = Path(resolved.details["registry"])
    lock_path = Path(resolved.details["lock"])
    pending = Path(resolved.details["pending"])
    last_good = Path(resolved.details["last_good"])

    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return results.failed(
            "resolve_registry",
            t("registry.016") % exc,
            command_id=command_id,
        )

    locked = acquire_lock(
        lock_path,
        command_id=command_id,
        pid=pid,
        host=host,
        now=now,
        pid_alive=pid_alive,
    )
    if not locked.ok:
        return locked

    published = False
    try:
        current = None
        if official.exists():
            loaded = atomic_io.read_json(official)
            if not loaded.ok:
                return results.failed(
                    "read_registry",
                    t("registry.020") % loaded.message,
                    command_id=command_id,
                    details={"filename": official.name},
                )
            current = loaded.details["payload"]
            if str(current.get("project_id") or "") != project_id:
                return results.blocked(
                    "read_registry",
                    t("registry.017"),
                    blocking=("project_id_mismatch",),
                    command_id=command_id,
                )

        body = _prepare_payload(payload, current)
        checked = validate_payload(body)
        if not checked.ok:
            return checked

        written = atomic_io.write_json_atomic(pending, body)
        if not written.ok:
            return results.failed(
                "write_registry_pending",
                written.message,
                command_id=command_id,
            )
        from_disk = atomic_io.read_json(pending)
        if not from_disk.ok:
            return results.failed(
                "validate_registry",
                t("registry.018") % from_disk.message,
                command_id=command_id,
            )
        rechecked = validate_payload(from_disk.details["payload"])
        if not rechecked.ok:
            return rechecked
        if callable(after_pending):
            after_pending(pending)

        if official.exists():
            copied = atomic_io.copy_file(official, last_good)
            if not copied.ok:
                return results.failed(
                    "replace_registry",
                    t("registry.021") % copied.message,
                    command_id=command_id,
                )

        try:
            _replace_with_retry(
                pending,
                official,
                replace,
                sleep or time.sleep,
                REPLACE_WAITS if replace_waits is None else replace_waits,
            )
        except OSError as exc:
            if _is_sharing_violation(exc):
                copied = atomic_io.copy_file(pending, last_good)
                extra = ""
                if copied.ok:
                    extra = " " + t("registry.022")
                return results.failed(
                    "replace_registry",
                    t("registry.012") + extra,
                    command_id=command_id,
                    details={
                        "filename": official.name,
                        "os_error": str(exc),
                    },
                )
            return results.failed(
                "replace_registry",
                t("registry.023") % exc,
                command_id=command_id,
            )
        published = True

        if not last_good.exists():
            copied = atomic_io.copy_file(official, last_good)
            if not copied.ok:
                return results.ok_with_warnings(
                    "publish_registry",
                    t("registry.024") % body["registry_revision"],
                    ("last_good_copy_failed",),
                    command_id=command_id,
                    details={
                        "filename": official.name,
                        "registry_revision": body["registry_revision"],
                        "path": str(official),
                    },
                )
        return results.ok(
            "publish_registry",
            t("registry.015") % body["registry_revision"],
            command_id=command_id,
            details={
                "filename": official.name,
                "registry_revision": body["registry_revision"],
                "path": str(official),
                "last_good": str(last_good),
            },
        )
    except Exception as exc:
        return results.failed(
            "publish_registry",
            t("registry.019") % exc,
            command_id=command_id,
            details={"exception": str(exc)},
        )
    finally:
        if not published and pending.exists():
            try:
                pending.unlink()
            except OSError:
                pass
        release_lock(lock_path, pid=pid, host=host, command_id=command_id)
