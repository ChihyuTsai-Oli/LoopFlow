# -*- coding: utf-8 -*-
"""LF-E07：既有 Anchor Frame 隨 2D 剖面變大或變小就地更新。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.view.keys import (  # noqa: E402
    CLIPPING_PLANE_ID_KEY,
    VIEW_ID_KEY,
    VIEW_TRANSFORM_KEY,
)
from loopflow.features.view.register import register_view  # noqa: E402
from loopflow.features.view.transform import decode_transform  # noqa: E402
from loopflow.features.view.update import recover_offset, run_anchor_update  # noqa: E402
from loopflow.platform.rhino.memory import MemorySession  # noqa: E402


def _block_session(max_x=200.0, *, scale_x=1.0, name="A-A"):
    session = MemorySession()
    session.set_layout_active(False)
    session.add_object("section", name=name, layer=name)
    session.set_block("section", (0.0, 0.0, 0.0), name=name)
    session.set_bbox("section", (0.0, 0.0, 0.0), (max_x, 100.0, 0.0))
    session.add_clipping_plane(
        "cp",
        name=name,
        section_bbox_local=(0.0, 0.0, max_x, 100.0),
    )
    result = register_view(session, ("section",), 50, scale_x=scale_x)
    if not result.ok:
        raise AssertionError(result.message)
    return session, result.details["frame_id"]


def _curve_session():
    session = MemorySession()
    session.set_layout_active(False)
    session.add_object("curve", layer="A-A::Curve")
    session.set_curve("curve", [(0, 0, 0), (200, 0, 0), (200, 100, 0), (0, 100, 0)], closed=True)
    session.set_bbox("curve", (0.0, 0.0, 0.0), (200.0, 100.0, 0.0))
    session.add_text_dot("dot", "A-A", (100.0, 120.0, 0.0))
    session.add_clipping_plane("cp", name="A-A", section_bbox_local=(0.0, 0.0, 200.0, 100.0))
    result = register_view(session, ("curve", "dot"), 50, scale_x=1.0)
    if not result.ok:
        raise AssertionError(result.message)
    return session, result.details["frame_id"]


def _payload(session, frame_id):
    return decode_transform(session.get_object_user_text(frame_id, VIEW_TRANSFORM_KEY))


class OffsetTests(unittest.TestCase):
    def test_repeated_nonnegative_gap_is_reused(self):
        self.assertEqual(recover_offset((-50, -50, 0, 250, 150, 0), (0, 0, 0, 300, 100, 0)), 50.0)

    def test_unique_gaps_use_default(self):
        self.assertEqual(recover_offset((-10, -20, 0, 80, 90, 0), (0, 5, 0, 40, 30, 0)), 50.0)


class UpdateTests(unittest.TestCase):
    def test_grown_block_keeps_margin_and_view_id(self):
        session, frame_id = _block_session()
        view_id = session.get_object_user_text(frame_id, VIEW_ID_KEY)
        session.set_bbox("section", (0.0, 0.0, 0.0), (300.0, 100.0, 0.0))
        session.add_clipping_plane("cp", name="A-A", section_bbox_local=(0.0, 0.0, 300.0, 100.0))
        result = run_anchor_update(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["updated"], [frame_id])
        self.assertEqual(session.get_object_user_text(frame_id, VIEW_ID_KEY), view_id)
        self.assertEqual(session.get_object_user_text(frame_id, CLIPPING_PLANE_ID_KEY), "cp")
        self.assertEqual(session.object_bbox(frame_id), (-50.0, -50.0, 0.0, 350.0, 150.0, 0.0))
        payload = _payload(session, frame_id)
        self.assertEqual(payload["origin_2d"], [150.0, 50.0, 0.0])
        self.assertEqual(payload["origin_3d_local"], [150.0, 50.0])
        self.assertEqual(payload["scale_x"], 1.0)

    def test_shrunk_curves_move_center_back_and_ignore_visible(self):
        session, frame_id = _curve_session()
        session.set_bbox("curve", (0.0, 0.0, 0.0), (100.0, 100.0, 0.0))
        session.add_object("visible", layer="A-A::Visible")
        session.set_curve("visible", [(0, 0, 0), (900, 0, 0)], closed=False)
        session.set_bbox("visible", (0.0, 0.0, 0.0), (900.0, 400.0, 0.0))
        session.add_clipping_plane("cp", name="A-A", section_bbox_local=(0.0, 0.0, 100.0, 100.0))
        result = run_anchor_update(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.object_bbox(frame_id), (-50.0, -50.0, 0.0, 150.0, 150.0, 0.0))
        payload = _payload(session, frame_id)
        self.assertEqual(payload["origin_2d"], [50.0, 50.0, 0.0])
        self.assertEqual(payload["origin_3d_local"], [50.0, 50.0])

    def test_uneven_gaps_use_default_offset(self):
        session, frame_id = _curve_session()
        session.set_bbox("curve", (0.0, 5.0, 0.0), (40.0, 30.0, 0.0))
        result = run_anchor_update(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.object_bbox(frame_id), (-50.0, -45.0, 0.0, 90.0, 80.0, 0.0))

    def test_ambiguous_section_leaves_frame(self):
        session, frame_id = _curve_session()
        before = session.object_bbox(frame_id)
        before_payload = _payload(session, frame_id)
        session.set_object_layer("curve", "A-A North::Curve")
        session.add_object("other", layer="A-A South::Curve")
        session.set_curve("other", [(0, 0, 0), (10, 0, 0), (10, 10, 0)], closed=True)
        session.set_bbox("other", (0.0, 0.0, 0.0), (10.0, 10.0, 0.0))
        result = run_anchor_update(session)
        self.assertFalse(result.ok)
        self.assertEqual(session.object_bbox(frame_id), before)
        self.assertEqual(_payload(session, frame_id), before_payload)

    def test_missing_clipping_plane_leaves_frame(self):
        session, frame_id = _block_session()
        before = session.object_bbox(frame_id)
        session.delete_object("cp")
        result = run_anchor_update(session)
        self.assertFalse(result.ok)
        self.assertEqual(session.object_bbox(frame_id), before)

    def test_ceiling_scale_is_kept(self):
        session, frame_id = _block_session(name="1F_CEILING", scale_x=-1.0)
        session.set_bbox("section", (0.0, 0.0, 0.0), (300.0, 100.0, 0.0))
        session.add_clipping_plane(
            "cp",
            name="1F_CEILING",
            section_bbox_local=(0.0, 0.0, 300.0, 100.0),
        )
        result = run_anchor_update(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(_payload(session, frame_id)["scale_x"], -1.0)
        self.assertEqual(_payload(session, frame_id)["scale_y"], -1.0)

    def test_one_miss_does_not_block_another_frame(self):
        session, frame_a = _block_session()
        session.add_object("section-b", name="B-B", layer="B-B")
        session.set_block("section-b", (0.0, 0.0, 0.0), name="B-B")
        session.set_bbox("section-b", (400.0, 0.0, 0.0), (500.0, 80.0, 0.0))
        session.add_clipping_plane("cp-b", name="B-B", section_bbox_local=(0.0, 0.0, 100.0, 80.0))
        registered = register_view(session, ("section-b",), 50, scale_x=1.0)
        self.assertTrue(registered.ok, registered.message)
        frame_b = registered.details["frame_id"]
        before_b = session.object_bbox(frame_b)
        session.delete_object("section-b")
        session.set_bbox("section", (0.0, 0.0, 0.0), (300.0, 100.0, 0.0))
        session.add_clipping_plane("cp", name="A-A", section_bbox_local=(0.0, 0.0, 300.0, 100.0))
        result = run_anchor_update(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["updated"], [frame_a])
        self.assertEqual(session.object_bbox(frame_a), (-50.0, -50.0, 0.0, 350.0, 150.0, 0.0))
        self.assertEqual(session.object_bbox(frame_b), before_b)
        self.assertTrue(result.warnings)

    def test_layout_and_empty_document_do_not_write(self):
        session, frame_id = _block_session()
        before = session.object_bbox(frame_id)
        session.set_layout_active(True)
        result = run_anchor_update(session)
        self.assertEqual(result.blocking, ("layout_active",))
        self.assertEqual(session.object_bbox(frame_id), before)
        empty = MemorySession()
        empty.set_layout_active(False)
        result = run_anchor_update(empty)
        self.assertEqual(result.blocking, ("missing_frame",))


if __name__ == "__main__":
    unittest.main()
