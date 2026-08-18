# -*- coding: utf-8 -*-
"""D04 Tagger Layout ID：建立 Sheet metadata，只寫已登錄圖框的圖號／圖名。"""
from __future__ import annotations

import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.bootstrap import run_command
from loopflow.command_catalog import get_command
from loopflow.features.sheet.keys import (
    DRAWING_NAME_KEY,
    DRAWING_NO_KEY,
    SCALE_KEY,
    SHEET_CODE_KEY,
    SHEET_ID_KEY,
    TITLE_FRAME_REGISTRY_KEY,
)
from loopflow.features.sheet.metadata import get_sheet_field
from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    LOCK_STATE_KEY,
    TAG_ID_KEY,
    TARGET_SHEET_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.features.tagger.layout_id import run_tagger_layout_id
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
LEGACY_NO = "DWG_NO"
LEGACY_NAME = "DWG_NAME"


def _session(pages=None) -> MemorySession:
    session = MemorySession(
        document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.project",
            "lf_schema_version": "1",
        }
    )
    if pages:
        session.set_layout_pages(pages)
    session.set_document_modified(False)
    return session


def _add_block(session, object_id, page_name, block_name, **user_text):
    session.add_object(object_id, name=block_name, user_text=user_text)
    session.set_block(object_id, (0, 0, 0), name=block_name)
    session.add_object_to_layout_page(page_name, object_id)


def _snapshot(session):
    return copy.deepcopy(session._object_meta), dict(session._document_text), list(session._layout_pages)


