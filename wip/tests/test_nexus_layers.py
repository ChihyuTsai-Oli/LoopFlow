# -*- coding: utf-8 -*-
"""NX-02 Type layer 同步：新建、保留、DNA_REF 取代、20_DW 排除、反向匯出。"""
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
from loopflow.features.dictionary.layer_paths import (
    DW_PLAN_LAYER,
    LAYER_CONSTRUCTION_KEY,
    LAYER_TYPE_ID_KEY,
    SYSTEM_LAYERS,
    color_for_layer_path,
    dna_ref_name,
    to_full_path,
)
from loopflow.features.dictionary.loader import load_from_table
from loopflow.features.dictionary.sync import export_layer_diff, sync_type_layers
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

from loopflow.features.project.console import (
    PROJECT_ID_KEY,
    SCHEMA_ID_KEY,
    SCHEMA_VERSION_KEY,
)


def _row(**overrides):
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
    session.add_object("model-a", selected=True, name="Wall", layer="Default")
    session.set_object_user_text("model-a", "lf_remarks", "人工備註")
    session.set_document_modified(False)
    return session


class LayerSyncTests(unittest.TestCase):
    def test_creates_new_layer_with_defaults_and_dna_ref(self):
        session = _session()
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            environ = {"LOOPFLOW_WORKFILES_ROOT": raw}
            result = sync_type_layers(session, environ=environ, catalog=catalog)
        self.assertTrue(result.ok, result.message)
        full = to_full_path("00_STR_結構::Beam.樑")
        self.assertTrue(session.has_layer(full))
        self.assertEqual(session.get_layer_user_text(full, LAYER_TYPE_ID_KEY), "EX-01")
        self.assertEqual(session.get_layer_user_text(full, LAYER_CONSTRUCTION_KEY), "Existing")
        names = [session.object_name(oid) for oid in session.objects_on_layer(full)]
        self.assertEqual(names, [dna_ref_name("EX-01")])
        self.assertEqual(session.get_object_user_text("model-a", "lf_remarks"), "人工備註")
        self.assertIsNone(session.get_object_user_text("model-a", "lf_construction_status"))
        self.assertTrue(session.get_view_state("model-a").selected)

    def test_layer_color_follows_prefix_map(self):
        self.assertEqual(color_for_layer_path("M3D::00_STR_結構::Beam.樑"), (202, 16, 16))
        self.assertEqual(color_for_layer_path("M3D::20_DW"), (206, 255, 0))
        self.assertEqual(color_for_layer_path(SYSTEM_LAYERS[0]), (0, 0, 0))

    def test_sync_applies_color_and_material_name(self):
        session = _session()
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            result = sync_type_layers(session, environ={"LOOPFLOW_WORKFILES_ROOT": raw}, catalog=catalog)
        self.assertTrue(result.ok, result.message)
        full = to_full_path("00_STR_結構::Beam.樑")
        self.assertEqual(session.layer_color(full), (202, 16, 16))
        self.assertEqual(session.layer_material_name(full), full)
        self.assertEqual(session.layer_color(SYSTEM_LAYERS[0]), (0, 0, 0))
        self.assertIsNone(session.layer_material_name(SYSTEM_LAYERS[0]))

    def test_existing_layer_keeps_data(self):
        session = _session()
        full = to_full_path("00_STR_結構::Beam.樑")
        session.ensure_layer(full)
        session.set_layer_user_text(full, LAYER_CONSTRUCTION_KEY, "Demolished")
        session.set_layer_user_text(full, LAYER_TYPE_ID_KEY, "OLD")
        catalog = _catalog(_row(construction_default="Existing"))
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            result = sync_type_layers(session, environ={"LOOPFLOW_WORKFILES_ROOT": raw}, catalog=catalog)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["kept_type_ids"], ("EX-01",))
        self.assertEqual(session.get_layer_user_text(full, LAYER_CONSTRUCTION_KEY), "Demolished")
        self.assertEqual(session.get_layer_user_text(full, LAYER_TYPE_ID_KEY), "OLD")
        self.assertEqual(session.layer_color(full), (202, 16, 16))
        self.assertEqual(session.layer_material_name(full), full)

    def test_dna_ref_replaces_and_does_not_accumulate(self):
        session = _session()
        full = to_full_path("00_STR_結構::Beam.樑")
        session.ensure_layer(full)
        session.add_placeholder(layer=full, name="DNA_REF_舊名")
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            environ = {"LOOPFLOW_WORKFILES_ROOT": raw}
            first = sync_type_layers(session, environ=environ, catalog=catalog)
            second = sync_type_layers(session, environ=environ, catalog=catalog)
        self.assertTrue(first.ok and second.ok)
        names = [session.object_name(oid) for oid in session.objects_on_layer(full)]
        self.assertEqual(names, [dna_ref_name("EX-01")])

    def test_dw_child_layers_are_excluded(self):
        session = _session()
        session.ensure_layer(DW_PLAN_LAYER + "::Frame")
        catalog = _catalog(
            _row(layer_path="20_DW", type_id="DW-01", construction_default="New"),
            _row(layer_path="20_DW::Frame", type_id="DW-02", construction_default="New"),
        )
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            result = sync_type_layers(session, environ={"LOOPFLOW_WORKFILES_ROOT": raw}, catalog=catalog)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["skipped_dw_children"], ("20_DW::Frame",))
        self.assertTrue(session.has_layer(DW_PLAN_LAYER))
        self.assertIsNone(session.get_layer_user_text(DW_PLAN_LAYER + "::Frame", LAYER_TYPE_ID_KEY))

    def test_reverse_export_skips_object_usertext_and_official_dictionary(self):
        session = _session()
        catalog = _catalog(_row())
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            root = Path(raw)
            official = root / "LoopFlow_Dictionary.xlsx"
            write_table(official, schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
            before = official.read_bytes()
            diff = root / "layer_diff.xlsx"
            result = sync_type_layers(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": raw},
                catalog=catalog,
                export_path=diff,
            )
            blocked = export_layer_diff(session, catalog, official, dictionary_path=official)
            self.assertTrue(result.ok, result.message)
            self.assertTrue(diff.exists())
            self.assertEqual(official.read_bytes(), before)
            self.assertEqual(blocked.blocking, ("overwrite_dictionary_forbidden",))
            self.assertEqual(session.get_object_user_text("model-a", "lf_remarks"), "人工備註")

    def test_cancel_does_not_create_layers(self):
        session = _session()
        catalog = _catalog(_row())
        session.set_view_state(ObjectViewState("model-a", True, False, False, (0, 0, 0), True))
        with tempfile.TemporaryDirectory(prefix="loopflow-nx02-") as raw:
            result = sync_type_layers(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": raw},
                catalog=catalog,
                cancel=True,
            )
        self.assertEqual(result.status, "cancelled")
        self.assertFalse(session.has_layer(to_full_path("00_STR_結構::Beam.樑")))
        self.assertTrue(session.get_view_state("model-a").selected)


if __name__ == "__main__":
    unittest.main()
