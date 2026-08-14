# -*- coding: utf-8 -*-
"""Dictionary reader／validator。以 A06 fixtures 驗證，不依賴 Rhino 或真實 Dropbox。"""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
CONTRACT = WIP / "fixtures" / "contract" / "dictionary"
if str(SRC) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(SRC))

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.loader import load_from_path, load_from_table, load_from_workfiles
from loopflow.platform.excel import (
    DICTIONARY_FONT_NAME,
    DICTIONARY_FONT_SIZE,
    STATUS_FONT_COLORS,
    read_font_table,
    read_status_cell_colors,
    read_table,
    write_table,
)


def _load_json(name: str):
    return json.loads((CONTRACT / name).read_text(encoding="utf-8"))


def _blank_row():
    return [None] * len(schema.DISPLAY_COLUMNS)


def _set(row, machine_key, value):
    row = list(row)
    row[schema.MACHINE_KEYS.index(machine_key)] = value
    return row


def _valid_row(**overrides):
    row = _blank_row()
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
        row = _set(row, key, value)
    return row


def _load(rows, **kwargs):
    return load_from_table(
        title=kwargs.get("title", schema.TITLE_ROW),
        headers=kwargs.get("headers", list(schema.DISPLAY_COLUMNS)),
        rows=rows,
        schema_id=kwargs.get("schema_id", schema.SCHEMA_ID),
        schema_version=kwargs.get("schema_version", schema.SCHEMA_VERSION),
    )


class SchemaFixtureTests(unittest.TestCase):
    def test_constants_match_columns_fixture(self):
        cols = _load_json("columns.json")
        self.assertEqual(schema.SCHEMA_ID, cols["schema_id"])
        self.assertEqual(schema.SCHEMA_VERSION, cols["schema_version"])
        self.assertEqual(schema.TITLE_ROW, cols["title_row"])
        self.assertEqual(list(schema.DISPLAY_COLUMNS), cols["display_columns"])
        self.assertEqual(list(schema.MACHINE_KEYS), cols["machine_keys"])
        self.assertEqual(list(schema.TYPE_CATEGORIES), cols["type_categories"])
        self.assertEqual(len(schema.DISPLAY_COLUMNS), 15)

    def test_split_type_id_uses_category_prefix_not_first_hyphen(self):
        result = schema.split_type_id("EX-A-01")
        self.assertTrue(result.ok)
        self.assertEqual(result.details["type_category"], "EX")
        self.assertEqual(result.details["type_sequence"], "A-01")

    def test_unknown_category_is_blocked(self):
        result = schema.split_type_id("ZZ-01")
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("unknown_type_category",))


class VersionAndHeaderTests(unittest.TestCase):
    def test_unknown_schema_id_stops(self):
        result = _load([_valid_row()], schema_id="loopflow.unknown")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "check_schema")
        self.assertIn("未知 schema_id", result.message)

    def test_unknown_schema_version_stops(self):
        result = _load([_valid_row()], schema_version=99)
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "check_schema")
        self.assertIn("未知 schema_version", result.message)

    def test_unknown_title_stops(self):
        result = _load([_valid_row()], title="LoopFlow Dictionary v1.0")
        self.assertFalse(result.ok)
        self.assertIn("未知 Dictionary 版本標題", result.message)

    def test_wrong_column_count_blocks(self):
        result = _load([_valid_row()], headers=list(schema.DISPLAY_COLUMNS[:14]))
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.blocking, ("wrong_column_count",))

    def test_unknown_column_blocks(self):
        result = _load([_valid_row()], headers=list(schema.DISPLAY_COLUMNS) + ["_99_測試"])
        self.assertEqual(result.blocking, ("unknown_column",))

    def test_cb_columns_forbidden(self):
        result = _load([_valid_row()], headers=list(schema.DISPLAY_COLUMNS) + ["_CB.01"])
        self.assertEqual(result.blocking, ("cb_columns_forbidden",))


