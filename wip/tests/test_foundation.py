# -*- coding: utf-8 -*-
"""foundation：Result、路徑、schema、設定與 log。不依賴 Rhino 或真實 Dropbox。"""
from __future__ import annotations

import io
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DRIVE_RE = re.compile(r"[A-Za-z]:\\")
PERSONAL_MARKERS = ("Dropbox", "WIP_loopflow", "Chihyu", "chihyu")


class ResultTests(unittest.TestCase):
    def test_ok_and_failed_are_distinct(self):
        from loopflow.foundation import results

        good = results.ok("dispatch", "完成")
        self.assertTrue(good.ok)
        self.assertEqual(good.status, "ok")
        bad = results.failed("resolve_workfiles", "停止")
        self.assertFalse(bad.ok)
        self.assertEqual(bad.status, "failed")

    def test_warnings_do_not_block(self):
        from loopflow.foundation import results

        warned = results.ok_with_warnings("dispatch", "可繼續", ("非 cm",))
        self.assertTrue(warned.ok)
        self.assertEqual(warned.warnings, ("非 cm",))

    def test_blocked_lists_reasons(self):
        from loopflow.foundation import results

        blocked = results.blocked("resolve_registry", "停止", ("invalid_project_id",))
        self.assertFalse(blocked.ok)
        self.assertEqual(blocked.status, "blocked")
        self.assertEqual(blocked.blocking, ("invalid_project_id",))

    def test_cancelled_is_not_success(self):
        from loopflow.foundation import results

        stopped = results.cancelled("dispatch", "使用者取消")
        self.assertFalse(stopped.ok)
        self.assertEqual(stopped.status, "cancelled")


