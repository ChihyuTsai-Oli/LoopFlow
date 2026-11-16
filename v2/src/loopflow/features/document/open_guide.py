# -*- coding: utf-8 -*-
"""LF_Document：開啟 GitHub 文件與本機官方範本資料夾。不改模型。"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional

from loopflow.foundation import results
from loopflow.foundation.i18n import t
from loopflow.foundation.templates import documents_loopflow_dir

COMMAND_ID = "LF_Document"
STAGE = "open_document"
DOCUMENT_URL = (
    "https://github.com/ChihyuTsai-Oli/LoopFlow/blob/main/docs/README.md"
)

Opener = Callable[[str], None]
FolderOpener = Callable[[Path], None]


def default_opener(url: str) -> None:
    os.startfile(url)


def default_folder_opener(folder: Path) -> None:
    os.startfile(str(folder))


def open_document(
    *,
    opener: Optional[Opener] = None,
    folder_opener: Optional[FolderOpener] = None,
    folder_path: Optional[Path] = None,
) -> results.Result:
    """各自嘗試開啟網頁與官方範本資料夾；其中一項失敗仍執行另一項。"""
    launch = opener or default_opener
    launch_folder = folder_opener or default_folder_opener
    folder = Path(folder_path) if folder_path is not None else documents_loopflow_dir()
    errors = []
    opened_url = False
    opened_folder = False
    try:
        launch(DOCUMENT_URL)
        opened_url = True
    except Exception as exc:
        errors.append(t("document.008") % exc)
    try:
        launch_folder(folder)
        opened_folder = True
    except Exception as exc:
        errors.append(t("document.010") % exc)
    details = {
        "url": DOCUMENT_URL,
        "folder": str(folder),
        "opened_url": opened_url,
        "opened_folder": opened_folder,
    }
    if errors:
        return results.failed(
            STAGE,
            "\n".join(errors),
            command_id=COMMAND_ID,
            details=details,
        )
    return results.ok(
        STAGE,
        t("document.009"),
        command_id=COMMAND_ID,
        details=details,
    )
