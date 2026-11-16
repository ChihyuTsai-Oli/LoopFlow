# -*- coding: utf-8 -*-
"""E06 Document：開啟 GitHub 使用說明與官方範本資料夾。"""
from __future__ import annotations

import sys
import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.document.open_guide import (
    COMMAND_ID,
    DOCUMENT_URL,
    open_document,
)
from loopflow.foundation import results


class DocumentCommandTests(unittest.TestCase):
    def test_opens_bilingual_docs_entry(self):
        opened = []
        folder = Path("C:/Users/test/Documents/LoopFlow")

        def opener(url: str) -> None:
            opened.append(url)

        result = open_document(
            opener=opener,
            folder_opener=lambda path: opened.append(path),
            folder_path=folder,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.command_id, COMMAND_ID)
        self.assertEqual(opened, [DOCUMENT_URL, folder])
        self.assertTrue(result.details["opened_url"])
        self.assertTrue(result.details["opened_folder"])
        self.assertTrue(DOCUMENT_URL.endswith("/docs/README.md"))
        self.assertIn("github.com/ChihyuTsai-Oli/LoopFlow", DOCUMENT_URL)
        self.assertNotIn("USER_GUIDE", DOCUMENT_URL)

    def test_open_failure_does_not_claim_success(self):
        opened_folders = []
        def opener(_url: str) -> None:
            raise OSError("browser missing")

        result = open_document(opener=opener, folder_opener=opened_folders.append)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertIn("browser missing", result.message)
        self.assertFalse(result.details["opened_url"])
        self.assertTrue(result.details["opened_folder"])
        self.assertEqual(len(opened_folders), 1)
        self.assertEqual(result.details["url"], DOCUMENT_URL)

    def test_folder_failure_still_opens_documentation(self):
        opened_urls = []

        def folder_opener(_folder: Path) -> None:
            raise OSError("folder missing")

        result = open_document(opener=opened_urls.append, folder_opener=folder_opener)
        self.assertFalse(result.ok)
        self.assertEqual(opened_urls, [DOCUMENT_URL])
        self.assertTrue(result.details["opened_url"])
        self.assertFalse(result.details["opened_folder"])
        self.assertIn("folder missing", result.message)

    def test_first_run_seeds_without_opening_folder_twice(self):
        from loopflow.bootstrap import run_command

        outcome = results.ok("open_document", "opened", command_id=COMMAND_ID)
        with patch("loopflow.foundation.templates.seed_official_templates") as seed:
            with patch("loopflow.features.document.language.ensure_locale", return_value=None):
                with patch("loopflow.runners.dispatch", return_value=outcome):
                    with redirect_stdout(io.StringIO()):
                        result = run_command(COMMAND_ID)
        self.assertTrue(result.ok)
        seed.assert_called_once_with(open_folder=False)


if __name__ == "__main__":
    unittest.main()
