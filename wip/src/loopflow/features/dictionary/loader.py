# -*- coding: utf-8 -*-
"""Dictionary Type Catalog 載入與驗證。不寫 Nexus、不計算 quantity。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary import schema
from loopflow.foundation import results
from loopflow.foundation.paths import resolve_workfiles
from loopflow.foundation.version import check_schema
from loopflow.platform import excel

TYPE_OWNED_KEYS = (
    "layer_path",
    "construction_default",
    "type_id",
    "type_display_name",
    "estimation_unit",
    "measurement_rule",
    "elevation_basis",
    "remarks_default",
)


@dataclass(frozen=True)
class TypeRecord:
    layer_path: str
    type_id: str
    type_category: str
    type_sequence: str
    type_display_name: str
    construction_default: Optional[str]
    estimation_unit: Optional[str]
    measurement_rule: Optional[str]
    elevation_basis: str
    remarks_default: Optional[str]


@dataclass(frozen=True)
class TypeCatalog:
    schema_id: str
    schema_version: int
    title: str
    types: Tuple[TypeRecord, ...]

    def by_type_id(self, type_id: str) -> Optional[TypeRecord]:
        for record in self.types:
            if record.type_id == type_id:
                return record
        return None

    def by_layer_path(self, layer_path: str) -> Optional[TypeRecord]:
        for record in self.types:
            if record.layer_path == layer_path:
                return record
        return None


def _text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    text = str(value).strip()
    return text or None


def _row_mapping(headers: Sequence[str], values: Sequence[object]) -> dict:
    mapping = {}
    for index, header in enumerate(headers):
        mapping[header] = values[index] if index < len(values) else None
    return mapping


def _header_failure(headers: Sequence[Optional[str]]) -> Optional[results.Result]:
    names = [h for h in headers if h not in (None, "")]
    if any(schema.is_forbidden_cb_column(name) for name in names):
        return results.blocked(
            "validate_dictionary",
            "Dictionary 含有禁止的 _CB.* 欄，已停止。",
            blocking=("cb_columns_forbidden",),
            details={"headers": tuple(names)},
        )
    if list(headers) != list(schema.DISPLAY_COLUMNS):
        extra = [name for name in names if name not in schema.DISPLAY_COLUMNS]
        code = "unknown_column" if extra or len(names) == len(schema.DISPLAY_COLUMNS) else "wrong_column_count"
        message = (
            "Dictionary 欄名與 schema 1 不符，已停止。不靠欄名前綴猜測。"
            if code == "unknown_column"
            else "Dictionary 應為 15 欄，實際為 %s 欄。已停止。" % len(names)
        )
        return results.blocked(
            "validate_dictionary",
            message,
            blocking=(code,),
            details={"headers": tuple(names), "expected": schema.DISPLAY_COLUMNS},
        )
    return None


def load_from_table(
    *,
    title: Optional[str],
    headers: Sequence[Optional[str]],
    rows: Sequence[Sequence[object]],
    schema_id: str = schema.SCHEMA_ID,
    schema_version: int = schema.SCHEMA_VERSION,
) -> results.Result:
    """從已讀入的標題／欄名／資料列建立 Type Catalog。"""
    version = check_schema(schema_id, schema_version)
    if not version.ok:
        return version
    if (title or "").strip() != schema.TITLE_ROW:
        return results.failed(
            "check_schema",
            "未知 Dictionary 版本標題：%s。已停止，不猜測解析。" % (title or "(空白)"),
            details={"title": title, "expected_title": schema.TITLE_ROW},
        )
    header_error = _header_failure(headers)
    if header_error is not None:
        return header_error

    records = []
    issues = []
    warnings = []
    seen_ids = {}
    seen_layers = {}
    for row_number, values in enumerate(rows, start=3):
        mapping = _row_mapping(headers, values)
        if all(_text(mapping.get(col)) is None for col in schema.DISPLAY_COLUMNS):
            continue
        owned = {key: _text(mapping.get(schema.MACHINE_TO_DISPLAY[key])) for key in TYPE_OWNED_KEYS}
        for display in schema.COMPUTED_DISPLAY_COLUMNS:
            if _text(mapping.get(display)) is not None:
                warnings.append("第 %s 列計算欄 %s 應留白，已忽略。" % (row_number, display))

        layer_path = owned["layer_path"]
        if not layer_path:
            issues.append(("missing_layer_path", "第 %s 列缺少 layer_path。" % row_number))
            continue
        split = schema.split_type_id(owned["type_id"])
        if not split.ok:
            issues.append((split.blocking[0], "第 %s 列：%s" % (row_number, split.message)))
            continue
        type_id = split.details["type_id"]
        if type_id in seen_ids:
            issues.append(
                (
                    "duplicate_type_id",
                    "第 %s 列 type_id 與第 %s 列重複：%s" % (row_number, seen_ids[type_id], type_id),
                )
            )
            continue
        if layer_path in seen_layers:
            issues.append(
                (
                    "duplicate_layer_path",
                    "第 %s 列 layer_path 與第 %s 列重複。" % (row_number, seen_layers[layer_path]),
                )
            )
            continue
        elevation = owned["elevation_basis"]
        if elevation not in schema.ELEVATION_BASES:
            issues.append(
                (
                    "invalid_elevation_basis",
                    "第 %s 列高程基準不合法：%s" % (row_number, elevation or "(空白)"),
                )
            )
            continue
        measure = schema.classify_measurement(owned["estimation_unit"], owned["measurement_rule"])
        if measure == "block":
            issues.append(
                (
                    "measurement_mismatch",
                    "第 %s 列單位／計量規則量綱不符或未知：%s／%s"
                    % (row_number, owned["estimation_unit"] or "(空白)", owned["measurement_rule"] or "(空白)"),
                )
            )
            continue
        if measure == "warn_no_quantity":
            warnings.append("第 %s 列計量規則未定義，quantity 將為空。" % row_number)
        if not owned["type_display_name"]:
            issues.append(("missing_type_display_name", "第 %s 列缺少 type_display_name。" % row_number))
            continue
        seen_ids[type_id] = row_number
        seen_layers[layer_path] = row_number
        records.append(
            TypeRecord(
                layer_path=layer_path,
                type_id=type_id,
                type_category=split.details["type_category"],
                type_sequence=split.details["type_sequence"],
                type_display_name=owned["type_display_name"],
                construction_default=owned["construction_default"],
                estimation_unit=owned["estimation_unit"],
                measurement_rule=owned["measurement_rule"],
                elevation_basis=elevation,
                remarks_default=owned["remarks_default"],
            )
        )

    if issues:
        codes = tuple(dict.fromkeys(code for code, _ in issues))
        return results.blocked(
            "validate_dictionary",
            "Dictionary 驗證失敗 %s 項，已停止。" % len(issues),
            blocking=codes,
            details={"issues": tuple(message for _, message in issues)},
        )
    catalog = TypeCatalog(
        schema_id=schema.SCHEMA_ID,
        schema_version=schema.SCHEMA_VERSION,
        title=schema.TITLE_ROW,
        types=tuple(records),
    )
    payload = {
        "catalog": catalog,
        "type_count": len(catalog.types),
    }
    if warnings:
        return results.ok_with_warnings(
            "load_dictionary",
            "已載入 Dictionary，%s 筆 Type，%s 則警告。" % (len(catalog.types), len(warnings)),
            tuple(warnings),
            details=payload,
        )
    return results.ok(
        "load_dictionary",
        "已載入 Dictionary，%s 筆 Type。" % len(catalog.types),
        details=payload,
    )


def load_from_path(path: Path) -> results.Result:
    """從 xlsx 路徑載入並驗證。"""
    table = excel.read_table(path)
    if not table.ok:
        return table
    return load_from_table(
        title=table.details["title"],
        headers=table.details["headers"],
        rows=table.details["rows"],
    )


def load_from_workfiles(environ: Optional[Mapping[str, str]] = None) -> results.Result:
    """經 LOOPFLOW_WORKFILES_ROOT 解析 Dictionary 路徑後載入。不建立檔案。"""
    workfiles = resolve_workfiles(environ=environ)
    if not workfiles.ok:
        return workfiles
    dictionary = workfiles.details["paths"].dictionary
    if not dictionary.exists() or not dictionary.is_file():
        return results.failed(
            "resolve_dictionary",
            "找不到 Dictionary 檔案 %s。不建立檔案。" % dictionary.name,
            details={"filename": dictionary.name},
        )
    return load_from_path(dictionary)
