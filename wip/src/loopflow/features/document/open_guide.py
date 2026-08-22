# -*- coding: utf-8 -*-
"""LF_Document：用系統瀏覽器開啟 GitHub 文件入口頁。不改模型。"""
from __future__ import annotations

import os
from typing import Callable, Optional

from loopflow.foundation import results
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Document"
STAGE = "open_document"
DOCUMENT_URL = (
    "https://github.com/ChihyuTsai-Oli/LoopFlow/blob/main/docs/README.md"
)

Opener = Callable[[str], None]


def default_opener(url: str) -> None:
    os.startfile(url)


def open_document(*, opener: Optional[Opener] = None) -> results.Result:
    """開啟公開使用說明頁。失敗只說明，不寫 Rhino 文件。"""
    launch = opener or default_opener
    try:
        launch(DOCUMENT_URL)
    except OSError as exc:
        return results.failed(
            STAGE,
            "無法開啟 LoopFlow 文件頁。\n%s" % exc,
            command_id=COMMAND_ID,
            details={"url": DOCUMENT_URL, "exception": repr(exc)},
        )
    except Exception as exc:
        return results.failed(
            STAGE,
            "無法開啟 LoopFlow 文件頁。\n%s" % exc,
            command_id=COMMAND_ID,
            details={"url": DOCUMENT_URL, "exception": repr(exc)},
        )
    return results.ok(
        STAGE,
        t("document.007"),
        command_id=COMMAND_ID,
        details={"url": DOCUMENT_URL},
    )
