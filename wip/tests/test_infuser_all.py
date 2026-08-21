# -*- coding: utf-8 -*-
"""D07 Infuser All：全檔 Layout 頁注入；規則與 Part 相同。"""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Infuser_All.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.bootstrap import run_command
from loopflow.command_catalog import get_command
from loopflow.features.infuser.all import run_infuser_all
from loopflow.features.infuser.keys import (
    ITEM_NAME_KEY,
    TYPE_CATEGORY_KEY,
    TYPE_DISPLAY_NAME_KEY,
)
from loopflow.features.infuser.part import run_infuser_part
from loopflow.features.tagger.keys import SOURCE_BLOCK_NAME_KEY, SOURCE_OBJECT_ID_KEY
from loopflow.platform.rhino.memory import MemorySession

from test_infuser_part import (
    OBJECT_ID,
    OTHER,
    PROJECT_ID,
    _add_block,
    _add_live_source,
    _catalog,
    _payload,
    _session,
    _snapshot,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import bind_project, read_project_config, registry_dir  # noqa: E402


def _run(session, **kwargs):
    kwargs.setdefault("catalog", _catalog())
    kwargs.setdefault("registry", _payload())
    return run_infuser_all(session, **kwargs)


class CatalogTests(unittest.TestCase):
    def test_all_is_ready(self):
        spec = get_command("LF_Infuser_All")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "D07")
        self.assertTrue(ENTRY.is_file())

    def test_run_command_without_rhino_does_not_claim_success(self):
        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_Infuser_All")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已處理", result.message)
        self.assertIn("Rhino", buffer.getvalue())


class InjectTests(unittest.TestCase):
    def test_infuses_current_and_other_pages(self):
        session = _session()
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _add_block(
            session,
            "there",
            "TAG_HEIGHT_GRAB",
            page=OTHER,
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["page_count"], 2)
        self.assertEqual(session.get_object_user_text("here", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("there", TYPE_CATEGORY_KEY), "PT")
        self.assertIn("已處理 2 頁", result.message)

    def test_part_still_leaves_other_page(self):
        session = _session()
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _add_block(
            session,
            "there",
            "TAG_HEIGHT_GRAB",
            page=OTHER,
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        result = run_infuser_part(
            session, catalog=_catalog(), registry=_payload()
        )
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("here", TYPE_CATEGORY_KEY), "PT")
        self.assertIsNone(session.get_object_user_text("there", TYPE_CATEGORY_KEY))

    def test_model_space_still_infuses_all_pages(self):
        session = _session()
        session.set_layout_active(False)
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _add_block(
            session,
            "there",
            "TAG_ITEM",
            page=OTHER,
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("here", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("there", ITEM_NAME_KEY), "Chair-1")

    def test_missing_schema_is_filled_and_continues(self):
        session = _session(write_config=False)
        root = Path(session.document_path()).parent
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _add_block(
            session,
            "there",
            "TAG_HEIGHT_GRAB",
            page=OTHER,
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(read_project_config(root)["schema_id"], "loopflow.project")
        self.assertEqual(session.get_object_user_text("here", TYPE_CATEGORY_KEY), "PT")

    def test_no_layout_pages_zero_write(self):
        session = MemorySession()
        bind_project(session, project_id=PROJECT_ID)
        result = _run(session)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("missing_layout_page",))

    def test_repeat_run_keeps_values(self):
        session = _session()
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        first = _run(session)
        second = _run(session)
        self.assertTrue(first.ok and second.ok)
        self.assertEqual(session.get_object_user_text("here", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("here", TYPE_DISPLAY_NAME_KEY), "Paint")


class RegistryFileTests(unittest.TestCase):
    def test_corrupt_official_stops_and_does_not_write(self):
        session = _session()
        root = Path(session.document_path()).parent
        folder = registry_dir(root, PROJECT_ID)
        (folder / "Project_Registry.json").write_text("{not json", encoding="utf-8")
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _add_block(
            session,
            "there",
            "TAG_ITEM",
            page=OTHER,
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        before = _snapshot(session)
        result = run_infuser_all(session, catalog=_catalog())
        self.assertFalse(result.ok)
        self.assertIsNone(session.get_object_user_text("here", TYPE_CATEGORY_KEY))
        self.assertIsNone(session.get_object_user_text("there", ITEM_NAME_KEY))
        self.assertEqual(session._object_meta, before["objects"])

    def test_missing_registry_still_injects_item_on_other_page(self):
        session = _session()
        _add_live_source(session)
        _add_block(
            session,
            "there",
            "TAG_ITEM",
            page=OTHER,
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        result = run_infuser_all(session, catalog=_catalog())
        self.assertTrue(result.ok, result.message)
        self.assertIn("missing_registry", result.warnings)
        self.assertEqual(session.get_object_user_text("there", ITEM_NAME_KEY), "Chair-1")


if __name__ == "__main__":
    unittest.main()
