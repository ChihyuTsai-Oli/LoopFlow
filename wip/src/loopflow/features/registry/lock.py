# -*- coding: utf-8 -*-
"""Registry exclusive lock。含 PID、主機與時間；活著的持有者不可搶。"""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

from loopflow.foundation import results

COMMAND_ID = "LF_Publish_Exchange"
STALE_LOCK_SECONDS = 30.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(raw) -> Optional[datetime]:
    text = str(raw or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        value = datetime.fromisoformat(text)
    except ValueError:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value


def default_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    except SystemError:
        return False
    return True


def _owner_payload(*, pid: int, host: str, acquired_at: datetime, command_id: str) -> dict:
    stamp = acquired_at.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "pid": pid,
        "host": host,
        "acquired_at": stamp,
        "command_id": command_id,
    }


def _read_lock(path: Path) -> Optional[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def _is_stale(
    path: Path,
    data: Optional[dict],
    *,
    now: datetime,
    host: str,
    pid_alive: Callable[[int], bool],
    stale_seconds: float,
) -> bool:
    if data is None:
        try:
            age = now.timestamp() - path.stat().st_mtime
        except OSError:
            return True
        return age >= stale_seconds
    acquired = _parse_time(data.get("acquired_at"))
    if acquired is None:
        return True
    if now - acquired >= timedelta(seconds=stale_seconds):
        return True
    lock_host = str(data.get("host") or "")
    try:
        lock_pid = int(data.get("pid"))
    except (TypeError, ValueError):
        return True
    if lock_host == host and not pid_alive(lock_pid):
        return True
    return False


def acquire_lock(
    path: Path,
    *,
    command_id: str = COMMAND_ID,
    pid: Optional[int] = None,
    host: Optional[str] = None,
    now: Optional[datetime] = None,
    pid_alive: Optional[Callable[[int], bool]] = None,
    stale_seconds: float = STALE_LOCK_SECONDS,
) -> results.Result:
    """以 O_EXCL 建立 lock。同機死 PID 或逾時視為 stale。"""
    target = Path(path)
    owner_pid = os.getpid() if pid is None else int(pid)
    owner_host = socket.gethostname() if host is None else str(host)
    clock = now or _utc_now()
    alive = pid_alive or default_pid_alive
    payload = _owner_payload(
        pid=owner_pid,
        host=owner_host,
        acquired_at=clock,
        command_id=command_id,
    )
    raw = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

    def try_create() -> Optional[results.Result]:
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        try:
            fd = os.open(str(target), flags)
        except FileExistsError:
            return None
        except OSError as exc:
            if getattr(exc, "errno", None) == 17:
                return None
            return results.failed(
                "acquire_registry_lock",
                "無法建立 lock：%s" % exc,
                command_id=command_id,
            )
        try:
            os.write(fd, raw)
            os.fsync(fd)
        finally:
            os.close(fd)
        return results.ok(
            "acquire_registry_lock",
            "已取得 Registry lock",
            command_id=command_id,
            details={"lock": str(target), "pid": owner_pid, "host": owner_host},
        )

    created = try_create()
    if created is not None:
        return created
    existing = _read_lock(target)
    if not _is_stale(
        target,
        existing,
        now=clock,
        host=owner_host,
        pid_alive=alive,
        stale_seconds=stale_seconds,
    ):
        return results.blocked(
            "acquire_registry_lock",
            "Registry 正被其他程序鎖定，不覆寫。",
            blocking=("registry_locked",),
            command_id=command_id,
            details={"lock": str(target), "owner": existing},
        )
    try:
        target.unlink()
    except OSError as exc:
        return results.failed(
            "acquire_registry_lock",
            "無法清除過期 lock：%s" % exc,
            command_id=command_id,
        )
    created = try_create()
    if created is not None:
        return created
    return results.blocked(
        "acquire_registry_lock",
        "Registry 正被其他程序鎖定，不覆寫。",
        blocking=("registry_locked",),
        command_id=command_id,
        details={"lock": str(target)},
    )


def release_lock(
    path: Path,
    *,
    pid: Optional[int] = None,
    host: Optional[str] = None,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """只刪自己持有的 lock，避免清掉別人的。"""
    target = Path(path)
    if not target.exists():
        return results.ok("acquire_registry_lock", "沒有 lock 可釋放", command_id=command_id)
    owner_pid = os.getpid() if pid is None else int(pid)
    owner_host = socket.gethostname() if host is None else str(host)
    data = _read_lock(target)
    if data is not None:
        try:
            lock_pid = int(data.get("pid"))
        except (TypeError, ValueError):
            lock_pid = None
        if lock_pid != owner_pid or str(data.get("host") or "") != owner_host:
            return results.ok(
                "acquire_registry_lock",
                "lock 已易主，不刪除。",
                command_id=command_id,
            )
    try:
        target.unlink()
    except OSError as exc:
        return results.failed(
            "acquire_registry_lock",
            "無法釋放 lock：%s" % exc,
            command_id=command_id,
        )
    return results.ok("acquire_registry_lock", "已釋放 Registry lock", command_id=command_id)
