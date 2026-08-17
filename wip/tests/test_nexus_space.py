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
from loopflow.features.dictionary.layer_paths import SYSTEM_LAYERS
from loopflow.features.model_data.space import (
    LEVEL_FFL_LAYER,
    LEVEL_ID_KEY,
    SPACE_BOUNDARY_LAYER,
    SPACE_DISPLAY_KEY,
    SPACE_ID_KEY,
    UUID_V4_RE,
    SpaceDraft,
    drafts_from_selection,
    isolate_closed_curves,
    register_level_boundaries_interactive,
    register_space_boundaries,
    register_space_boundaries_interactive,
)
from loopflow.foundation.usertext import LEVEL_DATUM_KEY
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
LEVEL_FL_LAYER = SYSTEM_LAYERS[2]
FLOOR_POLY = [[0, 0], [20, 0], [20, 20], [0, 20]]
ROOM_POLY = [[1, 1], [5, 1], [5, 5], [1, 5]]


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


def _add_level(
    session: MemorySession,
    object_id: str,
    name: str,
    polygon,
    *,
    layer: str = LEVEL_FFL_LAYER,
    elevation: float = 0.0,
    selected: bool = False,
):
    session.ensure_layer(layer)
    session.add_object(object_id, selected=selected, name=name, layer=layer)
    session.set_curve(object_id, polygon, closed=True, elevation=elevation)
    session.set_object_user_text(object_id, LEVEL_DATUM_KEY, name)


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


