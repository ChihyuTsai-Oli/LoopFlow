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
    LOCK_LEGACY_KEY,
    LOCK_LEGACY_HINT,
    LOCK_STATE_KEY,
    TAG_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_SHEET_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.features.sheet.naming import STATUS_BASELINE, STATUS_MANUAL, STATUS_NUMBERED, PagePlan
from loopflow.features.tagger.layout_id import (
    SERIES_START_HELP,
    SheetRow,
    preview_table_rows,
    run_tagger_layout_id,
)
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.prompts import format_result_popup
from loopflow.platform.rhino.state import ObjectViewState

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import bind_project  # noqa: E402

PROJECT_ID = "大安邸"
LEGACY_NO = "DWG_NO"
LEGACY_NAME = "DWG_NAME"
START_IN = "**IN__101__一樓平面圖"
PAGE_IN = START_IN
PAGE_IN_PLAIN = "IN__101__一樓平面圖"
PAGE_IN_2 = "IN__102__天花詳圖"


def _session(pages=None) -> MemorySession:
    session = MemorySession()
    bind_project(session, project_id=PROJECT_ID)
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
        session = _session([START_IN, "天花詳圖"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame", **{SCALE_KEY: "1:50"})
        _add_block(session, "frame-2", "天花詳圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NAME_KEY), "一樓平面圖")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 102")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NAME_KEY), "天花詳圖")
        self.assertEqual(session.get_object_user_text("frame-1", SCALE_KEY), "1:50")
        self.assertIsNone(session.get_object_user_text("frame-1", LEGACY_NO))
        self.assertIsNone(session.get_object_user_text("frame-1", LEGACY_NAME))
        sheet_id = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        self.assertTrue(sheet_id)
        self.assertEqual(get_sheet_field(session, sheet_id, "drawing_no"), "IN 101")
        self.assertEqual(session.get_object_user_text("frame-1", BINDING_MODE_KEY), "none")
        self.assertEqual(session.get_object_user_text("frame-1", TEMPLATE_ID_KEY), "Sample_Frame")
        self.assertIsNotNone(session.get_object_user_text("frame-1", TAG_ID_KEY))
        self.assertEqual(
            [page["name"] for page in session.listed_layout_pages()],
            [PAGE_IN, PAGE_IN_2],
        )

    def test_does_not_rewrite_legacy_drawing_keys(self):
        session = _session([START_IN])
        _add_block(
            session,
            "frame-1",
            START_IN,
            "Sample_Frame",
            **{LEGACY_NO: "舊號", LEGACY_NAME: "舊名"},
        )
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NAME_KEY), "一樓平面圖")
        self.assertEqual(session.get_object_user_text("frame-1", LEGACY_NO), "舊號")
        self.assertEqual(session.get_object_user_text("frame-1", LEGACY_NAME), "舊名")

    def test_rerun_keeps_sheet_id(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        first = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", SHEET_ID_KEY), first)
        self.assertEqual(result.details["created_sheet_ids"], 0)

    def test_insert_middle_renumbers_but_keeps_ids(self):
        session = _session([START_IN, "天花詳圖"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-2", "天花詳圖", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        first = session.get_object_user_text("frame-1", SHEET_ID_KEY)
        second = session.get_object_user_text("frame-2", SHEET_ID_KEY)
        session.set_layout_pages([PAGE_IN, "新增頁", PAGE_IN_2])
        _add_block(session, "frame-new", "新增頁", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertEqual(session.get_object_user_text("frame-1", SHEET_ID_KEY), first)
        self.assertEqual(session.get_object_user_text("frame-2", SHEET_ID_KEY), second)
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 103")
        self.assertEqual(session.get_object_user_text("frame-new", DRAWING_NO_KEY), "IN 102")

    def test_manual_page_rename_restored_from_metadata(self):
        session = _session([START_IN, "天花詳圖"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-2", "天花詳圖", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        sheet_id = session.get_object_user_text("frame-2", SHEET_ID_KEY)
        self.assertTrue(session.rename_layout_page(PAGE_IN_2, "隨便改名"))
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertEqual(session.get_object_user_text("frame-2", SHEET_ID_KEY), sheet_id)
        self.assertEqual(session.listed_layout_pages()[1]["name"], PAGE_IN_2)
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NAME_KEY), "天花詳圖")

    def test_stripped_star_stops_and_writes_nothing(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(session.rename_layout_page(PAGE_IN, PAGE_IN_PLAIN))
        objects, document, pages = _snapshot(session)
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIn("missing_series_start", result.blocking)
        self.assertEqual(result.message, SERIES_START_HELP)
        self.assertEqual(format_result_popup(result), SERIES_START_HELP)
        self.assertEqual(session._object_meta, objects)
        self.assertEqual(session._document_text, document)
        self.assertEqual(session._layout_pages, pages)

    def test_third_field_updates_drawing_name(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(session.rename_layout_page(PAGE_IN, "**IN__101__一樓平面"))
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NAME_KEY), "一樓平面")
        self.assertIsNone(session.get_object_user_text("frame-1", LEGACY_NAME))
        self.assertEqual(session.listed_layout_pages()[0]["name"], "**IN__101__一樓平面")

    def test_star_resets_series_start(self):
        session = _session([START_IN, "天花詳圖"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-2", "天花詳圖", "Sample_Frame")
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(session.rename_layout_page(PAGE_IN_2, "**IN__301__新系列"))
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 301")
        self.assertEqual(session.listed_layout_pages()[1]["name"], "**IN__301__新系列")

    def test_blank_layout_inherits_previous_series(self):
        session = _session([START_IN, "Layout 05"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-2", "Layout 05", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 102")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NAME_KEY), "Layout 05")

    def test_missing_star_explains_series_start(self):
        session = _session(["IN__101__一樓平面圖"])
        _add_block(session, "frame-1", "IN__101__一樓平面圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIn("missing_series_start", result.blocking)
        self.assertNotIn("missing_title_frame", result.blocking)
        self.assertEqual(result.message, SERIES_START_HELP)
        self.assertEqual(format_result_popup(result), SERIES_START_HELP)
        self.assertTrue(result.details["skipped"])
        self.assertIsNone(session.get_object_user_text("frame-1", DRAWING_NO_KEY))

    def test_missing_star_with_cover_still_only_help(self):
        session = _session(["Preset", "IN__101__一樓平面圖"])
        _add_block(session, "frame-1", "IN__101__一樓平面圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("missing_series_start",))
        self.assertEqual(result.message, SERIES_START_HELP)
        self.assertEqual(format_result_popup(result), SERIES_START_HELP)

    def test_slash_page_writes_without_consuming_series(self):
        session = _session([START_IN, "//S__901__結構平面圖", "天花詳圖"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-s", "//S__901__結構平面圖", "Sample_Frame")
        _add_block(session, "frame-2", "天花詳圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertEqual(session.get_object_user_text("frame-s", DRAWING_NO_KEY), "S 901")
        self.assertEqual(session.get_object_user_text("frame-s", DRAWING_NAME_KEY), "結構平面圖")
        self.assertEqual(session.get_object_user_text("frame-2", DRAWING_NO_KEY), "IN 102")
        self.assertEqual(
            [page["name"] for page in session.listed_layout_pages()],
            [PAGE_IN, "//S__901__結構平面圖", PAGE_IN_2],
        )

    def test_slash_only_writes_without_star(self):
        session = _session(["//S__901__結構平面圖"])
        _add_block(session, "frame-s", "//S__901__結構平面圖", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-s", DRAWING_NO_KEY), "S 901")
        self.assertEqual(session.listed_layout_pages()[0]["name"], "//S__901__結構平面圖")

    def test_invalid_slash_skips_page(self):
        session = _session([START_IN, "//結構"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-bad", "//結構", "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertIsNone(session.get_object_user_text("frame-bad", DRAWING_NO_KEY))

    def test_cover_before_series_is_skipped(self):
        session = _session(["封面", START_IN])
        _add_block(session, "frame-cover", "封面", "Sample_Frame")
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertIsNone(session.get_object_user_text("frame-cover", DRAWING_NO_KEY))
        self.assertEqual(session.get_object_user_text("frame-1", DRAWING_NO_KEY), "IN 101")
        self.assertEqual(len(result.details["skipped"]), 1)

    def test_unregistered_block_not_written_when_refused(self):
        session = _session([START_IN])
        _add_block(session, "chair", START_IN, "Random_Furniture")
        objects, document, pages = _snapshot(session)
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIn("missing_title_frame", result.blocking)
        self.assertEqual(session._object_meta, objects)
        self.assertEqual(session._document_text, document)
        self.assertEqual(session._layout_pages, pages)
        self.assertIsNone(session.document_user_text(TITLE_FRAME_REGISTRY_KEY))

    def test_register_only_picked_title_frame(self):
        session = _session([START_IN])
        _add_block(session, "tag-title", START_IN, "tag_title")
        _add_block(session, "tag-compass", START_IN, "tag_compass")
        _add_block(session, "frame", START_IN, "_Frame_A3_shop_drawing")
        result = run_tagger_layout_id(
            session,
            confirm=lambda _lines: True,
            ask_register=lambda names: tuple(
                name for name in names if name == "_Frame_A3_shop_drawing"
            ),
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.document_user_text(TITLE_FRAME_REGISTRY_KEY),
            "_Frame_A3_shop_drawing",
        )
        self.assertEqual(session.get_object_user_text("frame", DRAWING_NO_KEY), "IN 101")
        self.assertIsNone(session.get_object_user_text("tag-title", DRAWING_NO_KEY))
        self.assertIsNone(session.get_object_user_text("tag-compass", DRAWING_NO_KEY))

    def test_two_frames_skip_page(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-2", START_IN, "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIsNone(session.get_object_user_text("frame-1", DRAWING_NO_KEY))

    def test_locked_frame_skips_page(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame", **{LOCK_STATE_KEY: "true"})
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIsNone(session.get_object_user_text("frame-1", DRAWING_NO_KEY))

    def test_cancel_preview_is_zero_write(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        objects, document, pages = _snapshot(session)
        result = run_tagger_layout_id(session, confirm=lambda _lines: False, ask_register=lambda _names: ())
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(session._object_meta, objects)
        self.assertEqual(session._document_text, document)
        self.assertEqual(session._layout_pages, pages)

    def test_elev0_writes_current_sheet_code_not_index_fields(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "elev0", START_IN, "TAG_ELEV_0")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("elev0", SHEET_CODE_KEY), "101")
        self.assertIsNone(session.get_object_user_text("elev0", TARGET_SHEET_ID_KEY))
        self.assertIsNone(session.get_object_user_text("elev0", DRAWING_NO_KEY))

    def test_locked_elev0_skips_sheet_code(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "elev0", START_IN, "TAG_ELEV_0", **{LOCK_LEGACY_KEY: "x"})
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertIsNone(session.get_object_user_text("elev0", SHEET_CODE_KEY))
        self.assertEqual(session.get_object_user_text("elev0", LOCK_LEGACY_KEY), "x")
        self.assertIsNone(session.get_object_user_text("elev0", LOCK_STATE_KEY))

    def test_elev0_hint_still_writes_sheet_code(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "elev0", START_IN, "TAG_ELEV_0", **{LOCK_LEGACY_KEY: LOCK_LEGACY_HINT})
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("elev0", SHEET_CODE_KEY), "101")
        self.assertEqual(session.get_object_user_text("elev0", LOCK_LEGACY_KEY), LOCK_LEGACY_HINT)

    def test_missing_schema_blocks(self):
        session = MemorySession()
        bind_project(session, write_config=False)
        session.set_layout_pages([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIn("missing_document_schema", result.blocking)

    def test_rename_updates_index_target_layout(self):
        session = _session([START_IN, "天花詳圖"])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
        _add_block(session, "frame-2", "天花詳圖", "Sample_Frame")
        _add_block(
            session,
            "index-tag",
            START_IN,
            "TAG_SECTION_DETAIL",
            **{TARGET_LAYOUT_KEY: "天花詳圖"},
        )
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text("index-tag", TARGET_LAYOUT_KEY),
            PAGE_IN_2,
        )

    def test_no_layout_blocks(self):
        session = _session()
        result = run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
        self.assertFalse(result.ok)
        self.assertIn("missing_layout", result.blocking)

    def test_selection_restored(self):
        session = _session([START_IN])
        _add_block(session, "frame-1", START_IN, "Sample_Frame")
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
        run_tagger_layout_id(session, confirm=lambda _lines: True, ask_register=lambda _names: ())
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

    def test_preview_marks_new_sheet_with_arrow_name_and_number(self):
        new_row = SheetRow(
            page_name="地坪_Copy1",
            page_number=4,
            frame_id="frame-new",
            sheet_id=None,
            plan=PagePlan(
                page_name="地坪_Copy1",
                page_number=4,
                status=STATUS_NUMBERED,
                drawing_no="IN 101.02",
                drawing_name="地坪_Copy1",
                new_page_name="IN__101.02__地坪_Copy1",
            ),
            previous_drawing_no=None,
            previous_drawing_name=None,
        )
        existing = SheetRow(
            page_name="IN__101.01__地坪",
            page_number=3,
            frame_id="frame-old",
            sheet_id="sheet-1",
            plan=PagePlan(
                page_name="IN__101.01__地坪",
                page_number=3,
                status=STATUS_BASELINE,
                drawing_no="IN 101.01",
                drawing_name="地坪改",
                new_page_name="**IN__101.01__地坪改",
            ),
            previous_drawing_no="IN 101.01",
            previous_drawing_name="地坪",
        )
        table = preview_table_rows((new_row, existing), ())
        self.assertEqual(table[0][0], "IN__101.01__地坪")
        self.assertEqual(table[0][1], "**IN__101.01__地坪改")
        self.assertIn("系列起點", table[0][2])
        self.assertIn("圖名 地坪 → 地坪改", table[0][2])
        self.assertEqual(
            table[1],
            ("地坪_Copy1", "IN__101.02__地坪_Copy1", ""),
        )
        self.assertNotIn("[→]", table[1][2])
        self.assertNotIn("新頁", table[1][2])
        self.assertNotIn("頁名 →", table[0][2])

    def test_preview_follows_layout_page_order(self):
        first = SheetRow(
            page_name="**IN__101__一樓",
            page_number=1,
            frame_id="frame-1",
            sheet_id="sheet-1",
            plan=PagePlan(
                page_name="**IN__101__一樓",
                page_number=1,
                status=STATUS_BASELINE,
                drawing_no="IN 101",
                drawing_name="一樓",
                new_page_name="**IN__101__一樓",
            ),
            previous_drawing_no="IN 101",
            previous_drawing_name="一樓",
        )
        third = SheetRow(
            page_name="天花",
            page_number=3,
            frame_id="frame-3",
            sheet_id=None,
            plan=PagePlan(
                page_name="天花",
                page_number=3,
                status=STATUS_NUMBERED,
                drawing_no="IN 102",
                drawing_name="天花",
                new_page_name="IN__102__天花",
            ),
            previous_drawing_no=None,
            previous_drawing_name=None,
        )
        skipped = (
            {
                "page_name": "封面",
                "page_number": 2,
                "reason": "這一頁沒有圖框",
            },
        )
        table = preview_table_rows((third, first), skipped)
        self.assertEqual(
            [row[0] for row in table],
            ["**IN__101__一樓", "封面", "天花"],
        )
        self.assertIn("跳過", table[1][2])

    def test_preview_uses_layout_list_order_not_name_sort(self):
        manual = SheetRow(
            page_name="//IN__001.01__目錄1",
            page_number=1,
            frame_id="frame-2",
            sheet_id=None,
            plan=PagePlan(
                page_name="//IN__001.01__目錄1",
                page_number=1,
                status=STATUS_MANUAL,
                drawing_no="IN 001.01",
                drawing_name="目錄1",
                new_page_name="//IN__001.01__目錄1",
            ),
            previous_drawing_no=None,
            previous_drawing_name=None,
        )
        skipped = (
            {
                "page_name": "Preset",
                "page_number": 1,
                "reason": "頁序中還沒有系列起點，未編號",
            },
        )
        table = preview_table_rows(
            (manual,),
            skipped,
            page_order=("Preset", "//IN__001.01__目錄1", "//IN__001.02__目錄2"),
        )
        self.assertEqual(
            [row[0] for row in table],
            ["Preset", "//IN__001.01__目錄1"],
        )


if __name__ == "__main__":
    unittest.main()
