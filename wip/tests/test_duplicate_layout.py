# -*- coding: utf-8 -*-
"""E03 Duplicate Layout：新 ID、契約清／留、不碰剪貼簿、取消零寫入。"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.catalog.keys import CATALOG_ID_KEY, POINT_ID_KEY
from loopflow.features.catalog.keys import SHEET_ID_KEY as CATALOG_SHEET_ID_KEY
from loopflow.features.drawing import keys as drawing_keys
from loopflow.features.health.appearance import COLOR_BROKEN_RGB
from loopflow.features.infuser.keys import (
    DETAIL_NO_KEY,
    DW_HEIGHT_KEY,
    DW_ID_KEY,
    DW_WIDTH_KEY,
    ELEVATION_DISPLAY_KEY,
    REMARKS_MANUAL_KEY,
)
from loopflow.features.sheet.duplicate import (
    COMMAND_ID,
    MANUAL_BLANK,
    next_copy_page_name,
    run_duplicate_layout,
)
from loopflow.features.sheet.keys import DRAWING_NAME_KEY, DRAWING_NO_KEY, SCALE_KEY, SHEET_ID_KEY
from loopflow.features.sheet.naming import NamingRules
from loopflow.features.tagger.binding import UUID_V4_RE
from loopflow.features.tagger.keys import (
    HEALTH_STATE_BROKEN,
    HEALTH_STATE_KEY,
    HOST_SHEET_ID_KEY,
    LOCK_STATE_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_VIEW_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.platform.rhino.memory import MemorySession

PAGE = "**IN__201__立面圖"
PAGE2 = "IN__202__平面圖"
SHEET_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OTHER_SHEET = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
TAG_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
DW_TAG_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
INDEX_TAG_ID = "11111111-1111-4111-8111-111111111111"
ELEV0_TAG_ID = "22222222-2222-4222-8222-222222222222"
CATALOG_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
DRAWING_ID = "ffffffff-ffff-4fff-8fff-ffffffffffff"
ELEMENT_ID = "99999999-9999-4999-8999-999999999999"
VIEW_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
SOURCE_UUID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _session() -> MemorySession:
    session = MemorySession()
    session.set_layout_pages([PAGE])
    session.add_object(
        "frame",
        user_text={
            SHEET_ID_KEY: SHEET_ID,
            DRAWING_NO_KEY: "IN 201",
            DRAWING_NAME_KEY: "立面圖",
            SCALE_KEY: "1:50",
            TAG_ID_KEY: "55555555-5555-4555-8555-555555555555",
        },
    )
    session.set_block("frame", (0.0, 0.0, 0.0), "Sample_Frame")
    session.add_object_to_layout_page(PAGE, "frame")

    session.add_object(
        "grab",
        user_text={
            TAG_ID_KEY: TAG_ID,
            TEMPLATE_ID_KEY: "TAG_HEIGHT_GRAB",
            SOURCE_OBJECT_ID_KEY: SOURCE_UUID,
            HOST_SHEET_ID_KEY: SHEET_ID,
            ELEVATION_DISPLAY_KEY: "FL+150",
            REMARKS_MANUAL_KEY: "手寫備註",
            LOCK_STATE_KEY: "true",
            "attr_Lock_不更新>寫入x或X": "X",
        },
    )
    session.set_block("grab", (10.0, 0.0, 0.0), "TAG_HEIGHT_GRAB")
    session.add_object_to_layout_page(PAGE, "grab")

    session.add_object(
        "dw",
        user_text={
            TAG_ID_KEY: DW_TAG_ID,
            TEMPLATE_ID_KEY: "TAG_DW",
            DW_ID_KEY: "D-01",
            DW_WIDTH_KEY: "90",
            DW_HEIGHT_KEY: "210",
            HOST_SHEET_ID_KEY: SHEET_ID,
        },
    )
    session.set_block("dw", (20.0, 0.0, 0.0), "TAG_DW")
    session.add_object_to_layout_page(PAGE, "dw")

    session.add_object(
        "index",
        user_text={
            TAG_ID_KEY: INDEX_TAG_ID,
            TEMPLATE_ID_KEY: "TAG_SECTION_DETAIL",
            TARGET_VIEW_ID_KEY: VIEW_ID,
            TARGET_LAYOUT_KEY: PAGE,
            DETAIL_NO_KEY: "A",
            "lf_sheet_code": "IN",
            "lf_sheet_ref": "201",
        },
    )
    session.set_block("index", (30.0, 0.0, 0.0), "TAG_SECTION_DETAIL")
    session.add_object_to_layout_page(PAGE, "index")

    session.add_object(
        "elev0",
        user_text={
            TAG_ID_KEY: ELEV0_TAG_ID,
            TEMPLATE_ID_KEY: "TAG_ELEV_0",
            "lf_sheet_code": "IN 201",
            "lf_dir_num": "1",
            "lf_dir_elev": "北",
        },
    )
    session.set_block("elev0", (40.0, 0.0, 0.0), "TAG_ELEV_0")
    session.add_object_to_layout_page(PAGE, "elev0")

    session.add_object(
        "cat",
        layer="LoopFlow::Drawing_Number",
        user_text={
            CATALOG_ID_KEY: CATALOG_ID,
            CATALOG_SHEET_ID_KEY: SHEET_ID,
            POINT_ID_KEY: "cat",
        },
    )
    session._points["cat"] = (5.0, 5.0, 0.0)
    session.add_object_to_layout_page(PAGE, "cat")

    session.add_object(
        "cat_other",
        layer="LoopFlow::Drawing_Number",
        user_text={
            CATALOG_ID_KEY: CATALOG_ID,
            CATALOG_SHEET_ID_KEY: OTHER_SHEET,
        },
    )
    session._points["cat_other"] = (6.0, 5.0, 0.0)
    session.add_object_to_layout_page(PAGE, "cat_other")

    session.add_object(
        "drawing",
        user_text={
            drawing_keys.DRAWING_ID_KEY: DRAWING_ID,
            drawing_keys.DRAWING_ELEMENT_ID_KEY: ELEMENT_ID,
        },
    )
    session.add_object_to_layout_page(PAGE, "drawing")
    session.set_document_modified(False)
    return session


def _snapshot(session: MemorySession) -> dict:
    return {
        "ids": set(session.iter_object_ids()),
        "pages": tuple(item["name"] for item in session.listed_layout_pages()),
        "modified": session.document_modified(),
        "objects": copy.deepcopy(session._object_meta),
        "clipboard": list(session.clipboard_ops),
    }


def _copied_page(session: MemorySession) -> str:
    names = [item["name"] for item in session.listed_layout_pages() if item["name"] != PAGE]
    assert len(names) == 1
    return names[0]


def _on_page(session: MemorySession, page_name: str, block_name: str) -> str:
    for object_id in session.objects_on_layout_page(page_name):
        if session.block_definition_name(object_id) == block_name:
            return object_id
    raise AssertionError("找不到 %s" % block_name)


def _run(session, page=PAGE, count=1):
    messages = []
    result = run_duplicate_layout(
        session,
        pick_pages=lambda _current, _names: page,
        pick_count=lambda _current: count,
        show_message=messages.append,
    )
    return result, messages


class NamingTests(unittest.TestCase):
    def test_structured_name_keeps_three_columns_without_star(self):
        name = next_copy_page_name("**IN__201__立面圖", 1, (), NamingRules())
        self.assertEqual(name, "IN__201__立面圖_Copy1")
        self.assertFalse(name.startswith("**"))

    def test_unique_suffix_when_name_exists(self):
        name = next_copy_page_name(
            "**IN__201__立面圖", 1, ("IN__201__立面圖_Copy1",), NamingRules()
        )
        self.assertEqual(name, "IN__201__立面圖_Copy1_1")


class DuplicateLayoutTests(unittest.TestCase):
    def test_cancel_page_writes_nothing(self):
        session = _session()
        before = _snapshot(session)
        result = run_duplicate_layout(
            session,
            pick_pages=lambda _current, _names: None,
            pick_count=lambda _current: 1,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session), before)

    def test_cancel_count_writes_nothing(self):
        session = _session()
        before = _snapshot(session)
        result = run_duplicate_layout(
            session,
            pick_pages=lambda _current, _names: PAGE,
            pick_count=lambda _current: None,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session), before)

    def test_no_layouts_blocked(self):
        session = MemorySession()
        result, _messages = _run(session, page="x")
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "blocked")
        self.assertIn("no_layouts", result.blocking)

    def test_empty_layout_blocked(self):
        session = MemorySession()
        session.set_layout_pages(["Blank"])
        result, _messages = _run(session, page="Blank")
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "blocked")
        self.assertIn("empty_layout", result.blocking)
        self.assertEqual(tuple(item["name"] for item in session.listed_layout_pages()), ("Blank",))

    def test_duplicate_clears_and_keeps_contract_fields(self):
        session = _session()
        source_meta = copy.deepcopy(session._object_meta)
        result, messages = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.clipboard_ops, [])
        self.assertTrue(messages)
        copied = _copied_page(session)
        self.assertEqual(copied, "IN__201__立面圖_Copy1")

        frame = _on_page(session, copied, "Sample_Frame")
        new_sheet = session.get_object_user_text(frame, SHEET_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(new_sheet or ""))
        self.assertNotEqual(new_sheet, SHEET_ID)
        self.assertIsNone(session.get_object_user_text(frame, DRAWING_NO_KEY))
        self.assertIsNone(session.get_object_user_text(frame, DRAWING_NAME_KEY))
        self.assertEqual(session.get_object_user_text(frame, SCALE_KEY), "1:50")

        grab = _on_page(session, copied, "TAG_HEIGHT_GRAB")
        grab_id = session.get_object_user_text(grab, TAG_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(grab_id or ""))
        self.assertNotEqual(grab_id, TAG_ID)
        self.assertEqual(session.get_object_user_text(grab, TEMPLATE_ID_KEY), "TAG_HEIGHT_GRAB")
        self.assertIsNone(session.get_object_user_text(grab, SOURCE_OBJECT_ID_KEY))
        self.assertIsNone(session.get_object_user_text(grab, HOST_SHEET_ID_KEY))
        self.assertEqual(session.get_object_user_text(grab, ELEVATION_DISPLAY_KEY), "?")
        self.assertEqual(session.get_object_user_text(grab, REMARKS_MANUAL_KEY), MANUAL_BLANK)
        self.assertIn(REMARKS_MANUAL_KEY, session.object_user_text_keys(grab))
        self.assertEqual(session.get_object_user_text(grab, LOCK_STATE_KEY), "true")
        self.assertEqual(session.get_object_user_text(grab, "attr_Lock_不更新>寫入x或X"), "X")
        self.assertEqual(session.get_object_user_text(grab, HEALTH_STATE_KEY), HEALTH_STATE_BROKEN)
        grab_state = session.get_view_state(grab)
        self.assertIsNotNone(grab_state)
        self.assertEqual(grab_state.color, COLOR_BROKEN_RGB)
        self.assertFalse(grab_state.color_by_layer)

        dw = _on_page(session, copied, "TAG_DW")
        dw_id = session.get_object_user_text(dw, TAG_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(dw_id or ""))
        self.assertNotEqual(dw_id, DW_TAG_ID)
        self.assertEqual(session.get_object_user_text(dw, DW_ID_KEY), "D-01")
        self.assertEqual(session.get_object_user_text(dw, DW_WIDTH_KEY), "90")
        self.assertEqual(session.get_object_user_text(dw, DW_HEIGHT_KEY), "210")
        self.assertIsNone(session.get_object_user_text(dw, HOST_SHEET_ID_KEY))
        dw_state = session.get_view_state(dw)
        self.assertTrue(dw_state.color_by_layer)

        index = _on_page(session, copied, "TAG_SECTION_DETAIL")
        self.assertIsNone(session.get_object_user_text(index, TARGET_VIEW_ID_KEY))
        self.assertIsNone(session.get_object_user_text(index, TARGET_LAYOUT_KEY))
        self.assertEqual(session.get_object_user_text(index, DETAIL_NO_KEY), MANUAL_BLANK)
        self.assertIn(DETAIL_NO_KEY, session.object_user_text_keys(index))
        self.assertEqual(session.get_object_user_text(index, "lf_sheet_code"), "?")
        self.assertEqual(session.get_object_user_text(index, HEALTH_STATE_KEY), HEALTH_STATE_BROKEN)
        index_state = session.get_view_state(index)
        self.assertEqual(index_state.color, COLOR_BROKEN_RGB)
        self.assertFalse(index_state.color_by_layer)

        elev0 = _on_page(session, copied, "TAG_ELEV_0")
        self.assertEqual(session.get_object_user_text(elev0, "lf_dir_num"), MANUAL_BLANK)
        self.assertEqual(session.get_object_user_text(elev0, "lf_dir_elev"), MANUAL_BLANK)
        self.assertIn("lf_dir_num", session.object_user_text_keys(elev0))
        self.assertEqual(session.get_object_user_text(elev0, "lf_sheet_code"), "?")

        cat_ids = [
            object_id
            for object_id in session.objects_on_layout_page(copied)
            if session.get_object_user_text(object_id, CATALOG_ID_KEY)
        ]
        new_catalog = {
            session.get_object_user_text(object_id, CATALOG_ID_KEY) for object_id in cat_ids
        }
        self.assertEqual(len(new_catalog), 1)
        self.assertNotIn(CATALOG_ID, new_catalog)
        remapped = [
            object_id
            for object_id in cat_ids
            if session.get_object_user_text(object_id, CATALOG_SHEET_ID_KEY) == new_sheet
        ]
        kept_other = [
            object_id
            for object_id in cat_ids
            if session.get_object_user_text(object_id, CATALOG_SHEET_ID_KEY) == OTHER_SHEET
        ]
        self.assertEqual(len(remapped), 1)
        self.assertEqual(len(kept_other), 1)

        drawings = [
            object_id
            for object_id in session.objects_on_layout_page(copied)
            if session.get_object_user_text(object_id, drawing_keys.DRAWING_ID_KEY)
        ]
        self.assertEqual(len(drawings), 1)
        new_drawing = session.get_object_user_text(drawings[0], drawing_keys.DRAWING_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(new_drawing or ""))
        self.assertNotEqual(new_drawing, DRAWING_ID)
        self.assertNotEqual(
            session.get_object_user_text(drawings[0], drawing_keys.DRAWING_ELEMENT_ID_KEY),
            ELEMENT_ID,
        )

        self.assertEqual(session._object_meta["frame"], source_meta["frame"])
        self.assertEqual(session._object_meta["grab"], source_meta["grab"])
        self.assertEqual(session._object_meta["dw"], source_meta["dw"])
        self.assertIn("frame", session.objects_on_layout_page(PAGE))

    def test_rerun_makes_another_page_with_new_ids(self):
        session = _session()
        first, _ = _run(session)
        self.assertTrue(first.ok)
        second, _ = _run(session)
        self.assertTrue(second.ok)
        names = [item["name"] for item in session.listed_layout_pages()]
        self.assertEqual(len(names), 3)
        self.assertIn("IN__201__立面圖_Copy1", names)
        self.assertIn("IN__201__立面圖_Copy1_1", names)
        frames = [
            object_id
            for object_id in session.iter_object_ids()
            if session.block_definition_name(object_id) == "Sample_Frame"
        ]
        sheet_ids = {
            session.get_object_user_text(object_id, SHEET_ID_KEY) for object_id in frames
        }
        self.assertEqual(len(sheet_ids), 3)

    def test_registered_custom_frame_gets_new_sheet_id(self):
        from loopflow.features.sheet.metadata import register_title_frame_names

        session = _session()
        session.set_block("frame", (0.0, 0.0, 0.0), "_Frame_A3_shop_drawing")
        register_title_frame_names(session, ["_Frame_A3_shop_drawing"])
        result, _messages = _run(session)
        self.assertTrue(result.ok, result.message)
        copied = _copied_page(session)
        frame = _on_page(session, copied, "_Frame_A3_shop_drawing")
        new_sheet = session.get_object_user_text(frame, SHEET_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(new_sheet or ""))
        self.assertNotEqual(new_sheet, SHEET_ID)
        self.assertIsNone(session.get_object_user_text(frame, DRAWING_NO_KEY))
        self.assertIsNone(session.get_object_user_text(frame, DRAWING_NAME_KEY))
        self.assertEqual(session.get_object_user_text(frame, SCALE_KEY), "1:50")
        self.assertEqual(session.get_object_user_text("frame", SHEET_ID_KEY), SHEET_ID)

    def test_two_copies_create_two_pages(self):
        session = _session()
        result, _ = _run(session, count=2)
        self.assertTrue(result.ok, result.message)
        names = [item["name"] for item in session.listed_layout_pages()]
        self.assertEqual(
            names,
            [PAGE, "IN__201__立面圖_Copy1", "IN__201__立面圖_Copy2"],
        )

    def test_empty_selection_is_cancel(self):
        session = _session()
        before = _snapshot(session)
        result = run_duplicate_layout(
            session,
            pick_pages=lambda _current, _names: (),
            pick_count=lambda _current: 1,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session), before)

    def test_two_source_pages_use_one_copy_count(self):
        session = _session()
        session.add_object(
            "frame2",
            user_text={SHEET_ID_KEY: OTHER_SHEET, SCALE_KEY: "1:100"},
        )
        session.set_block("frame2", (0.0, 0.0, 0.0), "Sample_Frame")
        session.add_object_to_layout_page(PAGE2, "frame2")
        result, _ = _run(session, page=(PAGE, PAGE2), count=2)
        self.assertTrue(result.ok, result.message)
        names = [item["name"] for item in session.listed_layout_pages()]
        self.assertEqual(
            names,
            [
                PAGE,
                PAGE2,
                "IN__201__立面圖_Copy1",
                "IN__201__立面圖_Copy2",
                "IN__202__平面圖_Copy1",
                "IN__202__平面圖_Copy2",
            ],
        )
        self.assertEqual((result.details or {}).get("count"), 4)
        self.assertEqual(
            (result.details or {}).get("sources"),
            (PAGE, PAGE2),
        )

    def test_empty_page_in_selection_writes_nothing(self):
        session = _session()
        session.set_layout_pages([PAGE, "Blank"])
        before = _snapshot(session)
        result, _ = _run(session, page=(PAGE, "Blank"), count=1)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "blocked")
        self.assertIn("empty_layout", result.blocking)
        self.assertEqual(_snapshot(session), before)

    def test_source_does_not_use_clipboard(self):
        source = (SRC / "loopflow" / "features" / "sheet" / "duplicate.py").read_text(
            encoding="utf-8"
        )
        live = (SRC / "loopflow" / "platform" / "rhino" / "live.py").read_text(encoding="utf-8")
        for text in (source, live):
            self.assertNotIn("CopyToClipboard", text)
            self.assertNotIn("_-Paste", text)
        self.assertIn("ask_popup_integer", source)
        self.assertIn("ask_layout_pages_choice", source)
        self.assertNotIn("ask_integer(", source)
        prompts = (SRC / "loopflow" / "platform" / "rhino" / "prompts.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("forms.GridView", prompts)
        self.assertIn("def ask_layout_pages_choice", prompts)
        self.assertIn("forms.Scrollable", prompts)
        self.assertIn("def _ok_cancel_row", prompts)
        self.assertIn('btn_ok.Text = "OK"', prompts)
        self.assertIn("AddRow(None, btn_ok, btn_cancel)", prompts)
        self.assertNotIn("確定（Enter）", prompts)
        self.assertNotIn("取消（Esc）", prompts)
        self.assertNotIn("btn_cancel, btn_ok", prompts)

    def test_command_id(self):
        self.assertEqual(COMMAND_ID, "LF_Duplicate_Layout")


if __name__ == "__main__":
    unittest.main()
