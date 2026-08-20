# -*- coding: utf-8 -*-
"""D02 Tagger Laser：固定 View transform 射線，只寫 binding。"""
from __future__ import annotations

import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Tagger_Laser.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    LOCK_LEGACY_KEY,
    LOCK_LEGACY_HINT,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.features.tagger.laser import (
    bind_laser_hit,
    choice_labels,
    cluster_hits,
    hit_choice_label,
    origin_behind_plane,
    run_tagger_laser,
    view_frames_containing,
)
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.features.view.keys import SCHEMA_ID_KEY, VIEW_SCHEMA_ID, VIEW_TRANSFORM_KEY
from loopflow.features.view.transform import build_transform, encode_transform, ray_from_transform
from loopflow.foundation.usertext import OBJECT_ID_KEY
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OBJECT_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
POINT_2D = (10.0, 5.0, 0.0)


def _transform():
    return build_transform(
        origin_2d=(10, 5, 0),
        origin_3d_local=(10, 5),
        scale_x=1,
        scale_y=-1,
        plane={
            "origin": (0, 0, 0),
            "x_axis": (1, 0, 0),
            "y_axis": (0, 1, 0),
            "z_axis": (0, 0, 1),
        },
    )


def _session() -> MemorySession:
    session = MemorySession(
        document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.project",
            "lf_schema_version": "1",
        }
    )
    session.add_object(
        "wall",
        selected=True,
        name="Wall",
        layer="M3D::00_STR_結構::Beam.樑",
        user_text={OBJECT_ID_KEY: OBJECT_ID},
    )
    session.add_object("tag", selected=False, name="HeightLaser", layer="M2D::Tags")
    session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_LASER")
    session.add_object("frame", name="ViewFrame", layer="LoopFlow::Anchor_Frame")
    session.set_bbox("frame", (0, 0, 0), (20, 10, 0))
    session.set_object_user_text("frame", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
    session.set_object_user_text("frame", VIEW_TRANSFORM_KEY, encode_transform(_transform()))
    session.set_ray_hits(
        [
            {
                "object_id": "wall",
                "dist": 100.0,
                "hit_type": "FRONTAL",
                "layer": "M3D::00_STR_結構::Beam.樑",
                "name": "Wall",
            }
        ]
    )
    session.set_document_modified(False)
    return session


def _catalog():
    loaded = load_tag_templates()
    if not loaded.ok:
        raise AssertionError(loaded.message)
    return loaded.details["catalog"]


def _snapshot(session: MemorySession) -> dict:
    return {
        "document": dict(session._document_text),
        "modified": session.document_modified(),
        "objects": copy.deepcopy(session._object_meta),
        "selected": session.get_view_state("wall").selected,
    }


def _run(session, **kwargs):
    params = {
        "pick_tag": lambda _s: "tag",
        "pick_point": lambda _s: POINT_2D,
        "catalog": _catalog(),
    }
    params.update(kwargs)
    return run_tagger_laser(session, **params)


class ClusterTests(unittest.TestCase):
    def test_keeps_nearest_two_objects(self):
        hits = cluster_hits(
            (
                {"object_id": "far_front", "dist": 400.0, "hit_type": "FRONTAL"},
                {"object_id": "near_back", "dist": 10.0, "hit_type": "BACKFACE"},
                {"object_id": "near_front", "dist": 80.0, "hit_type": "FRONTAL"},
            )
        )
        ids = [item["object_id"] for item in hits]
        self.assertEqual(ids, ["near_back", "near_front"])

    def test_drops_third_object(self):
        hits = cluster_hits(
            (
                {"object_id": "a", "dist": 100.0, "hit_type": "FRONTAL"},
                {"object_id": "b", "dist": 280.0, "hit_type": "FRONTAL"},
                {"object_id": "c", "dist": 310.0, "hit_type": "FRONTAL"},
            )
        )
        ids = [item["object_id"] for item in hits]
        self.assertEqual(ids, ["a", "b"])

    def test_same_object_counts_once(self):
        hits = cluster_hits(
            (
                {"object_id": "wall", "dist": 10.0, "hit_type": "FRONTAL"},
                {"object_id": "wall", "dist": 40.0, "hit_type": "BACKFACE"},
                {"object_id": "tile", "dist": 50.0, "hit_type": "FRONTAL"},
                {"object_id": "toilet", "dist": 60.0, "hit_type": "FRONTAL"},
            )
        )
        ids = [item["object_id"] for item in hits]
        self.assertEqual(ids, ["wall", "tile"])


class ChoiceLabelTests(unittest.TestCase):
    def test_shows_layer_terminal_not_object_id(self):
        label = hit_choice_label(
            {
                "object_id": OBJECT_ID,
                "layer": "M3D::00_STR_結構::Beam.樑",
                "name": "",
                "dist": 123.4,
            }
        )
        self.assertEqual(label, "Beam.樑")
        self.assertNotIn(OBJECT_ID, label)

    def test_appends_object_name_when_present(self):
        label = hit_choice_label(
            {
                "object_id": OBJECT_ID,
                "layer": "M3D::FF",
                "name": "Chair",
            }
        )
        self.assertEqual(label, "FF  Chair")
        self.assertNotIn(OBJECT_ID, label)

    def test_duplicate_labels_get_index_suffix(self):
        labels = choice_labels(
            (
                {"layer": "M3D::Beam.樑", "name": "", "object_id": "one"},
                {"layer": "M3D::Beam.樑", "name": "", "object_id": "two"},
                {"layer": "M3D::Wall.牆", "name": "", "object_id": "three"},
            )
        )
        self.assertEqual(labels, ("Beam.樑（1）", "Beam.樑（2）", "Wall.牆"))
        self.assertNotIn("one", "".join(labels))
        self.assertNotIn("two", "".join(labels))


class BindTests(unittest.TestCase):
    def test_height_laser_writes_source_object_id(self):
        session = _session()
        before_wall = dict(session._object_meta["wall"]["user_text"])
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertEqual(session.get_object_user_text("tag", BINDING_MODE_KEY), "object")
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "TAG_HEIGHT_LASER")
        self.assertTrue(session.get_object_user_text("tag", TAG_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_BLOCK_NAME_KEY))
        self.assertEqual(session._object_meta["wall"]["user_text"], before_wall)

    def test_title_case_block_name_binds_and_keeps_actual_name(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="Tag_Height_Laser")
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "Tag_Height_Laser")

    def test_finish_laser_binds(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="TAG_FINISH_LASER")
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)

    def test_grab_item_dw_index_zero_write(self):
        session = _session()
        session.add_object("grab", name="GrabTag", layer="M2D::Tags")
        session.set_block("grab", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        session.add_object("item", name="ItemTag", layer="M2D::Tags")
        session.set_block("item", (0, 0, 0), name="TAG_ITEM")
        session.add_object("dw", name="DoorTag", layer="M2D::Tags")
        session.set_block("dw", (0, 0, 0), name="TAG_DW")
        session.add_object("idx", name="IndexTag", layer="M2D::Tags")
        session.set_block("idx", (0, 0, 0), name="TAG_ELEV_1")
        for object_id in ("grab", "item", "dw", "idx"):
            result = bind_laser_hit(session, object_id, "wall", _catalog())
            self.assertFalse(result.ok, object_id)
            self.assertEqual(result.blocking, ("unsupported_template",))
            self.assertIsNone(session.get_object_user_text(object_id, SOURCE_OBJECT_ID_KEY))
            self.assertIsNone(session.get_object_user_text(object_id, TAG_ID_KEY))

    def test_locked_tag_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_STATE_KEY, "true")
        session.set_document_modified(False)
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_legacy_x_lock_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_LEGACY_KEY, "x")
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", LOCK_STATE_KEY))

    def test_legacy_X_lock_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_LEGACY_KEY, "X")
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_legacy_lock_hint_still_binds(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_LEGACY_KEY, LOCK_LEGACY_HINT)
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertEqual(session.get_object_user_text("tag", LOCK_LEGACY_KEY), LOCK_LEGACY_HINT)

    def test_legacy_lock_empty_still_binds(self):
        session = _session()
        session._meta("tag")["user_text"][LOCK_LEGACY_KEY] = ""
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)

    def test_missing_source_uuid_zero_write(self):
        session = _session()
        session.set_object_user_text("wall", OBJECT_ID_KEY, "")
        result = bind_laser_hit(session, "tag", "wall", _catalog())
        self.assertEqual(result.blocking, ("missing_object_id",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))


