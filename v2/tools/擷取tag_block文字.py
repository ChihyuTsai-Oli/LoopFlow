# -*- coding: utf-8 -*-

import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc
import System

from System.IO import File
from System.Text import UTF8Encoding


def get_screen_sort_key(point):
    """
    按目前 Rhino 視圖由上到下、由左到右排序。
    """
    try:
        active_view = sc.doc.Views.ActiveView

        if active_view is None:
            return (-point.Y, point.X)

        viewport = active_view.ActiveViewport
        screen_point = viewport.WorldToClient(point)

        return (screen_point.Y, screen_point.X)

    except Exception:
        return (-point.Y, point.X)


def get_text_center(geometry, transform):
    """
    取得文字套用 Block 變換後的中心點。
    """
    try:
        bbox = geometry.GetBoundingBox(transform)

        if bbox.IsValid:
            return bbox.Center

    except Exception:
        pass

    try:
        point = geometry.Plane.Origin
        point.Transform(transform)
        return point

    except Exception:
        return Rhino.Geometry.Point3d.Origin


def get_text_content(geometry):
    """
    取得原始文字內容。

    PlainTextWithFields 會保留：
    %<UserText(...)>%

    不會將它轉換成外部顯示的 x、X 或其他值。
    """
    text = None

    if isinstance(geometry, Rhino.Geometry.TextEntity):

        # 優先取得未解析的文字欄位公式
        try:
            text = geometry.PlainTextWithFields
        except Exception:
            text = None

        # 普通文字的備援方式
        if not text:
            try:
                text = geometry.PlainText
            except Exception:
                text = None

        if not text:
            try:
                text = geometry.Text
            except Exception:
                text = None

    elif isinstance(geometry, Rhino.Geometry.TextDot):

        try:
            text = geometry.Text
        except Exception:
            text = None

    return text


def extract_text_from_block(instance_object):
    """
    讀取一個 Block 內的全部文字。

    True 表示包含巢狀 Block。
    只在記憶體中展開，不會修改模型。
    """
    records = []

    try:
        result = instance_object.Explode(True)

        pieces = result[0]
        piece_attributes = result[1]
        piece_transforms = result[2]

    except Exception as error:
        Rhino.RhinoApp.WriteLine(
            "無法讀取 Block：{0}".format(error)
        )
        return records

    if pieces is None or piece_transforms is None:
        return records

    for index in range(len(pieces)):
        piece = pieces[index]

        if piece is None:
            continue

        try:
            geometry = piece.Geometry
        except Exception:
            geometry = None

        if geometry is None:
            continue

        text = get_text_content(geometry)

        if text is None:
            continue

        text = str(text)

        if not text.strip():
            continue

        try:
            transform = piece_transforms[index]
        except Exception:
            transform = Rhino.Geometry.Transform.Identity

        center = get_text_center(
            geometry,
            transform
        )

        records.append({
            "text": text,
            "center": center,
            "sort_key": get_screen_sort_key(center)
        })

    return records


def clean_text_to_lines(text):
    """
    將每個文字物件整理成 TXT 的個別行。
    """
    if text is None:
        return []

    text = str(text)
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        cleaned_line = line.strip()

        if cleaned_line:
            lines.append(cleaned_line)

    return lines


def make_safe_filename(name):
    """
    移除 Windows 檔名不能使用的字元。
    """
    if not name:
        return "block_text"

    invalid_chars = '<>:"/\\|?*'

    safe_name = "".join(
        "_" if character in invalid_chars else character
        for character in str(name)
    )

    safe_name = safe_name.strip()
    safe_name = safe_name.rstrip(".")

    if not safe_name:
        safe_name = "block_text"

    return safe_name


def main():
    block_ids = rs.GetObjects(
        "選取要輸出文字的 Block",
        rs.filter.instance,
        preselect=True
    )

    if not block_ids:
        Rhino.RhinoApp.WriteLine(
            "未選取任何 Block。"
        )
        return

    all_records = []
    block_names = []

    for block_id in block_ids:
        try:
            rhino_object = sc.doc.Objects.FindId(
                block_id
            )
        except Exception:
            rhino_object = None

        if rhino_object is None:
            continue

        if not isinstance(
            rhino_object,
            Rhino.DocObjects.InstanceObject
        ):
            continue

        # 取得 Block 定義名稱
        try:
            definition = rhino_object.InstanceDefinition
            current_name = definition.Name
        except Exception:
            current_name = None

        if current_name:
            current_name = str(current_name)

            if current_name not in block_names:
                block_names.append(current_name)

        # 讀取 Block 文字
        block_records = extract_text_from_block(
            rhino_object
        )

        all_records.extend(block_records)

    if not all_records:
        rs.MessageBox(
            "選取的 Block 中找不到文字。",
            0,
            "輸出 Block 文字"
        )
        return

    # 按目前畫面位置排序
    all_records.sort(
        key=lambda record: record["sort_key"]
    )

    output_lines = []

    for record in all_records:
        lines = clean_text_to_lines(
            record["text"]
        )

        output_lines.extend(lines)

    if not output_lines:
        rs.MessageBox(
            "找到文字物件，但沒有可輸出的文字內容。",
            0,
            "輸出 Block 文字"
        )
        return

    # 一種 Block 名稱：使用該名稱
    if len(block_names) == 1:
        output_name = block_names[0]

    # 多種 Block 名稱：使用第一個名稱並加上 multiple
    elif len(block_names) > 1:
        output_name = block_names[0] + "_multiple"

    else:
        output_name = "block_text"

    output_name = make_safe_filename(
        output_name
    )

    default_filename = output_name + ".txt"

    save_path = rs.SaveFileName(
        "儲存 Block 文字",
        "Text file (*.txt)|*.txt||",
        filename=default_filename
    )

    if not save_path:
        Rhino.RhinoApp.WriteLine(
            "使用者取消儲存。"
        )
        return

    if not save_path.lower().endswith(".txt"):
        save_path += ".txt"

    try:
        lines_array = System.Array[str](
            output_lines
        )

        encoding = UTF8Encoding(True)

        File.WriteAllLines(
            save_path,
            lines_array,
            encoding
        )

    except Exception as error:
        rs.MessageBox(
            "TXT 儲存失敗：\n\n{0}".format(error),
            0,
            "輸出 Block 文字"
        )
        return

    Rhino.RhinoApp.WriteLine(
        "已輸出 {0} 行文字：{1}".format(
            len(output_lines),
            save_path
        )
    )

    rs.MessageBox(
        "完成，共輸出 {0} 行文字。\n\n{1}".format(
            len(output_lines),
            save_path
        ),
        0,
        "輸出 Block 文字"
    )


if __name__ == "__main__":
    main()