class CaseAndBaselineTests(unittest.TestCase):
    def test_cases_json(self):
        cases = _load_json("cases.json")["cases"]
        for case in cases:
            headers = list(schema.DISPLAY_COLUMNS)
            if case.get("extra_display_columns"):
                headers = headers + list(case["extra_display_columns"])
            elif case.get("display_column_count") not in (None, 15):
                headers = headers[: case["display_column_count"]]
            rows = [_valid_row()]
            if "estimation_unit" in case or "measurement_rule" in case:
                rows = [
                    _valid_row(
                        estimation_unit=case.get("estimation_unit", "樘"),
                        measurement_rule=case.get("measurement_rule"),
                    )
                ]
            if case.get("duplicate_type_id"):
                rows = [
                    _valid_row(type_id=case["duplicate_type_id"], layer_path="A::One"),
                    _valid_row(type_id=case["duplicate_type_id"], layer_path="A::Two"),
                ]
            result = _load(rows, headers=headers)
            expect = case["expect"]
            if expect == "pass":
                self.assertTrue(result.ok, case["id"])
                self.assertEqual(result.status, "ok", case["id"])
            elif expect == "warn_no_quantity":
                self.assertTrue(result.ok, case["id"])
                self.assertEqual(result.status, "ok_with_warnings", case["id"])
            else:
                self.assertFalse(result.ok, case["id"])
                self.assertEqual(result.status, "blocked", case["id"])

    def test_baseline_92_rows_pass(self):
        data = _load_json("measurement_rules.baseline.json")
        rows = []
        for item in data["rows"]:
            row = _blank_row()
            row = _set(row, "layer_path", item["layer_path"])
            row = _set(row, "type_id", item["type_id"])
            row = _set(row, "type_display_name", item["type_display_name"])
            row = _set(row, "estimation_unit", item["estimation_unit"])
            row = _set(row, "measurement_rule", item["measurement_rule"])
            row = _set(row, "elevation_basis", item["elevation_basis"])
            row = _set(row, "construction_default", item["construction_default"])
            row = _set(row, "remarks_default", item["remarks_default"])
            rows.append(row)
        result = _load(rows)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.status, "ok")
        catalog = result.details["catalog"]
        self.assertEqual(len(catalog.types), 92)
        self.assertEqual(catalog.by_type_id("EX-01").layer_path, data["rows"][0]["layer_path"])


class PathAndExcelTests(unittest.TestCase):
    def test_missing_env_does_not_create_files(self):
        before = set(Path(tempfile.gettempdir()).iterdir())
        result = load_from_workfiles(environ={})
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "resolve_workfiles")
        self.assertEqual(before, after)

    def test_missing_xlsx_does_not_create_file(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-dict-") as raw:
            root = Path(raw)
            xlsx = root / "LoopFlow_Dictionary.xlsx"
            result = load_from_workfiles(environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "resolve_dictionary")
            self.assertFalse(xlsx.exists())

    def test_xlsx_roundtrip(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-xlsx-") as raw:
            path = Path(raw) / "LoopFlow_Dictionary.xlsx"
            written = write_table(path, schema.TITLE_ROW, schema.DISPLAY_COLUMNS, [_valid_row()])
            self.assertTrue(written.ok)
            result = load_from_path(path)
            self.assertTrue(result.ok, result.message)
            record = result.details["catalog"].by_type_id("EX-01")
            self.assertEqual(record.type_display_name, "鋼筋混凝土")
            self.assertEqual(record.measurement_rule, "COUNT")

    def test_dictionary_profile_fonts_and_status_colors(self):
        headers = list(schema.DISPLAY_COLUMNS) + ["diff_status"]
        rows = [
            _valid_row() + ["unchanged"],
            _valid_row(type_id="EX-02") + ["missing_in_rhino"],
            _valid_row(type_id="EX-03") + ["added_in_rhino"],
            _valid_row(type_id="EX-04") + ["modified"],
        ]
        with tempfile.TemporaryDirectory(prefix="loopflow-xlsx-style-") as raw:
            plain = Path(raw) / "plain.xlsx"
            styled = Path(raw) / "styled.xlsx"
            self.assertTrue(write_table(plain, schema.TITLE_ROW, headers, rows).ok)
            self.assertTrue(
                write_table(styled, schema.TITLE_ROW, headers, rows, profile="dictionary").ok
            )
            self.assertEqual(read_font_table(plain), [])
            fonts = read_font_table(styled)
            self.assertTrue(all(item["name"] == DICTIONARY_FONT_NAME for item in fonts))
            self.assertTrue(all(item["size"] == DICTIONARY_FONT_SIZE for item in fonts))
            colors = read_status_cell_colors(styled)
            self.assertIsNone(colors["unchanged"])
            self.assertEqual(colors["missing_in_rhino"], STATUS_FONT_COLORS["missing_in_rhino"])
            self.assertEqual(colors["added_in_rhino"], STATUS_FONT_COLORS["added_in_rhino"])
            self.assertEqual(colors["modified"], STATUS_FONT_COLORS["modified"])
            table = read_table(styled)
            self.assertTrue(table.ok, table.message)
            self.assertEqual([row[-1] for row in table.details["rows"]], [row[-1] for row in rows])


if __name__ == "__main__":
    unittest.main()
