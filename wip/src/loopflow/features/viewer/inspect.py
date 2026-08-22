# -*- coding: utf-8 -*-
"""組只讀 canonical 報告。不寫 UserText、不改選取以外的文件狀態。"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Optional, Tuple

from loopflow.features.dictionary.loader import TypeCatalog
from loopflow.foundation import results
from loopflow.foundation.usertext import (
    CONSTRUCTION_KEY,
    DATA_REVISION_KEY,
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ELEVATION_VALUE_KEY,
    LEVEL_DATUM_KEY,
    LEVEL_ID_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    SPACE_DISPLAY_KEY,
    SPACE_FRAME_DISPLAY_KEY,
    SPACE_ID_KEY,
    STALE_OBJECT_KEYS,
    TYPE_CATEGORY_KEY,
    TYPE_ID_KEY,
    TYPE_SEQUENCE_KEY,
    legacy_keys,
)
from loopflow.foundation.project_config import (
    PROJECT_ID_FIELD,
    PROJECT_SCHEMA_ID,
    SCHEMA_ID_FIELD,
    SCHEMA_VERSION_FIELD,
    ensure_schema,
    read_config,
)
from loopflow.foundation.version import check_schema
from loopflow.platform.rhino.session import RhinoSession
from loopflow.foundation.i18n import t

COMMAND_ID = "LF_Data_Viewer"


def missing_mark() -> str:
    return t("data_viewer.004")


LEVEL_LAYER_MARK = "Level_Boundaries"
SPACE_LAYER_MARK = "Space_Boundaries"

CANONICAL_KEYS = (
    SPACE_DISPLAY_KEY,
    SPACE_FRAME_DISPLAY_KEY,
    CONSTRUCTION_KEY,
    TYPE_ID_KEY,
    ELEVATION_BASIS_KEY,
    ELEVATION_VALUE_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    SPACE_ID_KEY,
    LEVEL_ID_KEY,
    TYPE_CATEGORY_KEY,
    TYPE_SEQUENCE_KEY,
    ELEVATION_DISPLAY_KEY,
    DATA_REVISION_KEY,
    LEVEL_DATUM_KEY,
)


@dataclass(frozen=True)
class FieldView:
    key: str
    value: Optional[str]
    source: str
    source_key: Optional[str]
    notes: Tuple[str, ...] = ()

    @property
    def missing(self) -> bool:
        return self.source == "missing"


@dataclass(frozen=True)
class ObjectReport:
    object_id: str
    layer: Optional[str]
    name: Optional[str]
    block_name: Optional[str]
    project_id: Optional[str]
    schema_id: Optional[str]
    schema_version: Optional[str]
    fields: Tuple[FieldView, ...]
    stale: Tuple[str, ...]
    notes: Tuple[str, ...]
    type_display_name: Optional[str] = None

    @property
    def missing_keys(self) -> Tuple[str, ...]:
        return tuple(field.key for field in self.fields if field.missing)


def _text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def _pad_key(key: str, width: int) -> str:
    return key + (" " * max(0, width - _display_width(key)))


def ensure_project_schema(session: RhinoSession) -> None:
    """缺 schema 時順便寫入專案設定檔的 loopflow.project／1。"""
    ensure_schema(session)


def check_document_schema(session: RhinoSession) -> results.Result:
    """專案 schema 未知或不完整時停止；兩者都缺則警告後仍可查看。"""
    loaded = read_config(session)
    if not loaded.ok:
        return loaded
    values = loaded.details["values"]
    schema_id = _text(values.get(SCHEMA_ID_FIELD))
    version_text = _text(values.get(SCHEMA_VERSION_FIELD))
    if schema_id is None and version_text is None:
        return results.ok_with_warnings(
            "check_schema",
            t("data_viewer.005"),
            ("missing_document_schema",),
            command_id=COMMAND_ID,
            details={"schema_id": None, "schema_version": None},
        )
    if schema_id is None or version_text is None:
        return results.failed(
            "check_schema",
            t("data_viewer.010")
            % (schema_id or missing_mark(), version_text or missing_mark()),
            command_id=COMMAND_ID,
            details={"schema_id": schema_id, "schema_version": version_text},
        )
    try:
        version = int(version_text)
    except (TypeError, ValueError):
        return results.failed(
            "check_schema",
            t("data_viewer.018")
            % (schema_id, version_text),
            command_id=COMMAND_ID,
            details={"schema_id": schema_id, "schema_version": version_text},
        )
    checked = check_schema(schema_id, version)
    if not checked.ok:
        return results.failed(
            checked.stage,
            checked.message,
            command_id=COMMAND_ID,
            details=checked.details,
        )
    if schema_id != PROJECT_SCHEMA_ID:
        return results.failed(
            "check_schema",
            t("data_viewer.011")
            % (schema_id, PROJECT_SCHEMA_ID),
            command_id=COMMAND_ID,
            details={"schema_id": schema_id, "schema_version": version},
        )
    return results.ok(
        "check_schema",
        "%s schema_version %s" % (schema_id, version),
        command_id=COMMAND_ID,
        details={"schema_id": schema_id, "schema_version": version},
    )


def _resolve_field(session: RhinoSession, object_id: str, key: str, layer: Optional[str]) -> FieldView:
    current = _text(session.get_object_user_text(object_id, key))
    if current is not None:
        return FieldView(key, current, "canonical", key)
    for legacy in legacy_keys(key):
        value = _text(session.get_object_user_text(object_id, legacy))
        if value is not None:
            return FieldView(
                key,
                value,
                "legacy",
                legacy,
                (t("data_viewer.022") % legacy,),
            )
    if key == LEVEL_DATUM_KEY and LEVEL_LAYER_MARK in (layer or ""):
        name = _text(session.object_name(object_id))
        if name is not None:
            return FieldView(
                key,
                name,
                "object_name",
                "ObjectName",
                (t("data_viewer.019"),),
            )
    return FieldView(key, None, "missing", None)


def _override_notes(field: FieldView, catalog: Optional[TypeCatalog], type_id: Optional[str]) -> Tuple[str, ...]:
    if catalog is None or not type_id or field.missing or field.value is None:
        return ()
    record = catalog.by_type_id(type_id)
    if record is None:
        return ()
    if field.key == CONSTRUCTION_KEY:
        default = _text(record.construction_default)
        if default and field.value != default:
            return (t("data_viewer.020") % default,)
    if field.key == REMARKS_KEY:
        default = _text(record.remarks_default)
        if default and field.value != default:
            return (t("data_viewer.020") % default,)
    return ()


def _should_show(field: FieldView, layer: Optional[str]) -> bool:
    if field.key == SPACE_FRAME_DISPLAY_KEY:
        return SPACE_LAYER_MARK in (layer or "")
    if field.key == SPACE_DISPLAY_KEY:
        return SPACE_LAYER_MARK not in (layer or "")
    if field.key != LEVEL_DATUM_KEY:
        return True
    if not field.missing:
        return True
    return LEVEL_LAYER_MARK in (layer or "")


def inspect_object(
    session: RhinoSession,
    object_id: str,
    *,
    catalog: Optional[TypeCatalog] = None,
) -> ObjectReport:
    layer = _text(session.object_layer(object_id))
    name = _text(session.object_name(object_id))
    block_name = None
    getter = getattr(session, "block_definition_name", None)
    if callable(getter):
        block_name = _text(getter(object_id))
    elif session.is_block_instance(object_id):
        block_name = name

    loaded = read_config(session)
    config = loaded.details["values"] if loaded.ok else {}
    raw_fields = tuple(_resolve_field(session, object_id, key, layer) for key in CANONICAL_KEYS)
    type_id = next((field.value for field in raw_fields if field.key == TYPE_ID_KEY and not field.missing), None)
    notes = []
    type_display_name = None
    if catalog is not None and type_id:
        record = catalog.by_type_id(type_id)
        if record is None:
            notes.append(t("data_viewer.021") % type_id)
        else:
            type_display_name = record.type_display_name
    fields = []
    for field in raw_fields:
        if not _should_show(field, layer):
            continue
        extra = _override_notes(field, catalog, type_id)
        if extra:
            field = FieldView(
                field.key,
                field.value,
                field.source,
                field.source_key,
                field.notes + extra,
            )
        fields.append(field)

    stale = tuple(
        key
        for key in STALE_OBJECT_KEYS
        if _text(session.get_object_user_text(object_id, key)) is not None
    )
    has_any = any(not field.missing for field in fields) or bool(stale)
    if not has_any:
        notes.append(t("data_viewer.006"))

    return ObjectReport(
        object_id=str(object_id),
        layer=layer,
        name=name,
        block_name=block_name,
        project_id=_text(config.get(PROJECT_ID_FIELD)),
        schema_id=_text(config.get(SCHEMA_ID_FIELD)),
        schema_version=_text(config.get(SCHEMA_VERSION_FIELD)),
        fields=tuple(fields),
        stale=stale,
        notes=tuple(notes),
        type_display_name=type_display_name,
    )


def format_report(report: ObjectReport) -> str:
    lines = [
        t("data_viewer.007") % (report.layer or missing_mark()),
        t("data_viewer.008") % (report.name or t("grab.019")),
    ]
    if report.block_name:
        lines.append(t("data_viewer.012") % report.block_name)
    lines.append(t("data_viewer.009") % (report.project_id or missing_mark()))
    if report.schema_id or report.schema_version:
        lines.append(
            t("data_viewer.013")
            % (report.schema_id or missing_mark(), report.schema_version or missing_mark())
        )
    else:
        lines.append(t("data_viewer.014") % missing_mark())
    if report.type_display_name:
        lines.append(t("data_viewer.015") % report.type_display_name)
    lines.append("-" * 48)

    visible = report.fields
    labels = [field.key for field in visible]
    key_width = max([_display_width(label) for label in labels] + [12])
    for field, label in zip(visible, labels):
        value = field.value if field.value is not None else missing_mark()
        suffix = ("  " + "；".join(field.notes)) if field.notes else ""
        lines.append("  %s : %s%s" % (_pad_key(label, key_width), value, suffix))

    if report.missing_keys:
        lines.append("")
        lines.append(t("data_viewer.016") % "、".join(report.missing_keys))
    if report.stale:
        lines.append("")
        lines.append(t("data_viewer.017") % "、".join(report.stale))
    for note in report.notes:
        lines.append("")
        lines.append(note)
    return "\n".join(lines)
