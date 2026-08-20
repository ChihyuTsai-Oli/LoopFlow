# -*- coding: utf-8 -*-
"""Rhino Worksession 監看：FileSystemWatcher、Idle、Refresh。

模組載入不 import Rhino。只 Refresh 既有 Worksession，不 Attach／Detach。
"""
from __future__ import annotations

import time
from typing import Any, Callable, MutableMapping, Optional

from loopflow.platform.rhino.live import _load_rhino

REFRESH_SCRIPT = "_-Worksession _Refresh _Enter"


class LiveWorksessionHost:
    def document_path(self) -> Optional[str]:
        loaded, _error = _load_rhino()
        if loaded is None:
            return None
        _Rhino, _rs, sc = loaded
        doc = getattr(sc, "doc", None)
        path = getattr(doc, "Path", None) or ""
        return str(path) if path else None

    def note(self, message: str) -> None:
        loaded, _error = _load_rhino()
        if loaded is None:
            print(message)
            return
        Rhino, _rs, _sc = loaded
        try:
            Rhino.RhinoApp.WriteLine(str(message))
        except Exception:
            print(message)

    def now(self) -> float:
        return time.time()

    def refresh_worksession(self) -> bool:
        loaded, _error = _load_rhino()
        if loaded is None:
            return False
        Rhino, _rs, _sc = loaded
        try:
            return bool(Rhino.RhinoApp.RunScript(REFRESH_SCRIPT, False))
        except Exception:
            return False

    def start_watch(self, directory: str, on_changed: Callable[[str], None]) -> Callable[[], None]:
        loaded, error = _load_rhino()
        if loaded is None:
            raise RuntimeError(error or "無法載入 Rhino")
        import System.IO  # type: ignore

        watcher = System.IO.FileSystemWatcher()
        try:
            watcher.Path = directory
            watcher.Filter = "*.3dm"
            watcher.NotifyFilter = System.IO.NotifyFilters.LastWrite

            def _on_changed(_sender, event) -> None:
                name = getattr(event, "Name", "") or ""
                on_changed(str(name))

            watcher.Changed += _on_changed
            watcher.EnableRaisingEvents = True
        except Exception:
            dispose = getattr(watcher, "Dispose", None)
            if callable(dispose):
                try:
                    dispose()
                except Exception:
                    pass
            raise

        def stop() -> None:
            try:
                watcher.EnableRaisingEvents = False
            except Exception:
                pass
            try:
                watcher.Changed -= _on_changed
            except Exception:
                pass
            dispose = getattr(watcher, "Dispose", None)
            if callable(dispose):
                try:
                    dispose()
                except Exception:
                    pass

        return stop

    def start_idle(self, on_idle: Callable[[], None]) -> Callable[[], None]:
        loaded, error = _load_rhino()
        if loaded is None:
            raise RuntimeError(error or "無法載入 Rhino")
        Rhino, _rs, _sc = loaded

        def _on_idle(_sender, _event) -> None:
            on_idle()

        Rhino.RhinoApp.Idle += _on_idle

        def stop() -> None:
            try:
                Rhino.RhinoApp.Idle -= _on_idle
            except Exception:
                pass

        return stop


def sticky_store() -> MutableMapping[str, Any]:
    loaded, _error = _load_rhino()
    if loaded is None:
        return {}
    _Rhino, _rs, sc = loaded
    sticky = getattr(sc, "sticky", None)
    if sticky is None:
        sc.sticky = {}
        sticky = sc.sticky
    return sticky
