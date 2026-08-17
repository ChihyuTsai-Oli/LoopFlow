# -*- coding: utf-8 -*-
"""D03 Tagger Index：選已登記 View，只寫 lf_target_view_id。"""
from __future__ import annotations

import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Tagger_Index.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.tagger.index import (
    bind_index_view,
    listed_views,
    run_tagger_index,
    view_choice_label,
    view_choice_labels,
)
from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.features.view.keys import SCHEMA_ID_KEY, VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
VIEW_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
SHEET_CODE_KEY = "lf_sheet_code"
SHEET_REF_KEY = "lf_sheet_ref"
DETAIL_NO_KEY = "lf_detail_no"


def _session() -> MemorySession:
    session = MemorySession(
        document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.project",
            "lf_schema_version": "1",
        }
    )
    session.add_object("tag", selected=True, name="IndexTag", layer="M2D::Tags")
    session.set_block("tag", (0, 0, 0), name="TAG_SECTION_DETAIL")
    session.add_object("frame", name="A-A", layer="LoopFlow::Anchor_Frame")
    session.set_object_user_text("frame", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
    session.set_object_user_text("frame", VIEW_ID_KEY, VIEW_ID)
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
        "selected": session.get_view_state("tag").selected,
    }


def _run(session, **kwargs):
    params = {
        "pick_tag": lambda _s: "tag",
        "choose_view": lambda views: views[0],
        "catalog": _catalog(),
    }
    params.update(kwargs)
    return run_tagger_index(session, **params)


class LabelTests(unittest.TestCase):
    def test_label_uses_name_not_view_id(self):
        label = view_choice_label({"name": "A-A", "view_id": VIEW_ID, "frame_id": "frame"})
        self.assertEqual(label, "A-A")
        self.assertNotIn(VIEW_ID, label)

    def test_unnamed_and_duplicate_suffix(self):
        self.assertEqual(view_choice_label({"name": ""}), "（未命名 View）")
        labels = view_choice_labels(
            (
                {"name": "A-A", "view_id": "one"},
                {"name": "A-A", "view_id": "two"},
                {"name": "B-B", "view_id": "three"},
            )
        )
        self.assertEqual(labels, ("A-A（1）", "A-A（2）", "B-B"))
        self.assertNotIn("one", "".join(labels))


class BindTests(unittest.TestCase):
    def test_section_detail_writes_target_view_id(self):
        session = _session()
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY), VIEW_ID)
        self.assertEqual(session.get_object_user_text("tag", BINDING_MODE_KEY), "view")
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "TAG_SECTION_DETAIL")
        self.assertTrue(session.get_object_user_text("tag", TAG_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_SHEET_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_BLOCK_NAME_KEY))
        self.assertIsNone(session.get_object_user_text("tag", SHEET_CODE_KEY))
        self.assertIsNone(session.get_object_user_text("tag", SHEET_REF_KEY))
        self.assertIsNone(session.get_object_user_text("tag", DETAIL_NO_KEY))

    def test_title_case_elev_keeps_actual_block_name(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="Tag_Elev_1")
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY), VIEW_ID)
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "Tag_Elev_1")

    def test_grab_laser_elev0_frame_zero_write(self):
        session = _session()
        session.add_object("grab", name="GrabTag", layer="M2D::Tags")
        session.set_block("grab", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        session.add_object("laser", name="LaserTag", layer="M2D::Tags")
        session.set_block("laser", (0, 0, 0), name="TAG_HEIGHT_LASER")
        session.add_object("elev0", name="Elev0", layer="M2D::Tags")
        session.set_block("elev0", (0, 0, 0), name="TAG_ELEV_0")
        session.add_object("frame_tag", name="Title", layer="M2D::Tags")
        session.set_block("frame_tag", (0, 0, 0), name="Sample_Frame")
        for object_id in ("grab", "laser", "elev0", "frame_tag"):
            result = bind_index_view(session, object_id, VIEW_ID, _catalog())
            self.assertFalse(result.ok, object_id)
            self.assertEqual(result.blocking, ("unsupported_template",))
            self.assertIsNone(session.get_object_user_text(object_id, TARGET_VIEW_ID_KEY))
            self.assertIsNone(session.get_object_user_text(object_id, TAG_ID_KEY))

    def test_locked_tag_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_STATE_KEY, "true")
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_invalid_view_id_zero_write(self):
        session = _session()
        result = bind_index_view(session, "tag", "not-a-uuid", _catalog())
        self.assertEqual(result.blocking, ("missing_view",))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))


class CommandTests(unittest.TestCase):
    def test_command_binds_and_restores_selection(self):
        session = _session()
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY), VIEW_ID)
        self.assertTrue(session.get_view_state("tag").selected)
        self.assertEqual(listed_views(session)[0]["view_id"], VIEW_ID)

    def test_cancel_first_pick_does_not_write(self):
        session = _session()
        before = _snapshot(session)
        result = _run(session, pick_tag=lambda _s: None)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session)["objects"], before["objects"])
        self.assertTrue(session.get_view_state("tag").selected)

    def test_cancel_view_choice_does_not_write(self):
        session = _session()

        def choose(views):
            session.set_view_state(ObjectViewState("tag", False, False, False, (0, 0, 0), True))
            self.assertEqual(len(views), 1)
            return None

        result = _run(session, choose_view=choose)
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))
        self.assertTrue(session.get_view_state("tag").selected)

    def test_no_registered_view_zero_write(self):
        session = _session()
        session.delete_object("frame")
        chosen = []
        result = _run(session, choose_view=lambda views: chosen.append(views) or views[0])
        self.assertEqual(result.blocking, ("missing_view",))
        self.assertEqual(chosen, [])
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_grab_tag_refused_before_choose(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        chosen = []
        result = _run(session, choose_view=lambda views: chosen.append(True) or views[0])
        self.assertEqual(result.blocking, ("unsupported_template",))
        self.assertEqual(chosen, [])
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_missing_schema_stops_without_picking(self):
        session = MemorySession(document_text={})
        session.add_object("tag", name="Tag")
        session.set_block("tag", (0, 0, 0), name="TAG_SECTION_DETAIL")
        picked = []
        result = run_tagger_index(
            session,
            pick_tag=lambda _s: picked.append("tag") or "tag",
            choose_view=lambda views: views[0],
            catalog=_catalog(),
        )
        self.assertFalse(result.ok)
        self.assertEqual(picked, [])
        self.assertIn("schema", result.message)

    def test_catalog_and_entrypoint(self):
        from loopflow.command_catalog import get_command

        spec = get_command("LF_Tagger_Index")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "D03")
        self.assertTrue(ENTRY.is_file())

    def test_run_command_without_rhino_does_not_claim_success(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_Tagger_Index")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已綁定", result.message)
        self.assertIn("Rhino", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
