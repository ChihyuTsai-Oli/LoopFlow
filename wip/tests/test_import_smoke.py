# -*- coding: utf-8 -*-
"""確認 2.0 套件可載入，且 Nexus 入口不假裝功能完成。"""
from __future__ import annotations

import ast
import io
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
ENTRY = SRC / "entrypoints" / "LF_Nexus.py"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class ImportSmokeTests(unittest.TestCase):
    def test_package_imports(self):
        import loopflow
        from loopflow import bootstrap, command_catalog

        self.assertTrue(loopflow.__version__.startswith("2.0.0"))
        self.assertTrue(callable(bootstrap.run_command))
        self.assertGreaterEqual(len(command_catalog.CORE_COMMANDS), 1)

    def test_catalog_lists_nexus_console(self):
        from loopflow.command_catalog import CORE_COMMANDS, get_command

        self.assertIn("LF_Nexus", CORE_COMMANDS)
        spec = get_command("LF_Nexus")
        self.assertEqual(spec["status"], "console")
        self.assertEqual(spec["entrypoint"], "LF_Nexus.py")
        self.assertEqual(spec["task"], "C02/NX-01")

    def test_run_command_does_not_claim_scan_success(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()):
            result = run_command("LF_Nexus")
        self.assertFalse(result.ok)
        self.assertNotEqual(result.status, "ok")
        self.assertNotIn("套用完成", result.message)
        self.assertNotIn("已發布", result.message)

    def test_unknown_command_is_rejected(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()):
            result = run_command("LF_Cabinet_Suite")
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "unknown_command")

    def test_nexus_entrypoint_has_no_rhino_or_feature_code(self):
        source = ENTRY.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertIsInstance(tree, ast.Module)
        for forbidden in ("rhinoscriptsyntax", "Rhino", "scriptcontext", "Scan", "Apply"):
            self.assertNotIn(forbidden, source)

    def test_entrypoint_script_loads(self):
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        completed = subprocess.run(
            [sys.executable, str(ENTRY)],
            cwd=str(WIP.parent),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertNotIn("套用完成", completed.stdout)
        self.assertTrue(
            any(
                token in completed.stdout
                for token in ("不在 Rhino", "LOOPFLOW_WORKFILES_ROOT", "尚未有 project_id")
            ),
            completed.stdout,
        )


if __name__ == "__main__":
    unittest.main()
