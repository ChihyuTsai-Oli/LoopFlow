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
from loopflow.features.dictionary.layer_paths import SYSTEM_LAYERS
from loopflow.features.project.console import open_console
from loopflow.features.project.menu import parse_menu_choice, run_nexus_console
from loopflow.foundation.paths import CONFIG_DIR_NAME, PRODUCT_DIR_NAME
from loopflow.foundation.usertext import LEVEL_DATUM_KEY, LEVEL_ID_KEY, OBJECT_ID_KEY, SPACE_ID_KEY
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import read_project_config, write_project_config  # noqa: E402

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


def _session(root=None, **kwargs) -> MemorySession:
    """3dm 存在工作資料夾內；專案設定寫在同層的 _LoopFlow_Config/loopflow。"""
    unsaved = kwargs.pop("unsaved", False)
    config = kwargs.pop("config", {"project_id": PROJECT_ID})
    document_path = None
    if not unsaved:
        folder = Path(root if root is not None else tempfile.gettempdir())
        document_path = str(folder / "loopflow-nexus.3dm")
        if config is not None:
            write_project_config(folder, **config)
    session = MemorySession(
        document_text=kwargs.pop("document_text", {}),
        document_path=document_path,
        **kwargs,
    )
    session.add_object("a", selected=True, locked=False, hidden=False, color=(10, 20, 30), color_by_layer=False)
    session.set_document_modified(False)
    return session


class ConsoleOpenCheckTests(unittest.TestCase):
    def test_no_rhino_stops_without_creating(self):
        before = set(Path(tempfile.gettempdir()).iterdir())
        result = open_console()
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertEqual(before, after)

    def test_unsaved_document_blocks(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root, unsaved=True)
            result = open_console(session)
            self.assertFalse(result.ok)
            self.assertEqual(result.status, "blocked")
            self.assertEqual(result.blocking, ("unsaved_document",))
            self.assertFalse((root / CONFIG_DIR_NAME).exists())

    def test_missing_project_id_still_enters(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root, config=None)
            result = open_console(session)
            self.assertTrue(result.ok, result.message)
            self.assertIsNone(result.details["project_id"])
            stored = read_project_config(root)
            self.assertEqual(stored["schema_id"], "loopflow.project")
            self.assertEqual(stored["schema_version"], 1)
            self.assertTrue(any("選單 2" in item for item in result.warnings))

    def test_cm_session_lists_steps_and_does_not_write(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root)
            result = open_console(session)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.stage, "open_check")
            self.assertEqual(result.details["project_id"], PROJECT_ID)
            self.assertEqual(result.details["type_count"], 1)
            self.assertEqual(
                result.details["executable_steps"],
                (
                    "open_check",
                    "sync_type_layers",
                    "level_boundary",
                    "space_boundary",
                    "scan_apply_verify",
                ),
            )
            step_ids = [step["id"] for step in result.details["steps"]]
            self.assertEqual(
                step_ids,
                [
                    "open_check",
                    "sync_type_layers",
                    "level_boundary",
                    "space_boundary",
                    "scan_apply_verify",
                ],
            )
            self.assertTrue(all(step["status"] == "available" for step in result.details["steps"]))
            self.assertEqual(result.details["project_folder"], str(root))
            self.assertEqual(result.details["config_dir"], str(root / CONFIG_DIR_NAME / PRODUCT_DIR_NAME))
            self.assertFalse(result.details["registry_exists"])
            self.assertFalse((root / CONFIG_DIR_NAME / PRODUCT_DIR_NAME / "logs").exists())
            self.assertTrue(session.get_view_state("a").selected)

    def test_open_check_uses_stored_custom_dictionary_filename(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            custom = root / "TeamA.xlsx"
            written = write_table(custom, schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_valid_row()])
            self.assertTrue(written.ok)
            session = _session(
                root,
                config={"project_id": PROJECT_ID, "dictionary_filename": "TeamA.xlsx"},
            )
            result = open_console(session)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.details["dictionary_filename"], "TeamA.xlsx")

    def test_open_check_missing_dictionary_warns_and_still_enters(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            session = _session(root)
            seen = []

            def _ask(default):
                seen.append(default)
                return "TeamA.xlsx"

            result = open_console(session, ask_dictionary=_ask)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.status, "ok_with_warnings")
            self.assertTrue(any("放回" in item for item in result.warnings))
            self.assertEqual(seen, [])
            self.assertNotIn("dictionary_filename", read_project_config(root))
            self.assertIn("open_check", result.details["executable_steps"])

    def test_non_cm_warns_but_still_enters(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root, model_unit="Millimeters")
            result = open_console(session)
            self.assertTrue(result.ok)
            self.assertEqual(result.status, "ok_with_warnings")
            self.assertTrue(any("不是 cm" in item for item in result.warnings))
            self.assertEqual(result.details["steps"][0]["id"], "open_check")

    def test_unknown_schema_version_stops(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root, config={"project_id": PROJECT_ID, "schema_version": 99})
            result = open_console(session)
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "check_schema")

    def test_cancel_restores_rhino_state(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-nx01-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root)
            session.set_view_state(ObjectViewState("a", False, True, True, (0, 0, 0), True))
            session.set_document_modified(True)
            # 先把狀態改回去當「檢查前」基準，再在 cancel 路徑驗證還原。
            session.set_view_state(ObjectViewState("a", True, False, False, (10, 20, 30), False))
            session.set_document_modified(False)
            result = open_console(session, cancel=True)
            self.assertEqual(result.status, "cancelled")
            self.assertTrue(session.get_view_state("a").selected)
            self.assertFalse(session.get_view_state("a").locked)
            self.assertFalse(session.document_modified())
            self.assertFalse((root / CONFIG_DIR_NAME / PROJECT_ID).exists())


