# -*- coding: utf-8 -*-
"""D01 Tagger Grab：只寫 binding；TAG_DW／鎖定／未知圖塊零寫入。"""
from __future__ import annotations

import copy
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Tagger_Grab.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.tagger.grab import bind_tag, run_tagger_grab
from loopflow.features.tagger.keys import (
    BINDING_MODE_KEY,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TAG_ID_KEY,
    TEMPLATE_ID_KEY,
)
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.foundation.usertext import OBJECT_ID_KEY
from loopflow.platform.rhino.memory import MemorySession
from loopflow.platform.rhino.state import ObjectViewState

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OBJECT_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"


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
    session.add_object("tag", selected=False, name="HeightTag", layer="M2D::Tags")
    session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_GRAB")
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


class TemplateLoadTests(unittest.TestCase):
    def test_loads_ten_templates_and_finds_block_names(self):
        catalog = _catalog()
        self.assertEqual(len(catalog.templates), 10)
        self.assertEqual(catalog.by_block_name("TAG_HEIGHT_GRAB").template_id, "TAG_HEIGHT_GRAB")
        self.assertEqual(catalog.by_block_name("Tag_Height_Grab").template_id, "TAG_HEIGHT_GRAB")
        self.assertEqual(catalog.by_block_name("TAG_ELEV_3").template_id, "TAG_ELEV")
        self.assertIsNone(catalog.by_block_name("UNKNOWN_BLOCK"))


class BindTests(unittest.TestCase):
    def test_height_grab_writes_source_object_id_not_source_usertext(self):
        session = _session()
        before_wall = dict(session._object_meta["wall"]["user_text"])
        result = bind_tag(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertEqual(session.get_object_user_text("tag", BINDING_MODE_KEY), "object")
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "TAG_HEIGHT_GRAB")
        self.assertTrue(session.get_object_user_text("tag", TAG_ID_KEY))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_BLOCK_NAME_KEY))
        self.assertEqual(session._object_meta["wall"]["user_text"], before_wall)

    def test_title_case_block_name_binds_and_keeps_actual_name(self):
        session = _session()
        session.set_block("tag", (0, 0, 0), name="Tag_Height_Grab")
        result = bind_tag(session, "tag", "wall", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertEqual(session.get_object_user_text("tag", TEMPLATE_ID_KEY), "Tag_Height_Grab")

    def test_item_writes_block_name_not_object_uuid(self):
        session = _session()
        session.add_object("chair", name="Chair", layer="M3D::FF")
        session.set_block("chair", (1, 0, 0), name="FF-01__Chair-1")
        session.add_object("item", name="ItemTag", layer="M2D::Tags")
        session.set_block("item", (0, 1, 0), name="TAG_ITEM")
        result = bind_tag(session, "item", "chair", _catalog())
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("item", SOURCE_BLOCK_NAME_KEY), "FF-01__Chair-1")
        self.assertEqual(session.get_object_user_text("item", BINDING_MODE_KEY), "block_name")
        self.assertIsNone(session.get_object_user_text("item", SOURCE_OBJECT_ID_KEY))

    def test_item_rejects_bad_block_name(self):
        session = _session()
        session.add_object("chair", name="Chair", layer="M3D::FF")
        session.set_block("chair", (1, 0, 0), name="Chair")
        session.add_object("item", name="ItemTag", layer="M2D::Tags")
        session.set_block("item", (0, 1, 0), name="TAG_ITEM")
        before = _snapshot(session)
        result = bind_tag(session, "item", "chair", _catalog())
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("invalid_block_name",))
        self.assertIsNone(session.get_object_user_text("item", SOURCE_BLOCK_NAME_KEY))
        self.assertEqual(session._object_meta["item"]["user_text"], before["objects"]["item"]["user_text"])

    def test_tag_dw_zero_write(self):
        session = _session()
        session.add_object("dw", name="DoorTag", layer="M2D::Tags")
        session.set_block("dw", (0, 0, 0), name="TAG_DW")
        result = bind_tag(session, "dw", "wall", _catalog())
        self.assertFalse(result.ok)
        self.assertIn("純手動", result.message)
        self.assertIsNone(session.get_object_user_text("dw", SOURCE_OBJECT_ID_KEY))
        self.assertIsNone(session.get_object_user_text("dw", TAG_ID_KEY))

    def test_unknown_block_zero_write(self):
        session = _session()
        session.add_object("mystery", name="Mystery", layer="M2D::Tags")
        session.set_block("mystery", (0, 0, 0), name="SOME_OTHER_BLOCK")
        result = bind_tag(session, "mystery", "wall", _catalog())
        self.assertEqual(result.blocking, ("unknown_block",))
        self.assertIsNone(session.get_object_user_text("mystery", TAG_ID_KEY))

    def test_locked_tag_zero_write(self):
        session = _session()
        session.set_object_user_text("tag", LOCK_STATE_KEY, "true")
        session.set_document_modified(False)
        result = bind_tag(session, "tag", "wall", _catalog())
        self.assertEqual(result.blocking, ("tag_locked",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_missing_source_uuid_zero_write(self):
        session = _session()
        session.set_object_user_text("wall", OBJECT_ID_KEY, "")
        result = bind_tag(session, "tag", "wall", _catalog())
        self.assertEqual(result.blocking, ("missing_object_id",))
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))

    def test_laser_and_index_refused(self):
        session = _session()
        session.add_object("laser", name="LaserTag", layer="M2D::Tags")
        session.set_block("laser", (0, 0, 0), name="Tag_Height_Laser")
        session.add_object("idx", name="IndexTag", layer="M2D::Tags")
        session.set_block("idx", (0, 0, 0), name="TAG_ELEV_1")
        laser = bind_tag(session, "laser", "wall", _catalog())
        index = bind_tag(session, "idx", "wall", _catalog())
        self.assertIn("Laser", laser.message)
        self.assertIn("Index", index.message)
        self.assertIsNone(session.get_object_user_text("laser", SOURCE_OBJECT_ID_KEY))
        self.assertIsNone(session.get_object_user_text("idx", SOURCE_OBJECT_ID_KEY))

    def test_rebind_overwrites_source_and_keeps_tag_id(self):
        session = _session()
        first = bind_tag(session, "tag", "wall", _catalog())
        self.assertTrue(first.ok)
        tag_uuid = session.get_object_user_text("tag", TAG_ID_KEY)
        session.add_object(
            "other",
            name="Other",
            layer="M3D::00_STR_結構::Beam.樑",
            user_text={OBJECT_ID_KEY: "cccccccc-cccc-4ccc-8ccc-cccccccccccc"},
        )
        second = bind_tag(session, "tag", "other", _catalog())
        self.assertTrue(second.ok)
        self.assertEqual(session.get_object_user_text("tag", TAG_ID_KEY), tag_uuid)
        self.assertEqual(
            session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY),
            "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
        )


