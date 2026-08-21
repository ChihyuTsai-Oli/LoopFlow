# -*- coding: utf-8 -*-
"""C03 Registry 安全發布：lock、pending、validate、atomic replace、last-good。"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
CONTRACT = WIP / "fixtures" / "contract" / "registry"
SCHEMA = WIP / "fixtures" / "schema" / "registry.json"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.registry import schema
from loopflow.features.registry.lock import acquire_lock, release_lock
from loopflow.features.registry.publisher import publish_registry
from loopflow.features.registry.validate import validate_payload
from loopflow.foundation.atomic_io import read_json
from loopflow.foundation.paths import CONFIG_DIR_NAME

PROJECT_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"


def _min_payload(**overrides):
    body = {
        "schema_id": "loopflow.registry",
        "schema_version": 1,
        "project_id": PROJECT_ID,
        "registry_revision": 1,
        "published_at": "2026-08-14T00:00:00Z",
        "model_unit": "Centimeters",
        "types": [],
        "spaces": [{"space_id": "EXT", "level_id": None, "space_display": "EXT"}],
        "objects": [],
        "extension": {},
    }
    body.update(overrides)
    return body


def _paths(root: Path):
    """Registry 落在 .3dm 同層的 `_LoopFlow_Config/<專案名稱>/`。"""
    folder = root / CONFIG_DIR_NAME / PROJECT_ID
    return {
        "root": root,
        "document_path": str(root / "model.3dm"),
        "folder": folder,
        "registry": folder / "Project_Registry.json",
        "lock": folder / "Project_Registry.lock",
        "pending": folder / "Project_Registry.pending.json",
        "last_good": folder / "Project_Registry.last-good.json",
    }


def _publish(info, payload=None, **kwargs):
    kwargs.setdefault("document_path", info["document_path"])
    return publish_registry(payload if payload is not None else _min_payload(), **kwargs)


class SchemaAndValidateTests(unittest.TestCase):
    def test_schema_matches_fixture(self):
        spec = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema.SCHEMA_ID, spec["schema_id"])
        self.assertEqual(schema.SCHEMA_VERSION, spec["schema_version"])
        self.assertEqual(list(schema.REQUIRED_ROOT), spec["required_root"])
        self.assertEqual(list(schema.TYPE_KEYS), spec["type_keys"])
        self.assertEqual(list(schema.SPACE_KEYS), spec["space_keys"])
        self.assertEqual(list(schema.OBJECT_KEYS), spec["object_keys"])
        self.assertEqual(schema.RESERVED_SPACE_ID, spec["reserved_space_id"])

    def test_contract_cases(self):
        cases = json.loads((CONTRACT / "cases.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            result = validate_payload(case["payload"])
            if case["expect"] == "pass":
                self.assertTrue(result.ok, case["id"] + ": " + result.message)
            else:
                self.assertFalse(result.ok, case["id"])
                self.assertEqual(result.status, "blocked", case["id"])

    def test_forbidden_dimension_fields_block(self):
        payload = _min_payload()
        payload["types"] = [
            {
                "type_id": "EX-01",
                "type_category": "EX",
                "type_sequence": "01",
                "type_display_name": "樑",
                "layer_path": "00_STR_結構::Beam.樑",
                "estimation_unit": "樘",
                "measurement_rule": "COUNT",
                "elevation_basis": "BH",
                "construction_default": "Existing",
                "remarks_default": None,
            }
        ]
        payload["objects"] = [
            {
                "object_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                "type_id": "EX-01",
                "type_category": "EX",
                "type_sequence": "01",
                "type_display_name": "樑",
                "construction_status": "Existing",
                "space_id": "EXT",
                "space_display": "EXT",
                "elevation_basis": "BH",
                "elevation_value": 0,
                "elevation_display": "BH 0",
                "remarks": None,
                "data_revision": 1,
                "quantity": 1,
            }
        ]
        result = validate_payload(payload)
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("forbidden_object_field",))


class PublishTests(unittest.TestCase):
    def test_missing_document_path_does_not_create_files(self):
        before = set(Path(tempfile.gettempdir()).iterdir())
        result = publish_registry(_min_payload())
        after = set(Path(tempfile.gettempdir()).iterdir())
        self.assertFalse(result.ok)
        self.assertEqual(result.blocking, ("unsaved_document",))
        self.assertEqual(before, after)

    def test_first_publish_writes_official_and_last_good(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            result = _publish(info)
            self.assertTrue(result.ok, result.message)
            self.assertEqual(result.details["registry_revision"], 1)
            self.assertTrue(info["registry"].exists())
            self.assertTrue(info["last_good"].exists())
            self.assertFalse(info["pending"].exists())
            self.assertFalse(info["lock"].exists())
            loaded = read_json(info["registry"])
            self.assertTrue(loaded.ok)
            self.assertEqual(loaded.details["payload"]["registry_revision"], 1)
            self.assertEqual(info["registry"].read_bytes(), info["last_good"].read_bytes())

    def test_second_publish_increments_and_keeps_previous_last_good(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            first = _publish(info)
            self.assertTrue(first.ok, first.message)
            previous = info["registry"].read_bytes()
            second = _publish(info)
            self.assertTrue(second.ok, second.message)
            self.assertEqual(second.details["registry_revision"], 2)
            self.assertEqual(read_json(info["registry"]).details["payload"]["registry_revision"], 2)
            self.assertEqual(info["last_good"].read_bytes(), previous)

    def test_invalid_payload_does_not_write_official(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            result = _publish(info, _min_payload(spaces=[]))
            self.assertFalse(result.ok)
            self.assertEqual(result.blocking, ("missing_ext_space",))
            self.assertFalse(info["registry"].exists())
            self.assertFalse(info["pending"].exists())
            self.assertFalse(info["lock"].exists())

    def test_bad_official_json_stops_without_overwrite(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            info["folder"].mkdir(parents=True)
            info["registry"].write_text("{not json", encoding="utf-8")
            before = info["registry"].read_bytes()
            result = _publish(info)
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "read_registry")
            self.assertEqual(info["registry"].read_bytes(), before)
            self.assertFalse(info["pending"].exists())
            self.assertFalse(info["lock"].exists())

    def test_live_lock_blocks_second_publisher(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            first = _publish(info)
            self.assertTrue(first.ok, first.message)
            before = info["registry"].read_bytes()
            info["folder"].mkdir(parents=True, exist_ok=True)
            held = acquire_lock(info["lock"], pid=4242, host="test-host", pid_alive=lambda pid: True)
            self.assertTrue(held.ok, held.message)
            try:
                result = _publish(
                    info,
                    pid=4343,
                    host="test-host",
                    pid_alive=lambda pid: True,
                )
                self.assertFalse(result.ok)
                self.assertEqual(result.blocking, ("registry_locked",))
                self.assertEqual(info["registry"].read_bytes(), before)
            finally:
                release_lock(info["lock"], pid=4242, host="test-host")

    def test_stale_lock_can_be_taken(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            info["folder"].mkdir(parents=True)
            stale_time = datetime.now(timezone.utc) - timedelta(seconds=120)
            acquire_lock(
                info["lock"],
                pid=9999,
                host="test-host",
                now=stale_time,
                pid_alive=lambda pid: True,
            )
            result = _publish(
                info,
                pid=1000,
                host="test-host",
                now=datetime.now(timezone.utc),
                pid_alive=lambda pid: True,
            )
            self.assertTrue(result.ok, result.message)
            self.assertFalse(info["lock"].exists())

    def test_interrupt_after_pending_keeps_official(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            first = _publish(info)
            self.assertTrue(first.ok, first.message)
            before = info["registry"].read_bytes()
            last_good = info["last_good"].read_bytes()

            def _boom(_pending):
                raise RuntimeError("simulated interrupt")

            result = _publish(
                info,
                after_pending=_boom,
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "publish_registry")
            self.assertEqual(info["registry"].read_bytes(), before)
            self.assertEqual(info["last_good"].read_bytes(), last_good)
            self.assertFalse(info["pending"].exists())
            self.assertFalse(info["lock"].exists())

    def test_replace_failure_keeps_official(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            first = _publish(info)
            self.assertTrue(first.ok, first.message)
            before = info["registry"].read_bytes()
            last_good = info["last_good"].read_bytes()

            def _fail(_src, _dest):
                raise OSError("disk full")

            result = _publish(
                info,
                replace=_fail,
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "replace_registry")
            self.assertEqual(info["registry"].read_bytes(), before)
            self.assertEqual(info["last_good"].read_bytes(), last_good)
            self.assertFalse(info["pending"].exists())
            self.assertFalse(info["lock"].exists())

    def test_sharing_violation_retries_then_succeeds(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            first = _publish(info)
            self.assertTrue(first.ok, first.message)
            calls = []

            def _flaky(src, dest):
                calls.append(1)
                if len(calls) < 3:
                    err = OSError(32, "file in use")
                    err.winerror = 32
                    raise err
                os.replace(str(src), str(dest))

            result = _publish(
                info,
                replace=_flaky,
                sleep=lambda _wait: None,
            )
            self.assertTrue(result.ok, result.message)
            self.assertEqual(len(calls), 3)
            self.assertEqual(
                read_json(info["registry"]).details["payload"]["registry_revision"],
                2,
            )

    def test_sharing_violation_keeps_official_and_saves_last_good(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            info = _paths(Path(raw))
            first = _publish(info)
            self.assertTrue(first.ok, first.message)
            before = info["registry"].read_bytes()

            def _fail(_src, _dest):
                err = OSError(32, "file in use")
                err.winerror = 32
                raise err

            result = _publish(
                info,
                replace=_fail,
                sleep=lambda _wait: None,
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.stage, "replace_registry")
            self.assertIn("雲端同步", result.message)
            self.assertIn("不要刪", result.message)
            self.assertEqual(info["registry"].read_bytes(), before)
            self.assertEqual(
                read_json(info["last_good"]).details["payload"]["registry_revision"],
                2,
            )
            self.assertFalse(info["pending"].exists())
            self.assertFalse(info["lock"].exists())

    def test_lock_contains_pid_host_and_time(self):
        with tempfile.TemporaryDirectory(prefix="loopflow-reg-") as raw:
            lock_path = Path(raw) / "Project_Registry.lock"
            stamp = datetime(2026, 8, 15, 10, 0, tzinfo=timezone.utc)
            result = acquire_lock(
                lock_path,
                pid=321,
                host="studio-pc",
                now=stamp,
                pid_alive=lambda pid: True,
            )
            self.assertTrue(result.ok, result.message)
            data = json.loads(lock_path.read_text(encoding="utf-8"))
            self.assertEqual(data["pid"], 321)
            self.assertEqual(data["host"], "studio-pc")
            self.assertEqual(data["acquired_at"], "2026-08-15T10:00:00Z")
            release_lock(lock_path, pid=321, host="studio-pc")
            self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
