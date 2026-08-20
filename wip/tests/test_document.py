# -*- coding: utf-8 -*-
"""E06 Document：開啟 GitHub 使用說明，失敗不寫 Rhino 文件。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.document.open_guide import (
    COMMAND_ID,
    DOCUMENT_URL,
    open_document,
)


class DocumentCommandTests(unittest.TestCase):
    def test_opens_traditional_chinese_user_guide(self):
        opened = []

        def opener(url: str) -> None:
            opened.append(url)

        result = open_document(opener=opener)
        self.assertTrue(result.ok)
        self.assertEqual(result.command_id, COMMAND_ID)
        self.assertEqual(opened, [DOCUMENT_URL])
        self.assertIn("USER_GUIDE_TW.md", DOCUMENT_URL)
        self.assertIn("github.com/ChihyuTsai-Oli/LoopFlow", DOCUMENT_URL)

    def test_open_failure_does_not_claim_success(self):
        def opener(_url: str) -> None:
            raise OSError("browser missing")

        result = open_document(opener=opener)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertIn("無法開啟", result.message)
        self.assertEqual(result.details["url"], DOCUMENT_URL)


if __name__ == "__main__":
    unittest.main()
