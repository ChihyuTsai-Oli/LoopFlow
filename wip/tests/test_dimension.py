# -*- coding: utf-8 -*-
"""C05 尺寸／數量：local frame、8 種 token、坪／才、非 cm、禁止 World bbox。"""
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

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.layer_paths import to_full_path
from loopflow.features.dictionary.loader import load_from_table
from loopflow.features.dimension.frame import (
    FRAME_KEY,
    axes_from_plane,
    dump_frame,
    identity_frame,
    validate_frame,
)
from loopflow.features.dimension.measure import apply_dimensions, scan_dimensions
from loopflow.features.dimension.quantity import CAI_CM2, PING_FROM_M2, evaluate_quantity
from loopflow.features.project.console import PROJECT_ID_KEY, SCHEMA_ID_KEY, SCHEMA_VERSION_KEY
from loopflow.platform.rhino.memory import MemorySession

LAYER = "00_STR_結構::Beam.樑"
FULL = to_full_path(LAYER)
CASES = json.loads((WIP / "fixtures" / "contract" / "quantity" / "cases.json").read_text(encoding="utf-8"))
FRAMES = json.loads((WIP / "fixtures" / "contract" / "local_frame" / "cases.json").read_text(encoding="utf-8"))


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
    session = MemorySession(
        document_text={
            PROJECT_ID_KEY: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            SCHEMA_ID_KEY: "loopflow.project",
            SCHEMA_VERSION_KEY: "1",
        }
    )
    session.ensure_layer(FULL)
    session.set_layer_user_text(FULL, "lf_type_id", "EX-01")
    session.set_document_modified(False)
    return session


def _add(session: MemorySession, object_id: str, *, kind: str, bbox=((0, 0, 0), (90, 40, 210))):
    session.add_object(object_id, layer=FULL)
    session.set_geometry_kind(object_id, kind)
    session.set_bbox(object_id, bbox[0], bbox[1])
    if kind == "block_instance":
        session.set_block(object_id, bbox[0])


class QuantityEvalTests(unittest.TestCase):
    def test_a06_quantity_cases(self):
        for case in CASES["cases"]:
            with self.subTest(case["id"]):
                got = evaluate_quantity(
                    case["rule"],
                    case["unit"],
                    case["w"],
                    case["d"],
                    case["h"],
                    model_unit=case.get("model_unit", "Centimeters"),
                )
                self.assertIsNone(next((i for i in got["issues"] if i == "dimension_mismatch"), None))
                self.assertAlmostEqual(got["quantity"], case["expect_quantity"], places=6)

    def test_all_tokens_and_non_cm(self):
        self.assertEqual(evaluate_quantity("LEN_W", "cm", 90, 40, 210)["quantity"], 90)
        self.assertEqual(evaluate_quantity("LEN_D", "mm", 90, 40, 210)["quantity"], 400)
        self.assertEqual(evaluate_quantity("LEN_H", "cm", 90, 40, 210)["quantity"], 210)
        self.assertAlmostEqual(evaluate_quantity("AREA_WH", "才", 303, 10, 303)["quantity"], 100.0, places=6)
        self.assertAlmostEqual(evaluate_quantity("AREA_DH", "坪", 10, 100, 100)["quantity"], PING_FROM_M2, places=6)
        self.assertAlmostEqual(evaluate_quantity("VOL_WDH", "m3", 100, 100, 100)["quantity"], 1.0, places=6)
        mm = evaluate_quantity("LEN_W", "cm", 100, 40, 10, model_unit="Millimeters")
        self.assertEqual(mm["quantity"], 10)
        self.assertIn("model_unit_not_cm", mm["issues"])
        empty = evaluate_quantity(None, "樘", 90, 40, 210)
        self.assertIsNone(empty["quantity"])
        self.assertIn("measurement_rule_undefined", empty["issues"])
        bad = evaluate_quantity("AREA_WD", "樘", 90, 40, 210)
        self.assertIsNone(bad["quantity"])
        self.assertIn("dimension_mismatch", bad["issues"])
        self.assertAlmostEqual(CAI_CM2, 30.3 * 30.3, places=6)