class LayoutIdCommandTests(unittest.TestCase):
    def test_first_import_writes_canonical_keys(self):
        session = _session(["IN 101.01__一樓平面圖", "IN__天花詳圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame", **{SCALE_KEY: "1:50"})
        _add_block(session, "frame-2", "IN__天花詳圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101.01")
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NAME_KEY), "一樓平面圖")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 101.02")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NAME_KEY), "天花詳圖")
        self.assertEqual(session.get_object_user_text("frame-1", SCALE_KEY), "1:50")
        self.assertIsNone(session.get_object_user_text("frame-1", LEGACY_NO))
        self.assertIsNone(session.get_object_user_text("frame-1", LEGACY_NAME))
        sheet_id = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        self.assertTrue(sheet_id)
        self.assertEqual(get_sheet_field(session, sheet_id, "drawing_no"), "IN 101.01")
        self.assertEqual(session.get_object_user_text("frame-1", BINDING_MODE_KEY), "none")
        self.assertEqual(session.get_object_user_text("frame-1", TEMPLATE_ID_KEY), "Sample_Frame")
        self.assertIsNotNone(session.get_object_user_text("frame-1", TAG_ID_KEY))
        self.assertEqual(
            [page["name"] for page in session.listed_layout_pages()],
            ["IN 101.01__一樓平面圖", "IN 101.02__天花詳圖"],
        )

    def test_rerun_keeps_sheet_id(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        first = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", SHEET_ID_KEY), first)
        self.assertEqual(result.details["created_sheet_ids"], 0)

    def test_insert_middle_renumbers_but_keeps_ids(self):
        session = _session(["IN 101.01__一樓平面圖", "IN__天花詳圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        _add_block(session, "frame-2", "IN__天花詳圖", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        first = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        second = session.get_object_user_text("frame-2", SHEET_ID_KEY)
        session.set_layout_pages(["IN 101.01__一樓平面圖", "IN__新增頁", "IN 101.02__天花詳圖"])
        _add_block(session, "frame-new", "IN__新增頁", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertEqual(session.get_object_user_text("frame-1", SHEET_ID_KEY), first)
        self.assertEqual(session.get_object_user_text("frame-2", SHEET_ID_KEY), second)
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 101.03")
        self.assertEqual(session.get_object_user_text("frame-new", DRAWING_NO_KEY), "IN 101.02")

    def test_manual_page_rename_restored_from_metadata(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        sheet_id = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        self.assertTrue(session.rename_layout_page("IN 101.01__一樓平面圖", "隨便改名"))
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertEqual(session.get_object_user_text("frame-1", SHEET_ID_KEY), sheet_id)
        self.assertEqual(session.listed_layout_pages()[0]["name"], "IN 101.01__一樓平面圖")

    def test_blank_layout_inherits_previous_series(self):
        session = _session(["IN 101.01__一樓平面圖", "Layout 05"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        _add_block(session, "frame-2", "Layout 05", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 101.02")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NAME_KEY), "Layout 05")

    def test_cover_before_series_is_skipped(self):
        session = _session(["封面", "IN 101.01__一樓平面圖"])
        _add_block(session, "frame-cover", "封面", "Sample_Frame")
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertTrue(result.ok, result.message)
        self.assertIsNone(session.get_object_user_text("frame-cover", DRAWING_NO_KEY))
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101.01")
        self.assertEqual(len(result.details["skipped"]), 1)

    def test_unregistered_block_not_written_when_refused(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "chair", "IN 101.01__一樓平面圖", "Random_Furniture")
        objects, document, pages = _snapshot(session)
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertFalse(result.ok)
        self.assertIn("missing_title_frame", result.blocking)
        self.assertEqual(session._object_meta, objects)
        self.assertEqual(session._document_text, document)
        self.assertEqual(session._layout_pages, pages)
        self.assertIsNone(session.document_user_text(TITLE_FRAME_REGISTRY_KEY))

    def test_two_frames_skip_page(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        _add_block(session, "frame-2", "IN 101.01__一樓平面圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertFalse(result.ok)
        self.assertIsNone(session.get_object_user_text("frame-1", DRAWING_NO_KEY))

    def test_locked_frame_skips_page(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame", **{LOCK_STATE_KEY: "true"})
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertFalse(result.ok)
        self.assertIsNone(session.get_object_user_text("frame-1", DRAWING_NO_KEY))

    def test_cancel_preview_is_zero_write(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        objects, document, pages = _snapshot(session)
        result = run_tagger_layout_id(session, confirm=lambda _lines: False, ask_register=lambda _names: False)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(session._object_meta, objects)
        self.assertEqual(session._document_text, document)
        self.assertEqual(session._layout_pages, pages)

    def test_elev0_writes_current_sheet_code_not_index_fields(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        _add_block(session, "elev0", "IN 101.01__一樓平面圖", "TAG_ELEV_0")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("elev0", SHEET_CODE_KEY), "101.01")
        self.assertIsNone(session.get_object_user_text("elev0", TARGET_SHEET_ID_KEY))
        self.assertIsNone(session.get_object_user_text("elev0", DRAWING_NO_KEY))

    def test_missing_schema_blocks(self):
        session = MemorySession()
        session.set_layout_pages(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertFalse(result.ok)
        self.assertIn("missing_document_schema", result.blocking)

    def test_no_layout_blocks(self):
        session = _session()
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertFalse(result.ok)
        self.assertIn("missing_layout", result.blocking)

    def test_selection_restored(self):
        session = _session(["IN 101.01__一樓平面圖"])
        _add_block(session, "frame-1", "IN 101.01__一樓平面圖", "Sample_Frame")
        session.set_view_state(
            ObjectViewState(
                object_id="frame-1",
                selected=True,
                locked=False,
                hidden=False,
                color=(0, 0, 0),
                color_by_layer=True,
            )
        )
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: False)
        self.assertTrue(session.get_view_state("frame-1").selected)

    def test_catalog_marks_layout_id_ready(self):
        spec = get_command("LF_Tagger_Layout_ID")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "D04")

    def test_run_command_without_rhino_does_not_claim_success(self):
        with redirect_stdout(io.StringIO()):
            result = run_command("LF_Tagger_Layout_ID")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")


if __name__ == "__main__":
    unittest.main()
