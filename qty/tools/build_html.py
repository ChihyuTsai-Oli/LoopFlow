# -*- coding: utf-8 -*-
"""把 qty 的前期評估 Markdown 轉成寬版 HTML 閱讀檔。

格式參照 R2B 的 `wip/docs/前期規劃/資料生態決策表_三家建議.html`：
深色主題、側欄導覽、sticky 表頭與首欄、寬表可橫向捲動。

用法：
    python qty/tools/build_html.py

衍生的 .html 不應手動編輯；改 .md 後重跑本工具。
純 stdlib，不需要任何套件。
"""
from __future__ import annotations

import html
import io
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "docs" / "前期評估"

# 要產生 HTML 的檔案；strength=True 表示依三家建議強度替「你的決定」欄上色
TARGETS = [
    ("決策紀錄_2.md", "LoopFlow QTY — 決策紀錄（第二輪）", True),
    ("測試模型.md", "LoopFlow QTY — 測試模型補強項目", False),
]

CSS = """
:root{color-scheme:dark;--bg:#101417;--panel:#171d21;--line:#39444a;--text:#edf2f3;--muted:#a9b4b8;--accent:#74c9b4}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.65 system-ui,"Noto Sans TC",sans-serif}
.layout{display:grid;grid-template-columns:270px minmax(0,1fr);min-height:100vh}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 20px;border-right:1px solid var(--line);background:#0c1012}
nav strong{display:block;margin-bottom:14px;color:var(--accent);font-size:17px;line-height:1.4}
nav a{display:block;padding:5px 8px;color:var(--muted);text-decoration:none;border-radius:5px;font-size:14px}
nav a.sub{padding-left:20px;font-size:13px}
nav a:hover{color:var(--text);background:#20292d}
main{min-width:0;padding:34px 36px 70px}
h1{margin-top:0;font-size:28px}
h2{margin-top:42px;padding-top:8px;border-top:1px solid var(--line)}
h3{margin-top:28px;color:#cfe6df}
.notice{margin:0 0 22px;padding:12px 16px;border-left:4px solid var(--accent);background:#182421;color:#cde3de}
.tw{max-height:78vh;margin:18px 0 28px;overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel)}
table{width:100%;border-collapse:separate;border-spacing:0}
table.wide{min-width:2200px}
th,td{padding:10px 12px;vertical-align:top;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}
th{position:sticky;top:0;z-index:3;background:#243036;color:#f5faf9;text-align:left}
th:first-child,td:first-child{position:sticky;left:0;z-index:2;background:#1b2428;font-weight:650}
th:first-child{z-index:4;background:#243036}
td.s-strong{color:#ffffff;font-weight:650}
td.s-normal{color:#f5e04a}
td.s-light{color:#6fdc8c}
code{padding:.12em .35em;background:#252d31;border-radius:4px;font-size:.92em}
pre{padding:14px 16px;background:#0c1012;border:1px solid var(--line);border-radius:8px;overflow:auto}
pre code{padding:0;background:none}
blockquote{margin:16px 0;padding:10px 16px;border-left:4px solid #4b5a60;background:#141a1d;color:#cbd6da}
blockquote p:first-child{margin-top:0}blockquote p:last-child{margin-bottom:0}
a{color:var(--accent)}
.legend{margin:0 0 18px;font-size:14px}
.legend span{display:inline-block;margin-right:16px;font-weight:650}
"""

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def inline(text: str) -> str:
    """行內語法。先抽出 <br> 佔位，避免被跳脫。"""
    text = text.replace("<br>", "\x00BR\x00")
    out, last = [], 0
    for m in INLINE_CODE.finditer(text):
        out.append(html.escape(text[last:m.start()]))
        out.append("<code>%s</code>" % html.escape(m.group(1)))
        last = m.end()
    out.append(html.escape(text[last:]))
    s = "".join(out)
    s = BOLD.sub(lambda m: "<strong>%s</strong>" % m.group(1), s)
    s = LINK.sub(lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), s)
    return s.replace("\x00BR\x00", "<br>")


def slug(text: str) -> str:
    s = re.sub(r"[`*\[\]()]", "", text).strip()
    return re.sub(r"\s+", "-", s)


