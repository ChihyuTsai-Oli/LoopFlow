# -*- coding: utf-8 -*-
"""D05 TAG-O：檢查 Tag 活著或斷連；過期塗橘寫 !，斷連塗紅寫 ?。"""
from __future__ import annotations

import io
import sys
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
from loopflow.features.health.tag_o import (
    COLOR_BROK,
    COLOR_OK,
    COLOR_RULE,
    COLOR_WARN,
    PANEL_TITLE,
    UNASSIGNED_PAGE,
    run_tag_o,
)
from loopflow.foundation.usertext import SPACE_FRAME_DISPLAY_KEY
from loopflow.features.health.appearance import COLOR_BROKEN_RGB, COLOR_STALE_RGB
from loopflow.features.infuser.keys import (
    BROKEN_DISPLAY,
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ITEM_CATEGORY_KEY,
    ITEM_CODE_KEY,
    ITEM_NAME_KEY,
    MISSING_DISPLAY,
    SHEET_CODE_KEY,
    SHEET_REF_KEY,
    STALE_DISPLAY,
    TYPE_CATEGORY_KEY,
    TYPE_DISPLAY_NAME_KEY,
    TYPE_SEQUENCE_KEY,
)
from loopflow.features.sheet.keys import SHEET_ID_KEY
from loopflow.features.sheet.metadata import write_sheet_metadata
from loopflow.features.tagger.keys import (
    HEALTH_STATE_KEY,
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
    PROJECT_ID,
    SHEET_ID,
    TARGET_SHEET_ID,
    VIEW_ID,
    _add_block,
    _add_live_source,
    _catalog,
    _object_row,
    _payload,
    _session,
    _snapshot,
)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from project_fixture import bind_project, read_project_config, registry_dir  # noqa: E402

MISSING = "ffffffff-ffff-4fff-8fff-ffffffffffff"


def _filled_height(**extra):
    fields = {
        SOURCE_OBJECT_ID_KEY: OBJECT_ID,
        ELEVATION_BASIS_KEY: "CH",
        ELEVATION_DISPLAY_KEY: "000",
        TYPE_CATEGORY_KEY: "PT",
        TYPE_SEQUENCE_KEY: "01",
        TYPE_DISPLAY_NAME_KEY: "Paint",
    }
    fields.update(extra)
    return fields


def _filled_item(**extra):
    fields = {
        SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1",
        ITEM_CATEGORY_KEY: "FF",
        ITEM_CODE_KEY: "01",
        ITEM_NAME_KEY: "Chair-1",
    }
    fields.update(extra)
    return fields


def _filled_index(**extra):
    fields = {
        TARGET_VIEW_ID_KEY: VIEW_ID,
        TARGET_LAYOUT_KEY: PAGE,
        SHEET_CODE_KEY: "IN",
        SHEET_REF_KEY: "201",
    }
    fields.update(extra)
    return fields


def _panel_body(lines):
    return "\n".join(row[0] for row in lines)


def _panel_colors(lines, needle):
    return [row[1] for row in lines if needle in row[0]]


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
    def test_missing_schema_is_filled_and_continues(self):
        session = _session(write_config=False)
        root = Path(session.document_path()).parent
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(read_project_config(root)["schema_id"], "loopflow.project")

    def test_no_layout_pages_zero_write(self):
        session = MemorySession()
        bind_project(session, project_id=PROJECT_ID)
        result = _run(session)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("missing_layout_page",))

    def test_corrupt_official_stops_and_does_not_write(self):
        session = _session()
        root = Path(session.document_path()).parent
        folder = registry_dir(root, PROJECT_ID)
        (folder / "Project_Registry.json").write_text("{not json", encoding="utf-8")
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
        )
        before = _snapshot(session)
        result = run_tag_o(session, catalog=_catalog())
        self.assertFalse(result.ok)
        self.assertEqual(session._object_meta, before["objects"])


