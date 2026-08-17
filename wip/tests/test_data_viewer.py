# -*- coding: utf-8 -*-
"""C04 Data Viewer：只讀 canonical 欄、缺值可讀、未知版本停止、不寫入。"""
from __future__ import annotations

import ast
import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Data_Viewer.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.loader import load_from_table
from loopflow.features.viewer.command import run_data_viewer
from loopflow.features.viewer.inspect import (
    MISSING_MARK,
    format_report,
    inspect_object,
)
from loopflow.foundation.usertext import (
    CONSTRUCTION_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    SPACE_DISPLAY_KEY,
    TYPE_ID_KEY,
)
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OBJECT_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


def _session(document_text=None, **kwargs) -> MemorySession:
    text = {
        "lf_project_id": PROJECT_ID,
        "lf_schema_id": "loopflow.project",
        "lf_schema_version": "1",
    }
    if document_text is not None:
        text = dict(document_text)
    session = MemorySession(document_text=text, **kwargs)
    session.add_object(
        "wall",
        selected=True,
        locked=False,
        hidden=False,
        color=(10, 20, 30),
        color_by_layer=False,
        name="Wall",
        layer="M3D::00_STR_結構::Beam.樑",
    )
    session.set_document_modified(False)
    return session


def _catalog():
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
    loaded = load_from_table(
        title=schema.TITLE_ROW,
        headers=schema.DISPLAY_COLUMNS,
        rows=[row],
    )
    if not loaded.ok:
        raise AssertionError(loaded.message)
    return loaded.details["catalog"]


def _snapshot_text(session: MemorySession) -> dict:
    payload = {
        "document": dict(session._document_text),
        "modified": session.document_modified(),
        "objects": {},
    }
    for object_id, meta in session._object_meta.items():
        payload["objects"][object_id] = copy.deepcopy(meta)
    return payload


class InspectTests(unittest.TestCase):
    def test_canonical_fields_and_missing_mark(self):
        session = _session()
        session.set_object_user_text("wall", SPACE_DISPLAY_KEY, "客廳")
        session.set_object_user_text("wall", TYPE_ID_KEY, "EX-01")
        session.set_object_user_text("wall", OBJECT_ID_KEY, OBJECT_ID)
        session.set_document_modified(False)
        report = inspect_object(session, "wall", catalog=_catalog())
        text = format_report(report)
        self.assertIn("客廳", text)
        self.assertIn("EX-01", text)
        self.assertIn(OBJECT_ID, text)
        self.assertIn(MISSING_MARK, text)
        self.assertIn("_08_備註*", report.missing_keys)
        self.assertIn("_02_建構狀態*", text)
        self.assertIn("_08_備註*", text)
        self.assertIn("_01_空間名稱*", text)
        self.assertNotIn("_02_建構狀態**", text)
        self.assertNotIn("_14_資料版次*", text)
        self.assertIn("字典名稱：鋼筋混凝土", text)
        self.assertNotIn("Q_01", text)

    def test_legacy_key_is_labelled_not_written(self):
        session = _session()
        session.set_object_user_text("wall", "lf_object_id", OBJECT_ID)
        session.set_document_modified(False)
        before = _snapshot_text(session)
        report = inspect_object(session, "wall")
        field = next(item for item in report.fields if item.key == OBJECT_ID_KEY)
        self.assertEqual(field.value, OBJECT_ID)
        self.assertEqual(field.source, "legacy")
        self.assertIn("lf_object_id", field.notes[0])
        self.assertEqual(_snapshot_text(session), before)

    def test_stale_dimension_is_warning_not_canonical(self):
        session = _session()
        session.set_object_user_text("wall", "Q_01_寬度W", "120")
        report = inspect_object(session, "wall")
        text = format_report(report)
        self.assertIn("殘留（不屬 2.0）", text)
        self.assertIn("Q_01_寬度W", report.stale)
        self.assertNotIn("120", "\n".join(
            "%s:%s" % (field.key, field.value) for field in report.fields
        ))

    def test_empty_object_is_understandable(self):
        session = _session()
        report = inspect_object(session, "wall")
        text = format_report(report)
        self.assertIn("這個物件沒有 UserText。", text)
        self.assertTrue(report.missing_keys)

    def test_override_notes_from_dictionary(self):
        session = _session()
        session.set_object_user_text("wall", TYPE_ID_KEY, "EX-01")
        session.set_object_user_text("wall", CONSTRUCTION_KEY, "New")
        session.set_object_user_text("wall", REMARKS_KEY, "現場修改")
        report = inspect_object(session, "wall", catalog=_catalog())
        construction = next(item for item in report.fields if item.key == CONSTRUCTION_KEY)
        remarks = next(item for item in report.fields if item.key == REMARKS_KEY)
        self.assertTrue(any("覆寫" in note for note in construction.notes))
        self.assertTrue(any("覆寫" in note for note in remarks.notes))

    def test_level_datum_falls_back_to_object_name(self):
        session = _session()
        session.add_object(
            "ffl",
            name="320",
            layer="M3D::_Data::Level_Boundaries_FFL",
        )
        report = inspect_object(session, "ffl")
        field = next(item for item in report.fields if item.key == "_15_樓層高程*")
        self.assertEqual(field.value, "320")
        self.assertEqual(field.source, "object_name")
        self.assertIn("_15_樓層高程*", format_report(report))

    def test_space_frame_marks_display_name_manual(self):
        session = _session()
        session.add_object(
            "room",
            name="廊道",
            layer="M3D::_Data::Space_Boundaries",
        )
        session.set_object_user_text("room", SPACE_DISPLAY_KEY, "廊道")
        text = format_report(inspect_object(session, "room"))
        self.assertIn("_01_空間名稱*", text)


