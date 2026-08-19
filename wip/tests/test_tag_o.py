# -*- coding: utf-8 -*-
"""D05 TAG-O：只讀確認 Tag 活著或斷連；不寫入、不改顏色。"""
from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_TAG-O.py"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.bootstrap import run_command
from loopflow.command_catalog import get_command
from loopflow.features.health.tag_o import run_tag_o
from loopflow.features.infuser.keys import TYPE_CATEGORY_KEY
from loopflow.features.tagger.keys import (
    LAST_SYNCED_REVISION_KEY,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_VIEW_ID_KEY,
)
from loopflow.features.view.keys import SCHEMA_ID_KEY, VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.platform.rhino.memory import MemorySession

from test_infuser_part import (
    OBJECT_ID,
    OTHER,
    PAGE,
    VIEW_ID,
    _add_block,
    _add_live_source,
    _catalog,
    _payload,
    _session,
    _snapshot,
)

MISSING = "ffffffff-ffff-4fff-8fff-ffffffffffff"


def _run(session, **kwargs):
    kwargs.setdefault("catalog", _catalog())
    kwargs.setdefault("registry", _payload())
    return run_tag_o(session, **kwargs)


def _stamp(session, tag_id, revision=2):
    session.set_object_user_text(tag_id, LAST_SYNCED_REVISION_KEY, str(revision))


def _add_view(session, page=PAGE, view_id=VIEW_ID):
    session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
    session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
    session.set_object_user_text("view", VIEW_ID_KEY, view_id)
    session.set_bbox("view", (0, 0, 0), (100, 100, 0))
    session.set_layout_details(
        (
            {
                "layout": page,
                "page_number": 1,
                "detail_id": "dv-1",
                "dv_name": "A-A",
            },
        )
    )
    session.set_detail_model_point("dv-1", (50, 50, 0))


class CatalogTests(unittest.TestCase):
    def test_tag_o_is_ready(self):
        spec = get_command("LF_TAG-O")
        self.assertEqual(spec["status"], "ready")
        self.assertEqual(spec["task"], "D05")
        self.assertTrue(ENTRY.is_file())

    def test_run_command_without_rhino_does_not_claim_success(self):
        with redirect_stdout(io.StringIO()) as buffer:
            result = run_command("LF_TAG-O")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertNotIn("已檢查", result.message)
        self.assertIn("Rhino", buffer.getvalue())


class GuardTests(unittest.TestCase):
    def test_missing_schema_zero_write(self):
        session = _session()
        session._document_text.pop("lf_schema_id", None)
        session._document_text.pop("lf_schema_version", None)
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        before = _snapshot(session)
        result = _run(session)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("missing_document_schema",))
        self.assertEqual(session._object_meta, before["objects"])

    def test_no_layout_pages_zero_write(self):
        session = MemorySession(
            document_text={
                "lf_project_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                "lf_schema_id": "loopflow.project",
                "lf_schema_version": "1",
            }
        )
        result = _run(session)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("missing_layout_page",))

    def test_corrupt_official_stops_and_does_not_write(self):
        root = Path(tempfile.mkdtemp())
        (root / "exchange" / "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa").mkdir(parents=True)
        official = (
            root
            / "exchange"
            / "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
            / "Project_Registry.json"
        )
        official.write_text("{not json", encoding="utf-8")
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        before = _snapshot(session)
        result = run_tag_o(
            session,
            catalog=_catalog(),
            environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
        )
        self.assertFalse(result.ok)
        self.assertEqual(session._object_meta, before["objects"])


