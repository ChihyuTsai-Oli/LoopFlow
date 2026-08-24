# -*- coding: utf-8 -*-
"""獨立指令：匯出 Type Layers 為字典。先開案檢查，再呼叫既有匯出。"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from loopflow.features.dictionary.loader import TypeCatalog
from loopflow.features.dictionary.sync import export_dictionary
from loopflow.features.project.console import run_open_check
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession

COMMAND_ID = "LF_Export_Type_Layers"


def run_export_type_layers(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    export_path: Optional[Path] = None,
    show_message: Optional[Callable[[str], None]] = None,
    command_id: str = COMMAND_ID,
) -> results.Result:
    checked = run_open_check(session, command_id=command_id)
    if not checked.ok:
        return checked
    return export_dictionary(
        session,
        catalog=catalog,
        export_path=export_path,
        guarded=False,
        command_id=command_id,
        show_message=show_message,
    )