class ViewerCommandTests(unittest.TestCase):
    def test_unknown_schema_version_stops_without_picking(self):
        session = _session(document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.project",
            "lf_schema_version": "99",
        })
        picked = []
        shown = []

        def pick(_current):
            picked.append(True)
            return "wall"

        result = run_data_viewer(
            session,
            pick_object=pick,
            show_report=shown.append,
            notify=shown.append,
        )
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "check_schema")
        self.assertIn("未知 schema_version", result.message)
        self.assertEqual(picked, [])
        self.assertTrue(shown)
        self.assertFalse(session.document_modified())

    def test_unknown_schema_id_stops(self):
        session = _session(document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.unknown",
            "lf_schema_version": "1",
        })
        result = run_data_viewer(
            session,
            pick_object=lambda _s: "wall",
            show_report=lambda _t: None,
            notify=lambda _m: None,
        )
        self.assertFalse(result.ok)
        self.assertIn("未知 schema_id", result.message)

    def test_cancel_first_pick_does_not_write(self):
        session = _session()
        session.set_object_user_text("wall", OBJECT_ID_KEY, OBJECT_ID)
        session.set_document_modified(False)
        before = _snapshot_text(session)
        result = run_data_viewer(
            session,
            pick_object=lambda _s: None,
            show_report=lambda _t: None,
        )
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot_text(session), before)
        self.assertTrue(session.get_view_state("wall").selected)

    def test_view_then_exit_restores_selection_and_does_not_write(self):
        session = _session()
        session.set_object_user_text("wall", OBJECT_ID_KEY, OBJECT_ID)
        session.add_object("other", selected=False, name="Other", layer="M3D::00_STR_結構::Beam.樑")
        session.set_document_modified(False)
        before = _snapshot_text(session)
        picks = ["other", None]
        shown = []

        def pick(current):
            current.set_view_state(
                ObjectViewState("wall", False, False, False, (10, 20, 30), False)
            )
            current.set_view_state(
                ObjectViewState("other", True, False, False, (0, 0, 0), True)
            )
            return picks.pop(0)

        result = run_data_viewer(
            session,
            pick_object=pick,
            show_report=shown.append,
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["viewed"], 1)
        self.assertEqual(len(shown), 1)
        self.assertIn(MISSING_MARK, shown[0])
        self.assertEqual(_snapshot_text(session)["objects"], before["objects"])
        self.assertFalse(session.document_modified())
        self.assertTrue(session.get_view_state("wall").selected)
        self.assertFalse(session.get_view_state("other").selected)

    def test_missing_schema_warns_but_still_views(self):
        session = _session(document_text={})
        session.set_object_user_text("wall", TYPE_ID_KEY, "EX-01")
        session.set_document_modified(False)
        picks = ["wall", None]
        shown = []
        result = run_data_viewer(
            session,
            pick_object=lambda _s: picks.pop(0),
            show_report=shown.append,
        )
        self.assertTrue(result.ok)
        self.assertIn("missing_document_schema", result.warnings)
        self.assertIn("EX-01", shown[0])
        self.assertFalse(session.document_modified())


class CatalogAndEntrypointTests(unittest.TestCase):
    def test_catalog_marks_data_viewer_ready(self):
        from loopflow.command_catalog import get_command

        spec = get_command("LF_Data_Viewer")
        self.assertEqual(spec["status"], "console")
        self.assertEqual(spec["task"], "C04")
        self.assertEqual(spec["entrypoint"], "LF_Data_Viewer.py")

    def test_entrypoint_has_no_feature_code(self):
        source = ENTRY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIsInstance(tree, ast.Module)
        for forbidden in ("rhinoscriptsyntax", "Rhino", "scriptcontext", "SetUserText"):
            self.assertNotIn(forbidden, source)

    def test_run_command_without_rhino_does_not_claim_success(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_Data_Viewer")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已檢視", result.message)
        self.assertIn("Rhino", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
