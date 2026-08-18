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

    def test_does_not_invent_scale(self):
        session = _session()
        write_sheet_metadata(session, SHEET_A, {"drawing_no": "IN 101.01"})
        self.assertIsNone(get_sheet_metadata(session, SHEET_A).get("scale"))
        self.assertNotEqual(SCALE_KEY, "03-A3 Scale")


if __name__ == "__main__":
    unittest.main()
