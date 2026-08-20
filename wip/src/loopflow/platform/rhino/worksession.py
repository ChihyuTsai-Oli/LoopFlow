# -*- coding: utf-8 -*-
"""Rhino Worksession 監看：FileSystemWatcher、Idle、Refresh。

模組載入不 import Rhino。只 Refresh 既有 Worksession，不 Attach／Detach。
處理器做成實體方法並由 monitor 抓住，避免 pythonnet 把委派收掉後完全沒反應。
"""
from __future__ import annotations

import time
from typing import Any, Callable, MutableMapping, Optional

from loopflow.platform.rhino.live import _load_rhino

REFRESH_SCRIPT = "_-Worksession _Refresh _Enter"


def _rhino_modules():
    loaded, error = _load_rhino()
    if loaded is None:
        raise RuntimeError(error or "無法載入 Rhino")
    return loaded


class FileWatchHandle:
    """抓住 FileSystemWatcher 與委派，避免背景監看被 GC。"""

    def __init__(self, directory: str, on_changed: Callable[[str], None]) -> None:
        import System.IO  # type: ignore

        self._on_changed = on_changed
        self._watcher = System.IO.FileSystemWatcher()
        filters = System.IO.NotifyFilters
        try:
            self._watcher.Path = directory
            self._watcher.Filter = "*.3dm"
            self._watcher.IncludeSubdirectories = False
            self._watcher.NotifyFilter = (
                filters.LastWrite | filters.FileName | filters.Size | filters.CreationTime
            )
            self._watcher.Changed += self._dispatch
            self._watcher.Created += self._dispatch
            self._watcher.Renamed += self._dispatch
            self._watcher.EnableRaisingEvents = True
        except Exception:
            self.stop()
            raise

    def _dispatch(self, _sender, event) -> None:
        name = getattr(event, "Name", None) or getattr(event, "FullPath", "") or ""
        if "\\" in str(name) or "/" in str(name):
            import os

            name = os.path.basename(str(name))
        self._on_changed(str(name))

    def __call__(self) -> None:
        self.stop()

    def stop(self) -> None:
        watcher = getattr(self, "_watcher", None)
        if watcher is None:
            return
        try:
            watcher.EnableRaisingEvents = False
        except Exception:
            pass
        try:
            watcher.Changed -= self._dispatch
        except Exception:
            pass
        try:
            watcher.Created -= self._dispatch
        except Exception:
            pass
        try:
            watcher.Renamed -= self._dispatch
        except Exception:
            pass
        dispose = getattr(watcher, "Dispose", None)
        if callable(dispose):
            try:
                dispose()
            except Exception:
                pass
        self._watcher = None


class IdleHandle:
    """抓住 Idle 委派，避免訂閱後被 GC。"""

    def __init__(self, on_idle: Callable[[], None]) -> None:
        Rhino, _rs, _sc = _rhino_modules()
        self._Rhino = Rhino
        self._on_idle = on_idle
        Rhino.RhinoApp.Idle += self._dispatch

    def _dispatch(self, _sender, _event) -> None:
        self._on_idle()

    def __call__(self) -> None:
        self.stop()

    def stop(self) -> None:
        rhino = getattr(self, "_Rhino", None)
        if rhino is None:
            return
        try:
            rhino.RhinoApp.Idle -= self._dispatch
        except Exception:
            pass
        self._Rhino = None


class LiveWorksessionHost:
    def document_path(self) -> Optional[str]:
        try:
            Rhino, _rs, sc = _rhino_modules()
        except RuntimeError:
            return None
        doc = getattr(sc, "doc", None) or getattr(Rhino.RhinoDoc, "ActiveDoc", None)
        path = getattr(doc, "Path", None) or ""
        return str(path) if path else None

    def note(self, message: str) -> None:
        text = str(message)
        print(text)
        try:
            Rhino, _rs, _sc = _rhino_modules()
            Rhino.RhinoApp.WriteLine(text)
        except Exception:
            pass

    def now(self) -> float:
        return time.time()

    def refresh_worksession(self) -> bool:
        try:
            Rhino, rs, _sc = _rhino_modules()
        except RuntimeError:
            return False
        try:
            if bool(Rhino.RhinoApp.RunScript(REFRESH_SCRIPT, False)):
                return True
        except Exception:
            pass
        command = getattr(rs, "Command", None)
        if not callable(command):
            return False
        try:
            return bool(command(REFRESH_SCRIPT, False))
        except Exception:
            return False

    def start_watch(self, directory: str, on_changed: Callable[[str], None]) -> FileWatchHandle:
        return FileWatchHandle(directory, on_changed)

    def start_idle(self, on_idle: Callable[[], None]) -> IdleHandle:
        return IdleHandle(on_idle)


def sticky_store() -> MutableMapping[str, Any]:
    try:
        _Rhino, _rs, sc = _rhino_modules()
    except RuntimeError:
        return {}
    sticky = getattr(sc, "sticky", None)
    if sticky is None:
        sc.sticky = {}
        sticky = sc.sticky
    return sticky
