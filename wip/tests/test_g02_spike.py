# -*- coding: utf-8 -*-
"""G02 最小 yak spike：只登錄 LFDocument，不改開發期入口檔名。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SPIKE = WIP / "packaging" / "g02-spike"
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.command_catalog import CORE_COMMANDS
from loopflow.features.document.open_guide import COMMAND_ID, DOCUMENT_URL


class G02SpikePackagingTests(unittest.TestCase):
    def test_command_script_uses_official_name_and_existing_runner(self):
        script = (SPIKE / "commands" / "LFDocument.py").read_text(encoding="utf-8")
        self.assertIn("LFDocument", script)
        self.assertIn('run_command("LF_Document")', script)
        self.assertNotIn("LF_D08", script)
        self.assertIn("loopflow.bootstrap", script)

    def test_manifest_is_spike_only(self):
        text = (SPIKE / "manifest.yml").read_text(encoding="utf-8")
        self.assertIn("name: loopflow", text)
        self.assertIn("version: 0.1.0", text)
        self.assertIn("LFDocument", text)
        self.assertNotIn("LF_D08_Migrate_Display_Keys", text)
        self.assertNotIn("Package Manager 上架", text)

    def test_dev_entrypoint_filename_unchanged(self):
        self.assertTrue((SRC / "entrypoints" / "LF_Document.py").is_file())
        self.assertIn("LF_Document", CORE_COMMANDS)
        self.assertEqual(COMMAND_ID, "LF_Document")
        self.assertTrue(DOCUMENT_URL.endswith("/docs/README.md"))

    def test_command_script_can_resolve_repo_src(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "lfdocument_spike",
            SPIKE / "commands" / "LFDocument.py",
        )
        self.assertIsNotNone(spec)
        self.assertTrue((WIP / "src" / "loopflow" / "bootstrap.py").is_file())


if __name__ == "__main__":
    unittest.main()
