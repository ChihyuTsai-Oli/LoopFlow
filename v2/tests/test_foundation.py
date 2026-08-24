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
# 公開 GitHub 網址可含擁有者名稱；那不是本機路徑。
PUBLIC_URL_RE = re.compile(r"https://github\.com/[^\s\"']+")


class ResultTests(unittest.TestCase):
    def test_ok_and_failed_are_distinct(self):
        from loopflow.foundation import results

        good = results.ok("dispatch", "完成")
        self.assertTrue(good.ok)
        self.assertEqual(good.status, "ok")
        bad = results.failed("resolve_project_folder", "停止")
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
    def test_no_rhino_stops_without_creating(self):
        from loopflow.foundation.paths import resolve_project_folder

        before = set(Path(tempfile.gettempdir()).iterdir())
        result = resolve_project_folder(None)
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")
        self.assertEqual(before, after)

    def test_unsaved_document_stops_without_creating(self):
        from loopflow.foundation.paths import resolve_project_folder
        from loopflow.platform.rhino.memory import MemorySession

        before = set(Path(tempfile.gettempdir()).iterdir())
        result = resolve_project_folder(MemorySession())
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("unsaved_document",))
        self.assertEqual(before, after)

    def test_document_folder_is_the_project_folder(self):
        from loopflow.foundation.paths import (
            CONFIG_DIR_NAME,
            DICTIONARY_FILENAME,
            resolve_project_folder,
        )
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-root-") as raw:
            root = Path(raw)
            session = MemorySession(document_path=root / "案子.3dm")
            result = resolve_project_folder(session)
            self.assertTrue(result.ok, result.message)
            project = result.details["paths"]
            self.assertEqual(project.root, root)
            self.assertEqual(project.dictionary, root / DICTIONARY_FILENAME)
            self.assertEqual(project.config_dir, root / CONFIG_DIR_NAME)
            self.assertEqual(project.log_file().parent.parent, project.config_dir)
            self.assertFalse(project.dictionary.exists())
            self.assertFalse(project.config_dir.exists())

    def test_three_paths_stay_relative_across_parents(self):
        from loopflow.foundation.paths import resolve_project_folder
        from loopflow.platform.rhino.memory import MemorySession

        relatives = []
        for prefix in ("loopflow-carrier-a-", "loopflow-carrier-b-"):
            with tempfile.TemporaryDirectory(prefix=prefix) as raw:
                root = Path(raw) / "專案"
                root.mkdir()
                result = resolve_project_folder(MemorySession(document_path=root / "a.3dm"))
                self.assertTrue(result.ok, result.message)
                project = result.details["paths"]
                relatives.append(
                    (
                        project.document.relative_to(project.root),
                        project.dictionary.relative_to(project.root),
                        project.config_dir.relative_to(project.root),
                    )
                )
        self.assertEqual(relatives[0], relatives[1])

    def test_unsaved_document_does_not_create_registry_folder(self):
        from loopflow.foundation.paths import resolve_registry_for_document

        before = set(Path(tempfile.gettempdir()).iterdir())
        result = resolve_registry_for_document(None, "M3D")
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("unsaved_document",))
        self.assertEqual(before, after)

    def test_registry_follows_document_directory_not_filename(self):
        from loopflow.foundation.paths import CONFIG_DIR_NAME, resolve_registry_for_document

        with tempfile.TemporaryDirectory(prefix="loopflow-ex-") as raw:
            folder = Path(raw)
            first = resolve_registry_for_document(folder / "a.3dm", "M3D")
            second = resolve_registry_for_document(folder / "b.3dm", "M3D")
            renamed = resolve_registry_for_document(folder / "a.3dm", "Tower")
            self.assertTrue(first.ok, first.message)
            self.assertEqual(first.details["folder"], folder / CONFIG_DIR_NAME / "M3D")
            self.assertEqual(second.details["folder"], first.details["folder"])
            self.assertEqual(renamed.details["folder"], folder / CONFIG_DIR_NAME / "Tower")
            self.assertNotEqual(first.details["folder"], renamed.details["folder"])
            self.assertFalse((folder / CONFIG_DIR_NAME).exists())

    def test_registry_paths_require_project_id(self):
        from loopflow.foundation.paths import CONFIG_DIR_NAME, registry_paths

        result = registry_paths(Path(CONFIG_DIR_NAME), "")
        self.assertFalse(result.ok)
        self.assertIn("專案名稱", result.message)

    def test_registry_paths_reject_nested_id(self):
        from loopflow.foundation.paths import CONFIG_DIR_NAME, registry_paths

        result = registry_paths(Path(CONFIG_DIR_NAME), r"..\secret")
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "blocked")

    def test_registry_contract_filenames(self):
        from loopflow.foundation.paths import (
            CONFIG_DIR_NAME,
            REGISTRY_FILENAME,
            REGISTRY_LAST_GOOD_FILENAME,
            REGISTRY_LOCK_FILENAME,
            REGISTRY_PENDING_FILENAME,
            registry_paths,
        )

        result = registry_paths(Path(CONFIG_DIR_NAME), "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
        self.assertTrue(result.ok)
        folder = result.details["folder"]
        self.assertEqual(result.details["registry"].name, REGISTRY_FILENAME)
        self.assertEqual(result.details["lock"].name, REGISTRY_LOCK_FILENAME)
        self.assertEqual(result.details["pending"].name, REGISTRY_PENDING_FILENAME)
        self.assertEqual(result.details["last_good"].name, REGISTRY_LAST_GOOD_FILENAME)
        self.assertEqual(folder.name, "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")


class DictionaryFilenameTests(unittest.TestCase):
    def test_normalize_accepts_basename_and_adds_xlsx(self):
        from loopflow.foundation.paths import (
            normalize_dictionary_filename,
            export_dictionary_filename,
        )

        named = normalize_dictionary_filename("TeamA.xlsx")
        self.assertTrue(named.ok, named.message)
        self.assertEqual(named.details["filename"], "TeamA.xlsx")
        stem = normalize_dictionary_filename("TeamA")
        self.assertTrue(stem.ok, stem.message)
        self.assertEqual(stem.details["filename"], "TeamA.xlsx")
        self.assertEqual(export_dictionary_filename("TeamA.xlsx"), "TeamA_Export.xlsx")

    def test_normalize_rejects_path_and_export_file(self):
        from loopflow.foundation.paths import normalize_dictionary_filename

        nested = normalize_dictionary_filename("sub/TeamA.xlsx")
        self.assertFalse(nested.ok)
        exported = normalize_dictionary_filename("LoopFlow_Dictionary_Export.xlsx")
        self.assertFalse(exported.ok)
        self.assertEqual(exported.blocking, ("export_file_not_dictionary",))

    def test_normalize_accepts_absolute_and_extended_path_under_root(self):
        from loopflow.foundation.paths import normalize_dictionary_filename

        with tempfile.TemporaryDirectory(prefix="loopflow-dict-abs-") as raw:
            root = Path(raw)
            chosen = root / "LoopFlow_Dictionary.xlsx"
            chosen.write_bytes(b"")
            by_abs = normalize_dictionary_filename(str(chosen), root=root)
            self.assertTrue(by_abs.ok, by_abs.message)
            self.assertEqual(by_abs.details["filename"], "LoopFlow_Dictionary.xlsx")
            extended = "\\\\?\\" + str(chosen.resolve())
            by_extended = normalize_dictionary_filename(extended, root=root)
            self.assertTrue(by_extended.ok, by_extended.message)
            self.assertEqual(by_extended.details["filename"], "LoopFlow_Dictionary.xlsx")

    def test_normalize_outside_root_shows_both_paths(self):
        from loopflow.foundation.paths import normalize_dictionary_filename

        with tempfile.TemporaryDirectory(prefix="loopflow-dict-out-") as raw:
            root = Path(raw)
            outside = str(root.parent / "Downloads" / "LoopFlow_Dictionary.xlsx")
            blocked = normalize_dictionary_filename(outside, root=root)
            self.assertFalse(blocked.ok)
            self.assertEqual(blocked.blocking, ("dictionary_outside_project_folder",))
            self.assertIn("Downloads", blocked.message)
            self.assertIn(str(root), blocked.message)

    def test_dialog_file_name_joins_folder(self):
        from loopflow.platform.rhino.prompts import dialog_file_name

        folder = str(Path(tempfile.gettempdir()) / "loopflow-workfiles")
        joined = dialog_file_name(folder, "LoopFlow_Dictionary.xlsx")
        self.assertEqual(Path(joined).name, "LoopFlow_Dictionary.xlsx")
        self.assertEqual(Path(joined).parent, Path(folder))
        already = dialog_file_name(folder, str(Path(folder) / "TeamA.xlsx"))
        self.assertEqual(Path(already), Path(folder) / "TeamA.xlsx")

    def test_winforms_file_filter_strips_trailing_bars(self):
        from loopflow.platform.rhino.prompts import winforms_file_filter

        self.assertEqual(
            winforms_file_filter("Excel (*.xlsx)|*.xlsx||"),
            "Excel (*.xlsx)|*.xlsx",
        )

    def test_choose_dictionary_retries_outside_path(self):
        from loopflow.features.project.menu import choose_dictionary_path

        with tempfile.TemporaryDirectory(prefix="loopflow-dict-retry-") as raw:
            root = Path(raw)
            official = root / "LoopFlow_Dictionary.xlsx"
            official.write_bytes(b"")
            calls = []
            warnings = []

            def _open(default):
                calls.append(default)
                if len(calls) == 1:
                    return str(root.parent / "Downloads" / "qed.xlsx")
                return str(official)

            picked = choose_dictionary_path(
                _open,
                root,
                "LoopFlow_Dictionary.xlsx",
                warn=warnings.append,
            )
            self.assertEqual(Path(picked), official)
            self.assertEqual(len(calls), 2)
            self.assertEqual(len(warnings), 1)
            self.assertIn("qed.xlsx", warnings[0])

    def test_remembered_filename_none_without_project_config(self):
        from loopflow.foundation.paths import DICTIONARY_FILENAME
        from loopflow.foundation.project_config import (
            dictionary_filename_from_session,
            remembered_dictionary_filename,
        )
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-dict-none-") as raw:
            session = MemorySession(document_path=Path(raw) / "a.3dm")
            self.assertIsNone(remembered_dictionary_filename(session))
            self.assertIsNone(remembered_dictionary_filename(None))
            self.assertEqual(dictionary_filename_from_session(session), DICTIONARY_FILENAME)

    def test_project_folder_uses_custom_filename(self):
        from loopflow.foundation.paths import resolve_project_folder
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-dict-name-") as raw:
            root = Path(raw)
            result = resolve_project_folder(
                MemorySession(document_path=root / "a.3dm"),
                dictionary_filename="TeamA.xlsx",
            )
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.details["paths"].dictionary, root / "TeamA.xlsx")


