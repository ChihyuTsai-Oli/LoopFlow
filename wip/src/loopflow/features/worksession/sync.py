# -*- coding: utf-8 -*-
"""LF_Sync_Worksession：監看同資料夾 .3dm，Rhino idle 時 Refresh Worksession。

只呼叫 Rhino Worksession Refresh，不 Attach／Detach、不改 .rws。
失敗時保留上一份有效參照，延遲後再試。
"""
from __future__ import annotations

import os
from typing import Any, Callable, MutableMapping, Optional

from loopflow.foundation import results

COMMAND_ID = "LF_Sync_Worksession"
STAGE = "sync_worksession"
STICKY_KEY = "lf_worksession_monitor"
DEFAULT_DELAY_SECONDS = 0.5
MODEL_FILTER = "*.3dm"

StopFn = Callable[[], None]
FileChanged = Callable[[str], None]
IdleFn = Callable[[], None]


def is_temp_model_name(name: str) -> bool:
    """略過暫存／自動存檔名稱，避免 Refresh 打到半寫入檔。"""
    text = str(name or "")
    return "~" in text or "tmp" in text.lower()


def watch_directory(document_path: Optional[str]) -> Optional[str]:
    text = str(document_path or "").strip()
    if not text:
        return None
    parent = os.path.dirname(text)
    return parent or None


def same_directory(left: str, right: str) -> bool:
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(
        os.path.normpath(right)
    )


def is_active_monitor(existing: Any) -> bool:
    """不依賴 class 身分：ScriptEditor 重跑後 isinstance 會失效。"""
    return bool(getattr(existing, "active", False)) and callable(
        getattr(existing, "stop", None)
    )


def refresh_due(
    needs_refresh: bool,
    last_change: float,
    now: float,
    delay_seconds: float,
) -> bool:
    return bool(needs_refresh) and (now - last_change) > float(delay_seconds)


class WorksessionMonitor:
    """狀態機：檔案事件只記旗標，真正 Refresh 只在 idle。"""

    def __init__(
        self,
        directory: str,
        *,
        delay_seconds: float,
        refresh: Callable[[], bool],
        now: Callable[[], float],
        note: Callable[[str], None],
        start_watch: Callable[[str, FileChanged], StopFn],
        start_idle: Callable[[IdleFn], StopFn],
    ) -> None:
        self.directory = directory
        self.delay_seconds = float(delay_seconds)
        self._refresh = refresh
        self._now = now
        self._note = note
        self._start_watch = start_watch
        self._start_idle = start_idle
        self.needs_refresh = False
        self.last_change = 0.0
        self.active = False
        self._stop_watch: Optional[StopFn] = None
        self._stop_idle: Optional[StopFn] = None

    def start(self) -> None:
        if self.active:
            return
        try:
            self._stop_watch = self._start_watch(self.directory, self.on_file_changed)
            self._stop_idle = self._start_idle(self.on_idle)
        except Exception:
            self.stop()
            raise
        self.active = True

    def stop(self) -> None:
        self._release(self._stop_watch)
        self._stop_watch = None
        self._release(self._stop_idle)
        self._stop_idle = None
        self.active = False
        self.needs_refresh = False

    @staticmethod
    def _release(handle: Any) -> None:
        if handle is None:
            return
        try:
            if callable(handle):
                handle()
                return
            stop = getattr(handle, "stop", None)
            if callable(stop):
                stop()
        except Exception:
            pass

    def on_file_changed(self, name: str) -> None:
        if not self.active or is_temp_model_name(name):
            return
        self.last_change = self._now()
        self.needs_refresh = True
        self._note("偵測到檔案變動：%s" % name)

    def on_idle(self) -> None:
        if not self.active:
            return
        if not refresh_due(
            self.needs_refresh,
            self.last_change,
            self._now(),
            self.delay_seconds,
        ):
            return
        self.needs_refresh = False
        try:
            success = bool(self._refresh())
        except Exception:
            success = False
        if success:
            self._note("已更新 Worksession 參照。")
            return
        self.needs_refresh = True
        self.last_change = self._now()
        self._note("Worksession 更新未成功，稍後再試。上一份參照未改動。")


def _monitor_from(
    host: Any,
    directory: str,
    delay_seconds: float,
) -> WorksessionMonitor:
    return WorksessionMonitor(
        directory,
        delay_seconds=delay_seconds,
        refresh=host.refresh_worksession,
        now=host.now,
        note=host.note,
        start_watch=host.start_watch,
        start_idle=host.start_idle,
    )


def _start_monitor(
    host: Any,
    store: MutableMapping[str, Any],
    directory: str,
    delay_seconds: float,
    *,
    action: str,
    message: str,
) -> results.Result:
    monitor = _monitor_from(host, directory, delay_seconds)
    try:
        monitor.start()
    except Exception as exc:
        monitor.stop()
        return results.failed(
            STAGE,
            "無法監看資料夾「%s」。\n%s" % (directory, exc),
            command_id=COMMAND_ID,
            details={"action": "failed", "directory": directory, "exception": repr(exc)},
        )
    store[STICKY_KEY] = monitor
    host.note(message)
    return results.ok(
        STAGE,
        message,
        command_id=COMMAND_ID,
        details={
            "action": action,
            "directory": directory,
            "delay_seconds": delay_seconds,
        },
    )


def run_sync_worksession(
    host: Any,
    store: Optional[MutableMapping[str, Any]] = None,
    *,
    delay_seconds: Optional[float] = None,
) -> results.Result:
    """第一次開始監看，再跑一次停止；資料夾變了則改監看新位置。"""
    bag: MutableMapping[str, Any] = store if store is not None else {}
    delay = DEFAULT_DELAY_SECONDS if delay_seconds is None else float(delay_seconds)
    directory = watch_directory(host.document_path())
    existing = bag.get(STICKY_KEY)
    running = is_active_monitor(existing)

    if running:
        if directory and not same_directory(existing.directory, directory):
            existing.stop()
            bag.pop(STICKY_KEY, None)
            return _start_monitor(
                host,
                bag,
                directory,
                delay,
                action="reloaded",
                message="監看資料夾已變更，改監看：%s（延遲 %s 秒）"
                % (directory, delay),
            )
        existing.stop()
        bag.pop(STICKY_KEY, None)
        message = "已停止 Worksession 監看。"
        host.note(message)
        return results.ok(
            STAGE,
            message,
            command_id=COMMAND_ID,
            details={"action": "stopped", "directory": existing.directory},
        )

    if not directory:
        return results.failed(
            STAGE,
            "請先把檔案存到磁碟，再開始監看同資料夾的 .3dm。",
            command_id=COMMAND_ID,
            details={"action": "unsaved"},
        )

    return _start_monitor(
        host,
        bag,
        directory,
        delay,
        action="started",
        message="已開始監看：%s（延遲 %s 秒）" % (directory, delay),
    )
