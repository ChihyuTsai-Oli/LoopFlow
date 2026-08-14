# -*- coding: utf-8 -*-
"""NX-03 Space Boundary：多樓層、共邊、重疊、無效曲線；不改模型物件空間欄。"""
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
from loopflow.features.model_data.space import (
    LEVEL_ID_KEY,
    SPACE_DISPLAY_KEY,
    SPACE_ID_KEY,
    UUID_V4_RE,
    SpaceDraft,
    register_space_boundaries,
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

CASES_PATH = WIP / "fixtures" / "contract" / "space" / "cases.json"
LEVEL_1 = "11111111-1111-4111-8111-111111111111"
SPACE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _fixture_cases():
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]


def _session() -> MemorySession:
    session = MemorySession(
        document_text={
            PROJECT_ID_KEY: SPACE_A,
            SCHEMA_ID_KEY: "loopflow.project",
            SCHEMA_VERSION_KEY: "1",
        }
    )
    session.add_object("wall", selected=False, name="Wall", layer="M3D::00_STR_結構::Beam.樑")
    session.set_object_user_text("wall", "lf_remarks", "人工備註")
    session.set_document_modified(False)
    return session


def _add_spaces(session: MemorySession, spaces, *, selected: bool = True):
    drafts = []
    for index, space in enumerate(spaces):
        object_id = "curve-%s" % index
        session.add_object(object_id, selected=selected, name=space["space_display"])
        session.set_curve(object_id, space["polygon"], closed=True)
        drafts.append(
            SpaceDraft(
                object_id=object_id,
                space_display=space["space_display"],
                level_id=space["level_id"],
                space_id=space.get("space_id"),
            )
        )
    return drafts


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