class ConsoleMenuTests(unittest.TestCase):
    def test_parse_menu_choice(self):
        self.assertEqual(parse_menu_choice("5"), ("scan_apply_verify", "apply"))
        self.assertEqual(parse_menu_choice("5  寫入模型 Metadata"), ("scan_apply_verify", "apply"))
        self.assertEqual(parse_menu_choice("6"), ("scan_apply_verify", "verify"))
        self.assertEqual(parse_menu_choice("6  檢核模型 Metadata（不寫入）"), ("scan_apply_verify", "verify"))
        self.assertIsNone(parse_menu_choice("7"))
        self.assertIsNone(parse_menu_choice("8"))
        self.assertIsNone(parse_menu_choice("9"))
        self.assertEqual(parse_menu_choice("3"), ("level_boundary", "scan"))
        self.assertEqual(parse_menu_choice("3  登記高程框（封閉曲線）"), ("level_boundary", "scan"))
        self.assertEqual(parse_menu_choice("4"), ("space_boundary", "scan"))
        self.assertEqual(parse_menu_choice("2"), ("sync_type_layers", "scan"))
        self.assertEqual(parse_menu_choice("2  從字典同步 Type Layers"), ("sync_type_layers", "scan"))
        self.assertIsNone(parse_menu_choice(None))
        self.assertIsNone(parse_menu_choice("取消"))

    def test_dictionary_duplicate_id_popup_lists_row(self):
        extra = _valid_row()
        extra[schema.MACHINE_KEYS.index("layer_path")] = "02_Wall_牆面::Timber.木紋_new"
        popups = []
        with tempfile.TemporaryDirectory(prefix="loopflow-dict-dup-") as raw:
            root = Path(raw)
            written = write_table(
                root / "LoopFlow_Dictionary.xlsx",
                schema.TITLE_ROW,
                schema.DISPLAY_COLUMNS,
                [_valid_row(), extra],
            )
            self.assertTrue(written.ok, written.message)
            session = _session(root)
            result = run_nexus_console(
                session,
                interactive=False,
                show_message=popups.append,
            )
            self.assertFalse(result.ok)
            self.assertIn("duplicate_type_id", result.blocking)
            self.assertTrue(popups)
            self.assertIn("重複", popups[0])
            self.assertIn("EX-01", popups[0])
            self.assertIn("第 4 列", popups[0])

    def test_interactive_cancel_keeps_open_check(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-menu-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root)
            result = run_nexus_console(
                session,
                interactive=True,
                chooser=lambda _labels: None,
            )
            self.assertEqual(result.status, "cancelled")
            self.assertEqual(result.details["project_id"], PROJECT_ID)
            self.assertFalse(session.document_modified())

    def test_interactive_verify_does_not_write(self):
        popups = []
        with tempfile.TemporaryDirectory(prefix="loopflow-menu-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root)
            result = run_nexus_console(
                session,
                interactive=True,
                chooser=lambda _labels: "6",
                show_message=popups.append,
            )
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.stage, "verify_model")
            self.assertFalse(result.details["publish_ready"])
            self.assertIsNone(session.get_object_user_text("a", "Q_01_寬度W"))
            self.assertNotIn("已 Apply", result.message)
            self.assertTrue(popups)

    def test_apply_without_boundaries_blocks(self):
        from loopflow.features.dictionary.layer_paths import to_full_path

        full = to_full_path("00_STR_結構::Beam.樑")
        with tempfile.TemporaryDirectory(prefix="loopflow-nx05-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root)
            session.ensure_layer(full)
            session.set_layer_user_text(full, "lf_type_id", "EX-01")
            session.add_object("beam", layer=full)
            session.set_bbox("beam", (0, 0, 0), (90, 40, 210))
            applied = open_console(
                session,
                step="scan_apply_verify",
                identity_action="apply",
            )
            self.assertFalse(applied.ok)
            self.assertEqual(applied.blocking, ("missing_level_or_space_boundary",))
            self.assertIsNone(session.get_object_user_text("beam", OBJECT_ID_KEY))
            self.assertIn("高程框", applied.message)

    def test_apply_without_boundaries_popup(self):
        from loopflow.features.dictionary.layer_paths import to_full_path

        full = to_full_path("00_STR_結構::Beam.樑")
        popups = []
        with tempfile.TemporaryDirectory(prefix="loopflow-nx05-popup-") as raw:
            root = Path(raw)
            _write_dictionary(root)
            session = _session(root)
            session.ensure_layer(full)
            session.set_layer_user_text(full, "lf_type_id", "EX-01")
            session.add_object("beam", layer=full)
            session.set_bbox("beam", (0, 0, 0), (90, 40, 210))
            applied = run_nexus_console(
                session,
                interactive=True,
                chooser=lambda _labels: "5",
                show_message=popups.append,
            )
            self.assertFalse(applied.ok)
            self.assertEqual(applied.blocking, ("missing_level_or_space_boundary",))
            self.assertTrue(any("高程框" in msg for msg in popups))

    def test_apply_writes_id_space_not_dimensions(self):
        from loopflow.features.dictionary.layer_paths import to_full_path
        from loopflow.platform.excel import write_table

        full = to_full_path("02_Wall_牆面::_Partition_Lightweight.輕隔間")
        space_layer = SYSTEM_LAYERS[0]
        ffl_layer = SYSTEM_LAYERS[1]
        space_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
        level_id = "11111111-1111-4111-8111-111111111111"
        wall_row = [None] * len(schema.DISPLAY_COLUMNS)
        wall_values = {
            "layer_path": "02_Wall_牆面::_Partition_Lightweight.輕隔間",
            "construction_default": "New",
            "type_id": "WL-01",
            "type_display_name": "輕隔間牆",
            "estimation_unit": "cm",
            "measurement_rule": "LEN_W",
            "elevation_basis": "BH",
            "remarks_default": "(手動輸入備註)",
        }
        for key, value in wall_values.items():
            wall_row[schema.MACHINE_KEYS.index(key)] = value
        with tempfile.TemporaryDirectory(prefix="loopflow-nx05-") as raw:
            root = Path(raw)
            written = write_table(
                root / "LoopFlow_Dictionary.xlsx",
                schema.TITLE_ROW,
                schema.DISPLAY_COLUMNS,
                [wall_row],
            )
            if not written.ok:
                raise AssertionError(written.message)
            session = _session(root)
            session.ensure_layer(full)
            session.set_layer_user_text(full, "lf_type_id", "WL-01")
            session.ensure_layer(ffl_layer)
            session.add_object("level", layer=ffl_layer)
            session.set_curve("level", [[-1, -1], [20, -1], [20, 20], [-1, 20]], closed=True)
            session.set_object_user_text("level", LEVEL_ID_KEY, level_id)
            session.set_object_user_text("level", LEVEL_DATUM_KEY, "50")
            session.ensure_layer(space_layer)
            session.add_object("space", layer=space_layer)
            session.set_curve("space", [[0, 0], [10, 0], [10, 8], [0, 8]], closed=True)
            session.set_object_user_text("space", SPACE_ID_KEY, space_id)
            session.set_object_user_text("space", "_01_空間名稱", "客廳")
            session.set_object_user_text("space", LEVEL_ID_KEY, level_id)
            session.add_object("beam", layer=full)
            session.set_bbox("beam", (2, 2, 0), (3, 3, 210))
            session.set_object_user_text("beam", "_05_寬度W", "90")
            applied = open_console(
                session,
                step="scan_apply_verify",
                identity_action="apply",
            )
            self.assertTrue(applied.ok, applied.message)
            self.assertFalse(applied.details["publish_ready"])
            self.assertIn("ID／Type", applied.message)
            self.assertIn("空間／高程", applied.message)
            self.assertNotIn("尺寸", applied.message)
            self.assertIsNotNone(session.get_object_user_text("beam", OBJECT_ID_KEY))
            self.assertEqual(session.get_object_user_text("beam", SPACE_ID_KEY), space_id)
            self.assertEqual(session.get_object_user_text("beam", "_06_高程計算"), "50")
            self.assertIsNone(session.get_object_user_text("beam", "_05_寬度W"))
            self.assertIsNone(session.get_object_user_text("beam", "Q_01_寬度W"))


if __name__ == "__main__":
    unittest.main()