class LocalFrameTests(unittest.TestCase):
    def test_a06_frame_cases(self):
        catalog = _catalog(_row())
        for case in FRAMES["cases"]:
            with self.subTest(case["id"]):
                session = _session()
                session.add_object("obj", layer=FULL)
                session.set_bbox("obj", (0, 0, 0), (90, 40, 210))
                geom = case.get("geometry")
                if geom == "block_instance":
                    session.set_geometry_kind("obj", "block_instance")
                    session.set_block("obj", (0, 0, 0))
                elif geom == "extrusion":
                    session.set_geometry_kind("obj", "extrusion")
                elif geom == "planar_curve":
                    session.set_geometry_kind("obj", "planar_curve")
                elif geom == "oriented_box":
                    session.set_geometry_kind("obj", "oriented_box")
                elif geom == "closed_box":
                    session.set_geometry_kind("obj", "closed_box")
                stored = case.get("stored_frame")
                if stored:
                    if validate_frame(stored) is None:
                        session.set_object_user_text("obj", FRAME_KEY, dump_frame(stored))
                    else:
                        session.set_object_user_text("obj", FRAME_KEY, json.dumps(stored))
                with tempfile.TemporaryDirectory(prefix="loopflow-c05-") as raw:
                    result = scan_dimensions(
                        session,
                        catalog=catalog,
                        environ={"LOOPFLOW_WORKFILES_ROOT": raw},
                    )
                item = result.details["items"][0]
                expect = case["expect"]
                if expect == "derive":
                    self.assertEqual(item["frame_status"], "derive")
                    self.assertEqual(item["frame"]["derivation_method"], case["derivation_method"])
                    self.assertNotIn("no_unique_plane", item["issues"])
                elif expect == "reuse":
                    self.assertEqual(item["frame_status"], "reuse")
                    self.assertTrue(item["reused"])
                elif expect == "block":
                    self.assertIn(item["frame_status"], ("block", "reuse"))
                    self.assertTrue(
                        "no_unique_plane" in item["issues"] or "corrupt_frame" in item["issues"]
                    )
                    self.assertIsNone(session.get_object_user_text("obj", "lf_dimension_w"))

    def test_scan_does_not_write_and_apply_writes(self):
        session = _session()
        _add(session, "box", kind="extrusion", bbox=((0, 0, 0), (90, 40, 210)))
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-c05-") as raw:
            environ = {"LOOPFLOW_WORKFILES_ROOT": raw}
            scanned = scan_dimensions(session, catalog=catalog, environ=environ)
            self.assertTrue(scanned.ok, scanned.message)
            self.assertIsNone(session.get_object_user_text("box", FRAME_KEY))
            self.assertIsNone(session.get_object_user_text("box", "lf_quantity"))
            applied = apply_dimensions(session, catalog=catalog, environ=environ)
        self.assertTrue(applied.ok, applied.message)
        self.assertEqual(session.get_object_user_text("box", "lf_dimension_w"), "90")
        self.assertEqual(session.get_object_user_text("box", "lf_dimension_d"), "40")
        self.assertEqual(session.get_object_user_text("box", "lf_dimension_h"), "210")
        self.assertEqual(session.get_object_user_text("box", "lf_quantity"), "1")
        stored = json.loads(session.get_object_user_text("box", FRAME_KEY))
        self.assertEqual(stored["derivation_method"], "extrusion_base")
        self.assertIsNone(validate_frame(stored))

    def test_reuse_does_not_rederive_on_second_scan(self):
        session = _session()
        _add(session, "box", kind="closed_box", bbox=((0, 0, 0), (10, 20, 30)))
        session.set_object_user_text("box", FRAME_KEY, dump_frame(identity_frame("unique_plane")))
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-c05-") as raw:
            result = scan_dimensions(session, catalog=catalog, environ={"LOOPFLOW_WORKFILES_ROOT": raw})
        self.assertEqual(result.details["items"][0]["frame_status"], "reuse")
        self.assertEqual(result.details["items"][0]["dimension_w"], 10)
        self.assertEqual(result.details["items"][0]["dimension_d"], 20)
        self.assertEqual(result.details["items"][0]["dimension_h"], 30)

    def test_closed_box_without_frame_blocks_apply(self):
        session = _session()
        _add(session, "box", kind="closed_box")
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-c05-") as raw:
            result = apply_dimensions(session, catalog=catalog, environ={"LOOPFLOW_WORKFILES_ROOT": raw})
        self.assertEqual(result.status, "blocked")
        self.assertIn("no_unique_plane", result.blocking)
        self.assertIsNone(session.get_object_user_text("box", FRAME_KEY))

    def test_oriented_box_apply_writes(self):
        session = _session()
        _add(session, "slab", kind="oriented_box", bbox=((0, 0, 0), (90, 40, 12)))
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-c05-obox-") as raw:
            result = apply_dimensions(session, catalog=catalog, environ={"LOOPFLOW_WORKFILES_ROOT": raw})
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("slab", "lf_dimension_w"), "90")
        self.assertEqual(session.get_object_user_text("slab", "lf_dimension_d"), "40")
        self.assertEqual(session.get_object_user_text("slab", "lf_dimension_h"), "12")
        stored = json.loads(session.get_object_user_text("slab", FRAME_KEY))
        self.assertEqual(stored["derivation_method"], "oriented_box")

    def test_vertical_plane_puts_thickness_on_depth(self):
        aligned = axes_from_plane(
            (0, 0, 0),
            (0, 1, 0),
            (0, 0, 1),
            (1, 0, 0),
            normal_is_depth=True,
        )
        self.assertIsNotNone(aligned)
        _origin, x_axis, y_axis, z_axis = aligned
        self.assertAlmostEqual(z_axis[2], 1.0)
        self.assertAlmostEqual(abs(y_axis[0]), 1.0)
        self.assertLess(abs(x_axis[2]), 1e-6)


if __name__ == "__main__":
    unittest.main()