class SpaceBoundaryTests(unittest.TestCase):
    def test_a06_pass_cases_write_boundary_only(self):
        for case in _fixture_cases():
            if case["expect"] != "pass":
                continue
            with self.subTest(case["id"]):
                session = _session()
                drafts = _add_spaces(session, case["spaces"])
                result = register_space_boundaries(session, drafts)
                self.assertTrue(result.ok, result.message)
                self.assertEqual(result.details["count"], len(case["spaces"]))
                for index, space in enumerate(case["spaces"]):
                    object_id = "curve-%s" % index
                    self.assertEqual(session.get_object_user_text(object_id, SPACE_ID_KEY), space["space_id"])
                    self.assertEqual(session.get_object_user_text(object_id, LEVEL_ID_KEY), space["level_id"])
                    self.assertEqual(
                        session.get_object_user_text(object_id, SPACE_DISPLAY_KEY),
                        space["space_display"],
                    )
                    self.assertEqual(session.object_name(object_id), space["space_display"])
                self.assertIsNone(session.get_object_user_text("wall", SPACE_ID_KEY))
                self.assertEqual(session.get_object_user_text("wall", "lf_remarks"), "人工備註")
                self.assertFalse(session.get_view_state("wall").selected)

    def test_a06_overlap_blocks_and_lists_all_conflicts(self):
        case = next(item for item in _fixture_cases() if item["id"] == "area-overlap-block")
        session = _session()
        drafts = _add_spaces(session, case["spaces"])
        result = register_space_boundaries(session, drafts)
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.blocking, ("space_overlap",))
        self.assertEqual(result.details["conflicts"], (("客廳", "餐廳"),))
        self.assertIsNone(session.get_object_user_text("curve-0", SPACE_ID_KEY))
        self.assertIsNone(session.get_object_user_text("curve-1", SPACE_ID_KEY))
        self.assertIsNone(session.get_object_user_text("wall", SPACE_ID_KEY))

    def test_cross_level_xy_overlap_warns_but_passes(self):
        case = next(item for item in _fixture_cases() if item["id"] == "multi-level-ok")
        session = _session()
        drafts = _add_spaces(session, case["spaces"])
        result = register_space_boundaries(session, drafts)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.status, "ok_with_warnings")
        self.assertEqual(result.details["xy_overlap_other_level"], (("1F客廳", "2F臥室"),))
        self.assertTrue(any("樓層不同" in item for item in result.warnings))

    def test_three_way_overlap_lists_every_pair(self):
        session = _session()
        drafts = _add_spaces(
            session,
            [
                {
                    "space_display": "A",
                    "level_id": LEVEL_1,
                    "polygon": [[0, 0], [6, 0], [6, 4], [0, 4]],
                },
                {
                    "space_display": "B",
                    "level_id": LEVEL_1,
                    "polygon": [[4, 0], [10, 0], [10, 4], [4, 4]],
                },
                {
                    "space_display": "C",
                    "level_id": LEVEL_1,
                    "polygon": [[2, 0], [8, 0], [8, 4], [2, 4]],
                },
            ],
        )
        result = register_space_boundaries(session, drafts)
        self.assertEqual(result.blocking, ("space_overlap",))
        self.assertEqual(result.details["conflicts"], (("A", "B"), ("A", "C"), ("B", "C")))
        for index in range(3):
            self.assertIsNone(session.get_object_user_text("curve-%s" % index, SPACE_ID_KEY))

    def test_missing_space_id_creates_uuid_and_keeps_existing(self):
        session = _session()
        session.add_object("new-curve", selected=True, name="書房")
        session.set_curve("new-curve", [[0, 0], [3, 0], [3, 3], [0, 3]], closed=True)
        session.add_object("old-curve", selected=True, name="客廳")
        session.set_curve("old-curve", [[5, 0], [8, 0], [8, 3], [5, 3]], closed=True)
        session.set_object_user_text("old-curve", SPACE_ID_KEY, SPACE_A)
        result = register_space_boundaries(
            session,
            [
                SpaceDraft("new-curve", "書房", LEVEL_1),
                SpaceDraft("old-curve", "客廳", LEVEL_1),
            ],
        )
        self.assertTrue(result.ok, result.message)
        created = session.get_object_user_text("new-curve", SPACE_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(created))
        self.assertNotEqual(created, SPACE_A)
        self.assertEqual(session.get_object_user_text("old-curve", SPACE_ID_KEY), SPACE_A)

    def test_invalid_curves_block_without_writing(self):
        session = _session()
        session.add_object("open", selected=True, name="開放")
        session.set_curve("open", [[0, 0], [4, 0], [4, 3], [0, 3]], closed=False)
        session.add_object("short", selected=True, name="兩點")
        session.set_curve("short", [[0, 0], [1, 0]], closed=True)
        session.add_object("nameless", selected=True, name="")
        session.set_curve("nameless", [[0, 0], [2, 0], [2, 2], [0, 2]], closed=True)
        session.add_object("no-level", selected=True, name="無樓層")
        session.set_curve("no-level", [[3, 0], [5, 0], [5, 2], [3, 2]], closed=True)
        session.add_object("ext-id", selected=True, name="室外")
        session.set_curve("ext-id", [[6, 0], [8, 0], [8, 2], [6, 2]], closed=True)
        result = register_space_boundaries(
            session,
            [
                SpaceDraft("open", "開放", LEVEL_1),
                SpaceDraft("short", "兩點", LEVEL_1),
                SpaceDraft("nameless", "", LEVEL_1),
                SpaceDraft("no-level", "無樓層", ""),
                SpaceDraft("ext-id", "室外", LEVEL_1, space_id="EXT"),
            ],
        )
        self.assertEqual(result.status, "blocked")
        self.assertEqual(result.blocking, ("invalid_space_curve",))
        self.assertEqual(
            result.details["invalid_object_ids"],
            ("open", "short", "nameless", "no-level", "ext-id"),
        )
        for object_id in ("open", "short", "nameless", "no-level", "ext-id"):
            self.assertIsNone(session.get_object_user_text(object_id, SPACE_ID_KEY))

    def test_empty_selection_blocks(self):
        session = _session()
        result = register_space_boundaries(session, [])
        self.assertEqual(result.blocking, ("missing_space_selection",))
        self.assertIsNone(session.get_object_user_text("wall", SPACE_ID_KEY))

    def test_duplicate_space_id_blocks_without_renumbering(self):
        session = _session()
        drafts = _add_spaces(
            session,
            [
                {
                    "space_id": SPACE_A,
                    "space_display": "客廳",
                    "level_id": LEVEL_1,
                    "polygon": [[0, 0], [3, 0], [3, 3], [0, 3]],
                },
                {
                    "space_id": SPACE_A,
                    "space_display": "餐廳",
                    "level_id": LEVEL_1,
                    "polygon": [[5, 0], [8, 0], [8, 3], [5, 3]],
                },
            ],
        )
        result = register_space_boundaries(session, drafts)
        self.assertEqual(result.blocking, ("duplicate_space_id",))
        self.assertIsNone(session.get_object_user_text("curve-0", SPACE_DISPLAY_KEY))

    def test_cancel_restores_view_and_does_not_write(self):
        session = _session()
        drafts = _add_spaces(
            session,
            [
                {
                    "space_display": "客廳",
                    "level_id": LEVEL_1,
                    "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]],
                }
            ],
        )
        session.set_view_state(ObjectViewState("curve-0", True, False, False, (10, 20, 30), False))
        session.set_document_modified(False)
        result = register_space_boundaries(session, drafts, cancel=True)
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("curve-0", SPACE_ID_KEY))
        self.assertTrue(session.get_view_state("curve-0").selected)
        self.assertFalse(session.document_modified())

    def test_console_space_boundary_step(self):
        session = _session()
        drafts = _add_spaces(
            session,
            [
                {
                    "space_id": SPACE_A,
                    "space_display": "客廳",
                    "level_id": LEVEL_1,
                    "polygon": [[0, 0], [4, 0], [4, 4], [0, 4]],
                }
            ],
        )
        with tempfile.TemporaryDirectory(prefix="loopflow-nx03-") as raw:
            root = Path(raw)
            written = write_table(
                root / "LoopFlow_Dictionary.xlsx",
                schema.TITLE_ROW,
                schema.DISPLAY_COLUMNS,
                [_valid_row()],
            )
            self.assertTrue(written.ok, written.message)
            result = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="space_boundary",
                drafts=drafts,
            )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.stage, "register_spaces")
        self.assertEqual(session.get_object_user_text("curve-0", SPACE_ID_KEY), SPACE_A)
        self.assertIsNone(session.get_object_user_text("wall", SPACE_ID_KEY))

    def test_console_reads_selected_curves(self):
        session = _session()
        session.add_object("curve-0", selected=True, name="客廳")
        session.set_curve("curve-0", [[0, 0], [4, 0], [4, 4], [0, 4]], closed=True)
        session.set_object_user_text("curve-0", LEVEL_ID_KEY, LEVEL_1)
        with tempfile.TemporaryDirectory(prefix="loopflow-nx03-") as raw:
            root = Path(raw)
            write_table(
                root / "LoopFlow_Dictionary.xlsx",
                schema.TITLE_ROW,
                schema.DISPLAY_COLUMNS,
                [_valid_row()],
            )
            result = open_console(
                session,
                environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
                step="space_boundary",
            )
        self.assertTrue(result.ok, result.message)
        self.assertTrue(UUID_V4_RE.match(session.get_object_user_text("curve-0", SPACE_ID_KEY)))
        self.assertEqual(session.get_object_user_text("curve-0", SPACE_DISPLAY_KEY), "客廳")


if __name__ == "__main__":
    unittest.main()
