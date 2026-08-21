# -*- coding: utf-8 -*-
"""開啟原字典／匯出字典：檔在才開，缺檔停止且不建檔。"""
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
from loopflow.features.dictionary.open_workbook import (
    COMMAND_OPEN_EXPORT,
    COMMAND_OPEN_OFFICIAL,
    KIND_EXPORT,
    KIND_OFFICIAL,
    open_workbook,
)
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.memory import MemorySession

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import write_project_config  # noqa: E402

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


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


def _session(root, dictionary_filename=None, **kwargs) -> MemorySession:
    """3dm 與字典同層；記住的字典檔名寫在專案設定檔。"""
    write_project_config(root, project_id=PROJECT_ID, dictionary_filename=dictionary_filename)
    return MemorySession(document_path=Path(root) / "a.3dm", **kwargs)


class OpenWorkbookTests(unittest.TestCase):
    def test_opens_remembered_official_file(self):
        opened = []

        def _opener(path):
            opened.append(path)

        with tempfile.TemporaryDirectory(prefix="loopflow-open-dict-") as raw:
            root = Path(raw)
            write_table(root / "TeamA.xlsx", schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
            session = _session(root, dictionary_filename="TeamA.xlsx")
            result = open_workbook(session, kind=KIND_OFFICIAL, opener=_opener)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.command_id, COMMAND_OPEN_OFFICIAL)
            self.assertEqual(opened, [str(root / "TeamA.xlsx")])

    def test_missing_official_does_not_create(self):
        opened = []
        with tempfile.TemporaryDirectory(prefix="loopflow-open-dict-") as raw:
            session = _session(Path(raw))
            result = open_workbook(session, kind=KIND_OFFICIAL, opener=opened.append)
            self.assertFalse(result.ok)
            self.assertEqual(result.blocking, ("dictionary_not_selected",))
            self.assertEqual(opened, [])
            self.assertFalse((Path(raw) / "LoopFlow_Dictionary.xlsx").exists())

    def test_new_file_does_not_open_default_excel_beside_it(self):
        opened = []
        with tempfile.TemporaryDirectory(prefix="loopflow-open-dict-") as raw:
            root = Path(raw)
            write_table(root / "LoopFlow_Dictionary.xlsx", schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
            session = _session(root)
            result = open_workbook(session, kind=KIND_OFFICIAL, opener=opened.append)
            self.assertFalse(result.ok)
            self.assertEqual(result.blocking, ("dictionary_not_selected",))
            self.assertEqual(opened, [])
            export = open_workbook(session, kind=KIND_EXPORT, opener=opened.append)
            self.assertFalse(export.ok)
            self.assertEqual(export.blocking, ("dictionary_not_selected",))
            self.assertEqual(opened, [])

    def test_renamed_dictionary_stops_and_asks_to_move_it_back(self):
        opened = []
        with tempfile.TemporaryDirectory(prefix="loopflow-open-dict-") as raw:
            root = Path(raw)
            write_table(root / "TeamB.xlsx", schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
            session = _session(root, dictionary_filename="TeamA.xlsx")
            result = open_workbook(session, kind=KIND_OFFICIAL, opener=opened.append)
            self.assertFalse(result.ok)
            self.assertEqual(result.blocking, ("dictionary_file_missing",))
            self.assertIn("TeamA.xlsx", result.message)
            self.assertIn(".3dm", result.message)
            self.assertEqual(opened, [])

    def test_opens_export_beside_official(self):
        opened = []
        with tempfile.TemporaryDirectory(prefix="loopflow-open-dict-") as raw:
            root = Path(raw)
            write_table(root / "TeamA.xlsx", schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
            export = root / "TeamA_Export.xlsx"
            export.write_bytes(b"export")
            session = _session(root, dictionary_filename="TeamA.xlsx")
            result = open_workbook(session, kind=KIND_EXPORT, opener=opened.append)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.command_id, COMMAND_OPEN_EXPORT)
            self.assertEqual(opened, [str(export)])

    def test_missing_export_asks_to_run_export_command(self):
        opened = []
        with tempfile.TemporaryDirectory(prefix="loopflow-open-dict-") as raw:
            root = Path(raw)
            write_table(root / "LoopFlow_Dictionary.xlsx", schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_row()])
            session = _session(root, dictionary_filename="LoopFlow_Dictionary.xlsx")
            result = open_workbook(session, kind=KIND_EXPORT, opener=opened.append)
            self.assertFalse(result.ok)
            self.assertEqual(result.blocking, ("export_file_missing",))
            self.assertIn("LF_Export_Type_Layers", result.message)
            self.assertEqual(opened, [])
            self.assertFalse((root / "LoopFlow_Dictionary_Export.xlsx").exists())


if __name__ == "__main__":
    unittest.main()
