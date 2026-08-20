# -*- coding: utf-8 -*-
"""E02 Extract CP：複製 Section 線稿、辨識前次產出、寫來源索引。"""
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
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.drawing import keys as drawing_keys
from loopflow.features.drawing.extract import (
    classify_sources,
    listed_section_roots,
    run_extract_cp,
    target_layer_for,
)
from loopflow.features.view.keys import (
    SCHEMA_ID_KEY,
    SCHEMA_VERSION_KEY,
    VIEW_ID_KEY,
    VIEW_SCHEMA_ID,
    VIEW_SCHEMA_VERSION,
)
from loopflow.foundation.usertext import OBJECT_ID_KEY
from loopflow.platform.rhino.memory import MemorySession

VIEW_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"
SOURCE_A = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
SOURCE_B = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CASES_PATH = WIP / "fixtures" / "contract" / "drawing" / "provenance_cases.json"


def _session() -> MemorySession:
    session = MemorySession()
    session.set_layout_active(False)
    for path, rgb in (
        ("A-A::Visible", drawing_keys.COLOR_VISIBLE),
        ("A-A::Hatch", drawing_keys.COLOR_HATCH),
        ("A-A::Curve_Red", (255, 0, 0)),
    ):
        session.ensure_layer(path)
        session.set_layer_appearance(path, rgb)
    session.add_object(
        "vis",
        layer="A-A::Visible",
        color=drawing_keys.COLOR_VISIBLE,
        user_text={
            OBJECT_ID_KEY: SOURCE_A,
            "_01_空間名稱": "廊道",
        },
    )
    session.add_object("hat", layer="A-A::Hatch", color=drawing_keys.COLOR_HATCH)
    session.add_object(
        "crv",
        layer="A-A::Curve_Red",
        color=(255, 0, 0),
        color_by_layer=False,
        user_text={
            drawing_keys.SOURCE_OBJECT_IDS_KEY: json.dumps([SOURCE_A, SOURCE_B]),
        },
    )
    session.add_object(
        "frame",
        name="A-A",
        layer="LoopFlow::Anchor_Frame",
        user_text={
            SCHEMA_ID_KEY: VIEW_SCHEMA_ID,
            SCHEMA_VERSION_KEY: VIEW_SCHEMA_VERSION,
            VIEW_ID_KEY: VIEW_ID,
        },
    )
    session.set_layer_locked("A-A::Visible", True)
    session.set_document_modified(False)
    return session


def _snapshot(session: MemorySession) -> dict:
    return {
        "ids": set(session.iter_object_ids()),
        "modified": session.document_modified(),
        "objects": copy.deepcopy(session._object_meta),
        "layers": copy.deepcopy(session._layers),
        "locked": session.layer_locked("A-A::Visible"),
    }


def _extract_ids(session: MemorySession):
    return [
        object_id
        for object_id in session.iter_object_ids()
        if str(session.object_layer(object_id) or "").startswith(
            drawing_keys.EXTRACT_LAYER_ROOT
        )
    ]


def _run(session, roots=("A-A",), mode="add"):
    messages = []

    def _pick_roots(_current, _available):
        return tuple(roots)

    def _pick_mode(_current, _info):
        return mode

    return run_extract_cp(
        session,
        pick_roots=_pick_roots,
        pick_mode=_pick_mode,
        show_message=messages.append,
    ), messages


class ContractFixtureTests(unittest.TestCase):
    def test_provenance_cases_match_classifier(self):
        cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))["cases"]
        by_id = {item["id"]: item for item in cases}
        for required in (
            "zero-source",
            "one-source",
            "many-sources",
            "manual-edit-not-current",
            "incomplete-index-still-produces",
        ):
            self.assertIn(required, by_id)
        state, coverage, _method = classify_sources([])
        self.assertEqual(coverage, "unindexed")
        self.assertEqual(state, drawing_keys.STATE_UNINDEXED)
        state, coverage, _method = classify_sources([SOURCE_A])
        self.assertEqual(coverage, "indexed")
        self.assertEqual(state, drawing_keys.STATE_CURRENT)
        state, coverage, _method = classify_sources([SOURCE_A, SOURCE_B])
        self.assertEqual(coverage, "ambiguous")
        self.assertEqual(state, drawing_keys.STATE_AMBIGUOUS)
        self.assertEqual(
            by_id["manual-edit-not-current"]["provenance_state"],
            drawing_keys.STATE_MODIFIED,
        )
        self.assertFalse(by_id["incomplete-index-still-produces"].get("block_drawing"))


