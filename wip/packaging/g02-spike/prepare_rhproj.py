# -*- coding: utf-8 -*-
"""把 LoopFlow.rhproj 的指令路徑改成這台電腦的絕對路徑，供 RhinoCode 建置。"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: prepare_rhproj.py <rhproj> <command.py> <output>")
        return 2
    rhproj = Path(sys.argv[1])
    command = Path(sys.argv[2]).resolve()
    output = Path(sys.argv[3])
    data = json.loads(rhproj.read_text(encoding="utf-8"))
    if not data.get("codes"):
        print("LoopFlow.rhproj has empty codes")
        return 1
    data["codes"][0]["path"] = str(command)
    data["codes"][0]["uri"] = command.as_uri()
    # 字串 "python3" 會被當成 C#；必須是 LanguageSpec 物件。
    data["codes"][0]["language"] = {"id": "*.*.python", "version": "3.*.*"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("prepared", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
