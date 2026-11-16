# -*- coding: utf-8 -*-
"""Sheet metadata API 與頁名編號純邏輯。不需 Rhino。"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.sheet.keys import (
    CATALOG_RESERVED_PREFIX,
    NAMING_DEFAULTS,
    SCALE_KEY,
    SHEET_ID_KEY,
)
from loopflow.features.sheet.metadata import (
    document_key,
    get_sheet_metadata,
    list_active_sheets,
    sheet_state,
    stale_among_sheet_ids,
    stale_sheet_ids,
    write_sheet_metadata,
)
from loopflow.features.sheet.naming import (
    NamingRules,
    STATUS_UNNUMBERED,
    assign_sheet_numbers,
    increment_number,
    parse_page_name,
)
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.platform.rhino.live import _page_view_key, layout_tab_ids, select_layout_pages
from loopflow.platform.rhino.memory import MemorySession

CASES = json.loads(
    (WIP / "fixtures" / "contract" / "sheet" / "cases.json").read_text(encoding="utf-8")
)
PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SHEET_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SHEET_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _catalog():
    loaded = load_tag_templates()
    assert loaded.ok
    return loaded.details["catalog"]


def _session() -> MemorySession:
    return MemorySession(
        document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.project",
            "lf_schema_version": "1",
        }
    )


class NamingTests(unittest.TestCase):
    def setUp(self):
        self.rules = NamingRules()

    def test_page_name_cases_match_contract(self):
        for case in CASES["page_name_cases"]:
            parsed = parse_page_name(case["page_name"], self.rules)
            self.assertEqual(parsed.kind, case["expect"], case["id"])
            if case["expect"] == "skip":
                self.assertIsNone(parsed.drawing_name)
                continue
            self.assertEqual(parsed.drawing_name, case.get("drawing_name", ""), case["id"])
            if case["expect"] in ("baseline", "manual"):
                self.assertEqual(parsed.prefix, case["series"], case["id"])
                self.assertEqual(parsed.number, case.get("number"), case["id"])

    def test_numbering_cases_match_contract(self):
        for case in CASES["numbering_cases"]:
            pages = [
                {"name": name, "page_number": index + 1}
                for index, name in enumerate(case["pages"])
            ]
            plans = assign_sheet_numbers(pages, self.rules)
            got = [plan.drawing_no for plan in plans]
            self.assertEqual(got, case["expect_drawing_no"], case["id"])
            expected_names = case.get("expect_drawing_name")
            if expected_names:
                self.assertEqual([plan.drawing_name for plan in plans], expected_names)
            expected_pages = case.get("expect_page_name")
            if expected_pages:
                self.assertEqual([plan.new_page_name for plan in plans], expected_pages, case["id"])

    def test_defaults_use_star_and_space_drawing_no(self):
        self.assertEqual(NAMING_DEFAULTS["separator"], "__")
        self.assertEqual(NAMING_DEFAULTS["baseline_mark"], "**")
        pages = [
            {"name": "**IN__201__立面圖", "page_number": 1},
            {"name": "天花詳圖", "page_number": 2},
        ]
        plans = assign_sheet_numbers(pages, self.rules)
        self.assertEqual(plans[0].drawing_no, "IN 201")
        self.assertEqual(plans[1].drawing_no, "IN 202")
        self.assertEqual(plans[0].new_page_name, "**IN__201__立面圖")
        self.assertEqual(plans[1].new_page_name, "IN__202__天花詳圖")
        self.assertNotIn("**", plans[0].drawing_no)

    def test_metadata_does_not_invent_star_without_page_mark(self):
        pages = [{"name": "IN__201__立面圖", "page_number": 1}]
        plans = assign_sheet_numbers(
            pages,
            self.rules,
            known_series={"IN__201__立面圖": ("IN", "201")},
            known_names={"IN__201__立面圖": "立面圖"},
        )
        self.assertEqual(plans[0].status, STATUS_UNNUMBERED)
        self.assertIsNone(plans[0].drawing_no)

    def test_known_series_does_not_keep_old_number(self):
        pages = [
            {"name": "**IN__10__一", "page_number": 1},
            {"name": "IN__4__四", "page_number": 2},
        ]
        plans = assign_sheet_numbers(
            pages,
            self.rules,
            known_series={"IN__4__四": ("IN", "4")},
        )
        self.assertEqual(plans[1].number, "11")
        self.assertEqual(plans[1].drawing_no, "IN 11")
        self.assertEqual(plans[1].new_page_name, "IN__11__四")

    def test_rhino9_groups_number_once_in_all_layouts_order(self):
        names = [
            "//Preset",
            "//IN__001.01__目錄 1",
            "//IN__001.01__目錄 2",
            "**A__201__平面圖",
            "你說",
            "你愛了",
            "不該",
            "愛的人",
            "**S__105__天花反射平面圖",
            "你說你",
            "想要逃",
            "偏偏注定",
            "要落腳",
            "**IN__505.03__立面圖 1",
            "妳是妳",
            "我是我",
            "沒有對",
            "沒有錯",
            "**DS__221.a1__立面圖 2",
            "有幾間厝",
            "用磚仔砌",
            "看起來",
            "普通普通",
        ]
        plans = assign_sheet_numbers(
            [{"name": name, "page_number": index + 1} for index, name in enumerate(names)],
            self.rules,
        )
        drawing_nos = [plan.drawing_no for plan in plans]
        self.assertEqual(
            drawing_nos[3:9],
            ["A 201", "A 202", "A 203", "A 204", "A 205", "S 105"],
        )
        self.assertEqual(drawing_nos[9:14], ["S 106", "S 107", "S 108", "S 109", "IN 505.03"])
        self.assertEqual(drawing_nos[14:19], ["IN 505.04", "IN 505.05", "IN 505.06", "IN 505.07", "DS 221.a1"])
        self.assertEqual(drawing_nos[19:], ["DS 221.a2", "DS 221.a3", "DS 221.a4", "DS 221.a5"])
        kept = [name for name in names if name != "你愛了"]
        plans = assign_sheet_numbers(
            [{"name": name, "page_number": index + 1} for index, name in enumerate(kept)],
            self.rules,
        )
        self.assertEqual(
            [plan.drawing_no for plan in plans][3:8],
            ["A 201", "A 202", "A 203", "A 204", "S 105"],
        )

    def test_duplicate_group_listing_does_not_skip_number(self):
        pages = [
            {"id": "p1", "name": "**IN__5__一", "page_number": 1},
            {"id": "p2", "name": "二", "page_number": 2},
            {"id": "p2", "name": "二", "page_number": 2},
            {"id": "p4", "name": "四", "page_number": 4},
            {"id": "p5", "name": "五", "page_number": 5},
        ]
        selected = select_layout_pages(pages)
        plans = assign_sheet_numbers(
            [{"name": page["name"], "page_number": page["page_number"]} for page in selected],
            self.rules,
        )
        self.assertEqual([plan.drawing_no for plan in plans], ["IN 5", "IN 6", "IN 7", "IN 8"])

    def test_ungrouped_page_inside_group_span_does_not_keep_gap(self):
        pages = [
            {"id": "preset", "name": "//Preset", "page_number": 1, "group_count": 0},
            {"id": "toc1", "name": "//IN__001.01__目錄 1", "page_number": 2},
            {"id": "toc2", "name": "//IN__001.01__目錄 2", "page_number": 3},
            {"id": "a205", "name": "**A__205__平面圖", "page_number": 4},
            {"id": "a206", "name": "A__206__你說", "page_number": 5},
            {"id": "ghost-a", "name": "A__203__你愛了", "page_number": 6, "group_count": 0},
            {"id": "a208", "name": "A__208__不該", "page_number": 7},
            {"id": "a209", "name": "A__209__愛的人", "page_number": 8},
            {"id": "s101", "name": "**S__101__天花反射平面圖", "page_number": 9},
            {"id": "s102", "name": "S__102__你說你", "page_number": 10},
            {"id": "ghost-s", "name": "S__107__想要逃", "page_number": 11, "group_count": 0},
            {"id": "s104", "name": "S__104__偏偏注定", "page_number": 12},
            {"id": "s105", "name": "S__105__要落腳", "page_number": 13},
            {"id": "in08", "name": "**IN__505.08__立面圖 1", "page_number": 14},
            {"id": "in09", "name": "IN__505.09__妳是妳", "page_number": 15},
            {"id": "ghost-in", "name": "IN__505.05__我是我", "page_number": 16, "group_count": 0},
            {"id": "in11", "name": "IN__505.11__沒有對", "page_number": 17},
            {"id": "in12", "name": "IN__505.12__沒有錯", "page_number": 18},
            {"id": "ds5", "name": "**DS__221.a5__立面圖 2", "page_number": 19},
            {"id": "ds6", "name": "DS__221.a6__有幾間厝", "page_number": 20},
            {"id": "ghost-ds", "name": "DS__221.a3__用磚仔砌", "page_number": 21, "group_count": 0},
            {"id": "ds8", "name": "DS__221.a8__看起來", "page_number": 22},
            {"id": "ds9", "name": "DS__221.a9__看起來2", "page_number": 23},
            {"id": "ds10", "name": "DS__221.a10__普通普通", "page_number": 24},
        ]
        groups = [
            ["toc1", "toc2"],
            ["a205", "a206", "a208", "a209"],
            ["s101", "s102", "s104", "s105"],
            ["in08", "in09", "in11", "in12"],
            ["ds5", "ds6", "ds8", "ds9", "ds10"],
        ]
        tab_ids = layout_tab_ids(pages, groups)
        self.assertIn("preset", tab_ids)
        self.assertNotIn("ghost-a", tab_ids)
        self.assertNotIn("ghost-s", tab_ids)
        self.assertNotIn("ghost-in", tab_ids)
        self.assertNotIn("ghost-ds", tab_ids)
        selected = select_layout_pages(pages, tab_ids)
        plans = assign_sheet_numbers(
            [{"name": page["name"], "page_number": page["page_number"]} for page in selected],
            self.rules,
        )
        numbered = [
            plan.drawing_no
            for plan in plans
            if plan.drawing_no and not str(plan.page_name).startswith("//")
        ]
        self.assertEqual(
            numbered,
            [
                "A 205",
                "A 206",
                "A 207",
                "A 208",
                "S 101",
                "S 102",
                "S 103",
                "S 104",
                "IN 505.08",
                "IN 505.09",
                "IN 505.10",
                "IN 505.11",
                "DS 221.a5",
                "DS 221.a6",
                "DS 221.a7",
                "DS 221.a8",
                "DS 221.a9",
            ],
        )

    def test_page_missing_from_tabs_does_not_keep_gap(self):
        pages = [
            {"id": "p1", "name": "**IN__5__一", "page_number": 1},
            {"id": "p2", "name": "二", "page_number": 2},
            {"id": "ghost", "name": "三", "page_number": 3},
            {"id": "p4", "name": "四", "page_number": 4},
            {"id": "p5", "name": "五", "page_number": 5},
        ]
        selected = select_layout_pages(pages, tab_ids={"p1", "p2", "p4", "p5"})
        plans = assign_sheet_numbers(
            [{"name": page["name"], "page_number": page["page_number"]} for page in selected],
            self.rules,
        )
        self.assertEqual([plan.drawing_no for plan in plans], ["IN 5", "IN 6", "IN 7", "IN 8"])

    def test_missing_page_id_is_not_dropped_by_empty_tab_list(self):
        pages = [
            {"id": None, "name": "**A__201__平面圖", "page_number": 1},
            {"id": None, "name": "你說", "page_number": 2},
        ]
        selected = select_layout_pages(pages, tab_ids=set())
        self.assertEqual([page["name"] for page in selected], ["**A__201__平面圖", "你說"])

    def test_page_view_key_uses_viewport_id(self):
        class Viewport:
            Id = "viewport-1"

        class Page:
            MainViewport = Viewport()

        self.assertEqual(_page_view_key(Page()), "viewport-1")

    def test_increment_keeps_letter_prefix_and_rolls_single_digit_to_ten(self):
        self.assertEqual(increment_number("201"), "202")
        self.assertEqual(increment_number("201.02"), "201.03")
        self.assertEqual(increment_number("A09"), "A10")
        self.assertEqual(increment_number("A9"), "A10")
        self.assertEqual(increment_number("101.1"), "101.2")
        self.assertEqual(increment_number("101.9"), "101.10")
        self.assertEqual(increment_number("101.1", 9), "101.10")


class SheetApiTests(unittest.TestCase):
    def test_document_key_rejects_unknown_field(self):
        with self.assertRaises(ValueError):
            document_key(SHEET_A, "catalog_drawing_no")

    def test_catalog_prefix_is_reserved(self):
        self.assertTrue(CATALOG_RESERVED_PREFIX.startswith("lf_catalog"))

    def test_write_and_read_metadata(self):
        session = _session()
        write_sheet_metadata(
            session,
            SHEET_A,
            {"drawing_no": "IN 101.01", "drawing_name": "一樓平面圖", "page_position": 1},
        )
        meta = get_sheet_metadata(session, SHEET_A)
        self.assertEqual(meta["drawing_no"], "IN 101.01")
        self.assertEqual(meta["drawing_name"], "一樓平面圖")
        self.assertEqual(sheet_state(session, SHEET_A, 1), "current")
        self.assertEqual(sheet_state(session, SHEET_A, 2), "stale")

    def test_uppercase_sheet_id_still_active(self):
        session = _session()
        catalog = _catalog()
        page = "IN__201__立面圖"
        session.set_layout_pages([page])
        session.add_object("frame-a")
        session.set_block("frame-a", (0, 0, 0), name="Sample_Frame")
        session.set_object_user_text("frame-a", SHEET_ID_KEY, SHEET_A.upper())
        session.add_object_to_layout_page(page, "frame-a")
        write_sheet_metadata(session, SHEET_A, {"drawing_no": "IN 201", "page_position": 1})
        active = list_active_sheets(session, catalog)
        self.assertEqual([sheet.sheet_id for sheet in active], [SHEET_A])
        self.assertEqual(active[0].metadata.get("drawing_no"), "IN 201")

    def test_orphan_metadata_is_not_active(self):
        session = _session()
        catalog = _catalog()
        session.set_layout_pages(["IN__201__立面圖"])
        session.add_object("frame-a")
        session.set_block("frame-a", (0, 0, 0), name="Sample_Frame")
        session.set_object_user_text("frame-a", SHEET_ID_KEY, SHEET_A)
        session.add_object_to_layout_page("IN__201__立面圖", "frame-a")
        write_sheet_metadata(session, SHEET_A, {"drawing_no": "IN 201", "page_position": 1})
        write_sheet_metadata(session, SHEET_B, {"drawing_no": "IN 202", "page_position": 2})
        active = list_active_sheets(session, catalog)
        self.assertEqual([sheet.sheet_id for sheet in active], [SHEET_A])

    def test_stale_when_page_order_moved(self):
        session = _session()
        catalog = _catalog()
        session.set_layout_pages(["IN__201__立面圖", "IN__202__天花"])
        for index, name in enumerate(("IN__201__立面圖", "IN__202__天花"), start=1):
            frame_id = "frame-%s" % index
            sheet_id = SHEET_A if index == 1 else SHEET_B
            session.add_object(frame_id)
            session.set_block(frame_id, (0, 0, 0), name="Sample_Frame")
            session.set_object_user_text(frame_id, SHEET_ID_KEY, sheet_id)
            session.add_object_to_layout_page(name, frame_id)
            write_sheet_metadata(session, sheet_id, {"drawing_no": "IN 20%s" % index, "page_position": index})
        session.set_layout_pages(["IN__202__天花", "IN__201__立面圖"])
        self.assertEqual(set(stale_sheet_ids(session, catalog)), {SHEET_A, SHEET_B})

    def test_stale_among_does_not_poison_current_page(self):
        session = _session()
        catalog = _catalog()
        session.set_layout_pages(["IN__201__立面圖", "IN__201__立面圖_Copy1"])
        for index, name in enumerate(("IN__201__立面圖", "IN__201__立面圖_Copy1"), start=1):
            frame_id = "frame-%s" % index
            session.add_object(frame_id)
            session.set_block(frame_id, (0, 0, 0), name="Sample_Frame")
            session.set_object_user_text(frame_id, SHEET_ID_KEY, SHEET_A)
            session.add_object_to_layout_page(name, frame_id)
        write_sheet_metadata(session, SHEET_A, {"drawing_no": "IN 201", "page_position": 1})
        self.assertEqual(stale_among_sheet_ids(session, catalog, [SHEET_A]), ())
        self.assertEqual(set(stale_sheet_ids(session, catalog)), {SHEET_A})

    def test_does_not_invent_scale(self):
        session = _session()
        write_sheet_metadata(session, SHEET_A, {"drawing_no": "IN 101.01"})
        self.assertIsNone(get_sheet_metadata(session, SHEET_A).get("scale"))
        self.assertNotEqual(SCALE_KEY, "03-A3 Scale")


if __name__ == "__main__":
    unittest.main()