class ExtractTests(unittest.TestCase):
    def test_lists_section_roots_and_curve_hex_layer(self):
        session = _session()
        self.assertEqual(listed_section_roots(session), ("A-A",))
        self.assertEqual(
            target_layer_for(drawing_keys.KIND_CURVE, (255, 0, 0)),
            "LoopFlow_Extract::Curve_#FF0000",
        )

    def test_copies_visible_hatch_curve_and_writes_ids(self):
        session = _session()
        result, messages = _run(session)
        self.assertTrue(result.ok, result.message)
        ids = _extract_ids(session)
        self.assertEqual(len(ids), 3)
        layers = {session.object_layer(object_id) for object_id in ids}
        self.assertEqual(
            layers,
            {
                drawing_keys.LAYER_VISIBLE,
                drawing_keys.LAYER_HATCH,
                "LoopFlow_Extract::Curve_#FF0000",
            },
        )
        self.assertTrue(session.layer_printable(drawing_keys.EXTRACT_LAYER_ROOT))
        self.assertTrue(session.layer_printable(drawing_keys.LAYER_VISIBLE))
        self.assertEqual(
            session.layer_print_color(drawing_keys.LAYER_VISIBLE),
            drawing_keys.COLOR_PRINT_GRAY,
        )
        self.assertEqual(
            session.layer_print_color(drawing_keys.LAYER_HATCH),
            drawing_keys.COLOR_PRINT_GRAY,
        )
        self.assertEqual(
            session.layer_print_color(drawing_keys.EXTRACT_LAYER_ROOT),
            drawing_keys.COLOR_PRINT_BLACK,
        )
        self.assertEqual(
            session.layer_print_color("LoopFlow_Extract::Curve_#FF0000"),
            drawing_keys.COLOR_PRINT_BLACK,
        )
        drawing_ids = {
            session.get_object_user_text(object_id, drawing_keys.DRAWING_ID_KEY)
            for object_id in ids
        }
        self.assertEqual(len(drawing_ids), 1)
        view_ids = {
            session.get_object_user_text(object_id, VIEW_ID_KEY) for object_id in ids
        }
        self.assertEqual(view_ids, {VIEW_ID})
        vis = next(
            object_id
            for object_id in ids
            if session.object_layer(object_id) == drawing_keys.LAYER_VISIBLE
        )
        self.assertIsNone(session.get_object_user_text(vis, OBJECT_ID_KEY))
        self.assertIsNone(session.get_object_user_text(vis, "_01_空間名稱"))
        for key in session.object_user_text_keys(vis):
            self.assertTrue(str(key).startswith("lf_"), key)
        self.assertIn(
            SOURCE_A,
            session.get_object_user_text(vis, drawing_keys.SOURCE_OBJECT_IDS_KEY),
        )
        self.assertEqual(
            session.get_object_user_text(vis, drawing_keys.PROVENANCE_STATE_KEY),
            drawing_keys.STATE_CURRENT,
        )
        crv = next(
            object_id
            for object_id in ids
            if "Curve_" in str(session.object_layer(object_id))
        )
        self.assertEqual(
            session.get_object_user_text(crv, drawing_keys.PROVENANCE_STATE_KEY),
            drawing_keys.STATE_AMBIGUOUS,
        )
        counts = result.details["counts"]
        self.assertEqual(counts["copied"], 3)
        self.assertEqual(counts["indexed"], 1)
        self.assertEqual(counts["unindexed"], 1)
        self.assertEqual(counts["ambiguous"], 1)
        self.assertTrue(result.details["coverage_incomplete"])
        self.assertTrue(messages)
        self.assertEqual(session.object_layer("vis"), "A-A::Visible")

    def test_skip_keeps_previous(self):
        session = _session()
        first, _messages = _run(session)
        self.assertTrue(first.ok, first.message)
        before = set(_extract_ids(session))
        second, _messages = _run(session, mode=drawing_keys.MODE_SKIP)
        self.assertTrue(second.ok, second.message)
        self.assertEqual(set(_extract_ids(session)), before)
        self.assertEqual(second.details["counts"]["copied"], 0)

    def test_replace_deletes_previous_and_keeps_drawing_id(self):
        session = _session()
        first, _messages = _run(session)
        old_ids = set(_extract_ids(session))
        drawing_id = session.get_object_user_text(
            next(iter(old_ids)), drawing_keys.DRAWING_ID_KEY
        )
        second, _messages = _run(session, mode=drawing_keys.MODE_REPLACE)
        self.assertTrue(second.ok, second.message)
        new_ids = set(_extract_ids(session))
        self.assertEqual(len(new_ids), 3)
        self.assertTrue(old_ids.isdisjoint(new_ids))
        self.assertEqual(
            session.get_object_user_text(
                next(iter(new_ids)), drawing_keys.DRAWING_ID_KEY
            ),
            drawing_id,
        )

    def test_add_keeps_old_and_creates_new_drawing_id(self):
        session = _session()
        first, _messages = _run(session)
        old_ids = set(_extract_ids(session))
        old_drawing = session.get_object_user_text(
            next(iter(old_ids)), drawing_keys.DRAWING_ID_KEY
        )
        second, _messages = _run(session, mode=drawing_keys.MODE_ADD)
        self.assertTrue(second.ok, second.message)
        all_ids = set(_extract_ids(session))
        self.assertEqual(len(all_ids), 6)
        drawings = {
            session.get_object_user_text(object_id, drawing_keys.DRAWING_ID_KEY)
            for object_id in all_ids
        }
        self.assertEqual(len(drawings), 2)
        self.assertIn(old_drawing, drawings)

    def test_modified_replace_is_blocked(self):
        session = _session()
        first, _messages = _run(session)
        self.assertTrue(first.ok, first.message)
        for object_id in _extract_ids(session):
            session.set_object_user_text(
                object_id,
                drawing_keys.PROVENANCE_STATE_KEY,
                drawing_keys.STATE_MODIFIED,
            )
        before = _snapshot(session)
        second, _messages = _run(session, mode=drawing_keys.MODE_REPLACE)
        self.assertFalse(second.ok)
        self.assertEqual(second.status, "blocked")
        self.assertIn("modified_drawing", second.blocking)
        self.assertEqual(_snapshot(session)["ids"], before["ids"])

    def test_cancel_zero_write(self):
        session = _session()
        before = _snapshot(session)

        def _cancel(_current, _roots):
            return None

        result = run_extract_cp(session, pick_roots=_cancel)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session), before)

    def test_missing_section_layers_blocks(self):
        session = MemorySession()
        session.set_layout_active(False)
        result = run_extract_cp(session, pick_roots=lambda _s, roots: roots)
        self.assertEqual(result.status, "blocked")
        self.assertIn("missing_section_layers", result.blocking)

    def test_layout_active_blocks(self):
        session = _session()
        session.set_layout_active(True)
        before = _snapshot(session)
        result, _messages = _run(session)
        self.assertEqual(result.status, "blocked")
        self.assertIn("layout_active", result.blocking)
        self.assertEqual(_snapshot(session)["ids"], before["ids"])

    def test_does_not_unlock_source_layer(self):
        session = _session()
        self.assertTrue(session.layer_locked("A-A::Visible"))
        result, _messages = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertTrue(session.layer_locked("A-A::Visible"))

    def test_ambiguous_view_skips_without_write(self):
        session = _session()
        session.add_object(
            "frame-2",
            name="A-A",
            layer="LoopFlow::Anchor_Frame",
            user_text={
                SCHEMA_ID_KEY: VIEW_SCHEMA_ID,
                SCHEMA_VERSION_KEY: VIEW_SCHEMA_VERSION,
                VIEW_ID_KEY: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
            },
        )
        before = _snapshot(session)
        result, _messages = _run(session)
        self.assertEqual(result.status, "blocked")
        self.assertIn("ambiguous_view", result.blocking)
        self.assertEqual(_snapshot(session)["ids"], before["ids"])


if __name__ == "__main__":
    unittest.main()
