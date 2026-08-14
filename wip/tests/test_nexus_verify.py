# -*- coding: utf-8 -*-
"""Verify：比對 Apply 應寫的 UserText；不符則選取並彈窗。"""
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
from loopflow.features.dictionary.loader import load_from_table
from loopflow.features.model_data.identity import apply_identity
from loopflow.features.model_data.placement import apply_placement
from loopflow.features.model_data.space import SPACE_BOUNDARY_LAYER, SPACE_DISPLAY_KEY, SPACE_ID_KEY
from loopflow.features.model_data.verify import verify_model_data
from loopflow.foundation.usertext import OBJECT_ID_KEY
from loopflow.platform.rhino.memory import MemorySession

LAYER = "00_STR_結構::Beam.樑"
FULL = to_full_path(LAYER)
SPACE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


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
    session.set_layer_user_text(FULL, "lf_type_id", "EX-01")
    return session


def _add_space(session):
    session.ensure_layer(SPACE_BOUNDARY_LAYER)
    session.add_object("s1", layer=SPACE_BOUNDARY_LAYER)
    session.set_curve("s1", [[0, 0], [10, 0], [10, 8], [0, 8]], closed=True)
    session.set_object_user_text("s1", SPACE_ID_KEY, SPACE_A)
    session.set_object_user_text("s1", SPACE_DISPLAY_KEY, "客廳")


def _add_wall(session):
    session.add_object("wall", layer=FULL)
    session.set_bbox("wall", (2, 2, 0), (3, 3, 270))


def _apply(session, catalog):
    ident = apply_identity(session, catalog=catalog, guarded=False)
    if not ident.ok:
        raise AssertionError(ident.message)
    placed = apply_placement(session, catalog=catalog, guarded=False)
    if not placed.ok:
        raise AssertionError(placed.message)


class VerifyModelTests(unittest.TestCase):
    def test_after_apply_matches(self):
        session = _session()
        _add_space(session)
        _add_wall(session)
        catalog = _catalog(_row())
        _apply(session, catalog)
        popups = []
        result = verify_model_data(session, catalog=catalog, show_message=popups.append)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["mismatch_count"], 0)
        self.assertIn("相符", result.message)
        self.assertTrue(popups)
        self.assertIn("相符", popups[0])
        self.assertFalse(session.get_view_state("wall").selected)

    def test_mismatch_selects_object_and_explains(self):
        session = _session()
        _add_space(session)
        _add_wall(session)
        catalog = _catalog(_row())
        _apply(session, catalog)
        session.set_object_user_text("wall", SPACE_DISPLAY_KEY, "廁所")
        popups = []
        result = verify_model_data(session, catalog=catalog, show_message=popups.append)
        self.assertEqual(result.status, "ok_with_warnings")
        self.assertEqual(result.details["mismatch_object_ids"], ("wall",))
        self.assertTrue(session.get_view_state("wall").selected)
        self.assertIn("空間名稱", popups[0])
        self.assertIn("廁所", popups[0])
        self.assertIn("客廳", popups[0])
        self.assertIsNotNone(session.get_object_user_text("wall", OBJECT_ID_KEY))

    def test_before_apply_reports_missing_uuid(self):
        session = _session()
        _add_space(session)
        _add_wall(session)
        popups = []
        result = verify_model_data(session, catalog=_catalog(_row()), show_message=popups.append)
        self.assertEqual(result.status, "ok_with_warnings")
        self.assertIn("wall", result.details["mismatch_object_ids"])
        self.assertTrue(session.get_view_state("wall").selected)
        self.assertIn("UUID", popups[0])


if __name__ == "__main__":
    unittest.main()
