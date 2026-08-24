# -*- coding: utf-8 -*-
"""LF_G01_Check_Sample 開發期入口。只檢查目前檔，不寫入。不是產品指令。"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

for _name in list(sys.modules):
    if _name == "loopflow" or _name.startswith("loopflow."):
        del sys.modules[_name]

from loopflow.devtools.check_sample import check_sample  # noqa: E402
from loopflow.platform.rhino.live import open_session  # noqa: E402
from loopflow.platform.rhino.prompts import show_failure_popup, show_message  # noqa: E402


def main() -> None:
    opened = open_session()
    if not opened.ok:
        show_message(opened.message, title="G01 範例檔檢查")
        print(opened.message)
        return
    result = check_sample(opened.details["session"])
    print(result.message)
    if result.ok:
        show_message(result.message, title="G01 範例檔檢查")
    else:
        show_failure_popup(result, title="G01 範例檔檢查")


main()
