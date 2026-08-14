# -*- coding: utf-8 -*-
"""檢查 wip/fixtures/contract 與 schema 是否符合資料契約。

不依賴 Rhino。第一條規則：measurement_rule 與 estimation_unit 量綱必須一致。
用法：
    python wip/tools/check_contract_fixtures.py
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
    "m3": "volume",
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
    if FAILS:
        print("契約 fixtures 失敗 %s 項：" % len(FAILS))
        for msg in FAILS:
            print(" -", msg)
        return 1
    print("契約 fixtures 通過：92 筆量綱、15 欄、24 個 Tag key、Space／frame／Registry／Duplicate 案例。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
