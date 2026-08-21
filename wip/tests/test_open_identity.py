# -*- coding: utf-8 -*-
"""開空檔：專案名稱當身分、exchange 跟 3dm 資料夾走、schema 不擋。"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.dictionary.layer_paths import LAYER_PREFIX_KEY, PROJECT_ID_KEY
from loopflow.features.dictionary.sync import sync_type_layers
from loopflow.features.project.console import SCHEMA_ID_KEY, SCHEMA_VERSION_KEY, open_console
from loopflow.features.registry.publisher import publish_registry
from loopflow.foundation.paths import resolve_registry_for_document
from loopflow.platform.rhino.memory import MemorySession

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.loader import load_from_table
from loopflow.platform.excel import write_table


def _row():
    row = [None] * len(schema.DISPLAY_COLUMNS)
    values = {
        "layer_path": "00_STR_結構::Beam.樑",
        "construction_default": "Existing",
        "type_id": "EX-01",
        "type_display_name": "鋼筋混凝土",
        "estimation_unit": "樘",
        "measurement_rule": "COUNT",
        "elevation_basis": "BH",
        "remarks_default": "(手動輸入備註)",
    }
    for key, value in values.items():
        row[schema.MACHINE_KEYS.index(key)] = value
    return row


def _write_dictionary(root: Path) -> None:
    written = write_table(
        root / "LoopFlow_Dictionary.xlsx",
        schema.TITLE_ROW,
        schema.DISPLAY_COLUMNS,
        [_row()],
    )
    if not written.ok:
        raise AssertionError(written.message)


def _catalog():
    result = load_from_table(
        title=schema.TITLE_ROW,
        headers=list(schema.DISPLAY_COLUMNS),
        rows=[_row()],
    )
    if not result.ok:
        raise AssertionError(result.message)
    return result.details["catalog"]


def _min_payload(project_id="M3D"):
    return {
        "schema_id": "loopflow.registry",
        "schema_version": 1,
        "project_id": project_id,
        "registry_revision": 1,
        "published_at": "2026-08-21T00:00:00Z",
        "model_unit": "Centimeters",
        "types": [],
        "spaces": [{"space_id": "EXT", "level_id": None, "space_display": "EXT"}],
        "objects": [],
        "extension": {},
    }


class OpenIdentityTests(unittest.TestCase):
    def test_sync_writes_project_name_to_both_keys(self):
        session = MemorySession(document_text={})
        with tempfile.TemporaryDirectory(prefix="loopflow-id-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            result = sync_type_layers(
                session,
                catalog=_catalog(),
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                layer_prefix="Tower",
            )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.document_user_text(LAYER_PREFIX_KEY), "Tower")
        self.assertEqual(session.document_user_text(PROJECT_ID_KEY), "Tower")

    def test_renamed_3dm_keeps_same_exchange(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-id-") as raw:
            folder = Path(raw)
            first = folder / "draft.3dm"
            second = folder / "final.3dm"
            written = publish_registry(_min_payload("M3D"), document_path=str(first))
            self.assertTrue(written.ok, written.message)
            official = folder / "exchange" / "M3D" / "Project_Registry.json"
            self.assertTrue(official.exists())
            located = resolve_registry_for_document(second, "M3D")
            self.assertEqual(located.details["registry"], official)

    def test_renamed_project_uses_new_folder_without_moving(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-id-") as raw:
            folder = Path(raw)
            model = folder / "model.3dm"
            first = publish_registry(_min_payload("M3D"), document_path=str(model))
            self.assertTrue(first.ok, first.message)
            old_folder = folder / "exchange" / "M3D"
            self.assertTrue((old_folder / "Project_Registry.json").exists())
            second = publish_registry(_min_payload("Tower"), document_path=str(model))
            self.assertTrue(second.ok, second.message)
            new_folder = folder / "exchange" / "Tower"
            self.assertTrue((new_folder / "Project_Registry.json").exists())
            self.assertTrue((old_folder / "Project_Registry.json").exists())

    def test_open_check_does_not_look_up_old_uuid_exchange(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-id-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            old = root / "exchange" / "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
            old.mkdir(parents=True)
            (old / "Project_Registry.json").write_text("{}", encoding="utf-8")
            session = MemorySession(
                document_text={
                    LAYER_PREFIX_KEY: "M3D",
                    PROJECT_ID_KEY: "M3D",
                },
                document_path=str(root / "model.3dm"),
            )
            result = open_console(session, environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertTrue(result.ok, result.message)
            self.assertFalse(result.details["exchange_exists"])
            self.assertEqual(result.details["project_id"], "M3D")
            self.assertEqual(session.document_user_text(SCHEMA_ID_KEY), "loopflow.project")
            self.assertEqual(session.document_user_text(SCHEMA_VERSION_KEY), "1")


if __name__ == "__main__":
    unittest.main()
