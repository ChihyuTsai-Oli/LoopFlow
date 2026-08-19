# -*- coding: utf-8 -*-
"""D06 Infuser Part：當頁注入顯示欄；鎖定／門窗／人工欄零覆寫。"""
from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.bootstrap import run_command
from loopflow.command_catalog import get_command
from loopflow.features.infuser.keys import (
    DETAIL_NO_KEY,
    DW_ID_KEY,
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ITEM_CATEGORY_KEY,
    ITEM_CODE_KEY,
    ITEM_NAME_KEY,
    LEGACY_DISPLAY_KEYS,
    MISSING_DISPLAY,
    REMARKS_MANUAL_KEY,
    SHEET_CODE_KEY,
    SHEET_REF_KEY,
    TYPE_CATEGORY_KEY,
    TYPE_DISPLAY_NAME_KEY,
    TYPE_SEQUENCE_KEY,
)
from loopflow.features.infuser.part import run_infuser_part
from loopflow.features.infuser.reader import load_published_registry
from loopflow.features.sheet.keys import DRAWING_NAME_KEY, DRAWING_NO_KEY, SCALE_KEY, SHEET_ID_KEY
from loopflow.features.sheet.metadata import write_sheet_metadata
from loopflow.features.tagger.keys import (
    HOST_SHEET_ID_KEY,
    LAST_SYNCED_REVISION_KEY,
    LOCK_STATE_KEY,
    SOURCE_BLOCK_NAME_KEY,
    SOURCE_OBJECT_ID_KEY,
    TARGET_LAYOUT_KEY,
    TARGET_SHEET_ID_KEY,
    TARGET_VIEW_ID_KEY,
)
from loopflow.features.tagger.templates import load_tag_templates
from loopflow.features.view.keys import SCHEMA_ID_KEY, VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.foundation.usertext import (
    ELEVATION_BASIS_KEY as MODEL_ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY as MODEL_ELEVATION_DISPLAY_KEY,
    OBJECT_ID_KEY,
    TYPE_CATEGORY_KEY as MODEL_TYPE_CATEGORY_KEY,
    TYPE_ID_KEY,
    TYPE_SEQUENCE_KEY as MODEL_TYPE_SEQUENCE_KEY,
)
from loopflow.platform.rhino.memory import MemorySession

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
OBJECT_ID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
SHEET_ID = "cccccccc-cccc-4ccc-8ccc-cccccccccccc"
TARGET_SHEET_ID = "dddddddd-dddd-4ddd-8ddd-dddddddddddd"
VIEW_ID = "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
PAGE = "IN__201__立面"
OTHER = "IN__202__平面"


def _catalog():
    loaded = load_tag_templates()
    if not loaded.ok:
        raise AssertionError(loaded.message)
    return loaded.details["catalog"]


def _type_row():
    return {
        "type_id": "PT-01",
        "type_category": "PT",
        "type_sequence": "01",
        "type_display_name": "Paint",
        "layer_path": "M3D::01_FIN_裝修::PT.油漆",
        "estimation_unit": "m2",
        "measurement_rule": "AREA_WD",
        "elevation_basis": "CH",
        "construction_default": "new",
        "remarks_default": None,
    }


def _payload(objects=None, revision=2):
    return {
        "schema_id": "loopflow.registry",
        "schema_version": 1,
        "project_id": PROJECT_ID,
        "registry_revision": revision,
        "published_at": "2026-08-19T00:00:00Z",
        "model_unit": "Centimeters",
        "types": [_type_row()],
        "spaces": [{"space_id": "EXT", "level_id": None, "space_display": "EXT"}],
        "objects": objects if objects is not None else [_object_row()],
        "extension": {},
    }


def _object_row(**overrides):
    row = {
        "object_id": OBJECT_ID,
        "type_id": "PT-01",
        "type_category": "PT",
        "type_sequence": "01",
        "type_display_name": "Paint",
        "construction_status": "new",
        "space_id": "EXT",
        "space_display": "EXT",
        "elevation_basis": "CH",
        "elevation_value": 0,
        "elevation_display": "000",
        "remarks": None,
        "data_revision": 1,
    }
    row.update(overrides)
    return row


