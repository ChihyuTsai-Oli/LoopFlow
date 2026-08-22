# -*- coding: utf-8 -*-
"""G01：範例 .3dm 只讀檢查。不寫入、不是產品指令。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.devtools.check_sample import COMMAND_ID, check_sample
from loopflow.foundation.paths import CONFIG_DIR_NAME
from loopflow.foundation.project_config import CONFIG_FILENAME
from loopflow.platform.rhino.memory import MemorySession


class SampleCheckTests(unittest.TestCase):
    def _saved_session(self, folder: Path) -> MemorySession:
        document = folder / "sample.3dm"
        document.write_text("placeholder", encoding="utf-8")
        return MemorySession(document_path=str(document))

    def _write_config(self, folder: Path, **fields) -> None:
        config_dir = folder / CONFIG_DIR_NAME
        config_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_id": "loopflow.project",
            "schema_version": 1,
        }
        payload.update(fields)
        (config_dir / CONFIG_FILENAME).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def test_missing_session_fails(self):
        result = check_sample(None)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.command_id, COMMAND_ID)

    def test_unsaved_document_is_blocked(self):
        result = check_sample(MemorySession())
        self.assertFalse(result.ok)
        self.assertIn("存成 .3dm", result.message)

    def test_legacy_document_env_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            session.set_document_user_text("lf_project_id", "M3D")
            session.set_document_modified(False)
            result = check_sample(session)
            self.assertEqual(result.status, "blocked")
            self.assertIn("legacy_document_env", result.blocking)
            self.assertEqual(session.document_user_text("lf_project_id"), "M3D")
            self.assertFalse(session.document_modified())

    def test_stale_dimension_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            self._write_config(folder)
            session.add_object("obj-1", layer="M3D::Wall", user_text={"_05_寬度W": "120"})
            result = check_sample(session)
            self.assertEqual(result.status, "blocked")
            self.assertIn("stale_dimension", result.blocking)
            self.assertEqual(session.get_object_user_text("obj-1", "_05_寬度W"), "120")

    def test_legacy_tag_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            self._write_config(folder)
            session.add_object("tag-1", user_text={"attr_ch_key": "CH"})
            session.set_block("tag-1", (0, 0, 0), name="TAG_HEIGHT_GRAB")
            result = check_sample(session)
            self.assertEqual(result.status, "blocked")
            self.assertIn("legacy_tag_key", result.blocking)

    def test_legacy_frame_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            self._write_config(folder)
            session.add_object("frame-1", user_text={"DWG_NO": "101"})
            session.set_block("frame-1", (0, 0, 0), name="sample_frame")
            result = check_sample(session)
            self.assertEqual(result.status, "blocked")
            self.assertIn("legacy_tag_key", result.blocking)

    def test_object_legacy_uuid_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            self._write_config(folder)
            session.add_object("obj-2", user_text={"lf_object_id": "abc"})
            result = check_sample(session)
            self.assertEqual(result.status, "blocked")
            self.assertIn("legacy_object_key", result.blocking)

    def test_clean_canonical_object_is_ok_with_missing_dictionary_warning(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            self._write_config(folder, project_id="M3D", layer_prefix="M3D")
            session.add_object(
                "obj-3",
                layer="M3D::Wall",
                user_text={"_07_UUID": "11111111-1111-4111-8111-111111111111"},
            )
            session.set_document_user_text("lf_title_frame_blocks", "sample_frame")
            result = check_sample(session)
            self.assertTrue(result.ok)
            self.assertEqual(result.status, "ok_with_warnings")
            self.assertIn("missing_dictionary", result.warnings)
            self.assertNotIn("[阻擋]", result.message)

    def test_unknown_schema_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            session = self._saved_session(folder)
            self._write_config(folder, schema_id="loopflow.unknown", schema_version=1)
            result = check_sample(session)
            self.assertEqual(result.status, "blocked")
            self.assertIn("bad_schema", result.blocking)


if __name__ == "__main__":
    unittest.main()
