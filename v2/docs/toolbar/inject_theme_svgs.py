"""把 SVG 寫進現行 Rhino 8／9 共用的產品 LoopFlow.rui。

來源資料夾以參數傳入，不寫死 Dropbox 路徑。不改 icon GUID 或工具列分頁小圖。
產品圖拿掉 fill-dark，改走獨立 <dark> 稿；Rhino 9 剖切 SVG 另以 --section
寫入 RUI，讓 Rhino 8 不必依賴 Rhino 9 的內建圖示資源。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUI = HERE / "LoopFlow.rui"

SCRIPT_TO_SVG = {
    "! _LFCatalog": "LF_Catalog.svg",
    "! _LFPublishExchange": "LF_Publish Exchange.svg",
    "! _LFExtractCP": "LF_Extract_CP.svg",
    "! _LFInfuserPart": "LF_Infuser_Part.svg",
    "! _LFDuplicateLayout": "LF_Duplicate_Layout.svg",
    "! _LFAnchorFrame": "LF_Anchor_Frame.svg",
    "! _LFAnchorUpdate": "LF_Anchor_Update.svg",
    "! _LFTaggerIndex": "LF_Tagger_Index.svg",
    "! _LFSyncWorksession": "LF_LiveLink_Worksession.svg",
    "! _LFTaggerLaser": "LF_Tagger_Laser.svg",
    "! _LFDataViewer": "LF_Data_Viewer.svg",
    "! _LFExportTypeLayers": "LF_Export_Type_Layers.svg",
    "! _LFOpenDictExport": "LF_Open_Dictionary_Export.svg",
    "! _LFTaggerGrab": "LF_Tagger_Grab.svg",
    "! _LFNexus": "LF_Nexus.svg",
    "! _LFOpenDictionary": "LF_Open_Dictionary.svg",
    "! _LFDocument": "LF_Document.svg",
    "! _LFTagO": "LF_TAG-O.svg",
    "! _LFInfuserAll": "LF_Infuser_All.svg",
    "! _LFTaggerLayoutID": "LF_Tagger_Layout_ID.svg",
    "! _LFLanguage": "LF_Document.svg",
}

SECTION_SCRIPT_TO_SVG = {
    "! _ClippingSections": "Create clipping sections.svg",
    "! _ClippingDrawings": "Create clipping drawings.svg",
    "! _AlignClippingDrawings": "Align clipping drawings.svg",
    "! _ClearClippingSections": "Clear clipping sections.svg",
    "! _UpdateClippingDrawings": "Update clipping drawings.svg",
}

MACRO_RE = re.compile(
    r'<macro_item\b([^>]*)>.*?<script>(.*?)</script>',
    re.DOTALL,
)
BITMAP_RE = re.compile(r'\bbitmap_id="([^"]+)"')
ICON_RE = re.compile(r'(<icon guid="([^"]+)"[^>]*>)(.*?)(</icon>)', re.DOTALL)
OUTER = (
    '<svg width="48" height="48" version="1.1" '
    'xmlns="http://www.w3.org/2000/svg" '
    'xmlns:xlink="http://www.w3.org/1999/xlink" '
    'viewBox="0pt 0pt 48pt 48pt">'
)


def load_inner(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<\?xml[^?]*\?>\s*", "", text)
    text = re.sub(r"<!DOCTYPE[^>]*>\s*", "", text)
    text = text.replace(' xmlns:affinity="https://www.affinity.studio/"', "")
    text = text.strip()
    if not text.startswith("<svg"):
        raise SystemExit("不是 SVG：%s" % path)
    return text


def wrap(inner: str, slot: str) -> str:
    return "      <%s>%s\n  %s\n</svg></%s>" % (slot, OUTER, inner, slot)


def bitmap_ids(rui_text: str, script_to_svg: dict[str, str]) -> dict[str, str]:
    found: dict[str, str] = {}
    for attrs, script in MACRO_RE.findall(rui_text):
        command = re.sub(r"\s+", " ", script).strip()
        svg_name = script_to_svg.get(command)
        if svg_name is None:
            continue
        match = BITMAP_RE.search(attrs)
        if match is None:
            raise SystemExit("巨集沒有 bitmap_id：%s" % command)
        guid = match.group(1)
        previous = found.get(guid)
        if previous and previous != svg_name:
            raise SystemExit("同一 icon GUID 對到兩份 SVG：%s" % guid)
        found[guid] = svg_name
    missing = set(script_to_svg) - {
        re.sub(r"\s+", " ", script).strip() for _attrs, script in MACRO_RE.findall(rui_text)
    }
    if missing:
        raise SystemExit("rui 找不到這些巨集：%s" % ", ".join(sorted(missing)))
    return found


def inject(rui_text: str, light_dir: Path, dark_dir: Path) -> str:
    targets = bitmap_ids(rui_text, SCRIPT_TO_SVG)
    used: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        open_tag, guid, _body, close_tag = match.group(1), match.group(2), match.group(3), match.group(4)
        svg_name = targets.get(guid)
        if svg_name is None:
            return match.group(0)
        used.add(guid)
        light = load_inner(light_dir / svg_name)
        dark = load_inner(dark_dir / svg_name)
        inner = "\n%s\n%s\n    " % (wrap(light, "light"), wrap(dark, "dark"))
        return open_tag + inner + close_tag

    updated = ICON_RE.sub(replace, rui_text)
    leftover = set(targets) - used
    if leftover:
        raise SystemExit("rui 找不到這些 icon GUID：%s" % ", ".join(sorted(leftover)))
    for guid, svg_name in targets.items():
        block = next(
            match.group(0)
            for match in ICON_RE.finditer(updated)
            if match.group(2) == guid
        )
        if "fill-dark=" in block:
            raise SystemExit("產品圖仍有 fill-dark：%s (%s)" % (guid, svg_name))
        if "<light>" not in block or "<dark>" not in block:
            raise SystemExit("產品圖缺少 light/dark：%s (%s)" % (guid, svg_name))
    return updated


def inject_sections(rui_text: str, svg_dir: Path) -> str:
    """內嵌 R9 剖切 SVG；同一原稿放入 light/dark，保留其 fill-dark 資訊。"""
    targets = bitmap_ids(rui_text, SECTION_SCRIPT_TO_SVG)
    used: set[str] = set()
    blocks = []

    def icon_body(guid: str, svg_name: str) -> str:
        inner = load_inner(svg_dir / svg_name)
        return "\n%s\n%s\n    " % (wrap(inner, "light"), wrap(inner, "dark"))

    def replace(match: re.Match[str]) -> str:
        open_tag, guid, close_tag = match.group(1), match.group(2), match.group(4)
        svg_name = targets.get(guid)
        if svg_name is None:
            return match.group(0)
        used.add(guid)
        return open_tag + icon_body(guid, svg_name) + close_tag

    updated = ICON_RE.sub(replace, rui_text)
    for guid in set(targets) - used:
        blocks.append(
            '    <icon guid="%s" name="%s.svg">%s</icon>'
            % (guid, guid, icon_body(guid, targets[guid]))
        )
    if not blocks:
        return updated
    marker = "  </icons>"
    if marker not in updated:
        raise SystemExit("rui 找不到 </icons>")
    return updated.replace(marker, "\n".join(blocks) + "\n" + marker, 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="寫入 Rhino 8／9 共用工具列 SVG")
    parser.add_argument("--light", type=Path, help="產品按鈕淺色 SVG 資料夾")
    parser.add_argument("--dark", type=Path, help="產品按鈕深色 SVG 資料夾")
    parser.add_argument("--section", type=Path, help="Rhino 9 剖切按鈕 SVG 資料夾")
    args = parser.parse_args(argv)
    if bool(args.light) != bool(args.dark):
        raise SystemExit("--light 與 --dark 必須一起提供")
    if not args.light and not args.section:
        raise SystemExit("至少提供 --light/--dark 或 --section")
    text = RUI.read_text(encoding="utf-8")
    if args.light:
        light_dir = args.light.expanduser().resolve()
        dark_dir = args.dark.expanduser().resolve()
        if not light_dir.is_dir() or not dark_dir.is_dir():
            raise SystemExit("找不到淺色或深色資料夾")
        text = inject(text, light_dir, dark_dir)
    if args.section:
        section_dir = args.section.expanduser().resolve()
        if not section_dir.is_dir():
            raise SystemExit("找不到剖切 SVG 資料夾")
        text = inject_sections(text, section_dir)
    RUI.write_text(text, encoding="utf-8", newline="\n")
    print("updated", RUI)
    return 0


if __name__ == "__main__":
    sys.exit(main())