def _session() -> MemorySession:
    session = MemorySession(
        document_text={
            "lf_project_id": PROJECT_ID,
            "lf_schema_id": "loopflow.project",
            "lf_schema_version": "1",
        }
    )
    session.set_layout_pages([PAGE, OTHER])
    session.set_current_layout_page(PAGE)
    session.add_object("frame", name="Frame", layer="M2D")
    session.set_block("frame", (0, 0, 0), name="Sample_Frame")
    session.set_object_user_text("frame", SHEET_ID_KEY, SHEET_ID)
    session.set_object_user_text("frame", DRAWING_NO_KEY, "IN 201")
    session.set_object_user_text("frame", DRAWING_NAME_KEY, "立面")
    session.set_object_user_text("frame", SCALE_KEY, "1:50")
    session.add_object_to_layout_page(PAGE, "frame")
    write_sheet_metadata(
        session,
        SHEET_ID,
        {
            "drawing_no": "IN 201",
            "drawing_name": "立面",
            "series": "IN",
            "sequence": "201",
            "page_position": 1,
        },
    )
    write_sheet_metadata(
        session,
        TARGET_SHEET_ID,
        {
            "drawing_no": "IN 101.01",
            "drawing_name": "平面",
            "series": "IN",
            "sequence": "101.01",
            "page_position": 2,
        },
    )
    session.set_document_modified(False)
    return session


def _add_live_source(session, object_id=OBJECT_ID, **user_text):
    rhino_id = "src-" + object_id[:8]
    session.add_object(rhino_id, name="wall", layer="M3D::01_FIN")
    defaults = {
        OBJECT_ID_KEY: object_id,
        TYPE_ID_KEY: "PT-01",
        MODEL_TYPE_CATEGORY_KEY: "PT",
        MODEL_TYPE_SEQUENCE_KEY: "01",
        MODEL_ELEVATION_BASIS_KEY: "CH",
        MODEL_ELEVATION_DISPLAY_KEY: "320",
    }
    defaults.update(user_text)
    for key, value in defaults.items():
        session.set_object_user_text(rhino_id, key, value)
    return rhino_id


def _add_block(session, object_id, block_name, page=PAGE, user_text=None):
    session.add_object(object_id, name=block_name, layer="M2D::Tags")
    session.set_block(object_id, (0, 0, 0), name=block_name)
    for key, value in dict(user_text or {}).items():
        session.set_object_user_text(object_id, key, value)
    session.add_object_to_layout_page(page, object_id)


def _snapshot(session: MemorySession) -> dict:
    return {
        "document": dict(session._document_text),
        "modified": session.document_modified(),
        "objects": copy.deepcopy(session._object_meta),
    }


def _run(session, **kwargs):
    kwargs.setdefault("catalog", _catalog())
    kwargs.setdefault("registry", _payload())
    return run_infuser_part(session, **kwargs)


class CatalogTests(unittest.TestCase):
    def test_part_is_ready_and_all_is_not(self):
        part = get_command("LF_Infuser_Part")
        self.assertEqual(part["status"], "ready")
        self.assertEqual(part["task"], "D06")
        self.assertEqual(get_command("LF_Infuser_All")["status"], "not_implemented")
        with redirect_stdout(io.StringIO()):
            result = run_command("LF_Infuser_All")
        self.assertEqual(result.status, "not_implemented")


class GuardTests(unittest.TestCase):
    def test_model_space_zero_write(self):
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        session.set_layout_active(False)
        before = _snapshot(session)
        result = _run(session)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("not_on_layout",))
        self.assertEqual(session._object_meta, before["objects"])

    def test_missing_schema_zero_write(self):
        session = _session()
        session._document_text.pop("lf_schema_id", None)
        session._document_text.pop("lf_schema_version", None)
        _add_block(session, "tag", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        before = _snapshot(session)
        result = _run(session)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("missing_document_schema",))
        self.assertEqual(
            session.get_object_user_text("tag", ELEVATION_BASIS_KEY),
            before["objects"]["tag"]["user_text"].get(ELEVATION_BASIS_KEY),
        )