class PathTests(unittest.TestCase):
    def test_missing_env_stops_without_creating(self):
        from loopflow.foundation.paths import WORKFILES_ROOT_ENV, resolve_workfiles

        before = set(Path(tempfile.gettempdir()).iterdir())
        result = resolve_workfiles(environ={})
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "resolve_workfiles")
        self.assertIn(WORKFILES_ROOT_ENV, result.message)
        self.assertEqual(before, after)

    def test_missing_directory_stops_without_creating(self):
        from loopflow.foundation.paths import resolve_workfiles

        missing = Path(tempfile.gettempdir()) / "loopflow-missing-root-does-not-exist"
        if missing.exists():
            self.fail("測試路徑不應事先存在")
        result = resolve_workfiles(environ={"LOOPFLOW_WORKFILES_ROOT": str(missing)})
        self.assertFalse(result.ok)
        self.assertFalse(missing.exists())

    def test_file_instead_of_directory_fails(self):
        from loopflow.foundation.paths import resolve_workfiles

        with tempfile.NamedTemporaryFile(prefix="loopflow-root-", delete=False) as handle:
            fake = Path(handle.name)
        try:
            result = resolve_workfiles(environ={"LOOPFLOW_WORKFILES_ROOT": str(fake)})
            self.assertFalse(result.ok)
        finally:
            fake.unlink()

    def test_existing_directory_resolves_dictionary_and_exchange(self):
        from loopflow.foundation.paths import (
            DICTIONARY_FILENAME,
            EXCHANGE_DIR_NAME,
            resolve_workfiles,
        )

        with tempfile.TemporaryDirectory(prefix="loopflow-root-") as raw:
            root = Path(raw)
            result = resolve_workfiles(environ={"LOOPFLOW_WORKFILES_ROOT": str(root)})
            self.assertTrue(result.ok)
            workfiles = result.details["paths"]
            self.assertEqual(workfiles.root, root)
            self.assertEqual(workfiles.dictionary, root / DICTIONARY_FILENAME)
            self.assertEqual(workfiles.exchange_root, root / EXCHANGE_DIR_NAME)
            self.assertFalse(workfiles.dictionary.exists())
            self.assertFalse(workfiles.exchange_root.exists())

    def test_registry_paths_require_project_id(self):
        from loopflow.foundation.paths import registry_paths

        result = registry_paths(Path("exchange"), "")
        self.assertFalse(result.ok)
        self.assertIn("project_id", result.message)

    def test_registry_paths_reject_nested_id(self):
        from loopflow.foundation.paths import registry_paths

        result = registry_paths(Path("exchange"), r"..\secret")
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "blocked")

    def test_registry_contract_filenames(self):
        from loopflow.foundation.paths import (
            REGISTRY_FILENAME,
            REGISTRY_LAST_GOOD_FILENAME,
            REGISTRY_LOCK_FILENAME,
            REGISTRY_PENDING_FILENAME,
            registry_paths,
        )

        result = registry_paths(Path("exchange"), "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertTrue(result.ok)
        folder = result.details["folder"]
        self.assertEqual(result.details["registry"].name, REGISTRY_FILENAME)
        self.assertEqual(result.details["lock"].name, REGISTRY_LOCK_FILENAME)
        self.assertEqual(result.details["pending"].name, REGISTRY_PENDING_FILENAME)
        self.assertEqual(result.details["last_good"].name, REGISTRY_LAST_GOOD_FILENAME)
        self.assertEqual(folder.name, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


class VersionConfigLogTests(unittest.TestCase):
    def test_unknown_schema_stops(self):
        from loopflow.foundation.version import check_schema

        unknown = check_schema("loopflow.unknown", 1)
        self.assertFalse(unknown.ok)
        self.assertIn("未知 schema_id", unknown.message)
        old = check_schema("loopflow.registry", 99)
        self.assertFalse(old.ok)
        self.assertIn("未知 schema_version", old.message)

    def test_known_schema_passes(self):
        from loopflow.foundation.version import PACKAGE_VERSION, check_schema

        self.assertTrue(PACKAGE_VERSION.startswith("2.0.0"))
        result = check_schema("loopflow.registry", 1)
        self.assertTrue(result.ok)

    def test_config_does_not_own_registry_names(self):
        from loopflow.foundation.config import DEFAULT_CONFIG

        self.assertFalse(hasattr(DEFAULT_CONFIG, "registry_filename"))
        self.assertEqual(DEFAULT_CONFIG.log_filename, "loopflow.log")

    def test_log_write_uses_injected_path(self):
        from loopflow.foundation.logging import append_log

        with tempfile.TemporaryDirectory(prefix="loopflow-log-") as raw:
            target = Path(raw) / "injected.log"
            result = append_log("hello-foundation", log_path=target)
            self.assertTrue(result.ok)
            text = target.read_text(encoding="utf-8")
            self.assertIn("hello-foundation", text)

    def test_log_without_root_does_not_write(self):
        from loopflow.foundation.logging import append_log

        result = append_log("should-not-write", environ={})
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "resolve_workfiles")

    def test_package_version_is_single_source(self):
        import loopflow
        from loopflow.foundation.version import PACKAGE_VERSION

        self.assertEqual(loopflow.__version__, PACKAGE_VERSION)


class SourceHygieneTests(unittest.TestCase):
    def test_source_has_no_personal_or_drive_paths(self):
        root = SRC / "loopflow"
        offenders = []
        for path in root.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if DRIVE_RE.search(text) or any(marker in text for marker in PERSONAL_MARKERS):
                offenders.append(str(path.relative_to(SRC)))
        self.assertEqual(offenders, [])

    def test_bootstrap_returns_result(self):
        from loopflow.bootstrap import run_command

        with redirect_stdout(io.StringIO()):
            result = run_command("LF_Nexus")
        self.assertFalse(result.ok)
        self.assertNotEqual(result.status, "ok")
        self.assertNotEqual(result.status, "not_implemented")
        self.assertEqual(result.to_dict()["ok"], False)


if __name__ == "__main__":
    unittest.main()
