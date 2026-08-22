# -*- coding: utf-8 -*-
"""以標準庫讀寫簡單 xlsx 工作表。不依賴 openpyxl／pandas，也不寫死路徑。"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Sequence
from xml.etree import ElementTree as ET

from loopflow.foundation import results
from loopflow.foundation.i18n import t as ui

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CELL_REF_RE = re.compile(r"^([A-Z]+)(\d+)$")
# 繁中 Dictionary／匯出用微軟正黑體；英文版用 Arial。
DICTIONARY_FONT_NAME = "微軟正黑體"
DICTIONARY_FONT_NAME_EN = "Arial"
DICTIONARY_FONT_SIZE = "10"
DICTIONARY_HINT_FONT_SIZE = "20"
DICTIONARY_ROW_HEIGHT = "20.1"
DICTIONARY_TITLE_HEIGHT = "30"
DICTIONARY_HEADER_HEIGHT = "39.9"
DICTIONARY_HINT_HEIGHT = "60"
DICTIONARY_HEADER_MARKS = ("__Rhino Layer", "Rhino Layer")
DICTIONARY_TITLE_MARK = "LoopFlow Dictionary v2.0"
# 對齊正式 Dictionary 前 15 欄寬度；最後一欄給 diff_status。
DICTIONARY_COLUMN_WIDTHS = (
    44.4,
    11.2,
    11.4,
    9.7,
    13.2,
    11.9,
    11.8,
    11.6,
    13.9,
    12.8,
    12.8,
    12.8,
    12.8,
    14.6,
    12.8,
    18.0,
)
STATUS_FONT_COLORS = {
    "missing_in_rhino": "FFC00000",
    "added_in_rhino": "FF0070C0",
    "modified": "FFED7D31",
}
STYLE_BODY = "0"
STYLE_TITLE = "1"
STYLE_HEADER = "0"
STYLE_HINT = "5"
STATUS_STYLE_IDS = {
    "missing_in_rhino": "2",
    "added_in_rhino": "3",
    "modified": "4",
}
TITLE_FONT_COLOR = "FF3333FF"
HINT_FONT_COLOR = "FFFF0000"


def _qn(ns: str, tag: str) -> str:
    return "{%s}%s" % (ns, tag)


def _col_letters(index: int) -> str:
    letters = []
    n = index
    while n:
        n, rem = divmod(n - 1, 26)
        letters.append(chr(65 + rem))
    return "".join(reversed(letters))


def _col_index(letters: str) -> int:
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n


def _parse_xml(data: bytes) -> ET.Element:
    return ET.fromstring(data)


def _shared_strings(root: ET.Element) -> List[str]:
    values = []
    for si in root.findall(_qn(MAIN_NS, "si")):
        parts = [node.text or "" for node in si.iter(_qn(MAIN_NS, "t"))]
        values.append("".join(parts))
    return values


def _cell_value(cell: ET.Element, shared: Sequence[str]):
    cell_type = cell.get("t")
    if cell_type == "s":
        node = cell.find(_qn(MAIN_NS, "v"))
        if node is None or node.text is None:
            return None
        return shared[int(node.text)]
    if cell_type == "inlineStr":
        is_node = cell.find(_qn(MAIN_NS, "is"))
        if is_node is None:
            return None
        parts = [node.text or "" for node in is_node.iter(_qn(MAIN_NS, "t"))]
        return "".join(parts) or None
    node = cell.find(_qn(MAIN_NS, "v"))
    if node is None or node.text is None:
        return None
    text = node.text
    if cell_type == "b":
        return text in ("1", "true", "TRUE")
    if cell_type in (None, "n"):
        if "." in text or "e" in text.lower():
            number = float(text)
            if number.is_integer():
                return int(number)
            return number
        return int(text)
    return text


def _trim_trailing(values: List[Optional[object]]) -> List[Optional[object]]:
    end = len(values)
    while end > 0 and values[end - 1] in (None, ""):
        end -= 1
    return values[:end]


def _first_sheet_path(zf: zipfile.ZipFile) -> str:
    workbook = _parse_xml(zf.read("xl/workbook.xml"))
    rels = _parse_xml(zf.read("xl/_rels/workbook.xml.rels"))
    sheets = workbook.find(_qn(MAIN_NS, "sheets"))
    if sheets is None:
        raise ValueError("xlsx 沒有工作表")
    sheet = sheets.find(_qn(MAIN_NS, "sheet"))
    if sheet is None:
        raise ValueError("xlsx 沒有工作表")
    rel_id = sheet.get(_qn(OFFICE_REL_NS, "id")) or sheet.get("r:id")
    target = None
    for rel in rels.findall(_qn(PKG_REL_NS, "Relationship")):
        if rel.get("Id") == rel_id:
            target = rel.get("Target")
            break
    if not target:
        raise ValueError("找不到第一張工作表路徑")
    if target.startswith("/"):
        return target.lstrip("/")
    return "xl/" + target.lstrip("/")


def _first_nonempty(values: Sequence[Optional[object]]) -> Optional[str]:
    for cell in values:
        if cell not in (None, ""):
            return str(cell).strip()
    return None


def _header_row_number(grid: dict, max_row: int, max_col: int) -> int:
    for row_number in range(1, max_row + 1):
        for col in range(1, max_col + 1):
            value = grid.get((row_number, col))
            if str(value or "").strip() in DICTIONARY_HEADER_MARKS:
                return row_number
    return 2


def read_table(path: Path) -> results.Result:
    """讀取第一張工作表：標題列、欄名列、其後為資料列。匯出檔可在標題前多一列提示。"""
    xlsx = Path(path)
    if not xlsx.exists() or not xlsx.is_file():
        return results.failed(
            "read_excel",
            ui("other.015") % xlsx.name,
            details={"filename": xlsx.name},
        )
    try:
        with zipfile.ZipFile(xlsx) as zf:
            shared = []
            if "xl/sharedStrings.xml" in zf.namelist():
                shared = _shared_strings(_parse_xml(zf.read("xl/sharedStrings.xml")))
            sheet = _parse_xml(zf.read(_first_sheet_path(zf)))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError, ValueError, IndexError) as exc:
        return results.failed(
            "read_excel",
            ui("other.016") % exc,
            details={"filename": xlsx.name},
        )

    grid = {}
    max_row = 0
    max_col = 0
    for cell in sheet.iter(_qn(MAIN_NS, "c")):
        ref = cell.get("r") or ""
        match = CELL_REF_RE.match(ref)
        if not match:
            continue
        col = _col_index(match.group(1))
        row = int(match.group(2))
        grid[(row, col)] = _cell_value(cell, shared)
        max_row = max(max_row, row)
        max_col = max(max_col, col)

    if max_row < 2 or max_col < 1:
        return results.failed("read_excel", ui("other.012"))

    def row_values(row_number: int) -> List[Optional[object]]:
        return [grid.get((row_number, col)) for col in range(1, max_col + 1)]

    header_row = _header_row_number(grid, max_row, max_col)
    title_row = header_row - 1 if header_row > 1 else 1
    title = _first_nonempty(_trim_trailing(row_values(title_row)))
    headers = [None if h in (None, "") else str(h).strip() for h in _trim_trailing(row_values(header_row))]
    rows = []
    for row_number in range(header_row + 1, max_row + 1):
        values = _trim_trailing(row_values(row_number))
        if not values or all(v in (None, "") for v in values):
            continue
        padded = list(values) + [None] * (len(headers) - len(values))
        rows.append(padded[: len(headers)])
    return results.ok(
        "read_excel",
        ui("other.008"),
        details={"title": title, "headers": headers, "rows": rows, "header_row": header_row},
    )


def _dictionary_styles_xml(
    *,
    with_hint: bool = False,
    font_name: str = DICTIONARY_FONT_NAME,
) -> ET.Element:
    sheet = ET.Element("styleSheet", xmlns=MAIN_NS)
    fonts = ET.SubElement(sheet, "fonts", count="6" if with_hint else "5")
    charset = "0" if font_name == DICTIONARY_FONT_NAME_EN else "136"

    def add_font(*, bold=False, color_rgb=None, color_theme=None, size=None):
        font = ET.SubElement(fonts, "font")
        if bold:
            ET.SubElement(font, "b")
        ET.SubElement(font, "sz", val=size or DICTIONARY_FONT_SIZE)
        if color_rgb:
            ET.SubElement(font, "color", rgb=color_rgb)
        elif color_theme is not None:
            ET.SubElement(font, "color", theme=str(color_theme))
        ET.SubElement(font, "name", val=font_name)
        ET.SubElement(font, "family", val="2")
        ET.SubElement(font, "charset", val=charset)

    add_font(color_theme=1)
    add_font(color_rgb=STATUS_FONT_COLORS["missing_in_rhino"])
    add_font(color_rgb=STATUS_FONT_COLORS["added_in_rhino"])
    add_font(color_rgb=STATUS_FONT_COLORS["modified"])
    add_font(bold=True, color_rgb=TITLE_FONT_COLOR)
    if with_hint:
        add_font(color_rgb=HINT_FONT_COLOR, size=DICTIONARY_HINT_FONT_SIZE)

    fills = ET.SubElement(sheet, "fills", count="2")
    ET.SubElement(ET.SubElement(fills, "fill"), "patternFill", patternType="none")
    ET.SubElement(ET.SubElement(fills, "fill"), "patternFill", patternType="gray125")
    borders = ET.SubElement(sheet, "borders", count="2")
    empty = ET.SubElement(borders, "border")
    for edge in ("left", "right", "top", "bottom", "diagonal"):
        ET.SubElement(empty, edge)
    lined = ET.SubElement(borders, "border")
    for edge in ("left", "right", "top", "bottom"):
        ET.SubElement(ET.SubElement(lined, edge, style="thin"), "color", indexed="64")
    ET.SubElement(lined, "diagonal")
    cell_style_xfs = ET.SubElement(sheet, "cellStyleXfs", count="1")
    ET.SubElement(
        cell_style_xfs,
        "xf",
        numFmtId="0",
        fontId="0",
        fillId="0",
        borderId="0",
    )
    xfs = ET.SubElement(sheet, "cellXfs", count="6" if with_hint else "5")

    def add_xf(font_id: str, *, border=True, align=True):
        xf = ET.SubElement(
            xfs,
            "xf",
            numFmtId="0",
            fontId=font_id,
            fillId="0",
            borderId="1" if border else "0",
            xfId="0",
            applyFont="1",
        )
        if border:
            xf.set("applyBorder", "1")
        if align:
            xf.set("applyAlignment", "1")
            ET.SubElement(xf, "alignment", horizontal="left", vertical="center")
        return xf

    add_xf("0")
    add_xf("4", border=False)
    add_xf("1")
    add_xf("2")
    add_xf("3")
    if with_hint:
        add_xf("5", border=False)
    styles = ET.SubElement(sheet, "cellStyles", count="1")
    ET.SubElement(styles, "cellStyle", name="一般", xfId="0", builtinId="0")
    return sheet


def _text_status(value) -> str:
    if value in (None, ""):
        return ""
    return str(value).strip()


def write_table(
    path: Path,
    title: str,
    headers: Sequence[str],
    rows: Sequence[Sequence[object]],
    *,
    profile: Optional[str] = None,
    hint: Optional[str] = None,
    font_name: Optional[str] = None,
) -> results.Result:
    """寫入僅供測試／反向匯出使用的簡單 xlsx。不覆寫不存在的父目錄以外的檔案。"""
    target = Path(path)
    if not target.parent.exists():
        return results.failed("read_excel", ui("other.014"))
    styled = profile == "dictionary"
    dictionary_font = font_name or DICTIONARY_FONT_NAME
    strings = []
    index_of = {}

    def intern(text: str) -> int:
        if text not in index_of:
            index_of[text] = len(strings)
            strings.append(text)
        return index_of[text]

    def append_cell(row_el: ET.Element, col: int, row: int, value, style_id: Optional[str] = None) -> None:
        if value in (None, "") and not (styled and style_id is not None):
            return
        cell = ET.SubElement(row_el, "c", r="%s%s" % (_col_letters(col), row))
        if style_id is not None:
            cell.set("s", style_id)
        if value in (None, ""):
            return
        if isinstance(value, bool):
            cell.set("t", "b")
            ET.SubElement(cell, "v").text = "1" if value else "0"
            return
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            ET.SubElement(cell, "v").text = str(value)
            return
        cell.set("t", "s")
        ET.SubElement(cell, "v").text = str(intern(str(value)))

    sheet = ET.Element("worksheet", xmlns=MAIN_NS)
    if styled:
        ET.SubElement(
            sheet,
            "sheetFormatPr",
            defaultColWidth="9",
            defaultRowHeight=DICTIONARY_ROW_HEIGHT,
            customHeight="1",
        )
        cols = ET.SubElement(sheet, "cols")
        widths = list(DICTIONARY_COLUMN_WIDTHS)
        while len(widths) < len(headers):
            widths.append(18.0)
        for index, width in enumerate(widths[: max(len(headers), 1)], start=1):
            ET.SubElement(
                cols,
                "col",
                min=str(index),
                max=str(index),
                width=str(width),
                customWidth="1",
            )
    sheet_data = ET.SubElement(sheet, "sheetData")
    row_number = 1
    if hint:
        hint_row = ET.SubElement(sheet_data, "row", r="1")
        if styled:
            hint_row.set("ht", DICTIONARY_HINT_HEIGHT)
            hint_row.set("customHeight", "1")
        append_cell(hint_row, 1, 1, hint, STYLE_HINT if styled else None)
        row_number = 2
    title_row = ET.SubElement(sheet_data, "row", r=str(row_number))
    if styled:
        title_row.set("ht", DICTIONARY_TITLE_HEIGHT)
        title_row.set("customHeight", "1")
    append_cell(title_row, 1, row_number, title, STYLE_TITLE if styled else None)
    row_number += 1
    header_row = ET.SubElement(sheet_data, "row", r=str(row_number))
    if styled:
        header_row.set("ht", DICTIONARY_HEADER_HEIGHT)
        header_row.set("customHeight", "1")
    for col, header in enumerate(headers, start=1):
        append_cell(header_row, col, row_number, header, STYLE_HEADER if styled else None)
    status_col = None
    if styled:
        for index, header in enumerate(headers, start=1):
            if header == "diff_status":
                status_col = index
                break
    header_row_number = row_number
    for offset, values in enumerate(rows):
        data_row = header_row_number + 1 + offset
        row_el = ET.SubElement(sheet_data, "row", r=str(data_row))
        if styled:
            row_el.set("ht", DICTIONARY_ROW_HEIGHT)
            row_el.set("customHeight", "1")
        padded = list(values) + [None] * max(0, len(headers) - len(values))
        status_value = padded[status_col - 1] if status_col else None
        last_col = len(headers) if styled else max(len(values), 0)
        for col in range(1, last_col + 1):
            style_id = None
            if styled:
                if status_col and col == status_col:
                    style_id = STATUS_STYLE_IDS.get(_text_status(status_value), STYLE_BODY)
                else:
                    style_id = STYLE_BODY
            value = padded[col - 1] if col <= len(padded) else None
            append_cell(row_el, col, data_row, value, style_id)

    sst = ET.Element(
        "sst",
        xmlns=MAIN_NS,
        count=str(len(strings)),
        uniqueCount=str(len(strings)),
    )
    for text in strings:
        si = ET.SubElement(sst, "si")
        t = ET.SubElement(si, "t")
        t.text = text

    workbook = ET.Element("workbook", xmlns=MAIN_NS)
    workbook.set("xmlns:r", OFFICE_REL_NS)
    sheets = ET.SubElement(workbook, "sheets")
    sheet_el = ET.SubElement(sheets, "sheet", name="Dictionary", sheetId="1")
    sheet_el.set(_qn(OFFICE_REL_NS, "id"), "rId1")

    types = ET.Element("Types", xmlns=CONTENT_NS)
    ET.SubElement(
        types,
        "Default",
        Extension="rels",
        ContentType="application/vnd.openxmlformats-package.relationships+xml",
    )
    ET.SubElement(types, "Default", Extension="xml", ContentType="application/xml")
    ET.SubElement(
        types,
        "Override",
        PartName="/xl/workbook.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
    )
    ET.SubElement(
        types,
        "Override",
        PartName="/xl/worksheets/sheet1.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
    )
    ET.SubElement(
        types,
        "Override",
        PartName="/xl/sharedStrings.xml",
        ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml",
    )
    if styled:
        ET.SubElement(
            types,
            "Override",
            PartName="/xl/styles.xml",
            ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml",
        )

    root_rels = ET.Element("Relationships", xmlns=PKG_REL_NS)
    ET.SubElement(
        root_rels,
        "Relationship",
        Id="rId1",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        Target="xl/workbook.xml",
    )
    wb_rels = ET.Element("Relationships", xmlns=PKG_REL_NS)
    ET.SubElement(
        wb_rels,
        "Relationship",
        Id="rId1",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet",
        Target="worksheets/sheet1.xml",
    )
    ET.SubElement(
        wb_rels,
        "Relationship",
        Id="rId2",
        Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings",
        Target="sharedStrings.xml",
    )
    if styled:
        ET.SubElement(
            wb_rels,
            "Relationship",
            Id="rId3",
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles",
            Target="styles.xml",
        )

    def dump(element: ET.Element) -> bytes:
        return ET.tostring(element, encoding="utf-8", xml_declaration=True)

    try:
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", dump(types))
            zf.writestr("_rels/.rels", dump(root_rels))
            zf.writestr("xl/workbook.xml", dump(workbook))
            zf.writestr("xl/_rels/workbook.xml.rels", dump(wb_rels))
            zf.writestr("xl/worksheets/sheet1.xml", dump(sheet))
            zf.writestr("xl/sharedStrings.xml", dump(sst))
            if styled:
                zf.writestr(
                    "xl/styles.xml",
                    dump(
                        _dictionary_styles_xml(
                            with_hint=bool(hint),
                            font_name=dictionary_font,
                        )
                    ),
                )
    except OSError as exc:
        return results.failed("read_excel", ui("other.017") % exc)
    return results.ok("read_excel", ui("other.009"), details={"filename": target.name})


def read_font_table(path: Path) -> List[dict]:
    """測試用：讀 styles.xml 的字型名稱、大小與顏色。"""
    xlsx = Path(path)
    with zipfile.ZipFile(xlsx) as zf:
        if "xl/styles.xml" not in zf.namelist():
            return []
        root = _parse_xml(zf.read("xl/styles.xml"))
    fonts = []
    fonts_el = root.find(_qn(MAIN_NS, "fonts"))
    if fonts_el is None:
        return []
    for font in fonts_el.findall(_qn(MAIN_NS, "font")):
        name = font.find(_qn(MAIN_NS, "name"))
        size = font.find(_qn(MAIN_NS, "sz"))
        color = font.find(_qn(MAIN_NS, "color"))
        fonts.append(
            {
                "name": None if name is None else name.get("val"),
                "size": None if size is None else size.get("val"),
                "color_rgb": None if color is None else color.get("rgb"),
            }
        )
    return fonts


def read_status_cell_colors(path: Path, header: str = "diff_status") -> Dict[str, Optional[str]]:
    """測試用：每個 diff_status 值對應到的字型 RGB。"""
    xlsx = Path(path)
    with zipfile.ZipFile(xlsx) as zf:
        shared = []
        if "xl/sharedStrings.xml" in zf.namelist():
            shared = _shared_strings(_parse_xml(zf.read("xl/sharedStrings.xml")))
        sheet = _parse_xml(zf.read(_first_sheet_path(zf)))
        fonts = []
        xfs = []
        if "xl/styles.xml" in zf.namelist():
            styles = _parse_xml(zf.read("xl/styles.xml"))
            fonts_el = styles.find(_qn(MAIN_NS, "fonts"))
            if fonts_el is not None:
                for font in fonts_el.findall(_qn(MAIN_NS, "font")):
                    color = font.find(_qn(MAIN_NS, "color"))
                    fonts.append(None if color is None else color.get("rgb"))
            xfs_el = styles.find(_qn(MAIN_NS, "cellXfs"))
            if xfs_el is not None:
                for item in xfs_el.findall(_qn(MAIN_NS, "xf")):
                    xfs.append(int(item.get("fontId") or "0"))
    grid = {}
    styles_by_cell = {}
    max_col = 0
    for cell in sheet.iter(_qn(MAIN_NS, "c")):
        ref = cell.get("r") or ""
        match = CELL_REF_RE.match(ref)
        if not match:
            continue
        col = _col_index(match.group(1))
        row = int(match.group(2))
        grid[(row, col)] = _cell_value(cell, shared)
        styles_by_cell[(row, col)] = cell.get("s")
        max_col = max(max_col, col)
    status_col = None
    header_row = 2
    for col in range(1, max_col + 1):
        for row in range(1, 6):
            if str(grid.get((row, col)) or "").strip() == header:
                status_col = col
                header_row = row
                break
        if status_col is not None:
            break
    colors = {}
    if status_col is None:
        return colors
    for (row, col), value in grid.items():
        if col != status_col or row <= header_row or value in (None, ""):
            continue
        style_id = styles_by_cell.get((row, col))
        rgb = None
        if style_id not in (None, "") and xfs:
            font_id = xfs[int(style_id)]
            if 0 <= font_id < len(fonts):
                rgb = fonts[font_id]
        colors[str(value)] = rgb
    return colors