class InjectTests(unittest.TestCase):
    def test_height_writes_registry_fields_and_stamp(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={
                SOURCE_OBJECT_ID_KEY: OBJECT_ID,
                REMARKS_MANUAL_KEY: "手寫備註",
            },
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_BASIS_KEY), "CH")
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_DISPLAY_KEY), "000")
        self.assertEqual(session.get_object_user_text("tag", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("tag", TYPE_SEQUENCE_KEY), "01")
        self.assertEqual(session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), "Paint")
        self.assertEqual(session.get_object_user_text("tag", REMARKS_MANUAL_KEY), "手寫備註")
        self.assertEqual(session.get_object_user_text("tag", HOST_SHEET_ID_KEY), SHEET_ID)
        self.assertEqual(session.get_object_user_text("tag", LAST_SYNCED_REVISION_KEY), "2")
        for key in LEGACY_DISPLAY_KEYS:
            self.assertIsNone(session.get_object_user_text("tag", key))

    def test_finish_does_not_write_elevation(self):
        session = _session()
        _add_block(session, "tag", "TAG_FINISH_LASER", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), "Paint")
        self.assertIsNone(session.get_object_user_text("tag", ELEVATION_BASIS_KEY))
        self.assertIsNone(session.get_object_user_text("tag", ELEVATION_DISPLAY_KEY))

    def test_item_parses_block_name(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_ITEM",
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", ITEM_CATEGORY_KEY), "FF")
        self.assertEqual(session.get_object_user_text("tag", ITEM_CODE_KEY), "01")
        self.assertEqual(session.get_object_user_text("tag", ITEM_NAME_KEY), "Chair-1")

    def test_item_bad_name_writes_dash(self):
        session = _session()
        _add_block(session, "tag", "TAG_ITEM", user_text={SOURCE_BLOCK_NAME_KEY: "Chair"})
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertIn("invalid_block_name", result.warnings)
        self.assertEqual(session.get_object_user_text("tag", ITEM_CATEGORY_KEY), MISSING_DISPLAY)

    def test_index_from_target_sheet_id(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={
                TARGET_SHEET_ID_KEY: TARGET_SHEET_ID,
                DETAIL_NO_KEY: "A",
            },
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "IN")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "101.01")
        self.assertEqual(session.get_object_user_text("tag", DETAIL_NO_KEY), "A")

    def test_index_from_target_view(self):
        session = _session()
        _add_block(session, "tag", "TAG_ELEV_1", user_text={TARGET_VIEW_ID_KEY: VIEW_ID})
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
                    "layout": OTHER,
                    "page_number": 2,
                    "detail_id": "dv-1",
                    "dv_name": "A-A",
                },
            )
        )
        session.set_detail_model_point("dv-1", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "IN")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "101.01")

    def test_height_matches_uppercase_and_braced_uuid(self):
        session = _session()
        _add_block(
            session,
            "upper",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID.upper()},
        )
        _add_block(
            session,
            "braced",
            "TAG_FINISH_LASER",
            user_text={SOURCE_OBJECT_ID_KEY: "{%s}" % OBJECT_ID},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("upper", TYPE_DISPLAY_NAME_KEY), "Paint")
        self.assertEqual(session.get_object_user_text("braced", TYPE_DISPLAY_NAME_KEY), "Paint")

    def test_height_reads_live_object_when_not_in_registry(self):
        session = _session()
        _add_live_source(session)
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        result = _run(session, registry=_payload(objects=[]))
        self.assertTrue(result.ok, result.message)
        self.assertIn("used_live_object", result.warnings)
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_BASIS_KEY), "CH")
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_DISPLAY_KEY), "320")
        self.assertEqual(session.get_object_user_text("tag", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("tag", TYPE_SEQUENCE_KEY), "01")
        self.assertEqual(session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), "Paint")

    def test_index_from_uppercase_target_view(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_ELEV_1",
            user_text={TARGET_VIEW_ID_KEY: VIEW_ID.upper()},
        )
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
                    "layout": OTHER,
                    "page_number": 2,
                    "detail_id": "dv-1",
                    "dv_name": "A-A",
                },
            )
        )
        session.set_detail_model_point("dv-1", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "IN")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "101.01")

    def test_height_prefers_live_object_with_type_fields(self):
        session = _session()
        session.add_object("curve", name="section-2d", layer="LoopFlow_Extract")
        session.set_object_user_text("curve", OBJECT_ID_KEY, OBJECT_ID)
        _add_live_source(session)
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_LASER",
            user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID},
        )
        result = _run(session, registry=_payload(objects=[]))
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_DISPLAY_KEY), "320")
        self.assertEqual(session.get_object_user_text("tag", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), "Paint")

    def test_index_from_target_view_page_name_without_frame(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={TARGET_VIEW_ID_KEY: VIEW_ID},
        )
        session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("view", VIEW_ID_KEY, VIEW_ID)
        session.set_bbox("view", (0, 0, 0), (100, 100, 0))
        session.set_layout_details(
            (
                {
                    "layout": OTHER,
                    "page_number": 2,
                    "detail_id": "dv-1",
                    "dv_name": "A-A",
                },
            )
        )
        session.set_detail_model_point("dv-1", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "IN")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "202")

    def test_index_prefers_target_page_when_host_detail_also_hits_view(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={
                TARGET_VIEW_ID_KEY: VIEW_ID,
                DETAIL_NO_KEY: "A",
            },
        )
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
                    "detail_id": "dv-host",
                    "dv_name": "Host",
                },
                {
                    "layout": OTHER,
                    "page_number": 2,
                    "detail_id": "dv-1",
                    "dv_name": "A-A",
                },
            )
        )
        session.set_detail_model_point("dv-host", (50, 50, 0))
        session.set_detail_model_point("dv-1", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertNotIn("ambiguous", result.warnings or ())
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "IN")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "101.01")
        self.assertEqual(session.get_object_user_text("tag", DETAIL_NO_KEY), "A")

    def test_index_does_not_write_detail_no(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_ELEV_1",
            user_text={TARGET_SHEET_ID_KEY: TARGET_SHEET_ID},
        )
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "101.01")
        self.assertIsNone(session.get_object_user_text("tag", DETAIL_NO_KEY))

    def test_index_from_dc_page_name_with_letter_suffix(self):
        session = _session()
        page = "DC__201.a2"
        session.set_layout_pages([PAGE, page])
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={TARGET_VIEW_ID_KEY: VIEW_ID},
        )
        session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("view", VIEW_ID_KEY, VIEW_ID)
        session.set_bbox("view", (0, 0, 0), (100, 100, 0))
        session.set_layout_details(
            (
                {
                    "layout": page,
                    "page_number": 2,
                    "detail_id": "dv-1",
                    "dv_name": "A-A",
                },
            )
        )
        session.set_detail_model_point("dv-1", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "DC")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "201.a2")

    def test_index_from_dc_page_name_ending_with_letter(self):
        session = _session()
        page = "DC__201.2a"
        session.set_layout_pages([PAGE, page])
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            user_text={TARGET_VIEW_ID_KEY: VIEW_ID},
        )
        session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("view", VIEW_ID_KEY, VIEW_ID)
        session.set_bbox("view", (0, 0, 0), (100, 100, 0))
        session.set_layout_details(
            (
                {
                    "layout": page,
                    "page_number": 2,
                    "detail_id": "dv-1",
                    "dv_name": "A-A",
                },
            )
        )
        session.set_detail_model_point("dv-1", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "DC")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "201.2a")

    def test_index_falls_back_to_host_when_other_hits_are_unnumbered(self):
        host = "DC__201.a2"
        cover = "封面"
        session = _session()
        session.set_layout_pages([host, cover, PAGE, OTHER])
        session.set_current_layout_page(host)
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            page=host,
            user_text={TARGET_VIEW_ID_KEY: VIEW_ID},
        )
        session.add_object("view", name="A-A", layer="LoopFlow::Anchor_Frame")
        session.set_object_user_text("view", SCHEMA_ID_KEY, VIEW_SCHEMA_ID)
        session.set_object_user_text("view", VIEW_ID_KEY, VIEW_ID)
        session.set_bbox("view", (0, 0, 0), (100, 100, 0))
        session.set_layout_details(
            (
                {
                    "layout": host,
                    "page_number": 1,
                    "detail_id": "dv-host",
                    "dv_name": "Host",
                },
                {
                    "layout": cover,
                    "page_number": 2,
                    "detail_id": "dv-cover",
                    "dv_name": "Cover",
                },
            )
        )
        session.set_detail_model_point("dv-host", (50, 50, 0))
        session.set_detail_model_point("dv-cover", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertNotIn("missing_sheet", result.warnings or ())
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "DC")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "201.a2")

    def test_index_uses_stored_layout_when_two_sheets_hit_view(self):
        index_page = "目錄"
        session = _session()
        session.set_layout_pages([PAGE, OTHER, index_page])
        session.set_current_layout_page(index_page)
        _add_block(
            session,
            "tag",
            "TAG_SECTION_DETAIL",
            page=index_page,
            user_text={
                TARGET_VIEW_ID_KEY: VIEW_ID,
                TARGET_LAYOUT_KEY: OTHER,
            },
        )
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
                {
                    "layout": index_page,
                    "page_number": 3,
                    "detail_id": "dv-host",
                    "dv_name": "Host",
                },
            )
        )
        session.set_detail_model_point("dv-a", (50, 50, 0))
        session.set_detail_model_point("dv-b", (50, 50, 0))
        session.set_detail_model_point("dv-host", (50, 50, 0))
        result = _run(session)
        self.assertTrue(result.ok, result.message)
        self.assertNotIn("ambiguous", result.warnings or ())
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "IN")
        self.assertEqual(session.get_object_user_text("tag", SHEET_REF_KEY), "101.01")

    def test_other_page_not_touched(self):
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
        self.assertEqual(session.get_object_user_text("here", TYPE_CATEGORY_KEY), "PT")
        self.assertIsNone(session.get_object_user_text("there", TYPE_CATEGORY_KEY))