class HealthTests(unittest.TestCase):
    def test_healthy_bound_and_synced_tag(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
        )
        _stamp(session, "tag")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["healthy"], 1)
        self.assertEqual(result.details["counts"]["scanned"], 1)
        self.assertFalse(result.warnings)
        self.assertEqual(
            session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), "Paint"
        )
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("[正常]", body)
        state = session.get_view_state("tag")
        self.assertTrue(state.color_by_layer)
        self.assertIn("塗橘", result.message)

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
        self.assertEqual(
            session.get_object_user_text("tag", TYPE_CATEGORY_KEY), BROKEN_DISPLAY
        )
        state = session.get_view_state("tag")
        self.assertEqual(state.color, COLOR_BROKEN_RGB)
        self.assertFalse(state.color_by_layer)

    def test_live_model_is_not_orphaned(self):
        session = _session()
        _add_live_source(session)
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
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
            user_text=_filled_height(),
        )
        _stamp(session, "tag", revision=1)
        result = _run(session, registry=_payload(revision=3))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["stale"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        self.assertEqual(
            session.get_object_user_text("tag", TYPE_CATEGORY_KEY), STALE_DISPLAY
        )
        state = session.get_view_state("tag")
        self.assertEqual(state.color, COLOR_STALE_RGB)

    def test_never_infused_bound_tag_is_stale(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
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
            user_text=_filled_item(),
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

    def test_item_deleted_instance_is_orphaned(self):
        session = _session()
        session.add_object("chair", name="Chair", layer="M3D::FF")
        session.set_block("chair", (1, 0, 0), name="FF-01__Chair-1")
        _add_block(
            session,
            "tag",
            "TAG_ITEM",
            user_text=_filled_item(lf_source_object_id="chair"),
        )
        _stamp(session, "tag")
        session.delete_object("chair")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["orphaned"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        self.assertEqual(
            session.get_object_user_text("tag", ITEM_NAME_KEY), BROKEN_DISPLAY
        )
        state = session.get_view_state("tag")
        self.assertEqual(state.color, COLOR_BROKEN_RGB)

    def test_item_renamed_instance_is_stale_until_infuser(self):
        session = _session()
        session.add_object("chair", name="Chair", layer="M3D::FF")
        session.set_block("chair", (1, 0, 0), name="FF-01__Chair-2")
        _add_block(
            session,
            "tag",
            "TAG_ITEM",
            user_text=_filled_item(lf_source_object_id="chair"),
        )
        _stamp(session, "tag")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["stale"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        self.assertEqual(
            session.get_object_user_text("tag", ITEM_NAME_KEY), STALE_DISPLAY
        )
        state = session.get_view_state("tag")
        self.assertEqual(state.color, COLOR_STALE_RGB)

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
        self.assertIsNone(session.get_object_user_text("tag", TYPE_CATEGORY_KEY))
        state = session.get_view_state("tag")
        self.assertTrue(state.color_by_layer)
        self.assertNotEqual(state.color, COLOR_BROKEN_RGB)

    def test_unknown_block_is_ignored(self):
        session = _session()
        _add_block(session, "tag", "Random_Block")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertNotIn("unchecked", result.warnings or ())
        self.assertEqual(result.details["counts"]["unchecked"], 0)
        self.assertEqual(result.details["counts"]["scanned"], 0)
        self.assertEqual(result.details["issues"], ())

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
            user_text=_filled_height(),
        )
        _stamp(session, "here")
        _add_block(
            session,
            "there",
            "TAG_ITEM",
            page=OTHER,
            user_text=_filled_item(),
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
        self.assertEqual(result.details["counts"]["missing_target"], 1)

    def test_index_healthy_with_target_layout(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text=_filled_index(),
        )
        _stamp(session, "tag")
        _add_view(session)
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["healthy"], 1)

    def test_index_stale_when_sheet_code_changed(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text=_filled_index(),
        )
        _stamp(session, "tag")
        _add_view(session)
        write_sheet_metadata(
            session,
            SHEET_ID,
            {
                "drawing_no": "IN 301",
                "drawing_name": "立面",
                "series": "IN",
                "sequence": "301",
                "page_position": 1,
            },
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["stale"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("[過期]", body)
        colors = _panel_colors(result.details["panel_lines"], "[過期]")
        self.assertEqual(colors, [COLOR_WARN])
        self.assertEqual(
            session.get_object_user_text("tag", SHEET_CODE_KEY), STALE_DISPLAY
        )
        state = session.get_view_state("tag")
        self.assertEqual(state.color, COLOR_STALE_RGB)
        self.assertFalse(state.color_by_layer)

    def test_index_missing_target_when_layout_gone(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text=_filled_index(
                **{
                    TARGET_LAYOUT_KEY: OTHER,
                    SHEET_CODE_KEY: "IN",
                    SHEET_REF_KEY: "101.01",
                }
            ),
        )
        _stamp(session, "tag")
        session.add_object("other_frame", name="TargetFrame", layer="M2D")
        session.set_block("other_frame", (0, 0, 0), name="Sample_Frame")
        session.set_object_user_text("other_frame", SHEET_ID_KEY, TARGET_SHEET_ID)
        session.add_object_to_layout_page(OTHER, "other_frame")
        session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("view", VIEW_ID_KEY, VIEW_ID)
        session.set_bbox("view", (0, 0, 0), (100, 100, 0))
        session.set_layout_details(
            (
                {
                    "layout": PAGE,
                    "page_number": 1,
                    "detail_id": "dv-a",
                    "dv_name": "A",
                },
                {
                    "layout": OTHER,
                    "page_number": 2,
                    "detail_id": "dv-b",
                    "dv_name": "B",
                },
            )
        )
        session.set_detail_model_point("dv-a", (50, 50, 0))
        session.set_detail_model_point("dv-b", (50, 50, 0))
        session.set_layout_pages([PAGE])
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["missing_target"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        self.assertEqual(result.details["counts"]["stale"], 0)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("[斷連]", body)
        colors = _panel_colors(result.details["panel_lines"], "[斷連]")
        self.assertEqual(colors, [COLOR_BROK])
        self.assertEqual(
            session.get_object_user_text("tag", SHEET_CODE_KEY), BROKEN_DISPLAY
        )
        state = session.get_view_state("tag")
        self.assertEqual(state.color, COLOR_BROKEN_RGB)
        self.assertFalse(state.color_by_layer)

    def test_index_missing_target_when_detail_gone(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text=_filled_index(
                **{
                    TARGET_LAYOUT_KEY: OTHER,
                    SHEET_CODE_KEY: "IN",
                    SHEET_REF_KEY: "101.01",
                }
            ),
        )
        _stamp(session, "tag")
        session.add_object("other_frame", name="TargetFrame", layer="M2D")
        session.set_block("other_frame", (0, 0, 0), name="Sample_Frame")
        session.set_object_user_text("other_frame", SHEET_ID_KEY, TARGET_SHEET_ID)
        session.add_object_to_layout_page(OTHER, "other_frame")
        session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("view", VIEW_ID_KEY, VIEW_ID)
        session.set_bbox("view", (0, 0, 0), (100, 100, 0))
        session.set_layout_details(
            (
                {
                    "layout": PAGE,
                    "page_number": 1,
                    "detail_id": "dv-a",
                    "dv_name": "A",
                },
            )
        )
        session.set_detail_model_point("dv-a", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["missing_target"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("[斷連]", body)
        self.assertEqual(
            session.get_object_user_text("tag", SHEET_REF_KEY), BROKEN_DISPLAY
        )

    def test_repeat_run_still_zero_write(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID, TYPE_CATEGORY_KEY: "PT"},
        )
        _stamp(session, "tag")
        first = _run(session)
        second = _run(session)
        self.assertTrue(first.ok and second.ok)
        self.assertEqual(session.get_object_user_text("tag", TYPE_CATEGORY_KEY), "PT")

    def test_infused_dash_still_disconnected(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(
                **{
                    ELEVATION_BASIS_KEY: MISSING_DISPLAY,
                    ELEVATION_DISPLAY_KEY: MISSING_DISPLAY,
                    TYPE_CATEGORY_KEY: MISSING_DISPLAY,
                    TYPE_SEQUENCE_KEY: MISSING_DISPLAY,
                    TYPE_DISPLAY_NAME_KEY: MISSING_DISPLAY,
                }
            ),
        )
        _stamp(session, "tag")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["stale"], 1)
        self.assertEqual(result.details["counts"]["healthy"], 0)

    def test_unassigned_paper_tag_is_scanned(self):
        session = _session()
        session.add_object("loose", name="TAG_HEIGHT_GRAB", layer="M2D::Tags")
        session.set_block("loose", (0, 0, 0), name="TAG_HEIGHT_GRAB")
        session.add_unassigned_paper_object("loose")
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["unbound"], 1)
        self.assertEqual(result.details["issues"][0]["page_name"], UNASSIGNED_PAGE)


class PanelTests(unittest.TestCase):
    def test_panel_omits_unbound_tags(self):
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB")
        captured = []
        result = _run(session, show_panel=captured.append)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(result.details["counts"]["unbound"], 1)
        lines = result.details["panel_lines"]
        self.assertEqual(captured, [lines])
        self.assertEqual(lines[0][0], PANEL_TITLE)
        body = _panel_body(lines)
        self.assertNotIn("[缺來源]", body)
        self.assertNotIn("TAG_HEIGHT_GRAB", body)

    def test_panel_lists_orphaned_as_broken(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: MISSING},
        )
        _stamp(session, "tag")
        result = _run(session)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("[斷連]", body)
        colors = _panel_colors(result.details["panel_lines"], "[斷連]")
        self.assertEqual(colors, [COLOR_BROK])

    def test_panel_lists_stale_in_orange(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
        )
        _stamp(session, "tag", revision=1)
        result = _run(session, registry=_payload(revision=3))
        self.assertTrue(result.ok, result.message)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("[過期]", body)
        colors = _panel_colors(result.details["panel_lines"], "[過期]")
        self.assertEqual(colors, [COLOR_WARN])

    def test_panel_marks_locked_and_all_ok_green(self):
        session = _session()
        _add_block(
            session,
            "bad",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: MISSING, LOCK_STATE_KEY: "x"},
        )
        _stamp(session, "bad")
        result = _run(session)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("（鎖定）", body)

        clean = _session()
        _add_block(
            clean,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text=_filled_height(),
        )
        _stamp(clean, "tag")
        ok_result = _run(clean)
        body = _panel_body(ok_result.details["panel_lines"])
        self.assertIn("[正常]", body)
        greens = [
            row[0]
            for row in ok_result.details["panel_lines"]
            if row[1] == COLOR_OK
        ]
        self.assertTrue(any("[正常]" in text for text in greens))
        self.assertNotIn("全部 Tag 來源正常", body)

    def test_uncovered_space_listed(self):
        session = _session()
        session.add_object("room", name="廊道框", layer="M3D::_Data::Space_Boundaries")
        session.set_object_user_text("room", SPACE_FRAME_DISPLAY_KEY, "廊道")
        result = _run(session)
        self.assertIn("uncovered_space", result.warnings)
        self.assertEqual(result.details["space_missing"], ("廊道",))
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("廊道", body)

    def test_finish_tag_covers_space(self):
        session = _session()
        session.add_object("room", name="廊道框", layer="M3D::_Data::Space_Boundaries")
        session.set_object_user_text("room", SPACE_FRAME_DISPLAY_KEY, "廊道")
        payload = _payload(objects=[_object_row(space_display="廊道", space_id="hall")])
        _add_block(
            session,
            "tag",
            "TAG_FINISH_GRAB",
            user_text=_filled_height(),
        )
        _stamp(session, "tag")
        result = _run(session, registry=payload)
        self.assertNotIn("uncovered_space", result.warnings or ())
        self.assertEqual(result.details["space_missing"], ())
        greens = [
            row[0]
            for row in result.details["panel_lines"]
            if row[1] == COLOR_OK
        ]
        self.assertTrue(any("Finish Tag" in text for text in greens))

    def test_panel_paints_broken_objects_red(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: MISSING},
        )
        result = _run(session)
        after = session.get_view_state("tag")
        self.assertTrue(result.ok)
        self.assertEqual(after.color, COLOR_BROKEN_RGB)
        self.assertFalse(after.color_by_layer)
        self.assertEqual(
            session.get_object_user_text("tag", TYPE_CATEGORY_KEY), BROKEN_DISPLAY
        )

    def test_panel_follows_layout_page_order(self):
        session = _session()
        session.set_layout_pages(["Z__1", "A__1"])
        session.set_current_layout_page("Z__1")
        _add_block(
            session,
            "later",
            "TAG_HEIGHT_GRAB",
            page="A__1",
            user_text=_filled_height(),
        )
        _add_block(
            session,
            "first",
            "TAG_ITEM",
            page="Z__1",
            user_text=_filled_item(),
        )
        _stamp(session, "later")
        _stamp(session, "first")
        result = _run(session)
        body = _panel_body(result.details["panel_lines"])
        self.assertLess(body.index("Z__1"), body.index("A__1"))
        self.assertIn("已掃描 2 個 Tag", body)
        self.assertTrue(
            any(row[1] == COLOR_RULE for row in result.details["panel_lines"])
        )

    def test_empty_scan_does_not_claim_all_ok(self):
        session = _session()
        result = _run(session)
        body = _panel_body(result.details["panel_lines"])
        self.assertIn("已掃描 0 個 Tag", body)
        self.assertIn("沒有掃到可檢查的 Tag", body)
        self.assertNotIn("全部 Tag 來源正常", body)

    def test_issue_rows_include_tag_id_for_zoom(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: MISSING},
        )
        _stamp(session, "tag")
        result = _run(session)
        clickable = [
            row for row in result.details["panel_lines"] if len(row) >= 4 and row[2]
        ]
        self.assertEqual(clickable[0][2], "tag")
        self.assertEqual(clickable[0][3], PAGE)
        session.zoom_to_layout_object(PAGE, "tag")
        self.assertEqual(
            session.zoomed_layout_objects[-1],
            {"layout": PAGE, "object_id": "tag"},
        )
        self.assertEqual(session.current_layout_page_name(), PAGE)


if __name__ == "__main__":
    unittest.main()
