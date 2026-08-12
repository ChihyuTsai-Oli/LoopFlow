# -*- coding: utf-8 -*-
"""把 LOOPFLOW_WORKFLOW_SIMULATION.md 轉成深色好讀版 HTML。

用途
    `LOOPFLOW_WORKFLOW_SIMULATION.html` 是衍生檔，不應手動編輯。
    修改對應的 `.md` 之後執行本腳本重新產生，兩者才會一致。

執行
    python wip/tools/build_workflow_html.py
    python wip/tools/build_workflow_html.py --src <來源.md> --out <輸出.html>
    python wip/tools/build_workflow_html.py --check    # 只檢查是否過期，不寫檔

環境
    僅需 Python 3.8+ 標準函式庫，不依賴 Rhino，可在任何一台電腦執行。
    路徑一律相對於本檔位置解析，不寫死任何電腦的絕對路徑。

限制
    只支援本專案文件實際使用的 Markdown 子集：標題、段落、清單（含一層巢狀）、
    表格、圍欄程式碼區塊、引言區塊、水平線、粗體與行內程式碼。不支援圖片、連結與 HTML 內嵌。
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

# Windows 主控台預設可能是 cp950，統一改用 UTF-8 輸出中文訊息
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# 專案內的預設位置：<repo>/wip/tools/ → <repo>/wip/docs/architecture/
_ARCH_DIR = Path(__file__).resolve().parents[1] / "docs" / "architecture"
DEFAULT_SRC = _ARCH_DIR / "LOOPFLOW_WORKFLOW_SIMULATION.md"
DEFAULT_OUT = _ARCH_DIR / "LOOPFLOW_WORKFLOW_SIMULATION.html"


# ==================================================================
# 行內格式
# ==================================================================
def inline(text: str) -> str:
    """處理粗體與行內程式碼。

    程式碼區段先抽成佔位符再處理粗體，讓粗體能跨越程式碼配對。
    例如 `**指令 `LF_Nexus_Scan`**` 的兩個 `**` 必須視為同一組，
    若先切開程式碼再逐段套用粗體規則就會配對錯亂。
    """
    spans: list[str] = []

    def stash(m: re.Match) -> str:
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    return re.sub(
        r"\x00(\d+)\x00",
        lambda m: "<code>%s</code>" % html.escape(spans[int(m.group(1))]),
        text,
    )


def slug(text: str) -> str:
    """由標題文字產生錨點 id；保留中日韓字元，其餘非文字字元轉為連字號。"""
    return re.sub(r"[^\w一-鿿]+", "-", text).strip("-") or "sec"


# ==================================================================
# 區塊轉換
# ==================================================================
def convert(md: str) -> tuple[str, list[tuple[int, str, str, str]]]:
    """回傳 (HTML 內容, 目錄項目清單)。

    目錄項目為 (層級, 標題, 錨點 id, 章節變體)；變體用來決定配色。
    """
    lines = md.split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str, str]] = []
    i, n = 0, len(lines)
    variant = "intro"

    while i < n:
        stripped = lines[i].strip()

        # 圍欄程式碼區塊
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

        # 水平線
        if re.fullmatch(r"-{3,}", stripped):
            out.append("<hr>")
            i += 1
            continue

        # 表格：需要第二列是分隔列才視為表格
        if (
            stripped.startswith("|")
            and i + 1 < n
            and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip())
        ):
            def cells(row: str) -> list[str]:
                return [c.strip() for c in row.strip().strip("|").split("|")]

            head = cells(stripped)
            i += 2
            body = []
            while i < n and lines[i].strip().startswith("|"):
                body.append(cells(lines[i]))
                i += 1

            parts = ['<div class="tw"><table>', "<thead><tr>"]
            parts += ["<th>%s</th>" % inline(c) for c in head]
            parts.append("</tr></thead><tbody>")
            for row in body:
                row = (row + [""] * len(head))[: len(head)]
                parts.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in row) + "</tr>")
            parts.append("</tbody></table></div>")
            out.append("".join(parts))
            continue

        # 標題
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            level, title = len(m.group(1)), m.group(2).strip()
            sid = slug(title)

            if level == 1:
                if "CodeX" in title:
                    variant = "codex"
                elif "Claude" in title:
                    variant = "claude"

                if variant in ("codex", "claude"):
                    label = "CodeX" if variant == "codex" else "Claude Code"
                    rest = title.replace("CodeX ", "").replace("Claude Code ", "")
                    out.append('<section class="chapter %s" id="%s">' % (variant, sid))
                    out.append(
                        '<h1><span class="tagpill">%s</span>%s</h1>' % (label, inline(rest))
                    )
                    toc.append((1, title, sid, variant))
                else:
                    out.append('<h1 class="doctitle" id="%s">%s</h1>' % (sid, inline(title)))

            elif level == 2:
                stage = re.match(r"^階段\s*(\d+)｜(.+)$", title)
                if stage:
                    out.append(
                        '<h2 class="stage" id="%s"><span class="num">%s</span>%s</h2>'
                        % (sid, stage.group(1), inline(stage.group(2)))
                    )
                else:
                    out.append('<h2 id="%s">%s</h2>' % (sid, inline(title)))
                toc.append((2, title, sid, variant))

            else:
                out.append("<h%d id=\"%s\">%s</h%d>" % (level, sid, inline(title), level))

            i += 1
            continue

        # 有序清單（項目底下可帶一層巢狀項目符號）
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

        # 無序清單
        if re.match(r"^-\s+", stripped):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                items.append("<li>%s</li>" % inline(re.sub(r"^-\s+", "", lines[i].strip())))
                i += 1
            out.append("<ul>%s</ul>" % "".join(items))
            continue

        # 引言區塊（連續的 > 行併為一段）
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            out.append("<blockquote>%s</blockquote>" % inline(" ".join(buf).strip()))
            continue

        # 空行
        if not stripped:
            i += 1
            continue

        # 段落：連續非空且非其他區塊起始的行併為一段
        buf = []
        while (
            i < n
            and lines[i].strip()
            and not re.match(r"^(#{1,4}\s|```|-{3,}$|\||-\s|\d+\.\s|>)", lines[i].strip())
        ):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    if variant in ("codex", "claude"):
        out.append("</section>")

    return "\n".join(out), toc


def close_chapters(body: str) -> str:
    """在第二個 chapter 開始前補上結束標籤，讓兩個 section 正確配對。"""
    starts = [m.start() for m in re.finditer(r'<section class="chapter ', body)]
    if len(starts) >= 2:
        body = body[: starts[1]] + "</section>\n" + body[starts[1] :]
    return body


# ==================================================================
# 樣式與腳本（內嵌，確保離線可開）
# ==================================================================
CSS = """
/* ---- 色票與字體 ---- */
:root{
  --bg:#0e1014; --bg2:#141821; --panel:#171b25; --line:#252b39; --line2:#323a4d;
  --tx:#dbe0ea; --tx2:#a6afc2; --tx3:#79839a;
  --codex:#e0a458; --codex-d:#3a2c18;
  --claude:#5fb8c4; --claude-d:#16323a;
  --mono:"Cascadia Mono",Consolas,"SF Mono","Roboto Mono",monospace;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft JhengHei","PingFang TC","Noto Sans TC","Hiragino Sans",sans-serif;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--tx);font-family:var(--sans);
  font-size:15.5px;line-height:1.85;letter-spacing:.01em;-webkit-font-smoothing:antialiased}
