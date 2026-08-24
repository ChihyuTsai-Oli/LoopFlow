# -*- coding: utf-8 -*-
"""讀正式 Registry 或 last-good。只讀不寫、不建檔、不搶 lock。"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional

from loopflow.features.registry.validate import validate_payload
from loopflow.foundation import atomic_io, results
from loopflow.foundation.paths import normalize_project_id, resolve_registry_for_document
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Infuser_Part"


def _empty(command_id: str, warning: str, message: str) -> results.Result:
    return results.ok_with_warnings(
        "read_registry",
        message,
        (warning,),
        command_id=command_id,
        details={
            "payload": None,
            "source": None,
            "registry_revision": None,
            "path": None,
        },
    )


def _from_file(path: Path, source: str, command_id: str) -> results.Result:
    loaded = atomic_io.read_json(path)
    if not loaded.ok:
        return results.failed(
            "read_registry",
            t("infuser.038") % loaded.message,
            command_id=command_id,
            details={"filename": path.name, "source": source},
        )
    payload = loaded.details["payload"]
    checked = validate_payload(payload)
    if not checked.ok:
        return results.blocked(
            "validate_registry",
            t("infuser.039") % checked.message,
            checked.blocking or ("invalid_registry",),
            command_id=command_id,
            details={"filename": path.name, "source": source},
        )
    return results.ok(
        "read_registry",
        t("infuser.036") % payload.get("registry_revision"),
        command_id=command_id,
        details={
            "payload": payload,
            "source": source,
            "registry_revision": payload.get("registry_revision"),
            "path": str(path),
        },
    )


def load_published_registry(
    project_id: Optional[str],
    *,
    document_path: Optional[str] = None,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """正式檔優先；沒有正式檔才用 last-good。不建立空檔。"""
    pid = normalize_project_id(project_id)
    if not pid:
        return _empty(
            command_id,
            "missing_project_id",
            t("infuser.037"),
        )
    resolved = resolve_registry_for_document(document_path, pid)
    if not resolved.ok:
        return resolved
    official = Path(resolved.details["registry"])
    last_good = Path(resolved.details["last_good"])
    if official.is_file():
        return _from_file(official, "official", command_id)
    if last_good.is_file():
        loaded = _from_file(last_good, "last_good", command_id)
        if not loaded.ok:
            return loaded
        return results.ok_with_warnings(
            loaded.stage,
            t("infuser.040")
            % loaded.details.get("registry_revision"),
            ("used_last_good",),
            command_id=command_id,
            details=loaded.details,
        )
    return _empty(
        command_id,
        "missing_registry",
        t("infuser.035"),
    )