class ProjectConfigTests(unittest.TestCase):
    def setUp(self):
        from loopflow.foundation.project_config import clear_cache

        clear_cache()

    def test_settings_live_beside_the_document_not_in_the_3dm(self):
        from loopflow.foundation.paths import CONFIG_DIR_NAME
        from loopflow.foundation.project_config import (
            CONFIG_FILENAME,
            read_config,
            remember_project_name,
        )
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-cfg-") as raw:
            root = Path(raw)
            session = MemorySession(document_path=root / "a.3dm")
            written = remember_project_name(session, "大安邸")
            self.assertTrue(written.ok, written.message)
            config_file = root / CONFIG_DIR_NAME / CONFIG_FILENAME
            self.assertTrue(config_file.is_file())
            self.assertIn("大安邸", config_file.read_text(encoding="utf-8"))
            self.assertEqual(read_config(session).details["values"]["project_id"], "大安邸")
            for key in ("lf_project_id", "lf_layer_prefix", "lf_dictionary_filename"):
                self.assertIsNone(session.document_user_text(key))

    def test_legacy_document_keys_move_into_config_once(self):
        from loopflow.foundation.project_config import LEGACY_DOCUMENT_KEYS, read_config
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-legacy-") as raw:
            root = Path(raw)
            session = MemorySession(
                document_path=root / "a.3dm",
                document_text={
                    "lf_schema_id": "loopflow.project",
                    "lf_schema_version": "1",
                    "lf_project_id": "M3D",
                    "lf_layer_prefix": "M3D",
                    "lf_dictionary_filename": "TeamA.xlsx",
                },
            )
            values = read_config(session).details["values"]
            self.assertEqual(values["project_id"], "M3D")
            self.assertEqual(values["schema_version"], 1)
            self.assertEqual(values["dictionary_filename"], "TeamA.xlsx")
            for key, _field in LEGACY_DOCUMENT_KEYS:
                self.assertIsNone(session.document_user_text(key))

    def test_copying_the_3dm_alone_carries_no_project_settings(self):
        from loopflow.foundation.project_config import read_config, remember_project_name
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-copy-") as raw:
            source = Path(raw) / "來源"
            target = Path(raw) / "新案"
            source.mkdir()
            target.mkdir()
            session = MemorySession(document_path=source / "a.3dm")
            remember_project_name(session, "來源案")
            session.set_document_path(target / "a.3dm")
            self.assertEqual(read_config(session).details["values"], {})

    def test_unsaved_document_blocks_config(self):
        from loopflow.foundation.project_config import read_config
        from loopflow.platform.rhino.memory import MemorySession

        result = read_config(MemorySession())
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("unsaved_document",))

    def test_broken_config_stops_instead_of_guessing(self):
        from loopflow.foundation.paths import CONFIG_DIR_NAME
        from loopflow.foundation.project_config import CONFIG_FILENAME, read_config
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-broken-") as raw:
            root = Path(raw)
            folder = root / CONFIG_DIR_NAME
            folder.mkdir()
            (folder / CONFIG_FILENAME).write_text("{不是 JSON", encoding="utf-8")
            result = read_config(MemorySession(document_path=root / "a.3dm"))
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "read_project_config")


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

        self.assertTrue(PACKAGE_VERSION.startswith("2.0."))
        result = check_schema("loopflow.registry", 1)
        self.assertTrue(result.ok)

    def test_config_does_not_own_registry_names(self):
        from loopflow.foundation.config import DEFAULT_CONFIG

        self.assertFalse(hasattr(DEFAULT_CONFIG, "registry_filename"))
        self.assertEqual(DEFAULT_CONFIG.log_filename, "loopflow.log")
        self.assertEqual(DEFAULT_CONFIG.worksession_refresh_delay, 0.5)

    def test_log_write_uses_injected_path(self):
        from loopflow.foundation.logging import append_log

        with tempfile.TemporaryDirectory(prefix="loopflow-log-") as raw:
            target = Path(raw) / "injected.log"
            result = append_log("hello-foundation", log_path=target)
            self.assertTrue(result.ok)
            text = target.read_text(encoding="utf-8")
            self.assertIn("hello-foundation", text)

    def test_log_goes_next_to_the_document(self):
        from loopflow.foundation.logging import append_log
        from loopflow.foundation.paths import CONFIG_DIR_NAME
        from loopflow.platform.rhino.memory import MemorySession

        with tempfile.TemporaryDirectory(prefix="loopflow-log-doc-") as raw:
            root = Path(raw)
            result = append_log("hello-project", session=MemorySession(document_path=root / "a.3dm"))
            self.assertTrue(result.ok, result.message)
            written = Path(result.details["log_path"])
            self.assertEqual(written.parent.parent, root / CONFIG_DIR_NAME)
            self.assertIn("hello-project", written.read_text(encoding="utf-8"))

    def test_log_without_document_does_not_write(self):
        from loopflow.foundation.logging import append_log

        result = append_log("should-not-write")
        self.assertFalse(result.ok)
        self.assertEqual(result.stage, "rhino_session")

    def test_package_version_is_single_source(self):
        import loopflow
        from loopflow.foundation.version import PACKAGE_VERSION

        self.assertEqual(loopflow.__version__, PACKAGE_VERSION)