class SkipTests(unittest.TestCase):
    def test_locked_tag_not_overwritten(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={
                SOURCE_OBJECT_ID_KEY: OBJECT_ID,
                LOCK_STATE_KEY: "x",
                ELEVATION_BASIS_KEY: "OLD",
                REMARKS_MANUAL_KEY: "留著",
            },
        )
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertEqual(result.details["counts"]["skipped_locked"], 1)
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_BASIS_KEY), "OLD")
        self.assertEqual(session.get_object_user_text("tag", REMARKS_MANUAL_KEY), "留著")
        self.assertIsNone(session.get_object_user_text("tag", HOST_SHEET_ID_KEY))

    def test_tag_dw_not_overwritten(self):
        session = _session()
        _add_block(session, "tag", "TAG_DW", user_text={DW_ID_KEY: "D01"})
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertEqual(session.get_object_user_text("tag", DW_ID_KEY), "D01")
        self.assertIsNone(session.get_object_user_text("tag", HOST_SHEET_ID_KEY))

    def test_title_frame_scale_and_drawing_untouched(self):
        session = _session()
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertEqual(session.get_object_user_text("frame", SCALE_KEY), "1:50")
        self.assertEqual(session.get_object_user_text("frame", DRAWING_NO_KEY), "IN 201")
        self.assertEqual(session.get_object_user_text("frame", DRAWING_NAME_KEY), "立面")

    def test_elev_0_sheet_code_untouched(self):
        session = _session()
        _add_block(session, "tag", "TAG_ELEV_0", user_text={SHEET_CODE_KEY: "201"})
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertEqual(session.get_object_user_text("tag", SHEET_CODE_KEY), "201")
        self.assertIsNone(session.get_object_user_text("tag", HOST_SHEET_ID_KEY))

    def test_missing_source_writes_dash(self):
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB")
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertIn("missing_source", result.warnings)
        self.assertEqual(session.get_object_user_text("tag", ELEVATION_BASIS_KEY), MISSING_DISPLAY)
        self.assertEqual(session.get_object_user_text("tag", HOST_SHEET_ID_KEY), SHEET_ID)

    def test_orphaned_object_writes_dash(self):
        session = _session()
        _add_block(
            session,
            "tag",
            "TAG_HEIGHT_GRAB",
            user_text={SOURCE_OBJECT_ID_KEY: "ffffffff-ffff-4fff-8fff-ffffffffffff"},
        )
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertIn("orphaned", result.warnings)
        self.assertEqual(session.get_object_user_text("tag", TYPE_CATEGORY_KEY), MISSING_DISPLAY)

    def test_unknown_block_zero_write(self):
        session = _session()
        _add_block(session, "tag", "RANDOM_BLOCK")
        before = dict(session._object_meta["tag"]["user_text"])
        result = _run(session)
        self.assertTrue(result.ok)
        self.assertIn("unknown_template", result.warnings)
        self.assertEqual(session._object_meta["tag"]["user_text"], before)

    def test_ambiguous_duplicate_object_id(self):
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        payload = _payload(objects=[_object_row(), _object_row(type_display_name="Other")])
        result = _run(session, registry=payload)
        self.assertTrue(result.ok)
        self.assertIn("ambiguous", result.warnings)
        self.assertEqual(session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), MISSING_DISPLAY)


