#!/usr/bin/env python3
"""Build a wide, offline HTML view of 資料生態決策表.md."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from build_workflow_html import convert


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SRC = ROOT / "docs" / "前期規劃" / "資料生態決策表.md"
DEFAULT_OUT = DEFAULT_SRC.with_suffix(".html")

CSS = r"""
:root{color-scheme:dark;--bg:#101417;--panel:#171d21;--line:#39444a;--text:#edf2f3;--muted:#a9b4b8;--accent:#74c9b4;--amber:#e4b86a;--red:#ef8c84;--purple:#b9a2eb}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--text);font:15px/1.65 system-ui,-apple-system,"Segoe UI","Noto Sans TC",sans-serif}
.layout{display:grid;grid-template-columns:250px minmax(0,1fr);min-height:100vh}nav{position:sticky;top:0;height:100vh;overflow:auto;padding:28px 20px;border-right:1px solid var(--line);background:#0c1012}nav strong{display:block;margin-bottom:14px;color:var(--accent);font-size:18px}nav a{display:block;padding:6px 8px;color:var(--muted);text-decoration:none;border-radius:5px}nav a:hover,nav a.active{color:var(--text);background:#20292d}
main{min-width:0;padding:34px 36px 70px}h1{margin-top:0;font-size:30px}h2{margin-top:48px;padding-top:8px;border-top:1px solid var(--line)}h3{margin-top:30px;color:#dce9e7}a{color:#8fd9c7}code{padding:.12em .35em;background:#252d31;border-radius:4px}.notice{margin:0 0 26px;padding:12px 16px;border-left:4px solid var(--accent);background:#182421;color:#cde3de}
.tw{max-height:76vh;margin:18px 0 32px;overflow:auto;border:1px solid var(--line);border-radius:8px;background:var(--panel);box-shadow:0 10px 28px #0005}table{width:100%;border-collapse:separate;border-spacing:0}table.strength{min-width:720px}table.single-ai{min-width:1650px}table.dual-ai{min-width:2050px}th,td{padding:10px 12px;vertical-align:top;border-right:1px solid var(--line);border-bottom:1px solid var(--line)}th{position:sticky;top:0;z-index:3;background:#243036;color:#f5faf9;text-align:left}th:first-child,td:first-child{position:sticky;left:0;z-index:2;background:#1b2428;font-weight:650}th:first-child{z-index:4;background:#243036}.tw tr:last-child td{border-bottom:0}.tw th:last-child,.tw td:last-child{border-right:0}tbody tr:hover td{background:#202c30}tbody tr:hover td:first-child{background:#263338}
.dual-ai.cols-6 th:nth-child(1){width:5%}.dual-ai.cols-6 th:nth-child(2){width:15%}.dual-ai.cols-6 th:nth-child(3),.dual-ai.cols-6 th:nth-child(4),.dual-ai.cols-6 th:nth-child(5){width:21%}.dual-ai.cols-6 th:nth-child(6){width:17%}
.dual-ai.cols-7 th:nth-child(1){width:4%}.dual-ai.cols-7 th:nth-child(2){width:12%}.dual-ai.cols-7 th:nth-child(3){width:15%}.dual-ai.cols-7 th:nth-child(4),.dual-ai.cols-7 th:nth-child(5),.dual-ai.cols-7 th:nth-child(6){width:18%}.dual-ai.cols-7 th:nth-child(7){width:15%}
.single-ai th:nth-child(1){width:5%}.single-ai th:nth-child(2){width:13%}.single-ai th:nth-child(3){width:24%}.single-ai th:nth-child(4){width:20%}.single-ai th:nth-child(5){width:21%}.single-ai th:nth-child(6){width:17%}
tr.adopted td:last-child{background:#173329}tr.partial td:last-child{background:#3a2e18}tr.pending td:last-child{background:#292f32;color:#c1c9cc}tr.delayed td:last-child{background:#29233a}td.conflict{box-shadow:inset 4px 0 var(--red);background:#382322!important}
blockquote{margin:18px 0;padding:10px 16px;border-left:4px solid var(--amber);background:#211f18;color:#ded5bd}ul,ol{padding-left:24px}
@media(max-width:900px){.layout{display:block}nav{position:static;width:auto;height:auto;border-right:0;border-bottom:1px solid var(--line)}main{padding:24px 16px}}
@media print{body{background:#fff;color:#111}.layout{display:block}nav,.notice{display:none}main{padding:0}.tw{max-height:none;overflow:visible;box-shadow:none}table.dual-ai,table.single-ai,table.strength{min-width:0;font-size:8pt}th{position:static;background:#ddd;color:#111}th:first-child,td:first-child{position:static;background:#eee}}
"""

SCRIPT = r"""
document.querySelectorAll('.tw tbody tr').forEach(row=>{
  const cells=row.querySelectorAll('td'); if(!cells.length)return;
  const decision=cells[cells.length-1].textContent;
  if(decision.includes('部分採用'))row.classList.add('partial');
  else if(decision.includes('採用'))row.classList.add('adopted');
  else if(decision.includes('待決定'))row.classList.add('pending');
  else if(decision.includes('延後'))row.classList.add('delayed');
  if(cells.length>1 && cells[cells.length-2].textContent.includes('衝突'))cells[cells.length-2].classList.add('conflict');
});
const links=[...document.querySelectorAll('nav a')];
const sections=links.map(a=>document.getElementById(a.hash.slice(1))).filter(Boolean);
sections.forEach(s=>new IntersectionObserver(entries=>entries.forEach(e=>{if(e.isIntersecting){links.forEach(a=>a.classList.toggle('active',a.hash==='#'+e.target.id));}}),{rootMargin:'-15% 0px -75%'}).observe(s));
"""


def classify_tables(body: str) -> str:
    pattern = re.compile(r'<div class="tw"><table>(.*?)</table></div>', re.S)

    def replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        header_match = re.search(r"<thead>(.*?)</thead>", inner, re.S)
        header = header_match.group(1) if header_match else ""
        columns = len(re.findall(r"<th(?:\s|>)", header))
        if "Claude 建議" in header:
            kind = "dual-ai"
        elif "AI 建議整合／衝突" in header:
            kind = "single-ai"
        else:
            kind = "strength"
        return f'<div class="tw"><table class="{kind} cols-{columns}">{inner}</table></div>'

    return pattern.sub(replace, body)


def render(markdown: str) -> str:
    body, toc = convert(markdown)
    body = classify_tables(body)
    nav = "\n".join(
        f'<a href="#{anchor}">{title}</a>'
        for level, title, anchor, _variant in toc
        if level == 2
    )
    return f"""<!doctype html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>LoopFlow 資料生態決策表</title><style>{CSS}</style></head>
<body><div class="layout"><nav><strong>資料生態決策表</strong>{nav}</nav><main><div class="notice">這是由 Markdown 產生的寬版閱讀檔。內容請修改 <code>資料生態決策表.md</code>，再執行產生器更新本頁。</div>{body}</main></div><script>{SCRIPT}</script></body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(args.src.read_text(encoding="utf-8"))
    if args.check:
        if not args.out.exists() or args.out.read_text(encoding="utf-8") != expected:
            print(f"stale: {args.out}")
            return 1
        print(f"ok: {args.out}")
        return 0
    args.out.write_text(expected, encoding="utf-8", newline="\n")
    print(f"wrote: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
