# -*- coding: utf-8 -*-
"""NX-07：Verify 通過後組 payload，呼叫 C03 寫入。不自己做 lock。"""
from __future__ import annotations

from typing import Callable, Mapping, Optional

from loopflow.features.model_data.identity import _load_catalog
from loopflow.features.model_data.verify import compare_apply_usertext, format_verify_popup, select_only
from loopflow.features.registry.payload import assemble_payload
from loopflow.features.registry.publisher import publish_registry
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Publish_Exchange"
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
                "局部選取不得發布。請先跑 Nexus 選單 6 檢核通過後再發布。",
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
                format_verify_popup(verified, cannot_publish=True),
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
        outcome = action(session)
    else:
        outcome = run_guarded(session, action, command_id=command_id)
    if "verify_not_passed" in (outcome.blocking or ()):
        select_only(session, (outcome.details or {}).get("mismatch_object_ids") or ())
    return outcome


def run_publish_exchange(
    session: RhinoSession,
    *,
    environ: Optional[Mapping[str, str]] = None,
    catalog=None,
    selected_only: bool = False,
    show_message: Optional[Callable[[str], None]] = None,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """獨立發布指令：先開案檢查，再走既有發布。"""
    from loopflow.features.project.console import run_open_check

    checked = run_open_check(session, environ=environ, command_id=command_id)
    if not checked.ok:
        return checked
    return publish_from_session(
        session,
        environ=environ,
        catalog=catalog,
        selected_only=selected_only,
        cancel=False,
        guarded=False,
        command_id=command_id,
        show_message=show_message,
    )

