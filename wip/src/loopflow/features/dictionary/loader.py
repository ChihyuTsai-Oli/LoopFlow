# -*- coding: utf-8 -*-
"""Dictionary Type Catalog 載入與驗證。不寫 Nexus、不計算 quantity。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary import schema
from loopflow.foundation import results
from loopflow.foundation.paths import resolve_project_folder
from loopflow.foundation.project_config import dictionary_filename_from_session
from loopflow.foundation.version import check_schema
from loopflow.platform import excel
from loopflow.foundation.i18n import t

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
            t("dictionary.001"),
            blocking=("cb_columns_forbidden",),
            details={"headers": tuple(names)},
        )
    if list(headers) != list(schema.DISPLAY_COLUMNS):
        extra = [name for name in names if name not in schema.DISPLAY_COLUMNS]
        code = "unknown_column" if extra or len(names) == len(schema.DISPLAY_COLUMNS) else "wrong_column_count"
        message = (
            t("dictionary.002")
            if code == "unknown_column"
            else t("dictionary.004") % len(names)
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
            t("dictionary.005") % (title or t("dictionary.009")),
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
                warnings.append(t("dictionary.011") % (row_number, display))

        layer_path = owned["layer_path"]
        if not layer_path:
            issues.append(("missing_layer_path", t("dictionary.012") % row_number))
            continue
        split = schema.split_type_id(owned["type_id"])
        if not split.ok:
            issues.append((split.blocking[0], t("dictionary.013") % (row_number, split.message)))
            continue
        type_id = split.details["type_id"]
        if type_id in seen_ids:
            issues.append(
                (
                    "duplicate_type_id",
                    t("dictionary.014") % (row_number, seen_ids[type_id], type_id),
                )
            )
            continue
        if layer_path in seen_layers:
            issues.append(
                (
                    "duplicate_layer_path",
                    t("dictionary.015") % (row_number, seen_layers[layer_path]),
                )
            )
            continue
        elevation = owned["elevation_basis"]
        if elevation not in schema.ELEVATION_BASES:
            issues.append(
                (
                    "invalid_elevation_basis",
                    t("dictionary.016") % (row_number, elevation or t("dictionary.009")),
                )
            )
            continue
        measure = schema.classify_measurement(owned["estimation_unit"], owned["measurement_rule"])
        if measure == "block":
            issues.append(
                (
                    "measurement_mismatch",
                    t("dictionary.017")
                    % (row_number, owned["estimation_unit"] or t("dictionary.009"), owned["measurement_rule"] or t("dictionary.009")),
                )
            )
            continue
        if measure == "warn_no_quantity":
            warnings.append(t("dictionary.010") % row_number)
        if not owned["type_display_name"]:
            issues.append(("missing_type_display_name", t("dictionary.018") % row_number))
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
            t("dictionary.006") % len(issues),
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
            t("dictionary.007") % (len(catalog.types), len(warnings)),
            tuple(warnings),
            details=payload,
        )
    return results.ok(
        "load_dictionary",
        t("dictionary.003") % len(catalog.types),
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


def load_dictionary(
    session,
    dictionary_filename: Optional[str] = None,
) -> results.Result:
    """從 .3dm 同資料夾的 Dictionary 載入。不建立檔案。"""
    filename = dictionary_filename
    if filename in (None, "") and session is not None:
        filename = dictionary_filename_from_session(session)
    resolved = resolve_project_folder(session, dictionary_filename=filename)
    if not resolved.ok:
        return resolved
    dictionary = resolved.details["paths"].dictionary
    if not dictionary.exists() or not dictionary.is_file():
        return results.failed(
            "resolve_dictionary",
            t("dictionary.008")
            % dictionary.name,
            details={"filename": dictionary.name},
        )
    loaded = load_from_path(dictionary)
    if not loaded.ok:
        return loaded
    details = dict(loaded.details or {})
    details["dictionary_filename"] = dictionary.name
    details["dictionary_path"] = dictionary
    return results.Result(
        ok=loaded.ok,
        status=loaded.status,
        stage=loaded.stage,
        message=loaded.message,
        warnings=loaded.warnings,
        blocking=loaded.blocking,
        details=details,
        command_id=loaded.command_id,
    )
