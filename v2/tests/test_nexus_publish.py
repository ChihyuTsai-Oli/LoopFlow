# -*- coding: utf-8 -*-
"""NX-07：Verify 通過才發布；payload 不含 Tag／尺寸；C03 失敗保留 last-good。"""
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
from loopflow.features.dictionary.layer_paths import to_full_path
from loopflow.features.dictionary.loader import load_from_table
from loopflow.features.model_data.identity import apply_identity
from loopflow.features.model_data.placement import apply_placement
from loopflow.features.model_data.space import (
    SPACE_BOUNDARY_LAYER,
    SPACE_FRAME_DISPLAY_KEY,
    SPACE_ID_KEY,
)
from loopflow.features.registry.handoff import publish_from_session, run_publish_exchange
from loopflow.features.registry.lock import acquire_lock, release_lock
from loopflow.foundation.atomic_io import read_json
from loopflow.foundation.paths import CONFIG_DIR_NAME
from loopflow.foundation.usertext import DATA_REVISION_KEY, LEVEL_ID_KEY, OBJECT_ID_KEY
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.memory import MemorySession

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import bind_project  # noqa: E402

LAYER = "02_Wall_牆面::_Partition_Lightweight.輕隔間"
FULL = to_full_path(LAYER)
SPACE_A = "aaaaaaaa-aaaa-4bbb-8bbb-bbbbbbbbbbbb"
LEVEL_A = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
PROJECT_ID = "大安邸"


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