class _RhinoLikeSession:
    """模擬 rhinoscriptsyntax：圖層不存在時 ObjectsByLayer 丟 ValueError。"""

    def __init__(self, inner: MemorySession) -> None:
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def objects_on_layer(self, path: str):
        if not self._inner.has_layer(path):
            raise ValueError("%s does not exist in LayerTable" % path)
        return self._inner.objects_on_layer(path)


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
        self.assertEqual(session.object_layer("curve-0"), SPACE_BOUNDARY_LAYER)
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
                pick_objects=lambda: ("curve-0",),
                space_name="客廳",
                isolate=False,
            )
        self.assertTrue(result.ok, result.message)
        self.assertTrue(UUID_V4_RE.match(session.get_object_user_text("curve-0", SPACE_ID_KEY)))
        self.assertEqual(session.get_object_user_text("curve-0", SPACE_DISPLAY_KEY), "客廳")

    def test_matches_level_frame_within_z_tolerance(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", ROOM_POLY, closed=True, elevation=20.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertTrue(result.ok, result.message)
        level_id = session.get_object_user_text("ffl-1", LEVEL_ID_KEY)
        self.assertTrue(UUID_V4_RE.match(level_id))
        self.assertEqual(session.get_object_user_text("room", LEVEL_ID_KEY), level_id)
        self.assertEqual(session.get_object_user_text("room", SPACE_DISPLAY_KEY), "廊道")
        self.assertEqual(session.object_name("ffl-1"), "0")

    def test_level_datum_falls_back_to_object_name(self):
        session = _session()
        session.ensure_layer(LEVEL_FFL_LAYER)
        session.add_object("ffl-1", name="0", layer=LEVEL_FFL_LAYER)
        session.set_curve("ffl-1", FLOOR_POLY, closed=True, elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", ROOM_POLY, closed=True, elevation=0.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text("room", LEVEL_ID_KEY),
            session.get_object_user_text("ffl-1", LEVEL_ID_KEY),
        )

    def test_z_difference_over_tolerance_blocks(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", ROOM_POLY, closed=True, elevation=21.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertEqual(result.blocking, ("space_not_in_level",))
        self.assertIsNone(session.get_object_user_text("room", SPACE_ID_KEY))
        self.assertIsNone(session.get_object_user_text("ffl-1", LEVEL_ID_KEY))

    def test_space_outside_level_polygon_blocks(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", [[21, 21], [25, 21], [25, 25], [21, 25]], closed=True, elevation=0.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertEqual(result.blocking, ("space_not_in_level",))
        self.assertIsNone(session.get_object_user_text("room", SPACE_ID_KEY))

    def test_shared_edge_with_level_frame_passes(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", [[0, 0], [5, 0], [5, 5], [0, 5]], closed=True, elevation=0.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text("room", LEVEL_ID_KEY),
            session.get_object_user_text("ffl-1", LEVEL_ID_KEY),
        )

    def test_two_floors_get_distinct_level_ids(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        _add_level(session, "ffl-2", "320", FLOOR_POLY, elevation=320.0)
        session.add_object("room-1", selected=True, name="廊道")
        session.set_curve("room-1", ROOM_POLY, closed=True, elevation=5.0)
        session.add_object("room-2", selected=True, name="衛浴")
        session.set_curve("room-2", ROOM_POLY, closed=True, elevation=320.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.status, "ok_with_warnings")
        id1 = session.get_object_user_text("ffl-1", LEVEL_ID_KEY)
        id2 = session.get_object_user_text("ffl-2", LEVEL_ID_KEY)
        self.assertNotEqual(id1, id2)
        self.assertEqual(session.get_object_user_text("room-1", LEVEL_ID_KEY), id1)
        self.assertEqual(session.get_object_user_text("room-2", LEVEL_ID_KEY), id2)

    def test_ambiguous_same_height_level_frames_block(self):
        session = _session()
        _add_level(session, "ffl-a", "0", FLOOR_POLY, elevation=0.0)
        _add_level(session, "ffl-b", "0", [[0, 0], [30, 0], [30, 30], [0, 30]], elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", ROOM_POLY, closed=True, elevation=0.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertEqual(result.blocking, ("ambiguous_level_frame",))
        self.assertIsNone(session.get_object_user_text("room", SPACE_ID_KEY))

    def test_prefers_ffl_when_fl_also_matches(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        _add_level(session, "fl-1", "0", FLOOR_POLY, layer=LEVEL_FL_LAYER, elevation=0.0)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", ROOM_POLY, closed=True, elevation=0.0)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text("room", LEVEL_ID_KEY),
            session.get_object_user_text("ffl-1", LEVEL_ID_KEY),
        )
        self.assertIsNone(session.get_object_user_text("fl-1", LEVEL_ID_KEY))

    def test_skips_selected_level_frames_as_spaces(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0, selected=True)
        session.add_object("room", selected=True, name="廊道")
        session.set_curve("room", ROOM_POLY, closed=True, elevation=0.0)
        drafts = drafts_from_selection(session)
        self.assertEqual(tuple(item.object_id for item in drafts), ("room",))
        result = register_space_boundaries(session, drafts)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.object_name("ffl-1"), "0")
        self.assertEqual(session.object_layer("ffl-1"), LEVEL_FFL_LAYER)

    def test_missing_fl_layer_does_not_raise(self):
        inner = _session()
        _add_level(inner, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        inner.add_object("room", selected=True, name="廊道")
        inner.set_curve("room", ROOM_POLY, closed=True, elevation=0.0)
        self.assertFalse(inner.has_layer(LEVEL_FL_LAYER))
        session = _RhinoLikeSession(inner)
        result = register_space_boundaries(session, drafts_from_selection(session))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            inner.get_object_user_text("room", LEVEL_ID_KEY),
            inner.get_object_user_text("ffl-1", LEVEL_ID_KEY),
        )

    def test_isolate_reveals_closed_curves_without_locking_solids(self):
        session = _session()
        session.add_object("box", locked=False, name="Wall")
        session.add_object("room", locked=True, hidden=True, name="")
        session.set_curve("room", ROOM_POLY, closed=True)
        isolate_closed_curves(session)
        self.assertFalse(session.get_view_state("box").locked)
        self.assertFalse(session.get_view_state("room").locked)
        self.assertFalse(session.get_view_state("room").hidden)

    def test_level_kind_prompt_writes_fl_layer(self):
        session = _session()
        session.add_object("frame", name="")
        session.set_curve("frame", FLOOR_POLY, closed=True, elevation=0.0)
        seen = []

        def ask_kind(message, options, default):
            seen.append((message, tuple(options), default))
            return "FL"

        result = register_level_boundaries_interactive(
            session,
            object_ids=("frame",),
            datum="0",
            ask_kind=ask_kind,
            isolate=False,
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(seen, [("高程框類型", ("FFL", "FL"), "FFL")])
        self.assertEqual(session.object_layer("frame"), LEVEL_FL_LAYER)

    def test_level_prompt_writes_datum_and_restores_locks(self):
        session = _session()
        session.add_object("box", locked=False, name="Wall")
        session.add_object("frame", name="")
        session.set_curve("frame", FLOOR_POLY, closed=True, elevation=0.0)
        result = register_level_boundaries_interactive(
            session,
            kind="FFL",
            object_ids=("frame",),
            datum="320",
            isolate=True,
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("frame", LEVEL_DATUM_KEY), "320")
        self.assertEqual(session.object_name("frame") or "", "")
        self.assertEqual(session.object_layer("frame"), LEVEL_FFL_LAYER)
        self.assertTrue(UUID_V4_RE.match(session.get_object_user_text("frame", LEVEL_ID_KEY)))
        self.assertFalse(session.get_view_state("box").locked)

    def test_space_prompt_applies_one_name_to_multiple_curves(self):
        session = _session()
        _add_level(session, "ffl-1", "0", FLOOR_POLY, elevation=0.0)
        session.add_object("a", name="")
        session.set_curve("a", ROOM_POLY, closed=True, elevation=0.0)
        session.add_object("b", name="")
        session.set_curve("b", [[6, 6], [9, 6], [9, 9], [6, 9]], closed=True, elevation=0.0)
        result = register_space_boundaries_interactive(
            session,
            object_ids=("a", "b"),
            space_name="廊道",
            isolate=True,
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.object_name("a") or "", "")
        self.assertEqual(session.object_name("b") or "", "")
        self.assertEqual(session.get_object_user_text("a", SPACE_DISPLAY_KEY), "廊道")
        self.assertEqual(session.get_object_user_text("b", SPACE_DISPLAY_KEY), "廊道")
        self.assertEqual(
            session.get_object_user_text("a", LEVEL_ID_KEY),
            session.get_object_user_text("ffl-1", LEVEL_ID_KEY),
        )


if __name__ == "__main__":
    unittest.main()
