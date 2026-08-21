# -*- coding: utf-8 -*-
"""G02 yak spike：登錄全部正式指令，不改開發期入口檔名，不附 RUI。"""
from __future__ import annotations

import json
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


def _official_pairs():
    lines = [
        line.strip()
        for line in (WIP / "docs" / "指令名稱.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    if len(lines) % 2:
        raise AssertionError("指令名稱.txt 必須成對：開發期 ID、正式名稱")
    return list(zip(lines[0::2], lines[1::2]))


class G02SpikePackagingTests(unittest.TestCase):
    def test_command_scripts_match_name_table(self):
        pairs = _official_pairs()
        self.assertEqual(len(pairs), 19)
        for dev_id, official in pairs:
            script_path = SPIKE / "commands" / ("%s.py" % official)
            self.assertTrue(script_path.is_file(), official)
            script = script_path.read_text(encoding="utf-8")
            self.assertTrue(script.startswith("#! python 3"), official)
            self.assertIn(official, script)
            self.assertIn('run_command("%s")' % dev_id, script)
            self.assertNotIn("LF_D08", script)
            self.assertIn("loopflow.bootstrap", script)
            self.assertTrue((SRC / "entrypoints" / ("%s.py" % dev_id)).is_file(), dev_id)

    def test_rhproj_registers_all_official_commands(self):
        pairs = _official_pairs()
        data = json.loads((SPIKE / "LoopFlow.rhproj").read_text(encoding="utf-8"))
        codes = data["codes"]
        self.assertEqual(len(codes), 19)
        names = [code["name"] for code in codes]
        self.assertEqual(names, [official for _dev, official in pairs])
        ids = [code["id"] for code in codes]
        self.assertEqual(len(ids), len(set(ids)))
        document = next(code for code in codes if code["name"] == "LFDocument")
        self.assertEqual(document["id"], "c3a91f4e-2b7d-4e18-9f0a-6d5c8b1e4a22")
        for code, (_dev, official) in zip(codes, pairs):
            self.assertEqual(code["title"], official)
            self.assertEqual(code["path"], "commands/%s.py" % official)
            self.assertEqual(code["language"]["id"], "*.*.python")
            self.assertEqual(code["language"]["version"], "3.*.*")
            self.assertIsInstance(code["language"], dict)
        self.assertNotIn("LF_D08_Migrate_Display_Keys", json.dumps(data))

    def test_manifest_is_spike_only(self):
        text = (SPIKE / "manifest.yml").read_text(encoding="utf-8")
        self.assertIn("name: loopflow", text)
        self.assertIn("version: 0.2.0", text)
        self.assertIn("Toolbar RUI is not included yet", text)
        self.assertNotIn("LF_D08_Migrate_Display_Keys", text)
        self.assertNotIn("Package Manager 上架", text)

    def test_build_script_strips_generated_rui(self):
        text = (SPIKE / "build.ps1").read_text(encoding="utf-8")
        self.assertIn("LoopFlow.rui still present; refuse to pack yak", text)
        self.assertIn("yak still contains rui; refuse to install", text)
        self.assertIn('Version = "0.2.0"', text)

    def test_prepare_rhproj_rewrites_every_command_uri(self):
        source = (SPIKE / "prepare_rhproj.py").read_text(encoding="utf-8")
        self.assertIn('code["uri"] = command.as_uri()', source)
        self.assertIn("for code in codes", source)

    def test_dev_entrypoint_filename_unchanged(self):
        self.assertTrue((SRC / "entrypoints" / "LF_Document.py").is_file())
        self.assertIn("LF_Document", CORE_COMMANDS)
        self.assertEqual(len(CORE_COMMANDS), 19)
        self.assertEqual(COMMAND_ID, "LF_Document")
        self.assertTrue(DOCUMENT_URL.endswith("/docs/README.md"))

    def test_command_script_can_resolve_repo_src(self):
        self.assertTrue((WIP / "src" / "loopflow" / "bootstrap.py").is_file())
        for _dev, official in _official_pairs():
            self.assertTrue((SPIKE / "commands" / ("%s.py" % official)).is_file())


if __name__ == "__main__":
    unittest.main()
