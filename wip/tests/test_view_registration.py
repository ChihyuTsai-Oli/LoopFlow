# -*- coding: utf-8 -*-
"""E01 View Registration：寫 lf_view_id 與固定 transform；Esc／歧義零寫入。"""
from __future__ import annotations

import copy
import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Anchor_Frame.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.view.keys import (
    ANCHOR_LAYER,
    CLIPPING_PLANE_ID_KEY,
    LEGACY_ROLE_KEY,
    LEGACY_ROLE_VALUE,
    LEGACY_TARGET_CP_KEY,
    SCHEMA_ID_KEY,
    SCHEMA_VERSION_KEY,
    VIEW_ID_KEY,
    VIEW_SCHEMA_ID,
    VIEW_TRANSFORM_KEY,
)
from loopflow.features.view.register import match_clipping_planes, register_view, run_anchor_frame
from loopflow.features.view.transform import decode_transform, facing_direction, map_2d_to_cp_local
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

CASES_PATH = WIP / "fixtures" / "contract" / "view" / "cases.json"


def _session() -> MemorySession:
    session = MemorySession()
    session.add_object("curve", selected=True, name="SectionCurve", layer="M2D::Section")
    session.set_curve("curve", [[0, 0], [20, 0], [20, 10], [0, 10]], closed=True)
    session.set_bbox("curve", (0, 0, 0), (20, 10, 0))
    session.add_text_dot("dot", "A-A", (10, 12, 0))
    session.add_clipping_plane(
        "cp",
        name="A-A Section",
        origin=(0, 0, 0),
        section_bbox_local=(0, 0, 20, 10),
    )
    session.set_document_modified(False)
    return session


def _snapshot(session: MemorySession) -> dict:
    return {
        "modified": session.document_modified(),
        "objects": copy.deepcopy(session._object_meta),
        "ids": set(session.iter_object_ids()),
        "selected": session.get_view_state("curve").selected,
    }


def _frame_ids(session: MemorySession):
    return [
        object_id
        for object_id in session.iter_object_ids()
        if session.get_object_user_text(object_id, SCHEMA_ID_KEY) == VIEW_SCHEMA_ID
    ]


class ContractFixtureTests(unittest.TestCase):
    def test_cases_cover_zero_write_and_upgrade(self):
        cases = {item["id"]: item for item in json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]}
        for required in (
            "unique-cp-ok",
            "missing-text-dot-block",
            "missing-geom-block",
            "missing-cp-block",
            "ambiguous-cp-block",
            "cancel-zero-write",
            "upgrade-legacy-keep-geometry",
        ):
            self.assertIn(required, cases)