.wrap{display:grid;grid-template-columns:264px minmax(0,1fr);gap:0;max-width:1500px;margin:0 auto}

/* ---- 側邊目錄 ---- */
nav{position:sticky;top:0;height:100vh;overflow-y:auto;padding:26px 14px 40px 22px;
  border-right:1px solid var(--line);background:var(--bg)}
nav .brand{font-size:12px;letter-spacing:.16em;color:var(--tx3);text-transform:uppercase;margin-bottom:6px}
nav .bt{font-size:15px;font-weight:600;color:var(--tx);margin-bottom:20px;line-height:1.4}
nav a{display:block;color:var(--tx2);text-decoration:none;font-size:12.8px;padding:3.5px 9px;
  border-radius:5px;border-left:2px solid transparent;line-height:1.5}
nav a:hover{color:var(--tx);background:var(--bg2)}
nav a.l1{margin-top:16px;font-weight:650;font-size:13.4px;color:var(--tx)}
nav a.l2{padding-left:16px}
nav a.l1.codex{color:var(--codex);border-left-color:var(--codex)}
nav a.l1.claude{color:var(--claude);border-left-color:var(--claude)}
nav a.l2.codex:hover{border-left-color:var(--codex)}
nav a.l2.claude:hover{border-left-color:var(--claude)}

