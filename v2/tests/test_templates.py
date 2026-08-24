# -*- coding: utf-8 -*-
"""官方範本：缺檔才拷到文件\\LoopFlow，已有不蓋，測試不開檔案總管。"""
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
        second = seed.seed_official_templates(open_folder=False)
        self.assertEqual(second.copied, ())
        self.assertEqual(second.skipped, seed.TEMPLATE_FILES)
        self.assertFalse(second.copied_any)

    def test_does_not_overwrite_existing(self):
        dest = Path(self._dest.name)
        (dest / "Tag_Blocks.3dm").write_bytes(b"user-edited")
        result = seed.seed_official_templates(open_folder=False)
        self.assertIn("Tag_Blocks.3dm", result.skipped)
        self.assertEqual(len(result.copied), 2)
        self.assertEqual((dest / "Tag_Blocks.3dm").read_bytes(), b"user-edited")

    def test_missing_source_is_reported(self):
        Path(os.environ[seed.SOURCE_ENV], "Tag_Blocks.3dm").unlink()
        result = seed.seed_official_templates(open_folder=False)
        self.assertEqual(result.missing, ("Tag_Blocks.3dm",))
        self.assertEqual(len(result.copied), 2)

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