class RegisterTests(unittest.TestCase):
    def test_register_writes_view_id_transform_and_cp_id(self):
        session = _session()
        result = register_view(session, ("curve", "dot"), 50)
        self.assertTrue(result.ok, result.message)
        frame_id = result.details["frame_id"]
        self.assertEqual(session.object_layer(frame_id), ANCHOR_LAYER)
        self.assertEqual(session.object_layer(frame_id), "LoopFlow::Anchor_Frame")
        self.assertFalse(session.layer_printable("LoopFlow"))
        self.assertFalse(session.layer_printable(ANCHOR_LAYER))
        self.assertEqual(session.object_name(frame_id), "A-A")
        self.assertEqual(session.get_object_user_text(frame_id, SCHEMA_ID_KEY), VIEW_SCHEMA_ID)
        self.assertEqual(session.get_object_user_text(frame_id, SCHEMA_VERSION_KEY), "1")
        self.assertEqual(session.get_object_user_text(frame_id, CLIPPING_PLANE_ID_KEY), "cp")
        view_id = session.get_object_user_text(frame_id, VIEW_ID_KEY)
        self.assertRegex(view_id, r"^[0-9a-f-]{36}$")
        payload = decode_transform(session.get_object_user_text(frame_id, VIEW_TRANSFORM_KEY))
        self.assertIsNotNone(payload)
        self.assertEqual(payload["origin_2d"], [10.0, 5.0, 0.0])
        self.assertEqual(payload["origin_3d_local"], [10.0, 5.0])
        self.assertEqual(payload["scale_x"], 1.0)
        self.assertEqual(payload["scale_y"], -1.0)
        mapped = map_2d_to_cp_local(payload, (20.0, 5.0))
        self.assertEqual(mapped, (20.0, 5.0))
        self.assertIsNone(session.get_object_user_text(frame_id, LEGACY_ROLE_KEY))
        self.assertIsNone(session.get_object_user_text(frame_id, LEGACY_TARGET_CP_KEY))

    def test_ceiling_name_mirrors_x(self):
        session = _session()
        session.add_text_dot("dot", "1F_CEILING")
        session.add_clipping_plane("cp", name="1F_CEILING", section_bbox_local=(0, 0, 20, 10))
        result = register_view(session, ("curve", "dot"), 50)
        self.assertTrue(result.ok, result.message)
        payload = decode_transform(
            session.get_object_user_text(result.details["frame_id"], VIEW_TRANSFORM_KEY)
        )
        self.assertEqual(payload["scale_x"], -1.0)
        self.assertEqual(map_2d_to_cp_local(payload, (20.0, 5.0)), (0.0, 5.0))

    def test_missing_text_dot_zero_write(self):
        session = _session()
        before = _snapshot(session)
        result = register_view(session, ("curve",), 50)
        self.assertEqual(result.blocking, ("missing_text_dot",))
        self.assertEqual(_snapshot(session)["ids"], before["ids"])
        self.assertEqual(_frame_ids(session), [])

    def test_two_text_dots_zero_write(self):
        session = _session()
        session.add_text_dot("dot2", "A-A")
        before = _snapshot(session)
        result = register_view(session, ("curve", "dot", "dot2"), 50)
        self.assertEqual(result.blocking, ("ambiguous_text_dot",))
        self.assertEqual(_snapshot(session)["ids"], before["ids"])

    def test_missing_geometry_zero_write(self):
        session = _session()
        before = _snapshot(session)
        result = register_view(session, ("dot",), 50)
        self.assertEqual(result.blocking, ("missing_geometry",))
        self.assertEqual(_snapshot(session)["ids"], before["ids"])

    def test_missing_clipping_plane_zero_write(self):
        session = _session()
        session.delete_object("cp")
        before = _snapshot(session)
        result = register_view(session, ("curve", "dot"), 50)
        self.assertEqual(result.blocking, ("missing_clipping_plane",))
        self.assertEqual(_snapshot(session)["ids"], before["ids"])
        self.assertEqual(_frame_ids(session), [])

    def test_ambiguous_clipping_plane_zero_write(self):
        session = _session()
        session.add_clipping_plane("cp2", name="A-A South", section_bbox_local=(0, 0, 20, 10))
        before = _snapshot(session)
        result = register_view(session, ("curve", "dot"), 50)
        self.assertEqual(result.blocking, ("ambiguous_clipping_plane",))
        self.assertEqual(_snapshot(session)["ids"], before["ids"])

    def test_exact_clipping_plane_ignores_numbered_suffix(self):
        session = _session()
        session.add_text_dot("dot", "LF_立面")
        session.add_clipping_plane(
            "cp",
            name="LF_立面",
            origin=(0, 0, 0),
            section_bbox_local=(0, 0, 20, 10),
        )
        session.add_clipping_plane(
            "cp2",
            name="LF_立面2",
            origin=(10, 0, 0),
            section_bbox_local=(0, 0, 20, 10),
        )
        result = register_view(session, ("curve", "dot"), 50)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text(result.details["frame_id"], CLIPPING_PLANE_ID_KEY),
            "cp",
        )
        self.assertEqual(
            match_clipping_planes(session, "LF_立面"),
            ("cp",),
        )
        self.assertEqual(
            match_clipping_planes(session, "LF_立面2"),
            ("cp2",),
        )

    def test_missing_section_intersection_zero_write(self):
        session = _session()
        session.add_clipping_plane("cp", name="A-A Section", section_bbox_local=None)
        before = _snapshot(session)
        result = register_view(session, ("curve", "dot"), 50)
        self.assertEqual(result.blocking, ("missing_section_intersection",))
        self.assertEqual(_snapshot(session)["ids"], before["ids"])

    def test_upgrade_legacy_keeps_geometry_and_role(self):
        session = _session()
        host_id = session.add_closed_polyline(
            ((-5, -5, 0), (25, -5, 0), (25, 15, 0), (-5, 15, 0)),
            layer=ANCHOR_LAYER,
            name="A-A",
        )
        session.set_object_user_text(host_id, LEGACY_ROLE_KEY, LEGACY_ROLE_VALUE)
        session.set_object_user_text(host_id, LEGACY_TARGET_CP_KEY, "A-A")
        before_ids = set(session.iter_object_ids())
        result = register_view(session, ("curve", "dot", host_id), 50)
        self.assertTrue(result.ok, result.message)
        self.assertTrue(result.details["upgraded"])
        self.assertEqual(set(session.iter_object_ids()), before_ids)
        self.assertEqual(session.get_object_user_text(host_id, LEGACY_ROLE_KEY), LEGACY_ROLE_VALUE)
        self.assertEqual(session.get_object_user_text(host_id, LEGACY_TARGET_CP_KEY), "A-A")
        self.assertEqual(session.get_object_user_text(host_id, CLIPPING_PLANE_ID_KEY), "cp")
        self.assertTrue(session.get_object_user_text(host_id, VIEW_ID_KEY))
        self.assertIsNotNone(decode_transform(session.get_object_user_text(host_id, VIEW_TRANSFORM_KEY)))

    def test_upgrade_reuses_existing_view_id(self):
        session = _session()
        host_id = session.add_closed_polyline(
            ((-5, -5, 0), (25, -5, 0), (25, 15, 0), (-5, 15, 0)),
            layer=ANCHOR_LAYER,
            name="A-A",
        )
        session.set_object_user_text(host_id, SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text(host_id, VIEW_ID_KEY, "dddddddd-dddd-4ddd-8ddd-dddddddddddd")
        result = register_view(session, ("curve", "dot", host_id), 10)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text(host_id, VIEW_ID_KEY),
            "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
        )