class CommandTests(unittest.TestCase):
    def test_cancel_first_pick_restores_and_does_not_write(self):
        session = _session()
        before = _snapshot(session)
        result = run_tagger_grab(
            session,
            pick_tag=lambda _s: None,
            pick_source=lambda _s: "wall",
            catalog=_catalog(),
        )
        self.assertEqual(result.status, "cancelled")
        self.assertEqual(_snapshot(session)["objects"], before["objects"])
        self.assertTrue(session.get_view_state("wall").selected)

    def test_cancel_second_pick_does_not_write(self):
        session = _session()

        def pick_source(current):
            current.set_view_state(
                ObjectViewState("wall", False, False, False, (0, 0, 0), True)
            )
            return None

        result = run_tagger_grab(
            session,
            pick_tag=lambda _s: "tag",
            pick_source=pick_source,
            catalog=_catalog(),
        )
        self.assertEqual(result.status, "cancelled")
        self.assertIsNone(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY))
        self.assertTrue(session.get_view_state("wall").selected)

    def test_command_binds_and_restores_selection(self):
        session = _session()
        result = run_tagger_grab(
            session,
            pick_tag=lambda _s: "tag",
            pick_source=lambda _s: "wall",
            catalog=_catalog(),
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SOURCE_OBJECT_ID_KEY), OBJECT_ID)
        self.assertTrue(session.get_view_state("wall").selected)

    def test_missing_schema_stops_without_picking(self):
        session = MemorySession(document_text={})
        session.add_object("tag", name="Tag")
        session.set_block("tag", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        picked = []
        result = run_tagger_grab(
            session,
            pick_tag=lambda _s: picked.append("tag") or "tag",
            pick_source=lambda _s: "wall",
            catalog=_catalog(),
        )
        self.assertFalse(result.ok)
        self.assertEqual(picked, [])
        self.assertIn("schema", result.message)

    def test_catalog_and_entrypoint(self):
        from loopflow.command_catalog import get_command

        spec = get_command("LF_Tagger_Grab")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "D01")
        self.assertTrue(ENTRY.is_file())

    def test_run_command_without_rhino_does_not_claim_success(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_Tagger_Grab")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已綁定", result.message)
        self.assertIn("Rhino", buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