class CommandTests(unittest.TestCase):
    def test_command_binds_via_fixed_transform_and_restores_selection(self):
        session = _session()
        captured = []

        def probe(_session, origin, direction):
            captured.append((origin, direction))
            return (
                {
                    "object_id": "wall",
                    "dist": 100.0,
                    "hit_type": "FRONTAL",
                    "layer": "M3D",
                    "name": "Wall",
                },
            )

        result = _run(session, probe=probe)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertTrue(session.get_view_state("wall").selected)
        expected_origin, expected_dir = ray_from_transform(_transform(), POINT_2D)
        self.assertEqual(captured[0][0], origin_behind_plane(expected_origin, expected_dir))
        self.assertEqual(captured[0][1], expected_dir)

    def test_minus_y_elevation_shoots_toward_model(self):
        session = _session()
        payload = build_transform(
            origin_2d=(10, 5, 0),
            origin_3d_local=(10, 5),
            scale_x=1,
            scale_y=-1,
            plane={
                "origin": (0, 0, 0),
                "x_axis": (1, 0, 0),
                "y_axis": (0, 0, 1),
                "z_axis": (0, -1, 0),
            },
        )
        session.set_object_user_text("frame", VIEW_TRANSFORM_KEY, encode_transform(payload))
        session.set_bbox("wall", (0, 80, 0), (10, 100, 10))
        captured = []

        def probe(_session, origin, direction):
            captured.append((origin, direction))
            return (
                {
                    "object_id": "wall",
                    "dist": 90.0,
                    "hit_type": "FRONTAL",
                    "layer": "M3D",
                    "name": "Wall",
                },
            )

        result = _run(session, probe=probe)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(captured[0][1], (0.0, 1.0, 0.0))
        plane_origin, _stored = ray_from_transform(payload, POINT_2D)
        self.assertEqual(captured[0][0], origin_behind_plane(plane_origin, (0.0, 1.0, 0.0)))

    def test_default_probe_uses_injected_ray_hits(self):
        session = _session()
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)

    def test_title_case_command_keeps_actual_block_name(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="Tag_Height_Laser")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "Tag_Height_Laser")

    def test_cancel_first_pick_does_not_write(self):
        session = _session()
        before = _snapshot(session)
        result = _run(session, pick_tag=lambda _s: None)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session)["objects"], before["objects"])
        self.assertTrue(session.get_view_state("wall").selected)

    def test_cancel_point_pick_does_not_write(self):
        session = _session()

        def pick_point(current):
            current.set_view_state(ObjectViewState("wall", False, False, False, (0, 0, 0), True))
            return None

        result = _run(session, pick_point=pick_point)
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))
        self.assertTrue(session.get_view_state("wall").selected)

    def test_point_outside_view_zero_write(self):
        session = _session()
        result = _run(session, pick_point=lambda _s: (100.0, 100.0, 0.0))
        self.assertEqual(result.blocking, ("missing_view",))
        self.assertIn("Anchor Frame", result.message)
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))
        self.assertEqual(view_frames_containing(session, (100.0, 100.0, 0.0)), ())

    def test_overlapping_views_zero_write(self):
        session = _session()
        session.add_object("frame2", name="ViewFrame2", layer="M2D::Anchor_Frame")
        session.set_bbox("frame2", (0, 0, 0), (20, 10, 0))
        session.set_object_user_text("frame2", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("frame2", VIEW_TRANSFORM_KEY, encode_transform(_transform()))
        result = _run(session)
        self.assertEqual(result.blocking, ("ambiguous_view",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_no_hit_zero_write(self):
        session = _session()
        result = _run(session, probe=lambda *_a: ())
        self.assertEqual(result.blocking, ("no_hit",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_choose_cancel_zero_write(self):
        session = _session()
        hits = (
            {"object_id": "wall", "dist": 100.0, "hit_type": "FRONTAL", "layer": "A", "name": "One"},
            {"object_id": "wall", "dist": 120.0, "hit_type": "FRONTAL", "layer": "B", "name": "Two"},
        )
        result = _run(session, probe=lambda *_a: hits, choose_hit=lambda _hits: None)
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_multiple_hits_user_choice(self):
        session = _session()
        session.add_object(
            "other",
            name="Other",
            layer="M3D::FF",
            user_text={OBJECT_ID_KEY: "cccccccc-cccc-4ccc-8ccc-cccccccccccc"},
        )
        hits = (
            {"object_id": "wall", "dist": 100.0, "hit_type": "FRONTAL", "layer": "A", "name": "One"},
            {"object_id": "other", "dist": 120.0, "hit_type": "FRONTAL", "layer": "B", "name": "Two"},
        )
        result = _run(session, probe=lambda *_a: hits, choose_hit=lambda items: items[1])
        self.assertTrue(result.ok, result.message)
        self.assertEqual(
            session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY),
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        )

    def test_grab_tag_refused_before_point(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        picked_point = []
        result = _run(session, pick_point=lambda _s: picked_point.append(True) or POINT_2D)
        self.assertEqual(result.blocking, ("unsupported_template",))
        self.assertEqual(picked_point, [])
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_missing_schema_stops_without_picking(self):
        session = MemorySession(document_text={})
        session.add_object("tag", name="Tag")
        session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_LASER")
        picked = []
        result = run_tagger_laser(
            session,
            pick_tag=lambda _s: picked.append("tag") or "tag",
            pick_point=lambda _s: POINT_2D,
            catalog=_catalog(),
        )
        self.assertFalse(result.ok)
        self.assertEqual(picked, [])
        self.assertIn("schema", result.message)

    def test_prompt_uses_layout_getpoint_not_active_detail(self):
        text = (WIP / "src" / "loopflow" / "platform" / "rhino" / "prompts.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("def pick_layout_detail_model_point", text)
        self.assertIn("GetPoint()", text)
        self.assertIn("PageToWorldTransform", text)
        laser = (WIP / "src" / "loopflow" / "features" / "tagger" / "laser.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("pick_layout_detail_model_point", laser)
        self.assertNotIn("pick_source_through_detail", laser)

    def test_moved_frame_uses_live_origin(self):
        session = _session()
        session.set_bbox("frame", (0, 1000, 0), (20, 1010, 0))
        captured = []

        def probe(_session, origin, direction):
            captured.append((origin, direction))
            return (
                {
                    "object_id": "wall",
                    "dist": 100.0,
                    "hit_type": "FRONTAL",
                    "layer": "M3D",
                    "name": "Wall",
                },
            )

        result = _run(session, pick_point=lambda _s: (10.0, 1005.0, 0.0), probe=probe)
        self.assertTrue(result.ok, result.message)
        expected_origin, expected_dir = ray_from_transform(_transform(), POINT_2D)
        self.assertEqual(captured[0][0], origin_behind_plane(expected_origin, expected_dir))
        self.assertEqual(captured[0][1], expected_dir)

    def test_ceiling_scale_survives_frame_translate(self):
        session = _session()
        payload = _transform()
        payload["scale_x"] = -1.0
        session.set_object_user_text("frame", VIEW_TRANSFORM_KEY, encode_transform(payload))
        session.set_bbox("frame", (0, 1000, 0), (20, 1010, 0))
        captured = []

        def probe(_session, origin, direction):
            captured.append((origin, direction))
            return (
                {
                    "object_id": "wall",
                    "dist": 100.0,
                    "hit_type": "FRONTAL",
                    "layer": "M3D",
                    "name": "Wall",
                },
            )

        point = (15.0, 1005.0, 0.0)
        result = _run(session, pick_point=lambda _s: point, probe=probe)
        self.assertTrue(result.ok, result.message)
        unmoved = dict(payload)
        unmoved["origin_2d"] = [10.0, 5.0, 0.0]
        expected_origin, expected_dir = ray_from_transform(unmoved, (15.0, 5.0, 0.0))
        self.assertEqual(captured[0][0], origin_behind_plane(expected_origin, expected_dir))
        self.assertEqual(captured[0][1], expected_dir)

    def test_catalog_and_entrypoint(self):
        from loopflow.command_catalog import get_command

        spec = get_command("LF_Tagger_Laser")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "D02")
        self.assertTrue(ENTRY.is_file())

    def test_run_command_without_rhino_does_not_claim_success(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_Tagger_Laser")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已綁定", result.message)
        self.assertIn("Rhino", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