def strength_class(cells: list[str]) -> str:
    """依三家建議欄的強度多數決，決定最後一欄的顏色。"""
    body = " ".join(cells)
    n_strong = body.count("強烈建議")
    n_normal = body.count("一般建議")
    n_light = body.count("輕鬆建議")
    if n_strong >= 2:
        return "s-strong"
    if n_normal >= 2:
        return "s-normal"
    if n_light >= 2:
        return "s-light"
    return ""


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def convert(md: str, colour: bool) -> tuple[str, list[tuple[int, str, str]]]:
    lines = md.split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    i = 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>" % html.escape("\n".join(buf)))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lv, txt = len(m.group(1)), m.group(2)
            sid = slug(txt)
            if lv in (2, 3):
                toc.append((lv, sid, re.sub(r"[`*]", "", txt)))
            out.append("<h%d id=\"%s\">%s</h%d>" % (lv, sid, inline(txt), lv))
            i += 1
            continue

        if ln.startswith(">"):
            buf = []
            while i < len(lines) and (lines[i].startswith(">") or
                                      (buf and lines[i].strip() == "" and
                                       i + 1 < len(lines) and lines[i + 1].startswith(">"))):
                buf.append(re.sub(r"^>\s?", "", lines[i])); i += 1
            inner, _ = convert("\n".join(buf), False)
            out.append("<blockquote>%s</blockquote>" % inner)
            continue

        if ln.strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = split_row(ln)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(split_row(lines[i])); i += 1
            wide = " wide" if len(head) >= 5 else ""
            t = ["<div class=\"tw\"><table class=\"md%s\">" % wide, "<thead><tr>"]
            t += ["<th>%s</th>" % inline(h) for h in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                t.append("<tr>")
                cls = strength_class(r[:-1]) if (colour and len(r) == len(head) and len(head) >= 5) else ""
                for k, c in enumerate(r):
                    last = (k == len(r) - 1)
                    t.append("<td%s>%s</td>" % (
                        (' class="%s"' % cls) if (last and cls) else "", inline(c)))
                t.append("</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        if re.match(r"^\s*[-*]\s+", ln) or re.match(r"^\s*\d+\.\s+", ln):
            ordered = bool(re.match(r"^\s*\d+\.\s+", ln))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i])):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i])); i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue

        if ln.strip() == "" or set(ln.strip()) == {"-"}:
            i += 1
            continue

        para = [ln]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(
                r"^(#{1,4}\s|\||>|```|\s*[-*]\s|\s*\d+\.\s)", lines[i]):
            para.append(lines[i]); i += 1
        out.append("<p>%s</p>" % inline(" ".join(para)))

    return "\n".join(out), toc


def build(md_path: Path, title: str, colour: bool) -> Path:
    md = io.open(md_path, encoding="utf-8").read()
    body, toc = convert(md, colour)
    nav = "".join('<a class="%s" href="#%s">%s</a>' % ("sub" if lv == 3 else "", sid, html.escape(t))
                  for lv, sid, t in toc)
    legend = ""
    if colour:
        legend = ('<p class="legend">決定欄顏色（依三家建議強度）：'
                  '<span style="color:#ffffff">白＝強烈建議×2+</span>'
                  '<span style="color:#f5e04a">黃＝一般建議×2+</span>'
                  '<span style="color:#6fdc8c">綠＝輕鬆建議×2+</span></p>')
    doc = (
        '<!doctype html>\n<html lang="zh-Hant">\n<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>%s</title><style>%s</style></head>\n" % (html.escape(title), CSS) +
        '<body><div class="layout"><nav><strong>%s</strong>%s</nav>\n<main>' % (html.escape(title), nav) +
        '<div class="notice">本檔由 <code>qty/tools/build_html.py</code> 依 '
        '<code>%s</code> 產生，<strong>不應手動編輯</strong>。改 Markdown 後重跑工具。</div>\n' % md_path.name +
        legend + body + "</main></div></body></html>\n"
    )
    out = md_path.with_suffix(".html")
    io.open(out, "w", encoding="utf-8").write(doc)
    return out


def main() -> int:
    if not DOCS.is_dir():
        print("找不到文件資料夾：%s" % DOCS, file=sys.stderr)
        return 1
    for name, title, colour in TARGETS:
        p = DOCS / name
        if not p.is_file():
            print("略過（不存在）：%s" % name)
            continue
        out = build(p, title, colour)
        print("%-22s -> %-22s %7d bytes" % (name, out.name, out.stat().st_size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
