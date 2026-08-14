# -*- coding: utf-8 -*-
"""NX-05 Space 命中與高程：EXT 四因、不取第一個、BC 非 Block 阻擋。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.layer_paths import to_full_path
from loopflow.features.dictionary.loader import TypeCatalog, TypeRecord, load_from_table
from loopflow.features.model_data.placement import (
    ELEVATION_BASIS_KEY,
    ELEVATION_VALUE_KEY,
    SPACE_BOUNDARY_LAYER,
    apply_placement,
    scan_placement,
)
from loopflow.features.model_data.space import SPACE_DISPLAY_KEY, SPACE_ID_KEY
from loopflow.platform.rhino.memory import MemorySession

LAYER = "00_STR_結構::Beam.樑"
FULL = to_full_path(LAYER)
SPACE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SPACE_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
LEVEL_1 = "11111111-1111-4111-8111-111111111111"
LEVEL_2 = "22222222-2222-4222-8222-222222222222"


def _row(**overrides):
    row = [None] * len(schema.DISPLAY_COLUMNS)
    values = {
        "layer_path": LAYER,
        "construction_default": "Existing",
        "type_id": "EX-01",
        "type_display_name": "鋼筋混凝土",
        "estimation_unit": "樘",
        "measurement_rule": "COUNT",
        "elevation_basis": "BH",
        "remarks_default": "(手動輸入備註)",
    }
    values.update(overrides)
    for key, value in values.items():
        row[schema.MACHINE_KEYS.index(key)] = value
    return row


def _catalog(*rows):
    result = load_from_table(title=schema.TITLE_ROW, headers=list(schema.DISPLAY_COLUMNS), rows=list(rows))
    if not result.ok:
        raise AssertionError(result.message)
    return result.details["catalog"]


def _session() -> MemorySession:
    session = MemorySession()
    session.ensure_layer(FULL)
    return session


def _add_space(session, object_id, polygon, space_id, display, level_id=LEVEL_1):
    session.ensure_layer(SPACE_BOUNDARY_LAYER)
    session.add_object(object_id, name=display, layer=SPACE_BOUNDARY_LAYER)
    session.set_curve(object_id, polygon, closed=True)
    session.set_object_user_text(object_id, SPACE_ID_KEY, space_id)
    session.set_object_user_text(object_id, SPACE_DISPLAY_KEY, display)
    session.set_object_user_text(object_id, "lf_level_id", level_id)


def _add_model(session, object_id, *, bbox=None, block=None):
    session.add_object(object_id, layer=FULL)
    if bbox:
        session.set_bbox(object_id, bbox[0], bbox[1])
    if block:
        session.set_block(object_id, block)


class PlacementTests(unittest.TestCase):
    def test_ext_four_reasons(self):
        catalog = _catalog(_row())
        missing_layer = _session()
        _add_model(missing_layer, "a", bbox=((1, 1, 0), (2, 2, 3)))
        self.assertFalse(missing_layer.has_layer(SPACE_BOUNDARY_LAYER))
        r1 = scan_placement(missing_layer, catalog=catalog)
        self.assertEqual(r1.details["ext"][0]["reason"], "no_boundary_layer")

        empty = _session()
        empty.ensure_layer(SPACE_BOUNDARY_LAYER)
        _add_model(empty, "a", bbox=((1, 1, 0), (2, 2, 3)))
        r2 = scan_placement(empty, catalog=catalog)
        self.assertEqual(r2.details["ext"][0]["reason"], "layer_without_boundary")

        no_bbox = _session()
        _add_space(no_bbox, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(no_bbox, "a")
        r3 = scan_placement(no_bbox, catalog=catalog)
        self.assertEqual(r3.details["ext"][0]["reason"], "bbox_unavailable")

        miss = _session()
        _add_space(miss, "s1", [[0, 0], [4, 0], [4, 4], [0, 4]], SPACE_A, "客廳")
        _add_model(miss, "a", bbox=((20, 20, 0), (21, 21, 3)))
        r4 = scan_placement(miss, catalog=catalog)
        self.assertEqual(r4.details["ext"][0]["reason"], "outside_all_boundaries")

    def test_hit_writes_space_and_bh(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(session, "wall", bbox=((2, 2, 0), (3, 3, 270)))
        catalog = _catalog(_row(elevation_basis="BH"))
        applied = apply_placement(session, catalog=catalog)
        self.assertTrue(applied.ok, applied.message)
        self.assertEqual(session.get_object_user_text("wall", SPACE_ID_KEY), SPACE_A)
        self.assertEqual(session.get_object_user_text("wall", SPACE_DISPLAY_KEY), "客廳")
        self.assertEqual(session.get_object_user_text("wall", ELEVATION_BASIS_KEY), "BH")
        self.assertEqual(session.get_object_user_text("wall", ELEVATION_VALUE_KEY), "0")
        self.assertIsNone(session.get_object_user_text("wall", "Q_01_寬度W"))
        self.assertFalse(applied.details["publish_ready"])

    def test_th_ch_and_bc(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(session, "th", bbox=((1, 1, 10), (2, 2, 40)))
        catalog_th = _catalog(_row(elevation_basis="TH"))
        apply_placement(session, catalog=catalog_th)
        self.assertEqual(session.get_object_user_text("th", ELEVATION_VALUE_KEY), "40")

        session2 = _session()
        _add_space(session2, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(session2, "ch", bbox=((1, 1, 250), (2, 2, 270)))
        apply_placement(session2, catalog=_catalog(_row(elevation_basis="CH")))
        self.assertEqual(session2.get_object_user_text("ch", ELEVATION_VALUE_KEY), "250")

        session3 = _session()
        _add_space(session3, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(session3, "blk", bbox=((1, 1, 0), (2, 2, 10)), block=(1.5, 1.5, 15))
        apply_placement(session3, catalog=_catalog(_row(elevation_basis="BC")))
        self.assertEqual(session3.get_object_user_text("blk", ELEVATION_VALUE_KEY), "15")

    def test_bc_on_non_block_blocks_elevation(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(session, "wall", bbox=((1, 1, 0), (2, 2, 10)))
        result = apply_placement(session, catalog=_catalog(_row(elevation_basis="BC")))
        self.assertIn("wall", result.details["remaining"])
        self.assertEqual(session.get_object_user_text("wall", SPACE_ID_KEY), SPACE_A)
        self.assertIsNone(session.get_object_user_text("wall", ELEVATION_BASIS_KEY))

    def test_legacy_th_bh_is_migration_only(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "客廳")
        _add_model(session, "wall", bbox=((1, 1, 0), (2, 2, 10)))
        catalog = TypeCatalog(
            schema_id=schema.SCHEMA_ID,
            schema_version=schema.SCHEMA_VERSION,
            title=schema.TITLE_ROW,
            types=(
                TypeRecord(
                    layer_path=LAYER,
                    type_id="EX-01",
                    type_category="EX",
                    type_sequence="01",
                    type_display_name="鋼筋混凝土",
                    construction_default="Existing",
                    estimation_unit="樘",
                    measurement_rule="COUNT",
                    elevation_basis="TH/BH",
                    remarks_default=None,
                ),
            ),
        )
        scanned = scan_placement(session, catalog=catalog)
        self.assertIn("migration_th_bh", scanned.warnings)
        applied = apply_placement(session, catalog=catalog)
        self.assertEqual(session.get_object_user_text("wall", SPACE_ID_KEY), SPACE_A)
        self.assertIsNone(session.get_object_user_text("wall", ELEVATION_BASIS_KEY))

    def test_multi_level_same_xy_does_not_pick_first(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "1F客廳", LEVEL_1)
        _add_space(session, "s2", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_B, "2F臥室", LEVEL_2)
        _add_model(session, "wall", bbox=((2, 2, 0), (3, 3, 3)))
        scanned = scan_placement(session, catalog=_catalog(_row()))
        item = scanned.details["items"][0]
        self.assertIn("ambiguous_space", item["issues"])
        self.assertIsNone(item["space_id"])
        applied = apply_placement(session, catalog=_catalog(_row()))
        self.assertIsNone(session.get_object_user_text("wall", SPACE_ID_KEY))
        self.assertIn("wall", applied.details["remaining"])

    def test_shared_edge_rooms_hit_interior(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [5, 0], [5, 4], [0, 4]], SPACE_A, "客廳")
        _add_space(session, "s2", [[5, 0], [10, 0], [10, 4], [5, 4]], SPACE_B, "餐廳")
        _add_model(session, "left", bbox=((1, 1, 0), (2, 2, 3)))
        _add_model(session, "right", bbox=((7, 1, 0), (8, 2, 3)))
        apply_placement(session, catalog=_catalog(_row()))
        self.assertEqual(session.get_object_user_text("left", SPACE_ID_KEY), SPACE_A)
        self.assertEqual(session.get_object_user_text("right", SPACE_ID_KEY), SPACE_B)

    def test_named_curve_off_boundary_layer_is_ignored(self):
        """只有 Space_Boundaries 圖層上的曲線算 Space；登記（選單 3）會自動搬層。"""
        session = _session()
        session.add_object("hall", name="廊道", layer=FULL)
        session.set_curve("hall", [[0, 0], [10, 0], [10, 8], [0, 8]], closed=True)
        session.set_object_user_text("hall", SPACE_ID_KEY, SPACE_A)
        session.set_object_user_text("hall", SPACE_DISPLAY_KEY, "廊道")
        _add_model(session, "floor", bbox=((2, 2, 0), (3, 3, 1)))
        applied = apply_placement(session, catalog=_catalog(_row()))
        self.assertTrue(applied.ok, applied.message)
        self.assertEqual(session.get_object_user_text("floor", SPACE_ID_KEY), "EXT")

    def test_wall_outside_center_hits_by_corner(self):
        session = _session()
        _add_space(session, "s1", [[0, 0], [10, 0], [10, 8], [0, 8]], SPACE_A, "衛浴")
        _add_model(session, "wall", bbox=((-1, 2, 0), (0.4, 3, 270)))
        applied = apply_placement(session, catalog=_catalog(_row()))
        self.assertTrue(applied.ok, applied.message)
        self.assertEqual(session.get_object_user_text("wall", SPACE_DISPLAY_KEY), "衛浴")


if __name__ == "__main__":
    unittest.main()
