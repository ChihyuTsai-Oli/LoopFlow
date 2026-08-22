# -*- coding: utf-8 -*-
"""D08 開發輔助：全檔圖塊舊顯示欄抄到 lf_* 後刪除。不是產品指令。"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# ScriptEditor 重跑同一支時會沿用記憶體裡的舊模組；先清掉再載入。
for _name in list(sys.modules):
    if _name == "loopflow" or _name.startswith("loopflow."):
        del sys.modules[_name]

from loopflow.devtools.migrate_block_display_keys import (  # noqa: E402
    run_migrate_block_display_keys,
)
from loopflow.platform.rhino.live import open_session  # noqa: E402
from loopflow.platform.rhino.prompts import show_failure_popup, show_message  # noqa: E402


def main() -> None:
    opened = open_session()
    if not opened.ok:
        show_message(opened.message, title="清除圖塊舊欄")
        print(opened.message)
        return
    result = run_migrate_block_display_keys(opened.details["session"])
    print(result.message)
    if result.ok or result.status == "cancelled":
        show_message(result.message, title="清除圖塊舊欄")
    else:
        show_failure_popup(result, title="清除圖塊舊欄")


main()
