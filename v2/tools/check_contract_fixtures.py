# -*- coding: utf-8 -*-
"""檢查 v2/fixtures/contract 與 schema 是否符合資料契約。

不依賴 Rhino。第一條規則：measurement_rule 與 estimation_unit 量綱必須一致。
用法：
    python v2/tools/check_contract_fixtures.py
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "fixtures" / "contract"
SCHEMA = ROOT / "fixtures" / "schema"
LEGACY = ROOT / "fixtures" / "legacy" / "tag_block_text"

RULE_DIM = {
    "COUNT": "count",
    "LEN_W": "length",
    "LEN_D": "length",
    "LEN_H": "length",
    "AREA_WD": "area",
    "AREA_WH": "area",
    "AREA_DH": "area",
    "VOL_WDH": "volume",
}
UNIT_DIM = {
    "樘": "count",
    "片": "count",
    "組": "count",
    "台": "count",
    "座": "count",
    "cm": "length",
    "mm": "length",
    "坪": "area",
    "才": "area",
    "m2": "area",
    "m3": "volume",
    "ea": "count",
}
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
ITEM_NAME_RE = re.compile(r"^([A-Za-z]+)-([0-9]+)__(.+)$")

FAILS: list[str] = []


def fail(msg: str) -> None:
    FAILS.append(msg)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def classify_rule(unit, rule) -> str:
    if rule in (None, ""):
        return "warn_no_quantity"
    if rule not in RULE_DIM:
        return "block"
    if unit not in UNIT_DIM:
        return "block"
    if RULE_DIM[rule] != UNIT_DIM[unit]:
        return "block"
    return "pass"


def vec_len(v) -> float:
    return math.sqrt(sum(x * x for x in v))


def nearly_unit(v) -> bool:
    return abs(vec_len(v) - 1.0) < 1e-6


def nearly_ortho(a, b) -> bool:
    return abs(sum(x * y for x, y in zip(a, b))) < 1e-6


def aabb_overlap_area(p, q) -> float:
    ax0, ay0 = min(x for x, _ in p), min(y for _, y in p)
    ax1, ay1 = max(x for x, _ in p), max(y for _, y in p)
    bx0, by0 = min(x for x, _ in q), min(y for _, y in q)
    bx1, by1 = max(x for x, _ in q), max(y for _, y in q)
    dx = min(ax1, bx1) - max(ax0, bx0)
    dy = min(ay1, by1) - max(ay0, by0)
    if dx > 1e-9 and dy > 1e-9:
        return dx * dy
    return 0.0


def check_measurement_baseline() -> None:
    data = load(CONTRACT / "dictionary" / "measurement_rules.baseline.json")
    cols = load(CONTRACT / "dictionary" / "columns.json")
    rows = data["rows"]
    if data["row_count"] != 92 or len(rows) != 92:
        fail("baseline 應為 92 列，實際 %s/%s" % (data["row_count"], len(rows)))
    if sorted(data["type_categories"]) != cols["type_categories"]:
        fail("type_categories 與 columns.json 不一致")
    if len(cols["display_columns"]) != 15:
        fail("Dictionary 應為 15 欄")
    seen = set()
    for row in rows:
        tid = row["type_id"]
        if tid in seen:
            fail("baseline 重複 type_id %s" % tid)
        seen.add(tid)
        if row["type_category"] not in cols["type_categories"]:
            fail("未知 type_category %s" % row["type_category"])
        if row["type_id"] != "%s-%s" % (row["type_category"], row["type_sequence"]):
            fail("type_id 拆分不一致 %s" % tid)
        result = classify_rule(row["estimation_unit"], row["measurement_rule"])
        if result != "pass":
            fail("baseline 量綱不符 %s %s/%s -> %s" % (
                tid, row["estimation_unit"], row["measurement_rule"], result
            ))
        if row["elevation_basis"] not in ("BH", "TH", "CH", "BC"):
            fail("baseline 非法 elevation_basis %s %s" % (tid, row["elevation_basis"]))


def check_dictionary_cases() -> None:
    cols = load(CONTRACT / "dictionary" / "columns.json")
    cases = load(CONTRACT / "dictionary" / "cases.json")["cases"]
    for case in cases:
        cid = case["id"]
        got = "pass"
        if case.get("extra_display_columns") or case.get("display_column_count") not in (None, 15):
            got = "block"
        elif "duplicate_type_id" in case:
            got = "block"
        elif "estimation_unit" in case:
            got = classify_rule(case.get("estimation_unit"), case.get("measurement_rule"))
        if got != case["expect"]:
            fail("dictionary case %s 期望 %s 得到 %s" % (cid, case["expect"], got))
        if cid == "cb-columns-forbidden" and "_CB.01" not in case["extra_display_columns"]:
            fail("cb case 未覆蓋 _CB.01")
        if cid == "unknown-column" and not set(case["extra_display_columns"]).isdisjoint(cols["display_columns"]):
            fail("unknown-column 應使用不在 15 欄內的名稱")


def check_object_ids() -> None:
    for case in load(CONTRACT / "identity" / "object_id_cases.json")["cases"]:
        cid = case["id"]
        if case["action"] == "create":
            ok = bool(UUID_RE.match(case["value"]))
            got = "pass" if ok else "block"
            if got != case["expect"]:
                fail("object_id %s 期望 %s 得到 %s" % (cid, case["expect"], got))
        elif case["action"] == "migrate":
            if case["value"].lower() != case["normalized"] or not UUID_RE.match(case["normalized"]):
                fail("object_id %s 正規化失敗" % cid)
        elif case["action"] == "copy":
            if case["source_id"] == "SHOULD_NOT_REUSE":
                fail("object_id copy fixture 無效")
        elif case["action"] == "collide":
            if case["incoming"] not in case["existing"]:
                fail("object_id %s 未構成碰撞" % cid)
            if case["mapping"]["old_id"] == case["mapping"]["new_id"]:
                fail("object_id %s mapping 未換號" % cid)
        elif case["action"] == "rollback":
            if case["mapping"]["old_id"] == case["mapping"]["new_id"]:
                fail("object_id %s rollback mapping 無效" % cid)
        elif case["action"] == "silent_rebuild":
            if case["expect"] != "block":
                fail("object_id 靜默重建必須阻擋")


def check_spaces() -> None:
    for case in load(CONTRACT / "space" / "cases.json")["cases"]:
        cid = case["id"]
        if case["expect"] == "ext":
            if case["space_id"] != "EXT" or "reason" not in case:
                fail("space %s EXT 案例不完整" % cid)
            continue
        spaces = case["spaces"]
        conflict = False
        for i, a in enumerate(spaces):
            for b in spaces[i + 1 :]:
                if a["level_id"] != b["level_id"]:
                    continue
                if aabb_overlap_area(a["polygon"], b["polygon"]) > 0:
                    conflict = True
        got = "block" if conflict else "pass"
        if got != case["expect"]:
            fail("space %s 期望 %s 得到 %s" % (cid, case["expect"], got))


def check_elevation() -> None:
    data = load(CONTRACT / "elevation" / "cases.json")
    if data["allowed"] != ["BH", "TH", "CH", "BC"]:
        fail("elevation allowed 必須是 BH/TH/CH/BC")
    for case in data["cases"]:
        basis, geom = case["basis"], case["geometry"]
        if basis == "TH/BH":
            got = "migration_only"
        elif basis not in data["allowed"]:
            got = "block"
        elif basis == "BC" and geom != "block":
            got = "block"
        else:
            got = "pass"
        if got != case["expect"]:
            fail("elevation %s 期望 %s 得到 %s" % (case["id"], case["expect"], got))


def frame_ok(frame: dict) -> bool:
    if frame.get("schema_id") != "loopflow.local_frame" or frame.get("schema_version") != 1:
        return False
    axes = [frame["x_axis"], frame["y_axis"], frame["z_axis"]]
    if not all(nearly_unit(v) for v in axes):
        return False
    return nearly_ortho(axes[0], axes[1]) and nearly_ortho(axes[0], axes[2]) and nearly_ortho(axes[1], axes[2])


def check_local_frame() -> None:
    for case in load(CONTRACT / "local_frame" / "cases.json")["cases"]:
        cid = case["id"]
        stored = case.get("stored_frame")
        geom = case.get("geometry")
        if stored:
            got = "reuse" if frame_ok(stored) else "block"
        elif case.get("fallback") == "world_bbox":
            got = "block"
        elif geom == "oriented_box":
            got = "derive"
            if case.get("derivation_method") != "oriented_box":
                fail("local_frame %s method 錯誤" % cid)
        elif geom == "closed_box":
            got = "block"
        elif geom == "block_instance":
            got = "derive"
            if case.get("derivation_method") != "block_insertion":
                fail("local_frame %s method 錯誤" % cid)
        elif geom == "extrusion":
            got = "derive"
        elif geom == "planar_curve":
            got = "derive"
        else:
            got = "block"
        if got != case["expect"]:
            fail("local_frame %s 期望 %s 得到 %s" % (cid, case["expect"], got))


def check_drawing() -> None:
    spec = load(SCHEMA / "drawing.json")
    if spec.get("layer_root") != "LoopFlow_Extract":
        fail("drawing 根圖層必須是 LoopFlow_Extract")
    if spec.get("plot_weight") != -1:
        fail("drawing 根圖層 PlotWeight 必須是 -1（No Print）")
    for case in load(CONTRACT / "drawing" / "provenance_cases.json")["cases"]:
        ids = case.get("source_object_ids", [])
        n = len(ids)
        if n == 0:
            cov = "unindexed"
        elif n == 1:
            cov = "indexed"
        else:
            cov = "ambiguous"
        if "coverage" in case and case["coverage"] != cov:
            fail("drawing %s coverage 應為 %s" % (case["id"], cov))
        if case.get("forbid_state") and case.get("forbid_state") == case.get("provenance_state"):
            fail("drawing %s 禁止狀態卻出現了" % case["id"])
        if n > 1 and case["provenance_state"] != "ambiguous":
            fail("drawing 多來源必須 ambiguous")
        if case.get("coverage_incomplete") and case.get("block_drawing"):
            fail("索引不完整不得阻擋 Drawing")


def check_tags() -> None:
    templates = load(SCHEMA / "tag_templates.json")
    legacy = {templates["lock_legacy_key"]}
    title = 0
    by_id = {}
    for t in templates["templates"]:
        by_id[t["template_id"]] = t
        if t["role"] == "title_frame":
            title += 1
        for f in t["fields"]:
            legacy.update(f.get("legacy", []))
    if len(templates["templates"]) != 10 or title != 1:
        fail("應有 10 份 manifest 且恰好 1 個 title_frame")
    text_keys = set()
    for path in LEGACY.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        text_keys.update(re.findall(r'UserText\(\s*"block"\s*,\s*"([^"]+)"', text))
    if text_keys != legacy:
        fail("24 key 與畫面擷取不一致 missing=%s extra=%s" % (text_keys - legacy, legacy - text_keys))

    item = by_id["TAG_ITEM"]
    if not ITEM_NAME_RE.match("FF-01__Chair-1"):
        fail("家具名稱範例應通過")
    pattern = re.compile(item["source_block_name_pattern"])

    for case in load(CONTRACT / "tag" / "cases.json")["cases"]:
        cid = case["id"]
        if cid == "unknown-block-zero-write":
            known = {n for t in templates["templates"] for n in t["block_names"]}
            if case["block_name"] in known:
                fail("unknown block 案例用了已知名稱")
        elif cid == "title-frame-writes-drawing-ids":
            tf = by_id["SAMPLE_FRAME"]
            if tf["role"] != "title_frame":
                fail("Sample_Frame 必須是 title_frame")
        elif cid == "tag-dw-sync-skips":
            dw = by_id["TAG_DW"]
            if any(f["owner"] != "manual" for f in dw["fields"]) or dw["lock_allowed"]:
                fail("TAG_DW 必須全手動且無 lock")
        elif cid == "duplicate-clears-render-and-remarks":
            t = by_id[case["template_id"]]
            clearable = {"source_object_id"}
            for f in t["fields"]:
                if f.get("clear_on_duplicate"):
                    clearable.add(f["key"])
            if set(case["must_clear"]) - clearable:
                fail("duplicate clear 清單與 manifest 不符")
        elif cid == "duplicate-keeps-tag-dw":
            t = by_id["TAG_DW"]
            kept = {f["key"] for f in t["fields"] if not f.get("clear_on_duplicate")}
            if set(case["must_keep"]) - kept:
                fail("TAG_DW 保留清單與 manifest 不符")
        elif cid == "item-block-name-ok":
            if not pattern.match(case["source_block_name"]):
                fail("合法家具名稱未通過")
        elif cid == "item-block-name-bad":
            if pattern.match(case["source_block_name"]):
                fail("非法家具名稱不應通過")


def check_registry() -> None:
    spec = load(SCHEMA / "registry.json")
    allowed = set(spec["required_root"])
    for case in load(CONTRACT / "registry" / "cases.json")["cases"]:
        payload = case["payload"]
        extra = set(payload) - allowed
        got = "pass"
        if payload.get("schema_id") != "loopflow.registry":
            got = "block"
        elif payload.get("schema_version") != 1:
            got = "block"
        elif extra:
            got = "block"
        elif not any(s.get("space_id") == "EXT" for s in payload.get("spaces", [])):
            got = "block"
        if got != case["expect"]:
            fail("registry %s 期望 %s 得到 %s extra=%s" % (case["id"], case["expect"], got, extra))


def check_quantity() -> None:
    data = load(CONTRACT / "quantity" / "cases.json")
    if abs(data["cai_side_cm"] * data["cai_side_cm"] - data["cai_cm2"]) > 1e-9:
        fail("才的面積常數應為 30.3×30.3")
    if data["ping_from_m2"] != 0.3025:
        fail("坪換算必須是 0.3025")
    for case in data["cases"]:
        w, d, h = case["w"], case["d"], case["h"]
        rule, unit = case["rule"], case["unit"]
        if classify_rule(unit, rule) != "pass":
            fail("quantity %s 量綱不符" % case["id"])
        if rule == "COUNT":
            q = 1
        elif rule == "AREA_WD" and unit == "才":
            q = (w * d) / data["cai_cm2"]
        elif rule == "AREA_WD" and unit == "坪":
            q = (w * d / 10000.0) * data["ping_from_m2"]
        else:
            fail("quantity %s 未實作" % case["id"])
            continue
        if abs(q - case["expect_quantity"]) > 1e-6:
            fail("quantity %s 期望 %s 得到 %s" % (case["id"], case["expect_quantity"], q))


def view_transform_ok(payload: dict) -> bool:
    spec = load(SCHEMA / "view.json")
    if payload.get("schema_id") != spec["transform_schema_id"]:
        return False
    if payload.get("schema_version") != spec["transform_schema_version"]:
        return False
    if set(payload) != set(spec["transform_keys"]):
        return False
    if abs(abs(float(payload["scale_x"])) - 1.0) > 1e-9:
        return False
    if abs(abs(float(payload["scale_y"])) - 1.0) > 1e-9:
        return False
    if len(payload.get("origin_2d") or ()) != 3:
        return False
    if len(payload.get("origin_3d_local") or ()) != 2:
        return False
    axes = [payload["cp_x_axis"], payload["cp_y_axis"], payload["cp_z_axis"]]
    if not all(len(v) == 3 and nearly_unit(v) for v in axes):
        return False
    return nearly_ortho(axes[0], axes[1]) and nearly_ortho(axes[0], axes[2]) and nearly_ortho(axes[1], axes[2])


def classify_view_case(case: dict) -> str:
    if case.get("cancelled"):
        return "cancel"
    text = case.get("text_dot")
    if not text:
        return "block"
    if not case.get("has_geometry") and not case.get("upgrade_host"):
        return "block"
    needle = str(text).upper()
    hits = [
        name for name in (case.get("clipping_planes") or [])
        if needle in str(name).upper()
    ]
    if len(hits) != 1:
        return "block"
    payload = case.get("transform")
    if payload is not None and not view_transform_ok(payload):
        return "block"
    if case.get("upgrade_host"):
        return "upgrade"
    return "pass"


def check_view() -> None:
    spec = load(SCHEMA / "view.json")
    if spec["schema_id"] != "loopflow.view" or spec["schema_version"] != 1:
        fail("view schema 身分錯誤")
    if spec["layer"] != "LoopFlow::Anchor_Frame":
        fail("view 圖層必須是 LoopFlow::Anchor_Frame")
    required = {
        "view_id": "lf_view_id",
        "schema_id": "lf_schema_id",
        "schema_version": "lf_schema_version",
        "clipping_plane_id": "lf_clipping_plane_id",
        "view_transform": "lf_view_transform",
    }
    for key, usertext in required.items():
        if spec["usertext_keys"].get(key) != usertext:
            fail("view UserText %s 應為 %s" % (key, usertext))
    if "Role" not in spec["legacy_keys"] or "Target_CP" not in spec["legacy_keys"]:
        fail("view 必須列出 1.x Role／Target_CP 供 migration")
    for case in load(CONTRACT / "view" / "cases.json")["cases"]:
        got = classify_view_case(case)
        if got != case["expect"]:
            fail("view %s 期望 %s 得到 %s" % (case["id"], case["expect"], got))


def check_sheet() -> None:
    """檢查 Sheet schema 與案例的結構一致，不重寫編號邏輯（行為由 unittest 驗證）。"""
    spec = load(SCHEMA / "sheet.json")
    if spec["schema_id"] != "loopflow.sheet" or spec["schema_version"] != 1:
        fail("sheet schema 身分錯誤")
    if spec["document_namespace"] != "lf_sheet":
        fail("Sheet metadata 命名空間必須是 lf_sheet")
    if spec["usertext_keys"].get("sheet_id") != "lf_sheet_id":
        fail("Sheet 身分錨點必須是 lf_sheet_id")
    fields = set(spec["metadata_fields"])
    for group in ("layout_id_written_fields", "manual_fields", "derived_fields"):
        extra = set(spec[group]) - fields
        if extra:
            fail("sheet %s 出現未定義欄位 %s" % (group, sorted(extra)))
    if set(spec["manual_fields"]) & set(spec["layout_id_written_fields"]):
        fail("人工欄位不得同時由 Layout ID 寫入")
    if set(spec["persistent_fields"]) & set(spec["derived_fields"]):
        fail("persistent 與 derived 欄位不得重疊")
    if "scale" in spec["layout_id_written_fields"]:
        fail("比例是人工欄，Layout ID 不得寫入")
    if not spec["catalog_reserved_prefix"].startswith("lf_catalog"):
        fail("Catalog 保留前綴必須是 lf_catalog_")
    defaults = spec["naming_defaults"]
    try:
        sample = defaults["drawing_no_format"].format(prefix="IN", number="201")
    except (KeyError, IndexError, ValueError) as exc:
        fail("drawing_no_format 無法格式化：%s" % exc)
        sample = ""
    if sample and sample != "IN 201":
        fail("drawing_no_format 預設應產生 IN 201，得到 %s" % sample)
    if defaults.get("baseline_mark") != "**":
        fail("baseline_mark 預設應為 **")

    cases = load(CONTRACT / "sheet" / "cases.json")
    allowed_parse = {"baseline", "inherit", "skip", "manual", "manual_invalid"}
    for case in cases["page_name_cases"]:
        if case["expect"] not in allowed_parse:
            fail("sheet 頁名案例 %s 的 expect 不在 %s" % (case["id"], sorted(allowed_parse)))
        if case["expect"] in ("baseline", "manual") and not case.get("series"):
            fail("sheet 頁名案例 %s 宣告 %s 卻沒有 series" % (case["id"], case["expect"]))
        if case["expect"] == "skip" and "drawing_name" in case:
            fail("sheet 頁名案例 %s 要跳過就不該期望 drawing_name" % case["id"])
    for case in cases["numbering_cases"]:
        if len(case["pages"]) != len(case["expect_drawing_no"]):
            fail("sheet 編號案例 %s 的頁數與期望圖號數不符" % case["id"])
        numbered = [no for no in case["expect_drawing_no"] if no]
        if len(numbered) != len(set(numbered)):
            fail("sheet 編號案例 %s 出現重複圖號" % case["id"])
    for case in cases["active_cases"]:
        active = set(case["expect_active"])
        if active - set(case["frame_sheet_ids"]):
            fail("sheet active 案例 %s 把沒有圖框的 Sheet 當 active" % case["id"])
        if active - set(case["metadata_sheet_ids"]):
            fail("sheet active 案例 %s 的 active Sheet 缺 metadata" % case["id"])
        for sheet_id in case["metadata_sheet_ids"]:
            if not UUID_RE.match(sheet_id):
                fail("sheet active 案例 %s 的 sheet_id 不是 UUID v4" % case["id"])
    for case in cases["stale_cases"]:
        recorded = case["recorded_page_position"]
        expect = "current" if recorded == case["current_page_position"] else "stale"
        if case["expect"] != expect:
            fail("sheet stale 案例 %s 期望 %s 與頁序推算不符" % (case["id"], case["expect"]))
    for case in cases["frame_cases"]:
        if case["expect"] == "write" and (case["frames_on_page"] != 1 or case.get("locked")):
            fail("sheet 圖框案例 %s 只有單一未鎖圖框才能寫入" % case["id"])
        if case["expect"] == "skip" and case["frames_on_page"] == 1 and not case.get("locked"):
            fail("sheet 圖框案例 %s 沒有跳過的理由" % case["id"])


def check_catalog() -> None:
    """檢查 Catalog schema 與案例形狀；排序／配對行為由 unittest 驗證。"""
    spec = load(SCHEMA / "catalog.json")
    if spec["schema_id"] != "loopflow.catalog" or spec["schema_version"] != 1:
        fail("catalog schema 身分錯誤")
    if spec["layers"].get("drawing_no") != "LoopFlow::Drawing_Number":
        fail("圖號定位點圖層必須是 LoopFlow::Drawing_Number")
    if spec["layers"].get("drawing_name") != "LoopFlow::Drawing_Name":
        fail("圖名定位點圖層必須是 LoopFlow::Drawing_Name")
    if spec["layers"].get("text") != "LoopFlow::Drawing_Text":
        fail("目錄文字圖層必須是 LoopFlow::Drawing_Text")
    if spec["layer_colors"].get("drawing_no") != [255, 0, 0]:
        fail("圖號定位點顏色必須是紅 (255,0,0)")
    if spec["layer_colors"].get("drawing_name") != [0, 255, 0]:
        fail("圖名定位點顏色必須是綠 (0,255,0)")
    if spec["layer_colors"].get("text") != [205, 179, 139]:
        fail("目錄文字顏色必須是 #CDB38B")
    keys = spec["usertext_keys"]
    expected = {
        "catalog_id": "lf_catalog_id",
        "field": "lf_catalog_field",
        "sheet_id": "lf_catalog_sheet_id",
        "point_id": "lf_catalog_point_id",
        "home_layer": "lf_catalog_home_layer",
        "generated_by": "lf_generated_by",
        "text_font": "lf_catalog_text_font",
        "text_height": "lf_catalog_text_height",
        "text_layer": "lf_catalog_text_layer",
        "text_color": "lf_catalog_text_color",
    }
    for name, value in expected.items():
        if keys.get(name) != value:
            fail("catalog UserText %s 應為 %s" % (name, value))
    if spec.get("text_color_by_layer") != "by_layer":
        fail("catalog 跟圖層色必須寫 by_layer")
    if spec.get("default_text_font") != "Arial":
        fail("catalog 預設字型必須是 Arial")
    if spec["allowed_fields"] != ["drawing_no", "drawing_name"]:
        fail("catalog allowed_fields 只能是 drawing_no／drawing_name")
    if spec["generated_by_value"] != "LF_Catalog":
        fail("產生文字的 lf_generated_by 必須是 LF_Catalog")
    if float(spec["column_tolerance"]) <= 0 or float(spec["row_tolerance"]) <= 0:
        fail("catalog 容差必須為正數")

    allowed = {
        "pass",
        "page_count_mismatch",
        "row_mismatch",
        "too_many_sheets",
        "missing_anchors",
        "missing_sheets",
        "mixed_catalog_id",
        "block_instance",
    }
    cases = load(CONTRACT / "catalog" / "cases.json")
    if cases.get("schema_id") != "loopflow.catalog":
        fail("catalog cases 的 schema_id 必須是 loopflow.catalog")
    for case in cases["cases"]:
        expect = case.get("expect")
        if expect not in allowed:
            fail("catalog 案例 %s 的 expect 不在 %s" % (case.get("id"), sorted(allowed)))
        numbers = case.get("number_points") or []
        names = case.get("name_points") or []
        sheets = case.get("sheet_ids") or []
        for sheet_id in sheets:
            if not UUID_RE.match(sheet_id):
                fail("catalog 案例 %s 的 sheet_id 不是 UUID v4" % case["id"])
        if expect == "pass":
            n_pages = {}
            m_pages = {}
            for point in numbers:
                n_pages[point["page_number"]] = n_pages.get(point["page_number"], 0) + 1
            for point in names:
                m_pages[point["page_number"]] = m_pages.get(point["page_number"], 0) + 1
            if n_pages != m_pages:
                fail("catalog 通過案例 %s 的逐頁數量應相等" % case["id"])
            if len(sheets) > min(len(numbers), len(names)):
                fail("catalog 通過案例 %s 的 Sheet 數不可多於定位點" % case["id"])
            order = case.get("expect_order") or []
            if order and set(order) != {point["id"] for point in numbers}:
                fail("catalog 案例 %s 的 expect_order 必須涵蓋全部圖號定位點" % case["id"])
        if expect == "too_many_sheets" and len(sheets) <= min(len(numbers), len(names)):
            fail("catalog 案例 %s 宣告 too_many_sheets 但 Sheet 並不多於定位點" % case["id"])
        if expect == "page_count_mismatch":
            n_pages = {}
            m_pages = {}
            for point in numbers:
                n_pages[point["page_number"]] = n_pages.get(point["page_number"], 0) + 1
            for point in names:
                m_pages[point["page_number"]] = m_pages.get(point["page_number"], 0) + 1
            if n_pages == m_pages:
                fail("catalog 案例 %s 宣告 page_count_mismatch 但逐頁數量相同" % case["id"])


def main() -> int:
    check_measurement_baseline()
    check_dictionary_cases()
    check_object_ids()
    check_spaces()
    check_elevation()
    check_local_frame()
    check_drawing()
    check_tags()
    check_registry()
    check_quantity()
    check_view()
    check_sheet()
    check_catalog()
    if FAILS:
        print("契約 fixtures 失敗 %s 項：" % len(FAILS))
        for msg in FAILS:
            print(" -", msg)
        return 1
    print("契約 fixtures 通過：92 筆量綱、15 欄、24 個 Tag key、Space／Registry／Duplicate／View／Sheet／Catalog 案例；quantity／frame 常數保留給 GH。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
