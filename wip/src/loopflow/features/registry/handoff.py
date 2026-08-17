# -*- coding: utf-8 -*-
"""NX-07：Verify 通過後組 payload，呼叫 C03 寫入。不自己做 lock。"""
from __future__ import annotations

from typing import Callable, Mapping, Optional

from loopflow.features.model_data.identity import _load_catalog
from loopflow.features.model_data.verify import compare_apply_usertext
from loopflow.features.registry.payload import assemble_payload
from loopflow.features.registry.publisher import publish_registry
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
PROJECT_ID_KEY = "lf_project_id"


def publish_from_session(
    session: RhinoSession,
    *,
    environ: Optional[Mapping[str, str]] = None,
    catalog=None,
    selected_only: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
    show_message: Optional[Callable[[str], None]] = None,
) -> results.Result:
    """全案 Verify 通過才發布。局部選取不得宣告可發布。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "publish_registry",
                "使用者取消發布。",
                command_id=command_id,
            )
        if selected_only:
            return results.blocked(
                "publish_registry",
                "局部選取不得發布。請用全案 Verify 通過後再發布。",
                blocking=("partial_scan_cannot_publish",),
                command_id=command_id,
                details={"publish_ready": False},
            )
        project_id = current.document_user_text(PROJECT_ID_KEY)
        verified = compare_apply_usertext(
            current,
            catalog=catalog,
            environ=environ,
            selected_only=False,
            command_id=command_id,
        )
        if not verified.ok:
            return verified
        mismatches = (verified.details or {}).get("mismatch_count") or 0
        if mismatches or "usertext_mismatch" in (verified.warnings or ()):
            return results.blocked(
                "publish_registry",
                "尚未通過 Verify，不能發布。",
                blocking=("verify_not_passed",),
                command_id=command_id,
                details=dict(verified.details or {}, publish_ready=False),
            )
        loaded = _load_catalog(catalog, environ, current)
        if not loaded.ok:
            return loaded
        type_catalog = loaded.details["catalog"]
        payload = assemble_payload(
            current,
            type_catalog,
            project_id=project_id,
            model_unit=current.model_unit_system(),
        )
        written = publish_registry(
            payload,
            environ=environ,
            command_id=command_id,
        )
        details = dict(written.details or {})
        details["publish_ready"] = bool(written.ok)
        details["object_count"] = len(payload.get("objects") or ())
        if not written.ok:
            return results.Result(
                ok=written.ok,
                status=written.status,
                stage=written.stage,
                message=written.message,
                command_id=command_id,
                warnings=written.warnings,
                blocking=written.blocking,
                details=details,
            )
        from loopflow.features.model_data.identity import iter_scan_targets
        from loopflow.foundation.usertext import DATA_REVISION_KEY, write_text

        revision = details.get("registry_revision")
        if revision is not None:
            revision_text = str(revision)
            for object_id in iter_scan_targets(current, selected_only=False):
                write_text(current, object_id, DATA_REVISION_KEY, revision_text)
        message = written.message
        if callable(show_message):
            show_message(message)
        else:
            from loopflow.platform.rhino.prompts import show_message as live_popup

            live_popup(message)
        return results.ok(
            "publish_registry",
            message,
            command_id=command_id,
            details=details,
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)
