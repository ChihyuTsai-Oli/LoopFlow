# -*- coding: utf-8 -*-
"""NX-04 物件 ID／Type：Scan 不寫入、複製碰撞、hidden／locked、局部不可發布。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.layer_paths import dna_ref_name, to_full_path
from loopflow.features.dictionary.loader import load_from_table
from loopflow.features.model_data.identity import (
    CONSTRUCTION_KEY,
    DATA_REVISION_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    TYPE_ID_KEY,
    UUID_V4_RE,
    apply_identity,
    rollback_identity,
    scan_identity,
    verify_identity,
)
from loopflow.features.project.console import (
    PROJECT_ID_KEY,
    SCHEMA_ID_KEY,
    SCHEMA_VERSION_KEY,
    open_console,
)
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

LAYER = "00_STR_結構::Beam.樑"
FULL = to_full_path(LAYER)
VALID_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
OLD_ID = "11111111-1111-4111-8111-111111111111"
NEW_ID = "22222222-2222-4222-8222-222222222222"
PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


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
            PROJECT_ID_KEY: PROJECT_ID,
            SCHEMA_ID_KEY: "loopflow.project",
            SCHEMA_VERSION_KEY: "1",
        }
    )
    session.ensure_layer(FULL)
    session.set_document_modified(False)
    return session


def _add_model(session: MemorySession, object_id: str, **kwargs) -> None:
    hidden = kwargs.pop("hidden", False)
    locked = kwargs.pop("locked", False)
    selected = kwargs.pop("selected", False)
    layer = kwargs.pop("layer", FULL)
    session.add_object(object_id, selected=selected, hidden=hidden, locked=locked, layer=layer, **kwargs)


class IdentityScanApplyTests(unittest.TestCase):
    def test_scan_does_not_write_and_includes_hidden_locked(self):
        session = _session()
        _add_model(session, "visible")
        _add_model(session, "hidden-obj", hidden=True)
        _add_model(session, "locked-obj", locked=True)
        session.add_placeholder(layer=FULL, name=dna_ref_name("EX-01"))
        session.add_object("curve-0", selected=True, name="客廳", layer="M3D::_Data::Space_Boundaries")
        session.set_curve("curve-0", [[0, 0], [4, 0], [4, 4], [0, 4]], closed=True)
        session.add_object("outside", layer="Default")
        session.set_document_modified(False)
        result = scan_identity(session, catalog=_catalog(_row()))
        self.assertTrue(result.ok, result.message)
        self.assertFalse(result.details["publish_ready"])
        self.assertEqual(result.details["scope"], "full")
        rhino_ids = [item["rhino_id"] for item in result.details["items"]]
        self.assertEqual(sorted(rhino_ids), ["hidden-obj", "locked-obj", "visible"])
        self.assertIsNone(session.get_object_user_text("visible", OBJECT_ID_KEY))
        self.assertFalse(session.document_modified())
        self.assertTrue(any(item["hidden"] for item in result.details["items"]))
        self.assertTrue(any(item["locked"] for item in result.details["items"]))

    def test_partial_scan_cannot_mark_publish_ready(self):
        session = _session()
        _add_model(session, "a", selected=True)
        _add_model(session, "b", selected=False)
        result = scan_identity(session, catalog=_catalog(_row()), selected_only=True)
        self.assertEqual(result.details["scope"], "partial")
        self.assertFalse(result.details["publish_ready"])
        self.assertEqual([item["rhino_id"] for item in result.details["items"]], ["a"])

    def test_apply_mints_missing_ids_and_keeps_valid(self):
        session = _session()
        _add_model(session, "new")
        _add_model(session, "keep")
        session.set_object_user_text("keep", OBJECT_ID_KEY, VALID_ID)
        session.set_object_user_text("keep", "_01_空間ID", "EXT")
        session.set_object_user_text("keep", REMARKS_KEY, "人工備註")
        applied = apply_identity(session, catalog=_catalog(_row()))
        self.assertTrue(applied.ok, applied.message)
        created = session.get_object_user_text("new", OBJECT_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(created))
        self.assertNotEqual(created, VALID_ID)
        self.assertEqual(session.get_object_user_text("keep", OBJECT_ID_KEY), VALID_ID)
        self.assertEqual(session.get_object_user_text("new", TYPE_ID_KEY), "EX-01")
        self.assertEqual(session.get_object_user_text("new", CONSTRUCTION_KEY), "Existing")
        self.assertEqual(session.get_object_user_text("new", REMARKS_KEY), "(手動輸入備註)")
        self.assertEqual(session.get_object_user_text("new", DATA_REVISION_KEY), "0")
        self.assertEqual(session.get_object_user_text("keep", REMARKS_KEY), "人工備註")
        self.assertEqual(session.get_object_user_text("keep", "_01_空間ID"), "EXT")
        self.assertIsNone(session.get_object_user_text("new", "_01_空間ID"))
        self.assertFalse(applied.details["publish_ready"])

    def test_duplicate_requires_mapping_then_rollback(self):
        session = _session()
        _add_model(session, "a")
        _add_model(session, "b")
        session.set_object_user_text("a", OBJECT_ID_KEY, OLD_ID)
        session.set_object_user_text("b", OBJECT_ID_KEY, OLD_ID)
        scanned = scan_identity(session, catalog=_catalog(_row()))
        self.assertIn("duplicate_object_id", scanned.details["blocking"])
        blocked = apply_identity(session, catalog=_catalog(_row()))
        self.assertEqual(blocked.status, "ok_with_warnings")
        self.assertEqual(session.get_object_user_text("a", OBJECT_ID_KEY), OLD_ID)
        self.assertEqual(session.get_object_user_text("b", OBJECT_ID_KEY), OLD_ID)
        self.assertIn("b", blocked.details["remaining"])
        mapped = apply_identity(session, catalog=_catalog(_row()), mappings={"b": NEW_ID})
        self.assertTrue(mapped.ok, mapped.message)
        self.assertEqual(session.get_object_user_text("a", OBJECT_ID_KEY), OLD_ID)
        self.assertEqual(session.get_object_user_text("b", OBJECT_ID_KEY), NEW_ID)
        self.assertEqual(mapped.details["id_mappings"], ({"object_id": "b", "old_id": OLD_ID, "new_id": NEW_ID},))
        rolled = rollback_identity(session, mapped.details["id_mappings"])
        self.assertTrue(rolled.ok, rolled.message)
        self.assertEqual(session.get_object_user_text("b", OBJECT_ID_KEY), OLD_ID)

    def test_invalid_id_and_uppercase_need_mapping(self):
        session = _session()
        _add_model(session, "not-uuid")
        _add_model(session, "upper")
        session.set_object_user_text("not-uuid", OBJECT_ID_KEY, "EX-01")
        session.set_object_user_text("upper", OBJECT_ID_KEY, "3FA85F64-5717-4562-B3FC-2C963F66AFA6")
        scanned = scan_identity(session, catalog=_catalog(_row()))
        self.assertIn("invalid_object_id", scanned.details["blocking"])
        blocked = apply_identity(session, catalog=_catalog(_row()))
        self.assertEqual(blocked.status, "blocked")
        self.assertEqual(session.get_object_user_text("not-uuid", OBJECT_ID_KEY), "EX-01")
        mapped = apply_identity(
            session,
            catalog=_catalog(_row()),
            mappings={"not-uuid": OLD_ID, "upper": NEW_ID},
        )
        self.assertTrue(mapped.ok, mapped.message)
        self.assertEqual(session.get_object_user_text("not-uuid", OBJECT_ID_KEY), OLD_ID)
        self.assertEqual(session.get_object_user_text("upper", OBJECT_ID_KEY), NEW_ID)

    def test_unknown_type_remains_after_partial_apply(self):
        session = _session()
        session.ensure_layer("M3D::99_UNKNOWN::Thing")
        _add_model(session, "good")
        _add_model(session, "bad", layer="M3D::99_UNKNOWN::Thing")
        applied = apply_identity(session, catalog=_catalog(_row()))
        self.assertEqual(applied.status, "ok_with_warnings")
        self.assertTrue(UUID_V4_RE.match(session.get_object_user_text("good", OBJECT_ID_KEY)))
        self.assertIsNone(session.get_object_user_text("bad", OBJECT_ID_KEY))
        verified = verify_identity(session, catalog=_catalog(_row()))
        self.assertFalse(verified.details["publish_ready"])
        self.assertIn("bad", verified.details["remaining"])
        self.assertNotIn("good", verified.details["remaining"])

    def test_cancel_does_not_write(self):
        session = _session()
        _add_model(session, "a", selected=True)
        session.set_view_state(ObjectViewState("a", True, False, False, (1, 2, 3), False))
        session.set_document_modified(False)
        result = apply_identity(session, catalog=_catalog(_row()), cancel=True)
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("a", OBJECT_ID_KEY))
        self.assertTrue(session.get_view_state("a").selected)
        self.assertFalse(session.document_modified())

    def test_console_scan_step(self):
        session = _session()
        _add_model(session, "wall")
        with tempfile.TemporaryDirectory(prefix="loopflow-nx04-") as raw:
            root = Path(raw)
            write_table(
                root / "LoopFlow_Dictionary.xlsx",
                schema.TITLE_ROW,
                schema.DISPLAY_COLUMNS,
                [_row()],
            )
            scanned = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="scan_apply_verify",
            )
            self.assertEqual(scanned.stage, "scan_identity", scanned.message)
            self.assertTrue(scanned.ok, scanned.message)
            self.assertIsNone(session.get_object_user_text("wall", OBJECT_ID_KEY))
            applied = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="scan_apply_verify",
                identity_action="apply",
            )
        self.assertTrue(applied.ok, applied.message)
        self.assertTrue(UUID_V4_RE.match(session.get_object_user_text("wall", OBJECT_ID_KEY)))
        self.assertFalse(applied.details["publish_ready"])


if __name__ == "__main__":
    unittest.main()
