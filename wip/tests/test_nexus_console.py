# -*- coding: utf-8 -*-
"""NX-01 Console 開案檢查：缺設定停止、非 cm 可進入、取消不改 Rhino 狀態。"""
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
from loopflow.features.project.console import (
    PROJECT_ID_KEY,
    SCHEMA_ID_KEY,
    SCHEMA_VERSION_KEY,
    open_console,
)
from loopflow.features.project.menu import parse_menu_choice, run_nexus_console
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _valid_row():
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


def _write_dictionary(root: Path) -> Path:
    path = root / "LoopFlow_Dictionary.xlsx"
    written = write_table(path, schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_valid_row()])
    if not written.ok:
        raise AssertionError(written.message)
    return path


def _session(**kwargs) -> MemorySession:
    text = {
        PROJECT_ID_KEY: PROJECT_ID,
        SCHEMA_ID_KEY: "loopflow.project",
        SCHEMA_VERSION_KEY: "1",
    }
    text.update(kwargs.pop("document_text", {}))
    session = MemorySession(document_text=text, **kwargs)
    session.add_object("a", selected=True, locked=False, hidden=False, color=(10, 20, 30), color_by_layer=False)
    session.set_document_modified(False)
    return session


class ConsoleOpenCheckTests(unittest.TestCase):
    def test_missing_env_stops_without_creating(self):
        before = set(Path(tempfile.gettempdir()).iterdir())
        result = open_console(environ={})
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "resolve_workfiles")
        self.assertEqual(before, after)

    def test_missing_directory_stops_without_creating(self):
        missing = Path(tempfile.gettempdir()) / "loopflow-missing-console-root"
        self.assertFalse(missing.exists())
        result = open_console(environ={"LOOPFLOW_WORKFILES_ROOT": str(missing)})
        self.assertFalse(result.ok)
        self.assertFalse(missing.exists())

    def test_missing_project_id_blocks(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(document_text={PROJECT_ID_KEY: None, SCHEMA_ID_KEY: None, SCHEMA_VERSION_KEY: None})
            result = open_console(session, environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertFalse(result.ok)
            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.blocking, ("missing_project_id",))
            self.assertFalse((root / "exchange").exists())

    def test_cm_session_lists_steps_and_does_not_write(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            result = open_console(session, environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.stage, "open_check")
            self.assertEqual(result.details["project_id"], PROJECT_ID)
            self.assertEqual(result.details["type_count"], 1)
            self.assertEqual(
                result.details["executable_steps"],
                ("open_check", "sync_type_layers", "space_boundary", "scan_apply_verify"),
            )
            step_ids = [step["id"] for step in result.details["steps"]]
            self.assertEqual(
                step_ids,
                ["open_check", "sync_type_layers", "space_boundary", "scan_apply_verify", "publish_registry"],
            )
            self.assertEqual(result.details["steps"][1]["status"], "available")
            self.assertEqual(result.details["steps"][2]["status"], "available")
            self.assertEqual(result.details["steps"][3]["status"], "available")
            self.assertTrue(all(step["status"] == "not_implemented" for step in result.details["steps"][4:]))
            self.assertFalse((root / "exchange").exists())
            self.assertFalse((root / "logs").exists())
            self.assertTrue(session.get_view_state("a").selected)
            self.assertFalse(session.document_modified())

    def test_non_cm_warns_but_still_enters(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(model_unit="Millimeters")
            result = open_console(session, environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertTrue(result.ok)
            self.assertEqual(result.status, "ok_with_warnings")
            self.assertTrue(any("不是 cm" in item for item in result.warnings))
            self.assertEqual(result.details["steps"][0]["id"], "open_check")

    def test_unknown_schema_version_stops(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(document_text={SCHEMA_VERSION_KEY: "99"})
            result = open_console(session, environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "check_schema")

    def test_cancel_restores_rhino_state(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            session.set_view_state(ObjectViewState("a", False, True, True, (0, 0, 0), True))
            session.set_document_modified(True)
            # 先把狀態改回去當「檢查前」基準，再在 cancel 路徑驗證還原。
            session.set_view_state(ObjectViewState("a", True, False, False, (10, 20, 30), False))
            session.set_document_modified(False)
            result = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                cancel=True,
            )
            self.assertEqual(result.status, "cancelled")
            self.assertTrue(session.get_view_state("a").selected)
            self.assertFalse(session.get_view_state("a").locked)
            self.assertFalse(session.document_modified())
            self.assertFalse((root / "exchange").exists())


class ConsoleMenuTests(unittest.TestCase):
    def test_parse_menu_choice(self):
        self.assertEqual(parse_menu_choice("4  Scan（不寫入）"), ("scan_apply_verify", "scan"))
        self.assertEqual(parse_menu_choice("5"), ("scan_apply_verify", "apply"))
        self.assertEqual(parse_menu_choice("2"), ("sync_type_layers", "scan"))
        self.assertIsNone(parse_menu_choice(None))
        self.assertIsNone(parse_menu_choice("取消"))

    def test_interactive_cancel_keeps_open_check(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-menu-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            result = run_nexus_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                interactive=True,
                chooser=lambda _labels: None,
            )
            self.assertEqual(result.status, "cancelled")
            self.assertEqual(result.details["project_id"], PROJECT_ID)
            self.assertFalse(session.document_modified())

    def test_interactive_scan_does_not_write(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-menu-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            result = run_nexus_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                interactive=True,
                chooser=lambda _labels: "4",
            )
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.stage, "scan_identity")
            self.assertFalse(result.details["publish_ready"])
            self.assertIn("dimensions", result.details)
            self.assertIsNone(session.get_object_user_text("a", "lf_dimension_w"))
            self.assertNotIn("未寫 Space", result.message)
            self.assertNotIn("已 Apply", result.message)

    def test_apply_writes_dimensions_for_extrusion(self):
        from loopflow.features.dictionary.layer_paths import to_full_path
        from loopflow.features.dimension.frame import FRAME_KEY

        full = to_full_path("00_STR_結構::Beam.樑")
        with tempfile.TemporaryDirectory(prefix="loopflow-nx06-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            session.ensure_layer(full)
            session.set_layer_user_text(full, "lf_type_id", "EX-01")
            session.add_object("beam", layer=full)
            session.set_geometry_kind("beam", "extrusion")
            session.set_bbox("beam", (0, 0, 0), (90, 40, 210))
            scanned = run_nexus_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                interactive=True,
                chooser=lambda _labels: "4",
            )
            self.assertTrue(scanned.ok, scanned.message)
            self.assertIsNone(session.get_object_user_text("beam", FRAME_KEY))
            applied = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="scan_apply_verify",
                identity_action="apply",
            )
            self.assertTrue(applied.ok, applied.message)
            self.assertFalse(applied.details["publish_ready"])
            self.assertIn("尺寸", applied.message)
            self.assertNotIn("尺寸未寫入", applied.message)
            self.assertNotIn("未寫 Space", applied.message)
            self.assertEqual(session.get_object_user_text("beam", "lf_dimension_w"), "90")
            self.assertEqual(session.get_object_user_text("beam", "lf_quantity"), "1")
            self.assertIsNotNone(session.get_object_user_text("beam", FRAME_KEY))

    def test_closed_box_reports_unstable_frame(self):
        from loopflow.features.dictionary.layer_paths import to_full_path

        full = to_full_path("00_STR_結構::Beam.樑")
        with tempfile.TemporaryDirectory(prefix="loopflow-nx06-box-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            session.ensure_layer(full)
            session.add_object("box", layer=full)
            session.set_geometry_kind("box", "closed_box")
            session.set_bbox("box", (0, 0, 0), (10, 10, 10))
            result = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="scan_apply_verify",
                identity_action="scan",
            )
            self.assertTrue(result.ok, result.message)
            self.assertIn("no_unique_plane", result.warnings)
            self.assertIn("無穩定 local frame", result.message)
            self.assertIn("尚未寫入", result.message)
            self.assertNotIn("未寫 Space", result.message)
            self.assertFalse(result.details["publish_ready"])

    def test_apply_closed_box_writes_id_not_dimensions(self):
        from loopflow.features.dictionary.layer_paths import to_full_path
        from loopflow.features.dimension.frame import FRAME_KEY

        full = to_full_path("00_STR_結構::Beam.樑")
        with tempfile.TemporaryDirectory(prefix="loopflow-nx06-box-apply-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session()
            session.ensure_layer(full)
            session.set_layer_user_text(full, "lf_type_id", "EX-01")
            session.add_object("box", layer=full)
            session.set_geometry_kind("box", "closed_box")
            session.set_bbox("box", (0, 0, 0), (10, 10, 10))
            applied = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="scan_apply_verify",
                identity_action="apply",
            )
            self.assertTrue(applied.ok, applied.message)
            self.assertIn("ID／Type", applied.message)
            self.assertIn("空間／高程", applied.message)
            self.assertIn("尺寸未寫入：無穩定 local frame", applied.message)
            self.assertNotIn("未寫 Space", applied.message)
            self.assertIsNotNone(session.get_object_user_text("box", "lf_object_id"))
            self.assertEqual(session.get_object_user_text("box", "lf_space_id"), "EXT")
            self.assertIsNone(session.get_object_user_text("box", FRAME_KEY))


if __name__ == "__main__":
    unittest.main()
