# -*- coding: utf-8 -*-
"""Verify：比對 Apply 應寫的 UserText；不符則選取並彈窗。"""
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
from loopflow.features.model_data.identity import apply_identity
from loopflow.features.model_data.placement import apply_placement
from loopflow.features.model_data.space import (
    SPACE_BOUNDARY_LAYER,
    SPACE_DISPLAY_KEY,
    SPACE_FRAME_DISPLAY_KEY,
    SPACE_ID_KEY,
)
from loopflow.features.model_data.verify import verify_model_data
from loopflow.foundation.usertext import DATA_REVISION_KEY, OBJECT_ID_KEY
from loopflow.platform.rhino.memory import MemorySession

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import bind_project, registry_dir  # noqa: E402

LAYER = "02_Wall_牆面::_Partition_Lightweight.輕隔間"
FULL = to_full_path(LAYER)
SPACE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
PROJECT_NAME = "大安邸"


def _row(**overrides):
    row = [None] * len(schema.DISPLAY_COLUMNS)
    values = {
        "layer_path": LAYER,
        "construction_default": "New",
        "type_id": "WL-01",
        "type_display_name": "輕隔間牆",
        "estimation_unit": "cm",
        "measurement_rule": "LEN_W",
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
    session.set_layer_user_text(FULL, "lf_type_id", "WL-01")
    return session


def _add_space(session):
    session.ensure_layer(SPACE_BOUNDARY_LAYER)
    session.add_object("s1", layer=SPACE_BOUNDARY_LAYER)
    session.set_curve("s1", [[0, 0], [10, 0], [10, 8], [0, 8]], closed=True)
    session.set_object_user_text("s1", SPACE_ID_KEY, SPACE_A)
    session.set_object_user_text("s1", SPACE_FRAME_DISPLAY_KEY, "客廳")


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
        self.assertIn("Nexus 5 寫入模型 Metadata", popups[0])
        self.assertIsNotNone(session.get_object_user_text("wall", OBJECT_ID_KEY))

    def test_manual_revision_is_mismatch_and_apply_restores(self):
        session = _session()
        _add_space(session)
        _add_wall(session)
        catalog = _catalog(_row())
        _apply(session, catalog)
        self.assertEqual(session.get_object_user_text("wall", DATA_REVISION_KEY), "0")
        session.set_object_user_text("wall", DATA_REVISION_KEY, "99")
        popups = []
        result = verify_model_data(session, catalog=catalog, show_message=popups.append)
        self.assertEqual(result.status, "ok_with_warnings")
        self.assertIn("wall", result.details["mismatch_object_ids"])
        self.assertIn("資料版次", popups[0])
        self.assertIn("99", popups[0])
        self.assertIn("Nexus 5 寫入模型 Metadata", popups[0])
        _apply(session, catalog)
        self.assertEqual(session.get_object_user_text("wall", DATA_REVISION_KEY), "0")
        popups = []
        again = verify_model_data(session, catalog=catalog, show_message=popups.append)
        self.assertTrue(again.ok, again.message)
        self.assertEqual(again.details["mismatch_count"], 0)
        self.assertNotIn("寫入模型 Metadata", popups[0])

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

    def test_apply_restores_published_revision(self):
        session = _session()
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-rev-") as raw:
            root = Path(raw)
            bind_project(session, root, project_id=PROJECT_NAME)
            _add_space(session)
            _add_wall(session)
            folder = registry_dir(root, PROJECT_NAME)
            (folder / "Project_Registry.json").write_text(
                json.dumps({"registry_revision": 3, "project_id": PROJECT_NAME}),
                encoding="utf-8",
            )
            ident = apply_identity(session, catalog=catalog, guarded=False)
            self.assertTrue(ident.ok, ident.message)
            placed = apply_placement(session, catalog=catalog, guarded=False)
            self.assertTrue(placed.ok, placed.message)
            self.assertEqual(session.get_object_user_text("wall", DATA_REVISION_KEY), "3")
            session.set_object_user_text("wall", DATA_REVISION_KEY, "99")
            popups = []
            result = verify_model_data(session, catalog=catalog, show_message=popups.append)
            self.assertEqual(result.status, "ok_with_warnings")
            self.assertIn("資料版次", popups[0])
            ident = apply_identity(session, catalog=catalog, guarded=False)
            self.assertTrue(ident.ok, ident.message)
            self.assertEqual(session.get_object_user_text("wall", DATA_REVISION_KEY), "3")


    def test_structure_leftover_usertext_does_not_mismatch(self):
        session = _session()
        _add_space(session)
        _add_wall(session)
        structure = to_full_path("00_STR_結構::Beam.樑")
        session.ensure_layer(structure)
        session.add_object("beam", layer=structure)
        session.set_bbox("beam", (1, 1, 0), (2, 2, 10))
        catalog = _catalog(_row())
        _apply(session, catalog)
        session.set_object_user_text("beam", OBJECT_ID_KEY, "3fa85f64-5717-4562-b3fc-2c963f66afa6")
        session.set_object_user_text("beam", SPACE_DISPLAY_KEY, "亂填")
        popups = []
        result = verify_model_data(session, catalog=catalog, show_message=popups.append)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["mismatch_count"], 0)
        self.assertNotIn("beam", result.details.get("mismatch_object_ids") or ())


if __name__ == "__main__":
    unittest.main()
