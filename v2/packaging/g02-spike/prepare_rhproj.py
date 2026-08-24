# -*- coding: utf-8 -*-
"""把 LoopFlow.rhproj 的每支指令路徑改成這台電腦的絕對路徑，供 RhinoCode 建置。"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: prepare_rhproj.py <rhproj> <output>")
        return 2
    rhproj = Path(sys.argv[1])
    output = Path(sys.argv[2])
    data = json.loads(rhproj.read_text(encoding="utf-8"))
    codes = data.get("codes") or []
    if not codes:
        print("LoopFlow.rhproj has empty codes")
        return 1
    spike = rhproj.resolve().parent
    for code in codes:
        relative = Path(str(code.get("path") or ""))
        command = (spike / relative).resolve() if not relative.is_absolute() else relative
        if not command.is_file():
            print("missing command script:", command)
            return 1
        code["path"] = str(command)
        code["uri"] = command.as_uri()
        # 字串 "python3" 會被當成 C#；必須是 LanguageSpec 物件。
        code["language"] = {"id": "*.*.python", "version": "3.*.*"}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("prepared", output, "commands", len(codes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
