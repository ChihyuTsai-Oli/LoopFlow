# -*- coding: utf-8 -*-
"""從介面語系定稿產出 runtime 句子表。

    python wip/tools/build_i18n_catalog.py
    python wip/tools/build_i18n_catalog.py --check
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SOURCE = WIP / "docs" / "介面語系" / "3_claude" / "介面語系_final.md"
OUTPUT = WIP / "src" / "loopflow" / "foundation" / "i18n_catalog.json"


def _cells(line: str):
    if not line.startswith("|"):
        return None
    parts = [part.strip() for part in line.strip().strip("|").split("|")]
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]


def parse_catalog(text: str) -> dict:
    rows = {}
    in_table = False
    for line in text.splitlines():
        parsed = _cells(line)
        if parsed is None:
            in_table = False
            continue
        key, zh, en = parsed
        header = key.replace("`", "").replace("（現況標題）", "").strip()
        if header == "id":
            in_table = True
            continue
        if set(header) <= set("-: "):
            continue
        if not in_table:
            continue
        ident = key.strip().strip("`")
        if "." not in ident and not ident.startswith("locale") and not ident.startswith("dict"):
            continue
        if ident in rows:
            raise ValueError("重複句子 id：%s" % ident)
        rows[ident] = {"zh-TW": zh, "en": en}
    return rows


def build() -> dict:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    return parse_catalog(SOURCE.read_text(encoding="utf-8"))


def write_catalog(rows: dict) -> Path:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(rows, ensure_ascii=False, indent=2) + "\n"
    OUTPUT.write_text(payload, encoding="utf-8")
    return OUTPUT


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    rows = build()
    if not rows:
        print("句子表是空的。", file=sys.stderr)
        return 1
    if args.check:
        if not OUTPUT.is_file():
            print("缺少 %s，請先產出。" % OUTPUT.name, file=sys.stderr)
            return 1
        existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
        if existing != rows:
            print("i18n_catalog.json 已過期，請重新執行本腳本。", file=sys.stderr)
            return 1
        print("句子表 %s 筆，與定稿一致。" % len(rows))
        return 0
    path = write_catalog(rows)
    print("已寫入 %s（%s 筆）。" % (path.name, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