class UserTextKeyTests(unittest.TestCase):
    def test_numbers_are_unique_and_dictionary_columns_match(self):
        from loopflow.features.dictionary.schema import DISPLAY_COLUMNS
        from loopflow.foundation import usertext

        keys = [
            value
            for name, value in vars(usertext).items()
            if name.endswith("_KEY") and isinstance(value, str)
        ]
        numbers = [key.split("_")[1] for key in keys]
        from collections import Counter

        counts = Counter(numbers)
        self.assertEqual(counts["01"], 2)
        for number, count in counts.items():
            if number != "01":
                self.assertEqual(count, 1, number)
        for key in keys:
            self.assertFalse(key.startswith("Q_"))
            number = int(key.split("_")[1])
            display_key = key.rstrip("*")
            if number <= 8:
                self.assertIn(display_key, DISPLAY_COLUMNS)
            else:
                self.assertNotIn(display_key, DISPLAY_COLUMNS)

    def test_write_clears_legacy_and_read_falls_back(self):
        from loopflow.foundation.usertext import OBJECT_ID_KEY, read_text, write_text
        from loopflow.platform.rhino.memory import MemorySession

        session = MemorySession()
        session.add_object("obj")
        session.set_object_user_text("obj", "_12_UUID", "old")
        session.set_object_user_text("obj", "lf_object_id", "old")
        self.assertEqual(read_text(session, "obj", OBJECT_ID_KEY), "old")
        write_text(session, "obj", OBJECT_ID_KEY, "new")
        self.assertEqual(read_text(session, "obj", OBJECT_ID_KEY), "new")
        self.assertIsNone(session.get_object_user_text("obj", "_12_UUID"))
        self.assertIsNone(session.get_object_user_text("obj", "lf_object_id"))

    def test_apply_clears_stale_dimension_keys(self):
        from loopflow.foundation.usertext import clear_stale_object_text
        from loopflow.platform.rhino.memory import MemorySession

        session = MemorySession()
        session.add_object("obj")
        session.set_object_user_text("obj", "_05_寬度W", "90")
        session.set_object_user_text("obj", "_14_座標框", "{}")
        clear_stale_object_text(session, "obj")
        self.assertIsNone(session.get_object_user_text("obj", "_05_寬度W"))
        self.assertIsNone(session.get_object_user_text("obj", "_14_座標框"))


class SourceHygieneTests(unittest.TestCase):
    def test_source_has_no_personal_or_drive_paths(self):
        root = SRC / "loopflow"
        offenders = []
        for path in root.rglob("*.py"):
            text = PUBLIC_URL_RE.sub("", path.read_text(encoding="utf-8"))
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
