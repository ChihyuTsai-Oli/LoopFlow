# -*- coding: utf-8 -*-
"""官方範本：同版已有不蓋；換版或沒有戳記則重拷官方檔。測試不開檔案總管。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.foundation import templates as seed
from loopflow.foundation.version import PACKAGE_VERSION


class OfficialTemplateSeedTests(unittest.TestCase):
    def setUp(self):
        self._old_source = os.environ.get(seed.SOURCE_ENV)
        self._old_dest = os.environ.get(seed.DEST_ENV)
        self._old_no_open = os.environ.get(seed.NO_OPEN_ENV)
        self._source = tempfile.TemporaryDirectory()
        self._dest = tempfile.TemporaryDirectory()
        source = Path(self._source.name)
        for name in seed.TEMPLATE_FILES:
            (source / name).write_bytes(b"template-" + name.encode("ascii"))
        os.environ[seed.SOURCE_ENV] = str(source)
        os.environ[seed.DEST_ENV] = str(self._dest.name)
        os.environ[seed.NO_OPEN_ENV] = "1"

    def tearDown(self):
        for key, old in (
            (seed.SOURCE_ENV, self._old_source),
            (seed.DEST_ENV, self._old_dest),
            (seed.NO_OPEN_ENV, self._old_no_open),
        ):
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old
        self._source.cleanup()
        self._dest.cleanup()

    def _stamp_text(self):
        return (Path(self._dest.name) / seed.STAMP_FILENAME).read_text(encoding="utf-8").strip()

    def test_copies_missing_files_once(self):
        first = seed.seed_official_templates(open_folder=False)
        self.assertEqual(first.copied, seed.TEMPLATE_FILES)
        self.assertEqual(first.skipped, ())
        self.assertEqual(first.missing, ())
        dest = Path(self._dest.name)
        for name in seed.TEMPLATE_FILES:
            self.assertEqual(
                (dest / name).read_bytes(),
                b"template-" + name.encode("ascii"),
            )
        self.assertEqual(self._stamp_text(), PACKAGE_VERSION)
        second = seed.seed_official_templates(open_folder=False)
        self.assertEqual(second.copied, ())
        self.assertEqual(second.skipped, seed.TEMPLATE_FILES)
        self.assertFalse(second.copied_any)

    def test_same_version_does_not_overwrite_existing(self):
        dest = Path(self._dest.name)
        (dest / seed.STAMP_FILENAME).write_text("%s\n" % PACKAGE_VERSION, encoding="utf-8")
        (dest / "Tag_Blocks.3dm").write_bytes(b"user-edited")
        result = seed.seed_official_templates(open_folder=False)
        self.assertIn("Tag_Blocks.3dm", result.skipped)
        self.assertEqual(len(result.copied), 2)
        self.assertEqual((dest / "Tag_Blocks.3dm").read_bytes(), b"user-edited")
        self.assertEqual(self._stamp_text(), PACKAGE_VERSION)

    def test_version_change_replaces_official_files(self):
        dest = Path(self._dest.name)
        seed.seed_official_templates(open_folder=False)
        (dest / "Tag_Blocks.3dm").write_bytes(b"old-install")
        (dest / seed.STAMP_FILENAME).write_text("2.0.3\n", encoding="utf-8")
        (dest / "notes.txt").write_text("keep me", encoding="utf-8")
        result = seed.seed_official_templates(open_folder=False)
        self.assertIn("Tag_Blocks.3dm", result.copied)
        self.assertEqual(result.skipped, ())
        self.assertEqual(
            (dest / "Tag_Blocks.3dm").read_bytes(),
            b"template-Tag_Blocks.3dm",
        )
        self.assertEqual((dest / "notes.txt").read_text(encoding="utf-8"), "keep me")
        self.assertEqual(self._stamp_text(), PACKAGE_VERSION)

    def test_missing_stamp_replaces_official_files(self):
        dest = Path(self._dest.name)
        (dest / "Tag_Blocks.3dm").write_bytes(b"from-2.0.3")
        result = seed.seed_official_templates(open_folder=False)
        self.assertIn("Tag_Blocks.3dm", result.copied)
        self.assertEqual(
            (dest / "Tag_Blocks.3dm").read_bytes(),
            b"template-Tag_Blocks.3dm",
        )
        self.assertEqual(self._stamp_text(), PACKAGE_VERSION)

    def test_missing_source_is_reported(self):
        Path(os.environ[seed.SOURCE_ENV], "Tag_Blocks.3dm").unlink()
        result = seed.seed_official_templates(open_folder=False)
        self.assertEqual(result.missing, ("Tag_Blocks.3dm",))
        self.assertEqual(len(result.copied), 2)
        dest = Path(self._dest.name)
        self.assertFalse((dest / seed.STAMP_FILENAME).is_file())

    def test_repo_docs_are_findable_without_env(self):
        os.environ.pop(seed.SOURCE_ENV, None)
        found = seed.find_template_source("Tag_Blocks.3dm")
        self.assertIsNotNone(found)
        self.assertTrue(found.is_file())
        self.assertGreater(found.stat().st_size, 1000)
        tw = seed.find_template_source("LoopFlow_Dictionary_tw.xlsx")
        en = seed.find_template_source("LoopFlow_Dictionary_en.xlsx")
        self.assertTrue(tw.is_file())
        self.assertTrue(en.is_file())

    def test_unittest_without_override_does_not_touch_documents(self):
        os.environ.pop(seed.SOURCE_ENV, None)
        os.environ.pop(seed.DEST_ENV, None)
        result = seed.seed_official_templates(open_folder=True)
        self.assertEqual(result.copied, ())
        self.assertEqual(result.skipped, ())


if __name__ == "__main__":
    unittest.main()
