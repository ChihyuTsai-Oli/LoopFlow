# -*- coding: utf-8 -*-
"""指令腳本在 RhinoCode stage 之後仍找得到 yak 的 lib。"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SPIKE = WIP / "packaging" / "g02-spike"
if str(SPIKE) not in sys.path:
    sys.path.insert(0, str(SPIKE))

from command_locate import (  # noqa: E402
    PLUGIN_ID,
    resolve_loopflow_src,
    wrapper_source,
)


def _touch_bootstrap(root: Path) -> Path:
    bootstrap = root / "loopflow" / "bootstrap.py"
    bootstrap.parent.mkdir(parents=True, exist_ok=True)
    bootstrap.write_text("# test\n", encoding="utf-8")
    return root


class CommandLocateTests(unittest.TestCase):
    def test_finds_repo_src_from_command_script(self):
        script = SPIKE / "commands" / "LFNexus.py"
        found = resolve_loopflow_src(str(script), environ={})
        self.assertEqual(found, WIP / "src")
        self.assertTrue((found / "loopflow" / "bootstrap.py").is_file())

    def test_staged_script_uses_yak_install(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            stage = tmp / "rhinocode" / "stage"
            stage.mkdir(parents=True)
            staged = stage / "emwxmj5q.ldu"
            staged.write_text("# staged\n", encoding="utf-8")
            yak_lib = _touch_bootstrap(
                tmp / "AppData" / "McNeel" / "Rhinoceros" / "packages" / "8.0" / "loopflow" / "2.0.2" / "lib"
            )
            found = resolve_loopflow_src(
                str(staged),
                environ={"APPDATA": str(tmp / "AppData"), "LOCALAPPDATA": ""},
            )
            self.assertEqual(found, yak_lib)

    def test_prefers_newer_yak_version(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            packages = tmp / "McNeel" / "Rhinoceros" / "packages" / "8.0" / "loopflow"
            _touch_bootstrap(packages / "2.0.2" / "lib")
            newer = _touch_bootstrap(packages / "2.0.3" / "lib")
            staged = tmp / "stage" / "cmd.py"
            staged.parent.mkdir()
            staged.write_text("# staged\n", encoding="utf-8")
            found = resolve_loopflow_src(
                str(staged),
                environ={"APPDATA": str(tmp), "LOCALAPPDATA": ""},
            )
            self.assertEqual(found, newer)

    def test_plugin_rhp_next_to_lib(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            package = tmp / "loopflow" / "2.0.2"
            lib = _touch_bootstrap(package / "lib")
            rhp = package / "LoopFlow.rhp"
            rhp.write_bytes(b"rhp")
            staged = tmp / "stage" / "cmd.py"
            staged.parent.mkdir()
            staged.write_text("# staged\n", encoding="utf-8")
            found = resolve_loopflow_src(
                str(staged),
                environ={},
                plugin_rhps=(str(rhp),),
            )
            self.assertEqual(found, lib)

    def test_missing_raises_same_message(self):
        import tempfile

        with tempfile.TemporaryDirectory() as raw:
            staged = Path(raw) / "stage" / "cmd.py"
            staged.parent.mkdir()
            staged.write_text("# staged\n", encoding="utf-8")
            with self.assertRaises(RuntimeError) as ctx:
                resolve_loopflow_src(str(staged), environ={})
            self.assertIn("src 或 lib", str(ctx.exception))

    def test_wrappers_embed_yak_lookup(self):
        pairs_path = WIP / "docs" / "指令名稱.txt"
        lines = [
            line.strip()
            for line in pairs_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        ]
        pairs = list(zip(lines[0::2], lines[1::2]))
        self.assertEqual(len(pairs), 20)
        for dev_id, official in pairs:
            path = SPIKE / "commands" / ("%s.py" % official)
            text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
            self.assertEqual(text, wrapper_source(official, dev_id).replace("\r\n", "\n"), official)
            self.assertIn(PLUGIN_ID, text)
            self.assertIn("_from_yak_install", text)
            self.assertIn("PathFromId", text)
            self.assertIn('run_command("%s")' % dev_id, text)


if __name__ == "__main__":
    unittest.main()