class HealthTests(unittest.TestCase):
    def test_healthy_bound_and_synced_tag(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _stamp(session, "tag")
        before = _snapshot(session)
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["healthy"], 1)
        self.assertEqual(result.details["counts"]["scanned"], 1)
        self.assertFalse(result.warnings)
        self.assertEqual(session._object_meta, before["objects"])
        self.assertIn("只讀", result.message)

    def test_unbound_missing_source(self):
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertIn("unbound", result.warnings)
        self.assertEqual(result.details["counts"]["unbound"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)

    def test_orphaned_when_source_gone(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: MISSING},
        )
        _stamp(session, "tag")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["orphaned"], 1)

    def test_live_model_is_not_orphaned(self):
        session = _session()
        _add_live_source(session)
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _stamp(session, "tag")
        result = _run(session, registry=_payload(objects=[]))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["orphaned"], 0)
        self.assertEqual(result.details["counts"]["healthy"], 1)

    def test_stale_when_revision_lags(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _stamp(session, "tag", revision=1)
        result = _run(session, registry=_payload(revision=3))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["stale"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)

    def test_never_infused_bound_tag_is_stale(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["stale"], 1)

    def test_manual_dw_is_not_unbound(self):
        session = _session()
        _add_block(session, "tag", "TAG_DW")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["unbound"], 0)
        self.assertEqual(result.details["counts"]["healthy"], 1)
        self.assertEqual(result.details["counts"]["skipped_manual"], 1)

    def test_elev_0_is_checked_and_not_unbound(self):
        session = _session()
        _add_block(session, "tag", "TAG_ELEV_0")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["unbound"], 0)
        self.assertEqual(result.details["counts"]["healthy"], 1)
        self.assertEqual(result.details["counts"]["skipped_elev_0"], 1)

    def test_item_never_orphaned_even_without_registry_object(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_ITEM",
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        _stamp(session, "tag")
        result = _run(session, registry=_payload(objects=[]))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["orphaned"], 0)
        self.assertEqual(result.details["counts"]["healthy"], 1)

    def test_item_missing_name_is_unbound_not_orphaned(self):
        session = _session()
        _add_block(session, "tag", "TAG_ITEM")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["unbound"], 1)
        self.assertEqual(result.details["counts"]["orphaned"], 0)

    def test_locked_orphaned_still_reported(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={
                SOURCE_OBJECT_ID_KEY: MISSING,
                LOCK_STATE_KEY: "x",
            },
        )
        _stamp(session, "tag")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["orphaned"], 1)
        self.assertEqual(result.details["counts"]["locked_disconnected"], 1)
        self.assertEqual(result.details["issues"][0]["locked"], True)

    def test_unknown_block_is_unchecked_not_healthy(self):
        session = _session()
        _add_block(session, "tag", "Random_Block")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertIn("unchecked", result.warnings)
        self.assertEqual(result.details["counts"]["unchecked"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        self.assertEqual(result.details["counts"]["scanned"], 0)

    def test_title_frame_not_counted_as_pass(self):
        session = _session()
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertGreaterEqual(result.details["counts"]["skipped_title_frame"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)

    def test_scans_all_pages_from_model_space(self):
        session = _session()
        session.set_layout_active(False)
        _add_block(
            session,
            "here",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        _stamp(session, "here")
        _add_block(
            session,
            "there",
            "TAG_ITEM",
            page=OTHER,
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        _stamp(session, "there")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["page_count"], 2)
        self.assertEqual(result.details["counts"]["healthy"], 2)

    def test_index_unbound_without_target(self):
        session = _session()
        _add_block(session, "tag", "TAG_SECTION_DETAIL")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["unbound"], 1)

    def test_index_orphaned_when_view_gone(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={TARGET_VIEW_ID_KEY: VIEW_ID},
        )
        _stamp(session, "tag")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["orphaned"], 1)

    def test_index_healthy_with_target_layout(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={
                TARGET_VIEW_ID_KEY: VIEW_ID,
                TARGET_LAYOUT_KEY: PAGE,
            },
        )
        _stamp(session, "tag")
        _add_view(session)
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["healthy"], 1)

    def test_repeat_run_still_zero_write(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID, TYPE_CATEGORY_KEY: "PT"},
        )
        _stamp(session, "tag")
        before = _snapshot(session)
        first = _run(session)
        second = _run(session)
        self.assertTrue(first.ok and second.ok)
        self.assertEqual(session._object_meta, before["objects"])
        self.assertEqual(session.get_object_user_text("tag", TYPE_CATEGORY_KEY), "PT")


if __name__ == "__main__":
    unittest.main()
