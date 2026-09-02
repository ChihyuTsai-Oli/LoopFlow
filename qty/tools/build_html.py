# -*- coding: utf-8 -*-
"""把 QTY 前期評估的多份 Markdown 合併成單一離線 HTML，方便跨裝置檢視。

用途
    `docs/前期評估/前期評估總覽.html` 是衍生檔，不應手動編輯。
    修改對應的 .md 之後執行本腳本重新產生，才會跟來源一致。

執行
    python qty/tools/build_html.py
    python qty/tools/build_html.py --src 決策紀錄_2.md 測試模型.md   # 只合併指定檔案
    python qty/tools/build_html.py --out 我的總覽.html
    python qty/tools/build_html.py --check    # 只檢查是否過期，不寫檔

環境
    僅需 Python 3.8+ 標準函式庫，不依賴任何套件。路徑一律相對於本檔位置解析。

格式
    沿用 `D:\\Dropbox\\戰備物資\\tools\\build_html.py` 的版面與行為（兩層側邊
    目錄、捲動高亮、響應式、列印樣式、checkbox 保存、--check 過期檢查）。

    QTY 專屬的追加：決策表（六欄以上）的最後一欄依三家建議強度自動上色，
    白＝強烈建議×2+、黃＝一般建議×2+、綠＝輕鬆建議×2+。

限制
    只支援本專案文件實際使用的 Markdown 子集：標題（# ~ ####）、段落、清單、
    表格、圍欄程式碼區塊、引言區塊、水平線、粗體、行內程式碼、連結、`<br>`。
    文件間的相對連結若指向合併清單中的其他來源檔，會自動轉成頁內錨點。
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = PROJECT_ROOT / "docs" / "前期評估"
DEFAULT_ORDER = [
    "README.md",
    "範圍與邊界.md",
    "資料盤點.md",
    "量測方法.md",
    "決策紀錄_1.md",
    "決策紀錄_2.md",
    "測試模型.md",
    "開發順序計畫.md",
]
DEFAULT_OUT = DOCS_DIR / "前期評估總覽.html"

SITE_BRAND = "LoopFlow QTY"
SITE_TITLE = "前期評估總覽"


# ==================================================================
# 行內格式
# ==================================================================
def make_inline(link_resolver):
    """回傳 inline()；link_resolver 決定 .md 連結是否轉為頁內錨點。"""

    def inline(text: str) -> str:
        code_spans: list[str] = []
        link_spans: list[tuple[str, str]] = []

        def stash_code(m: re.Match) -> str:
            code_spans.append(m.group(1))
            return "\x00c%d\x00" % (len(code_spans) - 1)

        def stash_link(m: re.Match) -> str:
            link_spans.append((m.group(1), m.group(2)))
            return "\x00l%d\x00" % (len(link_spans) - 1)

        text = re.sub(r"`([^`]+)`", stash_code, text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", stash_link, text)
        text = text.replace("<br>", "\x00b\x00")
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = text.replace("\x00b\x00", "<br>")

        def unstash_link(m: re.Match) -> str:
            label, href = link_spans[int(m.group(1))]
            label_html = html.escape(label)
            anchor = link_resolver(href)
            if anchor is None:
                return '<a href="%s">%s</a>' % (html.escape(href), label_html)
            return '<a href="#%s">%s</a>' % (anchor, label_html)

        text = re.sub(r"\x00l(\d+)\x00", unstash_link, text)
        text = re.sub(
            r"\x00c(\d+)\x00",
            lambda m: "<code>%s</code>" % html.escape(code_spans[int(m.group(1))]),
            text,
        )
        return text

    return inline


def slug(text: str) -> str:
    return re.sub(r"[^\w一-鿿]+", "-", text).strip("-") or "sec"


def first_h1(md: str) -> str:
    m = re.search(r"^#\s+(.*)$", md, re.M)
    return m.group(1).strip() if m else "未命名文件"


def strength_class(cells: list[str]) -> str:
    """依三家建議欄的強度多數決決定最後一欄顏色（QTY 專屬）。"""
    body = " ".join(cells)
    if body.count("強烈建議") >= 2:
        return "s-strong"
    if body.count("一般建議") >= 2:
        return "s-normal"
    if body.count("輕鬆建議") >= 2:
        return "s-light"
    return ""


# ==================================================================
# 單一來源檔轉換
# ==================================================================
def convert_file(md: str, chapter_id: str, inline) -> tuple[str, list[tuple[int, str, str]]]:
    lines = md.split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    i, n = 0, len(lines)

    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    while i < n:
        stripped = lines[i].strip()

        if stripped.startswith("```"):
            lang = stripped[3:].strip() or "text"
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append(
                '<pre class="code" data-lang="%s"><code>%s</code></pre>'
                % (html.escape(lang), html.escape("\n".join(buf)))
            )
            continue

        if re.fullmatch(r"-{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        if (
            stripped.startswith("|")
            and i + 1 < n
            and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip())
        ):
            head = cells(stripped)
            i += 2
            body = []
            while i < n and lines[i].strip().startswith("|"):
                body.append(cells(lines[i]))
                i += 1

            wide = len(head) >= 5
            parts = ['<div class="tw"><table%s>' % (' class="wide"' if wide else ""), "<thead><tr>"]
            parts += ["<th>%s</th>" % inline(c) for c in head]
            parts.append("</tr></thead><tbody>")
            for ridx, row in enumerate(body):
                row = (row + [""] * len(head))[: len(head)]
                first = row[0].strip().lower()
                if first in ("[ ]", "[x]"):
                    checked = first == "[x]"
                    key = slug("%s-chk-%d-%s" % (chapter_id, ridx, row[1] if len(row) > 1 else ""))
                    box = ('<input type="checkbox" class="ck" data-key="%s"%s>'
                           % (html.escape(key), " checked" if checked else ""))
                    tds = ['<td class="ckcell">%s</td>' % box]
                    tds += ["<td>%s</td>" % inline(c) for c in row[1:]]
                    parts.append('<tr class="ckrow%s">%s</tr>'
                                 % (" done" if checked else "", "".join(tds)))
                else:
                    cls = strength_class(row[:-1]) if wide else ""
                    tds = []
                    for k, c in enumerate(row):
                        last = k == len(row) - 1
                        tds.append("<td%s>%s</td>"
                                   % ((' class="%s"' % cls) if (last and cls) else "", inline(c)))
                    parts.append("<tr>%s</tr>" % "".join(tds))
            parts.append("</tbody></table></div>")
            out.append("".join(parts))
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            if level == 1:
                sid = chapter_id
                out.append('<h1 class="chaptitle" id="%s">%s</h1>' % (sid, inline(title)))
            else:
                sid = "%s--%s" % (chapter_id, slug(title))
                out.append("<h%d id=\"%s\">%s</h%d>" % (level, sid, inline(title), level))
            toc.append((level, title, sid))
            i += 1
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                body = [inline(re.sub(r"^\d+\.\s+", "", lines[i].strip()))]
                i += 1
                sub = []
                while i < n and re.match(r"^\s{2,}[-·]\s+", lines[i]):
                    sub.append("<li>%s</li>" % inline(re.sub(r"^\s+[-·]\s+", "", lines[i])))
                    i += 1
                if sub:
                    body.append("<ul>%s</ul>" % "".join(sub))
                items.append("<li>%s</li>" % "".join(body))
            out.append("<ol>%s</ol>" % "".join(items))
            continue

        if re.match(r"^-\s+", stripped):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                items.append("<li>%s</li>" % inline(re.sub(r"^-\s+", "", lines[i].strip())))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items))
            continue

        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            inner, _ = convert_file("\n".join(buf), chapter_id + "-q", inline)
            inner = re.sub(r"<h([1-4]) id=\"[^\"]*\"[^>]*>", r"<p class=\"qh\"><strong>", inner)
            inner = re.sub(r"</h[1-4]>", "</strong></p>", inner)
            out.append("<blockquote>%s</blockquote>" % inner)
            continue

        if not stripped:
            i += 1
            continue

        buf = []
        while (
            i < n
            and lines[i].strip()
            and not re.match(r"^(#{1,4}\s|```|-{3,}$|\||-\s|\d+\.\s|>)", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    return "\n".join(out), toc


# ==================================================================
# 樣式與腳本
# ==================================================================
CSS = """
:root{
  --bg:#0e1013; --bg2:#151920; --panel:#171b22; --line:#262c37; --line2:#333b49;
  --tx:#dde2ea; --tx2:#a4aebf; --tx3:#767f92;
  --accent:#6fbfa2; --accent-d:#173129; --warn:#e0a458;
  --mono:"Cascadia Mono",Consolas,"SF Mono","Roboto Mono",monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft JhengHei","PingFang TC","Noto Sans TC","Hiragino Sans",sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font-family:var(--sans);
  font-size:15.5px;line-height:1.85;letter-spacing:.01em;-webkit-font-smoothing:antialiased}
