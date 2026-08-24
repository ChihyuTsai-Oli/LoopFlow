# -*- coding: utf-8 -*-
"""D03 Tagger Index：選 Layout Detail，只寫唯一對到的 lf_target_view_id。"""
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
    detail_choice_label,
    detail_choice_labels,
    listed_details,
    listed_views,
    preview_detail,
    run_tagger_index,
    view_choice_label,
    view_choice_labels,
)
from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    LOCK_LEGACY_KEY,
    LOCK_LEGACY_HINT,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.features.view.keys import SCHEMA_ID_KEY, VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import bind_project  # noqa: E402

PROJECT_ID = "大安邸"
VIEW_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
VIEW_ID_B = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
SHEET_CODE_KEY = "lf_sheet_code"
SHEET_REF_KEY = "lf_sheet_ref"
DETAIL_NO_KEY = "lf_detail_no"
DETAIL_A = {
    "layout": "A1__Plan",
    "page_number": 1,
    "detail_id": "dv-1",
    "dv_name": "LF_平面",
}
DETAIL_B = {
    "layout": "A2__Section",
    "page_number": 2,
    "detail_id": "dv-2",
    "dv_name": "A-A",
}


def _session() -> MemorySession:
    session = MemorySession()
    bind_project(session, project_id=PROJECT_ID)
    session.add_object("tag", selected=True, name="IndexTag", layer="M2D::Tags")
    session.set_block("tag", (0, 0, 0), name="TAG_SECTION_DETAIL")
    session.add_object("frame", name="A-A", layer="LoopFlow::Anchor_Frame")
    session.set_object_user_text("frame", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
    session.set_object_user_text("frame", VIEW_ID_KEY, VIEW_ID)
    session.set_bbox("frame", (0, 0, 0), (100, 100, 0))
    session.set_layout_details((DETAIL_A, DETAIL_B))
    session.set_detail_model_point("dv-1", (50, 50, 0))
    session.set_detail_model_point("dv-2", (50, 50, 0))
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
        "choose_detail": lambda details: details[0],
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

    def test_detail_label_uses_page_and_name_not_guid(self):
        label = detail_choice_label(DETAIL_A)
        self.assertEqual(label, "A1__Plan    LF_平面")
        self.assertNotIn("dv-1", label)
        self.assertEqual(detail_choice_label({"layout": "", "dv_name": ""}), "（未命名頁）    （未命名 Detail）")
        labels = detail_choice_labels((DETAIL_A, DETAIL_A, DETAIL_B))
        self.assertEqual(labels, ("A1__Plan    LF_平面（1）", "A1__Plan    LF_平面（2）", "A2__Section    A-A"))
        self.assertNotIn("dv-1", "".join(labels))
        self.assertNotIn(VIEW_ID, "".join(labels))


class BindTests(unittest.TestCase):
    def test_section_detail_writes_target_view_id(self):
        session = _session()
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY), VIEW_ID)
        self.assertEqual(session.get_object_user_text("tag", BINDING_MODE_KEY), "view")
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "TAG_SECTION_DETAIL")
        self.assertTrue(session.get_object_user_text("tag", TAG_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_LAYOUT_KEY))
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

    def test_legacy_x_lock_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_LEGACY_KEY, "x")
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", LOCK_STATE_KEY))

    def test_legacy_X_lock_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_LEGACY_KEY, "X")
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_legacy_lock_hint_still_binds(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_LEGACY_KEY, LOCK_LEGACY_HINT)
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY), VIEW_ID)
        self.assertEqual(session.get_object_user_text("tag", LOCK_LEGACY_KEY), LOCK_LEGACY_HINT)

    def test_legacy_lock_empty_still_binds(self):
        session = _session()
        session._meta("tag")["user_text"][LOCK_LEGACY_KEY] = ""
        result = bind_index_view(session, "tag", VIEW_ID, _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY), VIEW_ID)

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
        self.assertEqual(session.get_object_user_text("tag", TARGET_LAYOUT_KEY), "A1__Plan")
        self.assertTrue(session.get_view_state("tag").selected)
        self.assertEqual(listed_views(session)[0]["view_id"], VIEW_ID)
        self.assertIsNone(session.get_object_user_text("tag", SHEET_CODE_KEY))

    def test_lists_details_from_all_layouts(self):
        session = _session()
        captured = []
        result = _run(session, choose_detail=lambda details: captured.append(details) or details[1])
        self.assertTrue(result.ok, result.message)
        self.assertEqual([item["layout"] for item in captured[0]], ["A1__Plan", "A2__Section"])
        self.assertEqual([item["dv_name"] for item in captured[0]], ["LF_平面", "A-A"])
        self.assertEqual(listed_details(session)[1]["detail_id"], "dv-2")
        self.assertNotIn(VIEW_ID, "".join(item["dv_name"] for item in captured[0]))

    def test_preview_zooms_to_detail(self):
        session = _session()
        preview_detail(session, DETAIL_B)
        self.assertEqual(
            session.zoomed_layout_details,
            [{"layout": "A2__Section", "detail_id": "dv-2"}],
        )

    def test_cancel_first_pick_does_not_write(self):
        session = _session()
        before = _snapshot(session)
        result = _run(session, pick_tag=lambda _s: None)
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session)["objects"], before["objects"])
        self.assertTrue(session.get_view_state("tag").selected)

    def test_cancel_detail_choice_does_not_write(self):
        session = _session()

        def choose(details):
            session.set_view_state(ObjectViewState("tag", False, False, False, (0, 0, 0), True))
            self.assertEqual(len(details), 2)
            return None

        result = _run(session, choose_detail=choose)
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))
        self.assertTrue(session.get_view_state("tag").selected)

    def test_not_layout_stops_without_picking(self):
        session = _session()
        session.set_layout_active(False)
        picked = []
        chosen = []
        result = _run(
            session,
            pick_tag=lambda _s: picked.append("tag") or "tag",
            choose_detail=lambda details: chosen.append(details) or details[0],
        )
        self.assertEqual(result.blocking, ("not_layout",))
        self.assertEqual(picked, [])
        self.assertEqual(chosen, [])
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_no_details_zero_write(self):
        session = _session()
        session.set_layout_details(())
        chosen = []
        result = _run(session, choose_detail=lambda details: chosen.append(details) or details[0])
        self.assertEqual(result.blocking, ("missing_detail",))
        self.assertEqual(chosen, [])
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_no_registered_view_zero_write(self):
        session = _session()
        session.delete_object("frame")
        chosen = []
        result = _run(session, choose_detail=lambda details: chosen.append(details) or details[0])
        self.assertEqual(result.blocking, ("missing_view",))
        self.assertEqual(len(chosen), 1)
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_ambiguous_view_zero_write(self):
        session = _session()
        session.add_object("frame2", name="B-B", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("frame2", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("frame2", VIEW_ID_KEY, VIEW_ID_B)
        session.set_bbox("frame2", (0, 0, 0), (100, 100, 0))
        result = _run(session)
        self.assertEqual(result.blocking, ("ambiguous_view",))
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_grab_tag_refused_before_choose(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        chosen = []
        result = _run(session, choose_detail=lambda details: chosen.append(True) or details[0])
        self.assertEqual(result.blocking, ("unsupported_template",))
        self.assertEqual(chosen, [])
        self.assertIsNone(session.get_object_user_text("tag", TARGET_VIEW_ID_KEY))

    def test_missing_schema_stops_without_picking(self):
        session = MemorySession()
        bind_project(session, write_config=False)
        session.add_object("tag", name="Tag")
        session.set_block("tag", (0, 0, 0), name="TAG_SECTION_DETAIL")
        picked = []
        result = run_tagger_index(
            session,
            pick_tag=lambda _s: picked.append("tag") or "tag",
            choose_detail=lambda details: details[0],
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