class RegistryFileTests(unittest.TestCase):
    def _workfiles(self):
        folder = Path(tempfile.mkdtemp())
        (folder / "exchange" / PROJECT_ID).mkdir(parents=True)
        return folder

    def test_uses_last_good_when_official_missing(self):
        root = self._workfiles()
        last_good = root / "exchange" / PROJECT_ID / "Project_Registry.last-good.json"
        last_good.write_text(json.dumps(_payload(revision=3), ensure_ascii=False), encoding="utf-8")
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        result = run_infuser_part(
            session,
            catalog=_catalog(),
            environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
        )
        self.assertTrue(result.ok, result.message)
        self.assertIn("used_last_good", result.warnings)
        self.assertEqual(session.get_object_user_text("tag", TYPE_DISPLAY_NAME_KEY), "Paint")
        self.assertEqual(session.get_object_user_text("tag", LAST_SYNCED_REVISION_KEY), "3")
        self.assertFalse((root / "exchange" / PROJECT_ID / "Project_Registry.json").exists())

    def test_corrupt_official_stops_and_does_not_write(self):
        root = self._workfiles()
        official = root / "exchange" / PROJECT_ID / "Project_Registry.json"
        official.write_text("{not json", encoding="utf-8")
        session = _session()
        _add_block(session, "tag", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        before = _snapshot(session)
        result = run_infuser_part(
            session,
            catalog=_catalog(),
            environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
        )
        self.assertFalse(result.ok)
        self.assertIsNone(session.get_object_user_text("tag", TYPE_CATEGORY_KEY))
        self.assertEqual(session._object_meta["tag"]["user_text"], before["objects"]["tag"]["user_text"])

    def test_missing_registry_item_still_injects(self):
        root = self._workfiles()
        session = _session()
        _add_block(
            session,
            "item",
            "TAG_ITEM",
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        _add_block(session, "height", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        result = run_infuser_part(
            session,
            catalog=_catalog(),
            environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
        )
        self.assertTrue(result.ok)
        self.assertIn("missing_registry", result.warnings)
        self.assertEqual(session.get_object_user_text("item", ITEM_NAME_KEY), "Chair-1")
        self.assertEqual(session.get_object_user_text("height", TYPE_CATEGORY_KEY), MISSING_DISPLAY)
        self.assertFalse((root / "exchange" / PROJECT_ID / "Project_Registry.json").exists())

    def test_missing_registry_height_reads_live_object(self):
        root = self._workfiles()
        session = _session()
        _add_live_source(session)
        _add_block(
            session,
            "item",
            "TAG_ITEM",
            user_text={SOURCE_BLOCK_NAME_KEY: "FF-01__Chair-1"},
        )
        _add_block(session, "height", "TAG_HEIGHT_GRAB", user_text={SOURCE_OBJECT_ID_KEY: OBJECT_ID})
        result = run_infuser_part(
            session,
            catalog=_catalog(),
            environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
        )
        self.assertTrue(result.ok, result.message)
        self.assertIn("missing_registry", result.warnings)
        self.assertEqual(session.get_object_user_text("item", ITEM_NAME_KEY), "Chair-1")
        self.assertEqual(session.get_object_user_text("height", TYPE_CATEGORY_KEY), "PT")
        self.assertEqual(session.get_object_user_text("height", ELEVATION_DISPLAY_KEY), "320")
        self.assertEqual(session.get_object_user_text("height", TYPE_DISPLAY_NAME_KEY), MISSING_DISPLAY)
        self.assertFalse((root / "exchange" / PROJECT_ID / "Project_Registry.json").exists())

    def test_reader_does_not_create_files(self):
        root = Path(tempfile.mkdtemp())
        result = load_published_registry(
            PROJECT_ID,
            environ={"LOOPFLOW_WORKFILES_ROOT": str(root)},
        )
        self.assertTrue(result.ok)
        self.assertIn("missing_registry", result.warnings)
        self.assertFalse((root / "exchange").exists())


if __name__ == "__main__":
    unittest.main()
