# -*- coding: utf-8 -*-
"""E05 LF_Catalog：定位點排序、配對、Build／Refresh／TXT；Esc／stale 零寫入。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.catalog.catalog import (
    CatalogPoint,
    assign_catalog_points,
    bind_sheets_to_anchors,
    build_catalog,
    build_catalog_rows,
    export_catalog_txt,
    format_catalog_txt,
    generated_text_ids,
    pair_catalog_anchors,
    refresh_catalog,
    sort_catalog_points,
)
from loopflow.features.catalog.keys import (
    CATALOG_ID_KEY,
    FIELD_DRAWING_NAME,
    FIELD_DRAWING_NO,
    FIELD_KEY,
    GENERATED_BY_KEY,
    GENERATED_BY_VALUE,
    NAME_LAYER,
    NUMBER_LAYER,
    SHEET_ID_KEY,
)
from loopflow.features.sheet.keys import SHEET_ID_KEY as FRAME_SHEET_ID_KEY
from loopflow.features.sheet.metadata import write_sheet_metadata
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.platform.rhino.memory import MemorySession

CASES = json.loads(
    (WIP / "fixtures" / "contract" / "catalog" / "cases.json").read_text(encoding="utf-8")
)
PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SHEET_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SHEET_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
SHEET_C = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
CATALOG_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"


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


def _point_from_case(item: dict, field: str) -> CatalogPoint:
    return CatalogPoint(
        object_id=item["id"],
        page_name="P%s" % item["page_number"],
        page_number=int(item["page_number"]),
        x=float(item["x"]),
        y=float(item["y"]),
        field=field,
    )


def _add_sheet(session: MemorySession, page_name: str, sheet_id: str, drawing_no: str, drawing_name: str, position: int):
    frame_id = "frame-%s" % sheet_id[:8]
    session.add_object(frame_id)
    session.set_block(frame_id, (0, 0, 0), name="Sample_Frame")
    session.set_object_user_text(frame_id, FRAME_SHEET_ID_KEY, sheet_id)
    session.add_object_to_layout_page(page_name, frame_id)
    write_sheet_metadata(
        session,
        sheet_id,
        {
            "drawing_no": drawing_no,
            "drawing_name": drawing_name,
            "page_position": position,
        },
    )


def _add_anchor(session: MemorySession, object_id: str, xyz, *, page: str, layer: str, field: str, sheet_id=None):
    session.add_point(object_id, xyz, layer=layer)
    session.add_object_to_layout_page(page, object_id)
    session.set_object_user_text(object_id, CATALOG_ID_KEY, CATALOG_ID)
    session.set_object_user_text(object_id, FIELD_KEY, field)
    if sheet_id:
        session.set_object_user_text(object_id, SHEET_ID_KEY, sheet_id)


class SortAndPairTests(unittest.TestCase):
    def test_contract_cases(self):
        for case in CASES["cases"]:
            numbers = [_point_from_case(item, FIELD_DRAWING_NO) for item in case["number_points"]]
            names = [_point_from_case(item, FIELD_DRAWING_NAME) for item in case["name_points"]]
            paired = pair_catalog_anchors(numbers, names)
            if case["expect"] == "pass":
                self.assertTrue(paired.ok, case["id"])
                order = [pair.number.object_id for pair in paired.pairs]
                self.assertEqual(order, case["expect_order"], case["id"])
                bound = bind_sheets_to_anchors(paired.pairs, case["sheet_ids"])
                self.assertTrue(bound.ok, case["id"])
                empty = sum(1 for slot in bound.slots if slot.sheet_id is None)
                self.assertEqual(empty, case.get("expect_empty_slots", 0), case["id"])
            elif case["expect"] == "too_many_sheets":
                self.assertTrue(paired.ok, case["id"])
                bound = bind_sheets_to_anchors(paired.pairs, case["sheet_ids"])
                self.assertFalse(bound.ok)
                self.assertEqual(bound.reason, "too_many_sheets")
            else:
                self.assertFalse(paired.ok, case["id"])
                self.assertEqual(paired.reason, case["expect"], case["id"])

    def test_selection_order_does_not_change_sort(self):
        first = (
            CatalogPoint("b", "P1", 1, 100.0, 100.0),
            CatalogPoint("a", "P1", 1, 100.0, 200.0),
        )
        second = tuple(reversed(first))
        self.assertEqual(
            [p.object_id for p in sort_catalog_points(first)],
            [p.object_id for p in sort_catalog_points(second)],
        )


class AssignAndBuildTests(unittest.TestCase):
    def test_assign_name_reuses_number_catalog_id(self):
        session = _session()
        session.add_point("n1", (100, 200, 0))
        session.add_point("m1", (180, 200, 0))
        first = assign_catalog_points(session, ["n1"], FIELD_DRAWING_NO)
        second = assign_catalog_points(session, ["m1"], FIELD_DRAWING_NAME)
        self.assertTrue(first.ok, first.message)
        self.assertTrue(second.ok, second.message)
        self.assertEqual(
            session.get_object_user_text("n1", CATALOG_ID_KEY),
            session.get_object_user_text("m1", CATALOG_ID_KEY),
        )

    def test_assign_second_batch_reuses_same_catalog_id(self):
        session = _session()
        session.add_point("n1", (100, 200, 0))
        session.add_point("n2", (100, 100, 0))
        first = assign_catalog_points(session, ["n1"], FIELD_DRAWING_NO)
        second = assign_catalog_points(session, ["n2"], FIELD_DRAWING_NO)
        self.assertTrue(first.ok, first.message)
        self.assertTrue(second.ok, second.message)
        self.assertEqual(
            session.get_object_user_text("n1", CATALOG_ID_KEY),
            session.get_object_user_text("n2", CATALOG_ID_KEY),
        )

    def test_assign_rejects_block(self):
        session = _session()
        session.add_object("block-1")
        session.set_block("block-1", (0, 0, 0), name="Title")
        result = assign_catalog_points(session, ["block-1"], FIELD_DRAWING_NO)
        self.assertFalse(result.ok)
        self.assertIn("block_instance", result.blocking)
        self.assertIsNone(session.get_object_user_text("block-1", CATALOG_ID_KEY))

    def test_stray_point_on_layer_is_not_anchor(self):
        session = _session()
        session.set_layout_pages(["**IN__101__一樓"])
        _add_sheet(session, "**IN__101__一樓", SHEET_A, "IN 101", "一樓", 1)
        session.add_point("stray", (10, 10, 0), layer=NUMBER_LAYER)
        session.add_object_to_layout_page("**IN__101__一樓", "stray")
        _add_anchor(session, "n1", (100, 200, 0), page="**IN__101__一樓", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="**IN__101__一樓", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(session, [SHEET_A], confirm=lambda _lines: True, catalog=_catalog())
        self.assertTrue(result.ok)
        self.assertIsNone(session.get_object_user_text("stray", CATALOG_ID_KEY))

    def test_build_writes_sheet_id_not_drawing_no(self):
        session = _session()
        session.set_layout_pages(["**IN__101__一樓", "IN__102__二樓"])
        _add_sheet(session, "**IN__101__一樓", SHEET_A, "IN 101", "一樓", 1)
        _add_sheet(session, "IN__102__二樓", SHEET_B, "IN 102", "二樓", 2)
        _add_anchor(session, "n1", (100, 200, 0), page="**IN__101__一樓", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "n2", (100, 100, 0), page="**IN__101__一樓", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="**IN__101__一樓", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        _add_anchor(session, "m2", (180, 100, 0), page="**IN__101__一樓", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(
            session, [SHEET_A], confirm=lambda _lines: True, catalog=_catalog()
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("n1", SHEET_ID_KEY), SHEET_A)
        self.assertIsNone(session.get_object_user_text("n2", SHEET_ID_KEY))
        texts = generated_text_ids(session, CATALOG_ID)
        self.assertEqual(len(texts), 2)
        values = {session.text_content(item) for item in texts}
        self.assertEqual(values, {"IN 101", "一樓"})

    def test_preview_cancel_writes_nothing(self):
        session = _session()
        session.set_layout_pages(["**IN__101__一樓"])
        _add_sheet(session, "**IN__101__一樓", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(session, "n1", (100, 200, 0), page="**IN__101__一樓", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="**IN__101__一樓", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(session, [SHEET_A], confirm=lambda _lines: False, catalog=_catalog())
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("n1", SHEET_ID_KEY))
        self.assertEqual(generated_text_ids(session, CATALOG_ID), ())

    def test_cross_page_order_and_refresh_keeps_binding(self):
        session = _session()
        session.set_layout_pages(["P1", "P2"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_sheet(session, "P2", SHEET_B, "IN 102", "二樓", 2)
        _add_anchor(session, "p2", (100, 200, 0), page="P2", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "p1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m2", (180, 200, 0), page="P2", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        _add_anchor(session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(
            session, [SHEET_A, SHEET_B], confirm=lambda _lines: True, catalog=_catalog()
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("p1", SHEET_ID_KEY), SHEET_A)
        self.assertEqual(session.get_object_user_text("p2", SHEET_ID_KEY), SHEET_B)
        write_sheet_metadata(session, SHEET_A, {"drawing_name": "一樓平面", "drawing_no": "IN 201", "page_position": 1})
        refreshed = refresh_catalog(session, catalog=_catalog())
        self.assertTrue(refreshed.ok, refreshed.message)
        self.assertEqual(session.get_object_user_text("p1", SHEET_ID_KEY), SHEET_A)
        values = {session.text_content(item) for item in generated_text_ids(session, CATALOG_ID)}
        self.assertIn("IN 201", values)
        self.assertIn("一樓平面", values)

    def test_stale_blocks_refresh(self):
        session = _session()
        session.set_layout_pages(["P1", "P2"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_sheet(session, "P2", SHEET_B, "IN 102", "二樓", 2)
        _add_anchor(
            session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO, sheet_id=SHEET_A
        )
        _add_anchor(
            session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME, sheet_id=SHEET_A
        )
        session.set_layout_pages(["P2", "P1"])
        result = refresh_catalog(session, catalog=_catalog())
        self.assertFalse(result.ok)
        self.assertIn("stale", result.blocking)
        self.assertEqual(generated_text_ids(session, CATALOG_ID), ())

    def test_missing_sheet_skipped_others_written(self):
        session = _session()
        session.set_layout_pages(["P1"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "n2", (100, 100, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        _add_anchor(session, "m2", (180, 100, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(
            session, [SHEET_A, SHEET_C], confirm=lambda _lines: True, catalog=_catalog()
        )
        self.assertTrue(result.ok, result.message)
        self.assertIn("missing_sheet", result.warnings)
        values = {session.text_content(item) for item in generated_text_ids(session, CATALOG_ID)}
        self.assertEqual(values, {"IN 101", "一樓"})

    def test_refresh_does_not_delete_manual_text(self):
        session = _session()
        session.set_layout_pages(["P1"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(
            session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO, sheet_id=SHEET_A
        )
        _add_anchor(
            session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME, sheet_id=SHEET_A
        )
        manual = session.add_text("人工註記", (10, 10, 0), layer=NUMBER_LAYER, page_name="P1")
        refresh_catalog(session, catalog=_catalog())
        self.assertEqual(session.text_content(manual), "人工註記")
        self.assertIsNone(session.get_object_user_text(manual, GENERATED_BY_KEY))
        generated = generated_text_ids(session, CATALOG_ID)
        self.assertTrue(generated)
        for object_id in generated:
            self.assertEqual(session.get_object_user_text(object_id, GENERATED_BY_KEY), GENERATED_BY_VALUE)

    def test_row_mismatch_zero_write(self):
        session = _session()
        session.set_layout_pages(["P1"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "n2", (100, 100, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        _add_anchor(session, "m-wrong", (360, 150, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(session, [SHEET_A], confirm=lambda _lines: True, catalog=_catalog())
        self.assertFalse(result.ok)
        self.assertIn("row_mismatch", result.blocking)
        self.assertIsNone(session.get_object_user_text("n1", SHEET_ID_KEY))

    def test_export_txt_utf8_and_order(self):
        session = _session()
        session.set_layout_pages(["P1", "P2"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓平面圖", 1)
        _add_sheet(session, "P2", SHEET_B, "IN 102", "二樓平面圖", 2)
        _add_anchor(
            session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO, sheet_id=SHEET_A
        )
        _add_anchor(
            session, "n2", (100, 100, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO, sheet_id=SHEET_B
        )
        _add_anchor(
            session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME, sheet_id=SHEET_A
        )
        _add_anchor(
            session, "m2", (180, 100, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME, sheet_id=SHEET_B
        )
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "catalog.txt")
            result = export_catalog_txt(session, path, catalog=_catalog())
            self.assertTrue(result.ok, result.message)
            payload = Path(path).read_text(encoding="utf-8")
        self.assertEqual(payload, "圖名, 圖號\n一樓平面圖, IN 101\n二樓平面圖, IN 102\n")
        self.assertIn("一樓平面圖", format_catalog_txt(result.details["rows"]))

    def test_unsaved_document_requires_path(self):
        session = _session()
        session.set_layout_pages(["P1"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(
            session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO, sheet_id=SHEET_A
        )
        _add_anchor(
            session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME, sheet_id=SHEET_A
        )
        result = export_catalog_txt(session, catalog=_catalog(), ask_path=lambda _default: None)
        self.assertFalse(result.ok)
        self.assertIn("missing_path", result.blocking)

    def test_split_number_and_name_catalog_ids_unify_on_build(self):
        session = _session()
        session.set_layout_pages(["P1"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        session.set_object_user_text("m1", CATALOG_ID_KEY, "ffffffff-ffff-4fff-8fff-ffffffffffff")
        result = build_catalog(session, [SHEET_A], confirm=lambda _lines: True, catalog=_catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text("n1", CATALOG_ID_KEY),
            session.get_object_user_text("m1", CATALOG_ID_KEY),
        )

    def test_mixed_catalog_id_within_one_field_blocks(self):
        session = _session()
        session.set_layout_pages(["P1"])
        _add_sheet(session, "P1", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(session, "n1", (100, 200, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "n2", (100, 100, 0), page="P1", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        _add_anchor(session, "m2", (180, 100, 0), page="P1", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        session.set_object_user_text("n2", CATALOG_ID_KEY, "ffffffff-ffff-4fff-8fff-ffffffffffff")
        result = build_catalog(session, [SHEET_A], confirm=lambda _lines: True, catalog=_catalog())
        self.assertFalse(result.ok)
        self.assertIn("mixed_catalog_id", result.blocking)

    def test_does_not_parse_page_name_as_drawing_no(self):
        session = _session()
        session.set_layout_pages(["這不是圖號"])
        _add_sheet(session, "這不是圖號", SHEET_A, "IN 101", "一樓", 1)
        _add_anchor(session, "n1", (100, 200, 0), page="這不是圖號", layer=NUMBER_LAYER, field=FIELD_DRAWING_NO)
        _add_anchor(session, "m1", (180, 200, 0), page="這不是圖號", layer=NAME_LAYER, field=FIELD_DRAWING_NAME)
        result = build_catalog(session, [SHEET_A], confirm=lambda _lines: True, catalog=_catalog())
        self.assertTrue(result.ok, result.message)
        values = {session.text_content(item) for item in generated_text_ids(session, CATALOG_ID)}
        self.assertEqual(values, {"IN 101", "一樓"})
        self.assertNotIn("這不是圖號", values)


class SchemaFixtureTests(unittest.TestCase):
    def test_keys_match_schema_fixture(self):
        spec = json.loads(
            (WIP / "fixtures" / "schema" / "catalog.json").read_text(encoding="utf-8")
        )
        from loopflow.features.catalog import keys as catalog_keys

        self.assertEqual(spec["layers"]["drawing_no"], catalog_keys.NUMBER_LAYER)
        self.assertEqual(spec["layers"]["drawing_name"], catalog_keys.NAME_LAYER)
        self.assertEqual(tuple(spec["layer_colors"]["drawing_no"]), catalog_keys.NUMBER_COLOR)
        self.assertEqual(tuple(spec["layer_colors"]["drawing_name"]), catalog_keys.NAME_COLOR)
        self.assertEqual(spec["usertext_keys"]["catalog_id"], catalog_keys.CATALOG_ID_KEY)
        self.assertEqual(spec["usertext_keys"]["field"], catalog_keys.FIELD_KEY)
        self.assertEqual(spec["usertext_keys"]["sheet_id"], catalog_keys.SHEET_ID_KEY)
        self.assertEqual(spec["generated_by_value"], catalog_keys.GENERATED_BY_VALUE)
        self.assertEqual(spec["column_tolerance"], catalog_keys.COLUMN_TOLERANCE)
        self.assertEqual(spec["row_tolerance"], catalog_keys.ROW_TOLERANCE)


class RowSkipTests(unittest.TestCase):
    def test_orphan_and_missing_fields(self):
        slots_ok = bind_sheets_to_anchors(
            pair_catalog_anchors(
                [CatalogPoint("n1", "P1", 1, 100, 200)],
                [CatalogPoint("m1", "P1", 1, 180, 200)],
            ).pairs,
            [SHEET_A],
        )
        rows = build_catalog_rows(
            slots_ok.slots,
            metadata_by_id={SHEET_A: {"drawing_no": "IN 101"}},
            active_ids=(SHEET_A,),
        )
        self.assertEqual(rows[0].skip_reason, "missing_drawing_name")
        rows = build_catalog_rows(
            slots_ok.slots,
            metadata_by_id={SHEET_A: {"drawing_no": "IN 101", "drawing_name": "一樓"}},
            active_ids=(),
        )
        self.assertEqual(rows[0].skip_reason, "orphan")
        rows = build_catalog_rows(
            slots_ok.slots,
            metadata_by_id={},
            active_ids=(),
        )
        self.assertEqual(rows[0].skip_reason, "missing_sheet")


if __name__ == "__main__":
    unittest.main()
