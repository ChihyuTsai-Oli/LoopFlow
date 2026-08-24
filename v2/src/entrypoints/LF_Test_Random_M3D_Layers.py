# -*- coding: utf-8 -*-
"""開發期輔助：把選取物件隨機分到 M3D 類型子圖層。不是產品指令。"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1]
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loopflow.devtools.random_m3d_layers import run  # noqa: E402
from loopflow.platform.rhino.live import open_session  # noqa: E402
from loopflow.platform.rhino.prompts import show_message  # noqa: E402


def main() -> None:
    opened = open_session()
    if not opened.ok:
        show_message(opened.message, title="隨機分層（測試）")
        print(opened.message)
        return
    result = run(opened.details["session"])
    print(result.message)
    show_message(result.message, title="隨機分層（測試）")


main()