class CommandTests(unittest.TestCase):
    def test_cancel_selection_restores_and_does_not_write(self):
        session = _session()
        before = _snapshot(session)
        result = run_anchor_frame(
            session,
            pick_selection=lambda _s: None,
            ask_offset=lambda _s: 50,
        )
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session)["ids"], before["ids"])
        self.assertTrue(session.get_view_state("curve").selected)
        self.assertFalse(session.document_modified())

    def test_cancel_offset_zero_write(self):
        session = _session()
        before = _snapshot(session)
        result = run_anchor_frame(
            session,
            pick_selection=lambda _s: ("curve", "dot"),
            ask_offset=lambda _s: None,
        )
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session)["ids"], before["ids"])
        self.assertEqual(_frame_ids(session), [])

    def test_command_registers_and_restores_selection(self):
        session = _session()
        result = run_anchor_frame(
            session,
            pick_selection=lambda _s: ("curve", "dot"),
            ask_offset=lambda _s: 50,
        )
        self.assertTrue(result.ok, result.message)
        self.assertTrue(session.get_view_state("curve").selected)
        self.assertEqual(len(_frame_ids(session)), 1)
        self.assertTrue(session.document_modified())

    def test_blocked_command_restores_selection(self):
        session = _session()
        session.delete_object("cp")

        def pick(current):
            current.set_view_state(ObjectViewState("curve", False, False, False, (0, 0, 0), True))
            return ("curve", "dot")

        result = run_anchor_frame(session, pick_selection=pick, ask_offset=lambda _s: 50)
        self.assertEqual(result.blocking, ("missing_clipping_plane",))
        self.assertTrue(session.get_view_state("curve").selected)
        self.assertEqual(_frame_ids(session), [])

    def test_catalog_and_entrypoint(self):
        from loopflow.command_catalog import get_command

        spec = get_command("LF_Anchor_Frame")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "E01")
        self.assertTrue(ENTRY.is_file())

    def test_catalog_and_entrypoint(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_Anchor_Frame")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已登記", result.message)
        self.assertIn("Rhino", buffer.getvalue())

    def test_prompt_filter_includes_textdot_not_true_as_filter(self):
        from loopflow.platform.rhino.prompts import FILTER_CURVE, FILTER_TEXTDOT

        text = (WIP / "src" / "loopflow" / "platform" / "rhino" / "prompts.py").read_text(encoding="utf-8")
        self.assertEqual(FILTER_TEXTDOT, 8192)
        self.assertTrue(FILTER_CURVE)
        self.assertIn("GetObjects(message, filter_code, preselect=True)", text)
        self.assertNotIn("GetObjects(message, True", text)


class FacingDirectionTests(unittest.TestCase):
    def test_flips_when_model_is_behind_stored_normal(self):
        from loopflow.features.view.transform import build_transform

        payload = build_transform(
            origin_2d=(0, 0, 0),
            origin_3d_local=(0, 0),
            scale_x=1,
            scale_y=1,
            plane={
                "origin": (0, 0, 0),
                "x_axis": (1, 0, 0),
                "y_axis": (0, 0, 1),
                "z_axis": (0, -1, 0),
            },
        )
        self.assertEqual(facing_direction(payload, (0, 100, 0)), (0.0, 1.0, 0.0))

    def test_keeps_normal_when_model_already_in_front(self):
        from loopflow.features.view.transform import build_transform

        payload = build_transform(
            origin_2d=(0, 0, 0),
            origin_3d_local=(0, 0),
            scale_x=1,
            scale_y=1,
            plane={
                "origin": (0, 0, 0),
                "x_axis": (0, 0, 1),
                "y_axis": (0, 1, 0),
                "z_axis": (1, 0, 0),
            },
        )
        self.assertEqual(facing_direction(payload, (80, 0, 0)), (1.0, 0.0, 0.0))

    def test_minus_x_elevation_flips_toward_model(self):
        from loopflow.features.view.transform import build_transform

        payload = build_transform(
            origin_2d=(0, 0, 0),
            origin_3d_local=(0, 0),
            scale_x=1,
            scale_y=1,
            plane={
                "origin": (0, 0, 0),
                "x_axis": (0, 0, 1),
                "y_axis": (0, 1, 0),
                "z_axis": (-1, 0, 0),
            },
        )
        self.assertEqual(facing_direction(payload, (80, 0, 0)), (1.0, 0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
