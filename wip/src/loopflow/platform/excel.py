# -*- coding: utf-8 -*-
"""以標準庫讀寫簡單 xlsx 工作表。不依賴 openpyxl／pandas，也不寫死路徑。"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path
from typing import List, Optional, Sequence
from xml.etree import ElementTree as ET

from loopflow.foundation import results

MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CONTENT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
CELL_REF_RE = re.compile(r"^([A-Z]+)(\d+)$")


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


def read_table(path: Path) -> results.Result:
    """讀取第一張工作表：第 1 列標題、第 2 列欄名、其後為資料列。"""
    xlsx = Path(path)
    if not xlsx.exists() or not xlsx.is_file():
        return results.failed(
            "read_excel",
            "找不到 Dictionary 檔案 %s。不建立檔案。" % xlsx.name,
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
            "無法讀取 xlsx：%s" % exc,
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
        return results.failed("read_excel", "xlsx 缺少標題列或欄名列。")

    def row_values(row_number: int) -> List[Optional[object]]:
        return [grid.get((row_number, col)) for col in range(1, max_col + 1)]

    title_cells = _trim_trailing(row_values(1))
    title = None
    for cell in title_cells:
        if cell not in (None, ""):
            title = str(cell).strip()
            break
    headers = [None if h in (None, "") else str(h).strip() for h in _trim_trailing(row_values(2))]
    rows = []
    for row_number in range(3, max_row + 1):
        values = _trim_trailing(row_values(row_number))
        if not values or all(v in (None, "") for v in values):
            continue
        padded = list(values) + [None] * (len(headers) - len(values))
        rows.append(padded[: len(headers)])
    return results.ok(
        "read_excel",
        "已讀取工作表",
        details={"title": title, "headers": headers, "rows": rows},
    )


def write_table(path: Path, title: str, headers: Sequence[str], rows: Sequence[Sequence[object]]) -> results.Result:
    """寫入僅供測試／反向匯出使用的簡單 xlsx。不覆寫不存在的父目錄以外的檔案。"""
    target = Path(path)
    if not target.parent.exists():
        return results.failed("read_excel", "輸出目錄不存在，不建立。")
    strings = []
    index_of = {}

    def intern(text: str) -> int:
        if text not in index_of:
            index_of[text] = len(strings)
            strings.append(text)
        return index_of[text]

    def append_cell(row_el: ET.Element, col: int, row: int, value) -> None:
        if value in (None, ""):
            return
        cell = ET.SubElement(row_el, "c", r="%s%s" % (_col_letters(col), row))
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
    sheet_data = ET.SubElement(sheet, "sheetData")
    title_row = ET.SubElement(sheet_data, "row", r="1")
    append_cell(title_row, 1, 1, title)
    header_row = ET.SubElement(sheet_data, "row", r="2")
    for col, header in enumerate(headers, start=1):
        append_cell(header_row, col, 2, header)
    for offset, values in enumerate(rows):
        row_number = offset + 3
        row_el = ET.SubElement(sheet_data, "row", r=str(row_number))
        for col, value in enumerate(values, start=1):
            append_cell(row_el, col, row_number, value)

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
    except OSError as exc:
        return results.failed("read_excel", "無法寫入 xlsx：%s" % exc)
    return results.ok("read_excel", "已寫入工作表", details={"filename": target.name})