/* ---- 內文 ---- */
main{padding:44px 52px 120px;min-width:0}
.doctitle{font-size:29px;font-weight:700;letter-spacing:.01em;margin:0 0 6px;line-height:1.35}
p{margin:0 0 15px}
strong{color:#fff;font-weight:650}
hr{border:0;border-top:1px solid var(--line);margin:38px 0}
ul,ol{margin:0 0 16px;padding-left:22px}
li{margin:5px 0}
li>ul{margin:6px 0 2px}
code{font-family:var(--mono);font-size:.875em;background:#1d2230;color:#e8c07d;
  padding:1.5px 5px;border-radius:4px;border:1px solid #262d3d;word-break:break-word}
strong code{color:#f0cf9a}
pre.code{background:#12161f;border:1px solid var(--line);border-left:3px solid var(--line2);
  border-radius:7px;padding:15px 17px;overflow-x:auto;margin:0 0 18px}
pre.code code{background:none;border:0;padding:0;color:#b9c4d8;font-size:13px;line-height:1.72;white-space:pre}

/* ---- 章節（CodeX / Claude） ---- */
.chapter{padding-top:12px}
.chapter h1{font-size:25px;font-weight:700;margin:0 0 26px;padding:0 0 14px;
  display:flex;align-items:center;gap:13px;flex-wrap:wrap;border-bottom:2px solid var(--line)}
.tagpill{font-size:11.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  padding:4px 11px;border-radius:20px;white-space:nowrap}
.chapter.codex h1{border-bottom-color:var(--codex)}
.chapter.codex .tagpill{background:var(--codex-d);color:var(--codex);border:1px solid #5c4626}
.chapter.claude h1{border-bottom-color:var(--claude)}
.chapter.claude .tagpill{background:var(--claude-d);color:var(--claude);border:1px solid #2b5661}

h2{font-size:19px;font-weight:660;margin:38px 0 14px;line-height:1.45}
h3{font-size:16px;font-weight:640;margin:28px 0 11px;color:var(--tx)}
.chapter.codex h2{color:#f0c68c}
.chapter.claude h2{color:#93d5de}
h2.stage{display:flex;align-items:center;gap:11px}
h2.stage .num{display:inline-flex;align-items:center;justify-content:center;
  width:27px;height:27px;border-radius:7px;font-size:13px;font-weight:700;font-family:var(--mono);flex:none}
.chapter.claude h2.stage .num{background:var(--claude-d);color:var(--claude);border:1px solid #2b5661}
.chapter.codex h2.stage .num{background:var(--codex-d);color:var(--codex);border:1px solid #5c4626}

/* ---- 引言區塊 ---- */
blockquote{margin:0 0 20px;padding:13px 18px;background:#151a24;
  border-left:3px solid var(--line2);border-radius:0 7px 7px 0;color:var(--tx2);font-size:14.6px}
blockquote strong{color:var(--tx)}

/* ---- 表格 ---- */
.tw{overflow-x:auto;margin:0 0 22px;border:1px solid var(--line);border-radius:9px;background:var(--panel)}
table{border-collapse:collapse;width:100%;min-width:600px;font-size:13.6px}
th{background:#1b2130;color:var(--tx);font-weight:660;text-align:left;
  padding:11px 14px;border-bottom:1px solid var(--line2);white-space:nowrap;font-size:13px}
td{padding:11px 14px;border-bottom:1px solid var(--line);vertical-align:top;
  color:var(--tx2);line-height:1.72}
tbody tr:last-child td{border-bottom:0}
tbody tr:nth-child(even){background:rgba(255,255,255,.016)}
tbody tr:hover{background:rgba(255,255,255,.038)}
td:first-child{color:var(--tx);font-weight:550;white-space:nowrap}
.chapter table td strong{color:#fff}

/* ---- 響應式與列印 ---- */
@media (max-width:1080px){
  .wrap{grid-template-columns:1fr}
  nav{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);padding:20px 22px}
  nav a{display:inline-block;margin:2px 4px 2px 0}
  nav a.l2{display:none}
  main{padding:30px 22px 80px}
  .doctitle{font-size:24px}
  .chapter h1{font-size:21px}
}
@media print{
  nav{display:none} body{background:#fff;color:#111}
  .tw,table,td,th{border-color:#bbb} main{padding:0}
}
"""

JS = """
(function(){
  var links=[].slice.call(document.querySelectorAll('nav a'));
  var targets=links.map(function(a){return document.getElementById(a.getAttribute('href').slice(1));});
  function upd(){
    var y=window.scrollY+140, best=-1;
    for(var i=0;i<targets.length;i++){ if(targets[i]&&targets[i].offsetTop<=y) best=i; }
    links.forEach(function(a,i){ a.style.background = (i===best)?'#1e2432':''; });
  }
  window.addEventListener('scroll',upd,{passive:true}); upd();
})();
"""

PAGE = """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>LoopFlow 2.0 — 模擬執行流程</title>
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


def render(md: str) -> str:
    """由 Markdown 原文產生完整 HTML 頁面。"""
    body, toc = convert(md)
    body = close_chapters(body)

    nav = ['<div class="brand">LoopFlow 2.0</div>', '<div class="bt">模擬執行流程</div>']
    for level, title, sid, variant in toc:
        nav.append(
            '<a class="l%d %s" href="#%s">%s</a>' % (level, variant, sid, html.escape(title))
        )

    return PAGE % (CSS, "\n".join(nav), body, JS)


# ==================================================================
# 進入點
# ==================================================================
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="產生模擬執行流程的深色 HTML 版本")
    ap.add_argument("--src", type=Path, default=DEFAULT_SRC, help="來源 Markdown")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="輸出 HTML")
    ap.add_argument(
        "--check",
        action="store_true",
        help="只比對現有 HTML 是否為最新，不寫檔；過期時以離開碼 1 結束",
    )
    args = ap.parse_args(argv)

    if not args.src.exists():
        print("找不到來源檔：%s" % args.src, file=sys.stderr)
        return 2

    page = render(args.src.read_text(encoding="utf-8"))

    if args.check:
        if args.out.exists() and args.out.read_text(encoding="utf-8") == page:
            print("HTML 為最新：%s" % args.out.name)
            return 0
        print("HTML 已過期，請重新執行本腳本產生：%s" % args.out.name, file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8", newline="\n")
    print("已產生 %s（%d bytes）" % (args.out.name, len(page.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