.wrap{display:grid;grid-template-columns:260px minmax(0,1fr);gap:0;max-width:1560px;margin:0 auto}

nav{position:sticky;top:0;height:100vh;overflow-y:auto;padding:26px 14px 40px 22px;
  border-right:1px solid var(--line);background:var(--bg)}
nav .brand{font-size:12px;letter-spacing:.16em;color:var(--tx3);text-transform:uppercase;margin-bottom:6px}
nav .bt{font-size:15px;font-weight:600;color:var(--tx);margin-bottom:20px;line-height:1.4}
nav .group{margin:0 0 16px}
nav a.l1{display:block;font-weight:650;color:var(--tx);text-decoration:none;font-size:13.6px;
  padding:6px 9px;border-radius:6px;border-left:2px solid var(--accent)}
nav a.l1:hover{background:var(--bg2)}
nav a.l2{display:block;color:var(--tx2);text-decoration:none;font-size:12.8px;
  padding:3.5px 9px 3.5px 18px;border-radius:5px;border-left:2px solid transparent;line-height:1.5}
nav a.l2:hover,nav a.l2.active{color:var(--tx);background:var(--bg2);border-left-color:var(--accent)}
nav a.l1.active{background:var(--accent-d);color:var(--accent)}

main{padding:44px 52px 120px;min-width:0}
p{margin:0 0 15px}
strong{color:#fff;font-weight:650}
a{color:#8fd9c7}
hr{border:0;border-top:1px solid var(--line);margin:38px 0}
ul,ol{margin:0 0 16px;padding-left:22px}
li{margin:5px 0}
li>ul{margin:6px 0 2px}
code{font-family:var(--mono);font-size:.875em;background:#1d2230;color:#e8c07d;
  padding:1.5px 5px;border-radius:4px;border:1px solid #262d3d;word-break:break-word}
pre.code{background:#12161f;border:1px solid var(--line);border-left:3px solid var(--line2);
  border-radius:7px;padding:15px 17px;overflow-x:auto;margin:0 0 18px}
pre.code code{background:none;border:0;padding:0;color:#b9c4d8;font-size:13px;line-height:1.72;white-space:pre}

.chaptitle{font-size:27px;font-weight:700;margin:64px 0 22px;padding:20px 0 14px;
  border-bottom:2px solid var(--accent);scroll-margin-top:20px}
.wrap main>.chaptitle:first-of-type{margin-top:0}
h2{font-size:19px;font-weight:660;margin:38px 0 14px;line-height:1.45;color:var(--tx);scroll-margin-top:20px}
h3{font-size:16px;font-weight:640;margin:28px 0 11px;color:var(--tx2);scroll-margin-top:20px}
h4{font-size:14.5px;font-weight:640;margin:22px 0 9px;color:var(--tx2)}

blockquote{margin:0 0 20px;padding:13px 18px;background:#151a24;
  border-left:3px solid var(--line2);border-radius:0 7px 7px 0;color:var(--tx2);font-size:14.6px}
blockquote p{margin:0 0 5px}
blockquote p:last-child{margin-bottom:0}
blockquote p.qh{color:var(--tx);margin-top:2px}
blockquote .tw{margin:10px 0}

.tw{overflow-x:auto;margin:0 0 22px;border:1px solid var(--line);border-radius:9px;background:var(--panel)}
table{border-collapse:collapse;width:100%;min-width:520px;font-size:13.6px;font-variant-numeric:tabular-nums}
table.wide{min-width:1700px}
th{background:#1b2130;color:var(--tx);font-weight:660;text-align:left;position:sticky;top:0;z-index:2;
  padding:11px 14px;border-bottom:1px solid var(--line2);font-size:13px}
td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top;
  color:var(--tx2);line-height:1.72}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:rgba(255,255,255,.016)}
tbody tr:hover{background:rgba(255,255,255,.038)}
table:not(.wide) td:nth-child(2){color:var(--tx);font-weight:550}
table.wide td:first-child{color:var(--tx);font-weight:650;white-space:nowrap}
td.s-strong{color:#ffffff;font-weight:660}
td.s-normal{color:#f5e04a;font-weight:600}
td.s-light{color:#6fdc8c;font-weight:600}

td.ckcell{width:34px;padding-left:16px;padding-right:0}
input.ck{width:16px;height:16px;accent-color:var(--accent);cursor:pointer}
tr.ckrow.done td{color:var(--tx3);text-decoration:line-through;opacity:.62}
tr.ckrow.done td.ckcell{text-decoration:none;opacity:1}

.legend{margin:0 0 18px;font-size:13.5px;color:var(--tx2)}
.legend span{display:inline-block;margin-right:16px;font-weight:650}

@media (max-width:1000px){
  .wrap{grid-template-columns:1fr}
  nav{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);padding:20px 22px}
  main{padding:30px 22px 80px}
  .chaptitle{font-size:22px;margin-top:36px}
  th{position:static}
}
@media print{
  nav{display:none} body{background:#fff;color:#111}
  .tw,table,td,th{border-color:#bbb} main{padding:0}
  td.s-strong,td.s-normal,td.s-light{color:#111}
}
"""

JS = """
(function(){
  document.querySelectorAll('input.ck').forEach(function(box){
    var key='qty:'+box.getAttribute('data-key');
    try{
      var saved=localStorage.getItem(key);
      if(saved!==null){ box.checked = saved==='1'; }
    }catch(e){}
    var row=box.closest('tr');
    row.classList.toggle('done', box.checked);
    box.addEventListener('change', function(){
      try{ localStorage.setItem(key, box.checked?'1':'0'); }catch(e){}
      row.classList.toggle('done', box.checked);
    });
  });

  var links=[].slice.call(document.querySelectorAll('nav a'));
  var targets=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  function upd(){
    var y=window.scrollY+140, best=-1;
    for(var i=0;i<targets.length;i++){ if(targets[i]&&targets[i].offsetTop<=y) best=i; }
    links.forEach(function(a,i){ a.classList.toggle('active', i===best); });
  }
  window.addEventListener('scroll',upd,{passive:true});
  upd();
})();
"""

PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<style>%s</style>
</head>
<body>
<div class="wrap">
<nav>%s</nav>
<main>%s</main>
</div>
<script>%s</script>
</body>
</html>
"""

LEGEND = ('<p class="legend">決策表「你的決定」欄顏色（依三家建議強度自動判定）：'
          '<span style="color:#ffffff">白＝強烈建議×2+</span>'
          '<span style="color:#f5e04a">黃＝一般建議×2+</span>'
          '<span style="color:#6fdc8c">綠＝輕鬆建議×2+</span></p>')


# ==================================================================
# 合併
# ==================================================================
def render(sources: list[Path]) -> str:
    texts = [(p, p.read_text(encoding="utf-8")) for p in sources]

    chapter_map: dict[str, str] = {}
    chapter_ids: list[str] = []
    for p, md in texts:
        title = first_h1(md)
        cid = base = slug(title)
        k = 2
        while cid in chapter_ids:
            cid = "%s-%d" % (base, k)
            k += 1
        chapter_ids.append(cid)
        chapter_map[p.name] = cid

    def link_resolver(href: str):
        return chapter_map.get(Path(href).name)

    inline = make_inline(link_resolver)

    body_parts: list[str] = []
    toc: list[tuple[int, str, str]] = []
    for (p, md), cid in zip(texts, chapter_ids):
        body, file_toc = convert_file(md, cid, inline)
        body_parts.append(body)
        toc.extend(file_toc)

    nav = ['<div class="brand">%s</div>' % html.escape(SITE_BRAND),
           '<div class="bt">%s</div>' % html.escape(SITE_TITLE)]
    open_group = False
    for level, title, sid in toc:
        if level == 1:
            if open_group:
                nav.append("</div>")
            nav.append('<div class="group">')
            nav.append('<a class="l1" href="#%s">%s</a>' % (sid, html.escape(title)))
            open_group = True
        elif level == 2:
            nav.append('<a class="l2" href="#%s">%s</a>' % (sid, html.escape(title)))
    if open_group:
        nav.append("</div>")

    body = LEGEND + "\n".join(body_parts)
    return PAGE % (html.escape(SITE_TITLE), CSS, "\n".join(nav), body, JS)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="把 QTY 前期評估的多份 Markdown 合併成單一 HTML")
    ap.add_argument("--src", type=Path, nargs="*", default=None,
                    help="要合併的 Markdown（依指定順序）；預設依內建順序讀取 docs/前期評估/")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="輸出 HTML 路徑")
    ap.add_argument("--check", action="store_true",
                    help="只比對現有 HTML 是否為最新，不寫檔；過期時以離開碼 1 結束")
    args = ap.parse_args(argv)

    if args.src:
        sources = [p if p.is_absolute() or p.exists() else DOCS_DIR / p for p in args.src]
    else:
        sources = [DOCS_DIR / name for name in DEFAULT_ORDER if (DOCS_DIR / name).exists()]

    missing = [p for p in sources if not p.exists()]
    if missing:
        for p in missing:
            print("找不到來源檔：%s" % p, file=sys.stderr)
        return 2
    if not sources:
        print("沒有可合併的 Markdown 檔案", file=sys.stderr)
        return 2

    page = render(sources)

    if args.check:
        if args.out.exists() and args.out.read_text(encoding="utf-8") == page:
            print("HTML 為最新：%s" % args.out.name)
            return 0
        print("HTML 已過期，請重新執行本腳本產生：%s" % args.out.name, file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8", newline="\n")
    print("已合併 %d 份文件 → %s（%d bytes）"
          % (len(sources), args.out.name, len(page.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
