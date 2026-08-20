# -*- coding: utf-8 -*-
"""E04 Sync Worksession：register／unregister、debounce Refresh、失敗保留參照。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.worksession.sync import (
    COMMAND_ID,
    DEFAULT_DELAY_SECONDS,
    STICKY_KEY,
    is_temp_model_name,
    refresh_due,
    run_sync_worksession,
    same_directory,
    watch_directory,
)


class FakeHost:
    def __init__(self, path=None, refresh_ok=True) -> None:
        self.path = path
        self.refresh_ok = refresh_ok
        self.fail_remaining = 0
        self.notes = []
        self.refresh_calls = 0
        self.watch_dirs = []
        self.watch_cb = None
        self.idle_cb = None
        self.stopped_watch = 0
        self.stopped_idle = 0
        self._now = 0.0
        self.watch_error = None

    def document_path(self):
        return self.path

    def note(self, message: str) -> None:
        self.notes.append(message)

    def now(self) -> float:
        return self._now

    def refresh_worksession(self) -> bool:
        self.refresh_calls += 1
        if self.fail_remaining > 0:
            self.fail_remaining -= 1
            return False
        return bool(self.refresh_ok)

    def start_watch(self, directory: str, on_changed):
        if self.watch_error:
            raise RuntimeError(self.watch_error)
        self.watch_dirs.append(directory)
        self.watch_cb = on_changed

        def stop() -> None:
            self.stopped_watch += 1
            self.watch_cb = None

        return stop

    def start_idle(self, on_idle):
        self.idle_cb = on_idle

        def stop() -> None:
            self.stopped_idle += 1
            self.idle_cb = None

        return stop


class WorksessionHelperTests(unittest.TestCase):
    def test_temp_names_are_ignored(self):
        self.assertTrue(is_temp_model_name("model.3dm~"))
        self.assertTrue(is_temp_model_name("~auto.3dm"))
        self.assertTrue(is_temp_model_name("model.tmp.3dm"))
        self.assertFalse(is_temp_model_name("House.3dm"))

    def test_watch_directory_needs_saved_path(self):
        self.assertIsNone(watch_directory(None))
        self.assertIsNone(watch_directory(""))
        self.assertEqual(
            watch_directory(r"E:\proj\sheet.3dm"),
            r"E:\proj",
        )

    def test_same_directory_ignores_case(self):
        self.assertTrue(same_directory(r"E:\Proj", r"e:\proj"))
        self.assertFalse(same_directory(r"E:\a", r"E:\b"))

    def test_refresh_waits_for_delay(self):
        self.assertFalse(refresh_due(True, 1.0, 1.4, 0.5))
        self.assertTrue(refresh_due(True, 1.0, 1.6, 0.5))
        self.assertFalse(refresh_due(False, 1.0, 9.0, 0.5))


class WorksessionCommandTests(unittest.TestCase):
    def test_unsaved_document_does_not_watch(self):
        host = FakeHost(path=None)
        store = {}
        result = run_sync_worksession(host, store)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertIn("存到磁碟", result.message)
        self.assertEqual(host.watch_dirs, [])
        self.assertNotIn(STICKY_KEY, store)

    def test_start_then_stop_unregisters(self):
        host = FakeHost(path=r"E:\proj\sheet.3dm")
        store = {}
        started = run_sync_worksession(host, store, delay_seconds=0.5)
        self.assertTrue(started.ok)
        self.assertEqual(started.details["action"], "started")
        self.assertEqual(started.command_id, COMMAND_ID)
        self.assertEqual(len(host.watch_dirs), 1)
        self.assertIsNotNone(host.idle_cb)

        stopped = run_sync_worksession(host, store, delay_seconds=0.5)
        self.assertTrue(stopped.ok)
        self.assertEqual(stopped.details["action"], "stopped")
        self.assertEqual(host.stopped_watch, 1)
        self.assertEqual(host.stopped_idle, 1)
        self.assertNotIn(STICKY_KEY, store)
        self.assertIsNone(host.idle_cb)

    def test_reload_when_directory_changes(self):
        host = FakeHost(path=r"E:\old\sheet.3dm")
        store = {}
        run_sync_worksession(host, store)
        host.path = r"E:\new\sheet.3dm"
        reloaded = run_sync_worksession(host, store)
        self.assertTrue(reloaded.ok)
        self.assertEqual(reloaded.details["action"], "reloaded")
        self.assertEqual(len(host.watch_dirs), 2)
        self.assertTrue(host.watch_dirs[-1].endswith("new"))
        self.assertEqual(host.stopped_watch, 1)

    def test_temp_change_does_not_refresh(self):
        host = FakeHost(path=r"E:\proj\sheet.3dm")
        store = {}
        run_sync_worksession(host, store, delay_seconds=0.5)
        host.watch_cb("model.tmp.3dm")
        host._now = 2.0
        host.idle_cb()
        self.assertEqual(host.refresh_calls, 0)

    def test_change_refreshes_after_delay(self):
        host = FakeHost(path=r"E:\proj\sheet.3dm")
        store = {}
        run_sync_worksession(host, store, delay_seconds=0.5)
        host._now = 1.0
        host.watch_cb("House.3dm")
        host.idle_cb()
        self.assertEqual(host.refresh_calls, 0)
        host._now = 1.6
        host.idle_cb()
        self.assertEqual(host.refresh_calls, 1)
        self.assertIn("已更新 Worksession 參照。", host.notes)

    def test_failed_refresh_keeps_reference_and_retries(self):
        host = FakeHost(path=r"E:\proj\sheet.3dm")
        host.fail_remaining = 1
        store = {}
        run_sync_worksession(host, store, delay_seconds=0.5)
        host._now = 1.0
        host.watch_cb("House.3dm")
        host._now = 1.6
        host.idle_cb()
        self.assertEqual(host.refresh_calls, 1)
        self.assertIn("上一份參照未改動", "".join(host.notes))
        host._now = 2.2
        host.idle_cb()
        self.assertEqual(host.refresh_calls, 2)
        self.assertIn("已更新 Worksession 參照。", host.notes)

    def test_idle_after_stop_does_not_refresh(self):
        host = FakeHost(path=r"E:\proj\sheet.3dm")
        store = {}
        run_sync_worksession(host, store, delay_seconds=0.5)
        idle = host.idle_cb
        host.watch_cb("House.3dm")
        run_sync_worksession(host, store, delay_seconds=0.5)
        host._now = 9.0
        idle()
        self.assertEqual(host.refresh_calls, 0)

    def test_watch_error_does_not_leave_sticky(self):
        host = FakeHost(path=r"E:\proj\sheet.3dm")
        host.watch_error = "path missing"
        store = {}
        result = run_sync_worksession(host, store)
        self.assertFalse(result.ok)
        self.assertNotIn(STICKY_KEY, store)
        self.assertEqual(host.stopped_watch, 0)

    def test_default_delay_matches_legacy(self):
        self.assertEqual(DEFAULT_DELAY_SECONDS, 0.5)


if __name__ == "__main__":
    unittest.main()
