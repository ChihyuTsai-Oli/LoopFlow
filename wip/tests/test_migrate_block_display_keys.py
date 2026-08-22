# -*- coding: utf-8 -*-
"""D08：把圖塊舊顯示欄抄到 lf_* 後刪除。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.devtools.migrate_block_display_keys import (
    collect_steps,
    run_migrate_block_display_keys,
)
from loopflow.features.tagger.keys import (
    LOCK_CANONICAL_HINT,
    LOCK_LEGACY_HINT,
    LOCK_LEGACY_KEY,
    LOCK_STATE_KEY,
    LOCK_STATE_PREV_KEY,
)
from loopflow.platform.rhino.memory import MemorySession


def _block(session, object_id, name, **user_text):
    session.add_object(object_id, name=name, user_text=user_text)
    session.set_block(object_id, (0, 0, 0), name=name)


class MigrateBlockDisplayKeysTests(unittest.TestCase):
    def test_item_note_goes_to_item_name_not_type_name(self):
        session = MemorySession()
        _block(
            session,
            "item-1",
            "Tag_Item",
            **{
                "attr_note": "Chair-1",
                "attr_item_key": "FF",
                LOCK_LEGACY_KEY: "x",
            }
        )
        result = run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertTrue(result.ok)
        self.assertEqual(session.get_object_user_text("item-1", "lf_item_name"), "Chair-1")
        self.assertIsNone(session.get_object_user_text("item-1", "lf_type_display_name"))
        self.assertIsNone(session.get_object_user_text("item-1", "attr_note"))
        self.assertEqual(session.get_object_user_text("item-1", LOCK_STATE_KEY), "x")
        self.assertIsNone(session.get_object_user_text("item-1", LOCK_LEGACY_KEY))

    def test_height_note_goes_to_type_display_name(self):
        session = MemorySession()
        _block(session, "h-1", "Tag_Height_Grab", **{"attr_note": "石材", "attr_mat_key": "ST"})
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("h-1", "lf_type_display_name"), "石材")
        self.assertEqual(session.get_object_user_text("h-1", "lf_type_category"), "ST")
        self.assertIsNone(session.get_object_user_text("h-1", "attr_note"))

    def test_keeps_existing_canonical_and_copies_scale(self):
        session = MemorySession()
        _block(
            session,
            "frame-1",
            "Sample_Frame",
            **{
                "DWG_NO": "IN 101",
                "DWG_NAME": "舊名",
                "03-A3 Scale": "1:50",
                "lf_drawing_no": "IN 151.01",
                "lf_drawing_name": "地坪",
            }
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("frame-1", "lf_drawing_no"), "IN 151.01")
        self.assertEqual(session.get_object_user_text("frame-1", "lf_drawing_name"), "地坪")
        self.assertEqual(session.get_object_user_text("frame-1", "lf_scale"), "1:50")
        self.assertIsNone(session.get_object_user_text("frame-1", "DWG_NO"))
        self.assertIsNone(session.get_object_user_text("frame-1", "03-A3 Scale"))
        self.assertNotIn("DWG_NO", session.object_user_text_keys("frame-1"))

    def test_unknown_title_frame_still_migrates_drawing_keys(self):
        session = MemorySession()
        _block(
            session,
            "frame-x",
            "_Frame_A3_shop_drawing",
            **{"DWG_NO": "A 01", "03-A3 Scale": "1:100"},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("frame-x", "lf_drawing_no"), "A 01")
        self.assertEqual(session.get_object_user_text("frame-x", "lf_scale"), "1:100")
        self.assertIsNone(session.get_object_user_text("frame-x", "DWG_NO"))

    def test_cancel_is_zero_write(self):
        session = MemorySession()
        _block(session, "frame-1", "Sample_Frame", **{"DWG_NO": "IN 101", "03-A3 Scale": "1:50"})
        result = run_migrate_block_display_keys(session, confirm=lambda _lines: False)
        self.assertFalse(result.ok)
        self.assertEqual(session.get_object_user_text("frame-1", "DWG_NO"), "IN 101")
        self.assertIsNone(session.get_object_user_text("frame-1", "lf_scale"))

    def test_ignores_non_blocks_and_lock_hint(self):
        session = MemorySession()
        session.add_object("curve-1", user_text={"DWG_NO": "should stay"})
        _block(
            session,
            "elev-0",
            "TAG_ELEV_0",
            **{
                "Category": "201",
                LOCK_LEGACY_KEY: LOCK_LEGACY_HINT,
            }
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("curve-1", "DWG_NO"), "should stay")
        self.assertEqual(session.get_object_user_text("elev-0", "lf_sheet_code"), "201")
        self.assertIsNone(session.get_object_user_text("elev-0", LOCK_LEGACY_KEY))
        self.assertIsNone(session.get_object_user_text("elev-0", LOCK_STATE_KEY))
        self.assertEqual(collect_steps(session), [])

    def test_title_frame_drops_category_and_ref_without_copying(self):
        session = MemorySession()
        _block(
            session,
            "frame-1",
            "_Frame_A3_shop_drawing",
            **{
                "Category": "IN",
                "REF_ID": "201.01",
                "lf_drawing_no": "IN 201.01",
                "lf_drawing_name": "立面",
                "lf_scale": "1 : 100",
                "lf_sheet_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            }
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("frame-1", "lf_drawing_no"), "IN 201.01")
        self.assertEqual(session.get_object_user_text("frame-1", "lf_scale"), "1 : 100")
        self.assertIsNone(session.get_object_user_text("frame-1", "Category"))
        self.assertIsNone(session.get_object_user_text("frame-1", "REF_ID"))
        self.assertIsNone(session.get_object_user_text("frame-1", "lf_sheet_code"))
        self.assertIsNone(session.get_object_user_text("frame-1", "lf_sheet_ref"))

    def test_index_tag_still_copies_category(self):
        session = MemorySession()
        _block(
            session,
            "idx-1",
            "TAG_SECTION_DETAIL",
            **{"Category": "IN", "REF_ID": "201.01", "Detail_NO": "01"},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("idx-1", "lf_sheet_code"), "IN")
        self.assertEqual(session.get_object_user_text("idx-1", "lf_sheet_ref"), "201.01")
        self.assertEqual(session.get_object_user_text("idx-1", "lf_detail_no"), "01")
        self.assertIsNone(session.get_object_user_text("idx-1", "Category"))


    def test_lock_x_copied_to_canonical(self):
        session = MemorySession()
        _block(
            session,
            "h-1",
            "Tag_Height_Grab",
            **{LOCK_LEGACY_KEY: " X ", "attr_mat_key": "PT"},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("h-1", LOCK_STATE_KEY), "X")
        self.assertIsNone(session.get_object_user_text("h-1", LOCK_LEGACY_KEY))
        self.assertEqual(session.get_object_user_text("h-1", "lf_type_category"), "PT")

    def test_existing_lock_state_not_overwritten(self):
        session = MemorySession()
        _block(
            session,
            "h-1",
            "Tag_Height_Grab",
            **{LOCK_LEGACY_KEY: "x", LOCK_STATE_KEY: "true"},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("h-1", LOCK_STATE_KEY), "true")
        self.assertIsNone(session.get_object_user_text("h-1", LOCK_LEGACY_KEY))

    def test_english_lock_hint_deleted_without_copy(self):
        session = MemorySession()
        _block(
            session,
            "item-1",
            "Tag_Item",
            **{LOCK_LEGACY_KEY: LOCK_CANONICAL_HINT},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertIsNone(session.get_object_user_text("item-1", LOCK_LEGACY_KEY))
        self.assertIsNone(session.get_object_user_text("item-1", LOCK_STATE_KEY))

    def test_previous_lock_key_copied_to_sort_key(self):
        session = MemorySession()
        _block(
            session,
            "h-1",
            "Tag_Height_Grab",
            **{LOCK_STATE_PREV_KEY: "x", "attr_mat_key": "PT"},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("h-1", LOCK_STATE_KEY), "x")
        self.assertIsNone(session.get_object_user_text("h-1", LOCK_STATE_PREV_KEY))
        self.assertNotEqual(LOCK_STATE_KEY, LOCK_STATE_PREV_KEY)

    def test_lock_key_alias_copied(self):
        session = MemorySession()
        _block(
            session,
            "h-1",
            "Tag_Height_Grab",
            **{"foo_不更新": "x"},
        )
        run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertEqual(session.get_object_user_text("h-1", LOCK_STATE_KEY), "x")
        self.assertIsNone(session.get_object_user_text("h-1", "foo_不更新"))

    def test_nothing_left_explains_lock_formula(self):
        session = MemorySession()
        _block(session, "h-1", "Tag_Height_Grab", **{"lf_type_category": "PT"})
        result = run_migrate_block_display_keys(session, confirm=lambda _lines: True)
        self.assertTrue(result.ok)
        self.assertIn("BlockEdit", result.message)
        self.assertIn("lf_00_lock_state", result.message)


if __name__ == "__main__":
    unittest.main()

