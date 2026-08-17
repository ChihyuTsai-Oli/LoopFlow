# -*- coding: utf-8 -*-
"""Rhino 視圖狀態 snapshot／restore：成功、取消、失敗與例外。"""
from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.foundation import results
from loopflow.platform.rhino.live import LIVE_VERIFIED_IN_RHINO, open_session, rgb_tuple
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.session import run_guarded
from loopflow.platform.rhino.state import ObjectViewState


def _sample_session() -> MemorySession:
    session = MemorySession()
    session.add_object("a", selected=True, locked=False, hidden=False, color=(10, 20, 30), color_by_layer=False)
    session.add_object("b", selected=False, locked=True, hidden=True, color=(1, 2, 3), color_by_layer=True)
    session.set_document_modified(False)
    return session


class SnapshotRestoreTests(unittest.TestCase):
    def test_restore_brings_back_view_fields(self):
        session = _sample_session()
        snap = session.snapshot()
        self.assertEqual(snap.object_ids(), ("a", "b"))
        session.set_view_state(ObjectViewState("a", False, True, True, (9, 9, 9), True))
        session.set_view_state(ObjectViewState("b", True, False, False, (8, 8, 8), False))
        restored = session.restore(snap, restore_document_modified=True)
        self.assertTrue(restored.ok)
        self.assertEqual(session.get_view_state("a"), snap.get("a"))
        self.assertEqual(session.get_view_state("b"), snap.get("b"))

    def test_lists_hidden_and_locked(self):
        session = _sample_session()
        self.assertEqual(session.iter_object_ids(include_hidden=True, include_locked=True), ("a", "b"))
        self.assertEqual(session.iter_object_ids(include_hidden=False, include_locked=True), ("a",))
        self.assertEqual(session.iter_object_ids(include_hidden=True, include_locked=False), ("a",))

    def test_success_keeps_document_modified(self):
        session = _sample_session()

        def apply_data(current):
            current.set_document_modified(True)
            current.set_view_state(ObjectViewState("a", False, False, False, (99, 0, 0), False))
            return results.ok("dispatch", "套用完成")

        outcome = run_guarded(session, apply_data, command_id="LF_Nexus")
        self.assertTrue(outcome.ok)
        self.assertTrue(session.document_modified())
        self.assertTrue(session.get_view_state("a").selected)
        self.assertEqual(session.get_view_state("a").color, (10, 20, 30))

    def test_cancel_restores_modified_and_selection(self):
        session = _sample_session()

        def cancel(current):
            current.set_document_modified(True)
            current.set_view_state(ObjectViewState("a", False, True, True, (0, 0, 0), True))
            return results.cancelled("dispatch", "使用者取消")

        outcome = run_guarded(session, cancel, command_id="LF_Nexus")
        self.assertEqual(outcome.status, "cancelled")
        self.assertFalse(session.document_modified())
        self.assertTrue(session.get_view_state("a").selected)
        self.assertFalse(session.get_view_state("a").locked)

    def test_failure_restores(self):
        session = _sample_session()

        def boom(current):
            current.set_view_state(ObjectViewState("b", True, False, False, (4, 5, 6), False))
            return results.failed("dispatch", "驗證失敗")

        outcome = run_guarded(session, boom)
        self.assertEqual(outcome.status, "failed")
        self.assertTrue(session.get_view_state("b").hidden)
        self.assertTrue(session.get_view_state("b").locked)

    def test_exception_restores_and_returns_failed(self):
        session = _sample_session()

        def crash(current):
            current.set_document_modified(True)
            current.set_view_state(ObjectViewState("a", False, False, False, (0, 0, 0), True))
            raise RuntimeError("simulated")

        outcome = run_guarded(session, crash, command_id="LF_Nexus")
        self.assertFalse(outcome.ok)
        self.assertEqual(outcome.status, "failed")
        self.assertEqual(outcome.stage, "guarded_run")
        self.assertFalse(session.document_modified())
        self.assertTrue(session.get_view_state("a").selected)
        self.assertIn("simulated", outcome.message)
        self.assertIn("RuntimeError", outcome.details["exception"])

    def test_missing_object_on_restore_fails(self):
        session = _sample_session()
        snap = session.snapshot()
        session.delete_object("b")
        restored = session.restore(snap, restore_document_modified=False)
        self.assertFalse(restored.ok)
        self.assertIn("b", restored.blocking)
        self.assertEqual(session.get_view_state("a"), snap.get("a"))


class LiveAdapterGuardTests(unittest.TestCase):
    def test_live_is_marked_verified(self):
        self.assertTrue(LIVE_VERIFIED_IN_RHINO)

    def test_open_session_without_rhino_fails(self):
        result = open_session()
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertIn("Rhino", result.message)

    def test_live_module_has_no_top_level_rhino_import(self):
        path = SRC / "loopflow" / "platform" / "rhino" / "live.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = []
        for node in tree.body:
            if isinstance(node, ast.Import):
                imported.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module.split(".")[0])
        self.assertNotIn("Rhino", imported)
        self.assertNotIn("rhinoscriptsyntax", imported)
        self.assertNotIn("scriptcontext", imported)


class ColorHelperTests(unittest.TestCase):
    def test_rgb_tuple_accepts_tuple_and_object(self):
        self.assertEqual(rgb_tuple((12, 34, 56)), (12, 34, 56))
        self.assertEqual(rgb_tuple(None), (0, 0, 0))

        class _Color:
            R, G, B = 1, 2, 3

        self.assertEqual(rgb_tuple(_Color()), (1, 2, 3))


class RedHintPopupTests(unittest.TestCase):
    def test_split_hint_message_pulls_out_reminder(self):
        from loopflow.platform.rhino.prompts import split_hint_message

        body, hint = split_hint_message(
            "有 1 件不符\n請執行選單 5 寫入模型 Metadata，把正確資料寫回。",
            "請執行選單 5 寫入模型 Metadata，把正確資料寫回。",
        )
        self.assertEqual(body, "有 1 件不符")
        self.assertEqual(hint, "請執行選單 5 寫入模型 Metadata，把正確資料寫回。")

    def test_split_hint_message_without_hint_keeps_body(self):
        from loopflow.platform.rhino.prompts import split_hint_message

        body, hint = split_hint_message("全部相符。", "請執行選單 5 寫入模型 Metadata，把正確資料寫回。")
        self.assertEqual(body, "全部相符。")
        self.assertIsNone(hint)


if __name__ == "__main__":
    unittest.main()