def _write_dictionary(root: Path) -> None:
    path = root / "LoopFlow_Dictionary.xlsx"
    written = write_table(path, schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
    if not written.ok:
        raise AssertionError(written.message)


def _catalog(*rows):
    result = load_from_table(title=schema.TITLE_ROW, headers=list(schema.DISPLAY_COLUMNS), rows=list(rows))
    if not result.ok:
        raise AssertionError(result.message)
    return result.details["catalog"]


def _session(root) -> MemorySession:
    session = MemorySession()
    bind_project(session, root, project_id=PROJECT_ID)
    session.ensure_layer(FULL)
    session.set_layer_user_text(FULL, "lf_type_id", "WL-01")
    return session


def _registry_folder(root) -> Path:
    return Path(root) / CONFIG_DIR_NAME / PROJECT_ID


def _add_space(session):
    session.ensure_layer(SPACE_BOUNDARY_LAYER)
    session.add_object("s1", layer=SPACE_BOUNDARY_LAYER)
    session.set_curve("s1", [[0, 0], [10, 0], [10, 8], [0, 8]], closed=True)
    session.set_object_user_text("s1", SPACE_ID_KEY, SPACE_A)
    session.set_object_user_text("s1", SPACE_FRAME_DISPLAY_KEY, "客廳")
    session.set_object_user_text("s1", LEVEL_ID_KEY, LEVEL_A)


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


class PublishHandoffTests(unittest.TestCase):
    def test_before_verify_cannot_publish(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx07-") as raw:
            session = _session(raw)
            _add_space(session)
            _add_wall(session)
            result = publish_from_session(
                session,
                catalog=_catalog(_row()),
                show_message=lambda _msg: None,
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.blocking, ("verify_not_passed",))
            self.assertIn("尚未通過檢核，不能發布。", result.message)
            self.assertIn("檢核發現", result.message)
            self.assertIn("UUID", result.message)
            self.assertIn("Nexus 5 寫入模型 Metadata", result.message)
            self.assertTrue(session.get_view_state("wall").selected)
            self.assertEqual(list(_registry_folder(raw).glob("Project_Registry.json")), [])

    def test_partial_selection_cannot_publish(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx07-") as raw:
            session = _session(raw)
            _add_wall(session)
            result = publish_from_session(
                session,
                catalog=_catalog(_row()),
                selected_only=True,
                show_message=lambda _msg: None,
            )
            self.assertEqual(result.blocking, ("partial_scan_cannot_publish",))

    def test_after_verify_writes_registry_without_tag_or_quantity(self):
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx07-") as raw:
            session = _session(raw)
            _add_space(session)
            _add_wall(session)
            _write_dictionary(Path(raw))
            _apply(session, catalog)
            popups = []
            result = run_publish_exchange(session, show_message=popups.append)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.command_id, "LF_Publish_Exchange")
            self.assertTrue(result.details["publish_ready"])
            self.assertTrue(popups)
            official = _registry_folder(raw) / "Project_Registry.json"
            last_good = _registry_folder(raw) / "Project_Registry.last-good.json"
            self.assertTrue(official.exists())
            self.assertTrue(last_good.exists())
            payload = read_json(official).details["payload"]
            self.assertEqual(payload["schema_id"], "loopflow.registry")
            self.assertEqual(payload["registry_revision"], 1)
            self.assertNotIn("Tag_Links", payload)
            self.assertEqual(len(payload["objects"]), 1)
            obj = payload["objects"][0]
            self.assertEqual(obj["object_id"], session.get_object_user_text("wall", OBJECT_ID_KEY))
            self.assertEqual(obj["type_id"], "WL-01")
            self.assertEqual(obj["type_display_name"], "輕隔間牆")
            self.assertEqual(obj["space_display"], "客廳")
            self.assertNotIn("quantity", obj)
            self.assertNotIn("dimension_w", obj)
            self.assertNotIn("local_frame", obj)
            space_ids = [item["space_id"] for item in payload["spaces"]]
            self.assertIn("EXT", space_ids)
            self.assertIn(SPACE_A, space_ids)
            self.assertEqual(session.get_object_user_text("wall", DATA_REVISION_KEY), "1")

    def test_c03_lock_failure_keeps_last_good(self):
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx07-") as raw:
            session = _session(raw)
            _add_space(session)
            _add_wall(session)
            _apply(session, catalog)
            first = publish_from_session(
                session,
                catalog=catalog,
                show_message=lambda _msg: None,
            )
            self.assertTrue(first.ok, first.message)
            folder = _registry_folder(raw)
            official = folder / "Project_Registry.json"
            last_good = folder / "Project_Registry.last-good.json"
            before = official.read_bytes()
            good = last_good.read_bytes()
            held = acquire_lock(folder / "Project_Registry.lock", pid=4242, host="test-host", pid_alive=lambda pid: True)
            self.assertTrue(held.ok, held.message)
            try:
                second = publish_from_session(
                    session,
                    catalog=catalog,
                    show_message=lambda _msg: None,
                )
                self.assertFalse(second.ok)
                self.assertEqual(second.blocking, ("registry_locked",))
                self.assertEqual(second.stage, "acquire_registry_lock")
                self.assertEqual(official.read_bytes(), before)
                self.assertEqual(last_good.read_bytes(), good)
            finally:
                release_lock(folder / "Project_Registry.lock", pid=4242, host="test-host")

    def test_structure_object_is_not_in_registry_objects(self):
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx07-") as raw:
            session = _session(raw)
            _add_space(session)
            _add_wall(session)
            _write_dictionary(Path(raw))
            _apply(session, catalog)
            structure = to_full_path("00_STR_結構::Beam.樑")
            session.ensure_layer(structure)
            session.add_object("beam", layer=structure)
            session.set_bbox("beam", (4, 4, 0), (5, 5, 10))
            session.set_object_user_text(
                "beam",
                OBJECT_ID_KEY,
                "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            )
            result = run_publish_exchange(session, show_message=lambda _msg: None)
            self.assertTrue(result.ok, result.message)
            payload = read_json(_registry_folder(raw) / "Project_Registry.json").details["payload"]
            self.assertEqual(len(payload["objects"]), 1)
            self.assertEqual(
                payload["objects"][0]["object_id"],
                session.get_object_user_text("wall", OBJECT_ID_KEY),
            )


if __name__ == "__main__":
    unittest.main()
