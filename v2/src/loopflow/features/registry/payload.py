# -*- coding: utf-8 -*-
"""從 Rhino 現況組 Registry payload。不寫檔、不快照全部 UserText。"""
from __future__ import annotations

from loopflow.features.dictionary.loader import TypeCatalog
from loopflow.features.model_data.identity import iter_scan_targets
from loopflow.features.model_data.placement import collect_spaces
from loopflow.features.registry import schema
from loopflow.foundation.usertext import (
    CONSTRUCTION_KEY,
    DATA_REVISION_KEY,
    ELEVATION_BASIS_KEY,
    ELEVATION_DISPLAY_KEY,
    ELEVATION_VALUE_KEY,
    LEVEL_ID_KEY,
    OBJECT_ID_KEY,
    REMARKS_KEY,
    SPACE_DISPLAY_KEY,
    SPACE_ID_KEY,
    TYPE_CATEGORY_KEY,
    TYPE_ID_KEY,
    TYPE_SEQUENCE_KEY,
    read_text,
)
from loopflow.platform.rhino.session import RhinoSession


def _empty_to_none(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _as_number(value):
    text = _empty_to_none(value)
    if text is None:
        return None
    try:
        number = float(text)
    except ValueError:
        return text
    if number.is_integer():
        return int(number)
    return number


def assemble_payload(
    session: RhinoSession,
    catalog: TypeCatalog,
    *,
    project_id: str,
    model_unit: str,
) -> dict:
    """組 types／spaces／objects。不含 Tag 或任意 UserText。"""
    types = []
    for record in catalog.types:
        types.append(
            {
                "type_id": record.type_id,
                "type_category": record.type_category,
                "type_sequence": record.type_sequence,
                "type_display_name": record.type_display_name,
                "layer_path": record.layer_path,
                "estimation_unit": record.estimation_unit,
                "measurement_rule": record.measurement_rule,
                "elevation_basis": record.elevation_basis,
                "construction_default": record.construction_default,
                "remarks_default": record.remarks_default,
            }
        )
    spaces = [
        {
            "space_id": schema.RESERVED_SPACE_ID,
            "level_id": None,
            "space_display": schema.RESERVED_SPACE_ID,
        }
    ]
    _status, found = collect_spaces(session)
    seen = {schema.RESERVED_SPACE_ID}
    for item in found:
        space_id = item["space_id"]
        if space_id in seen:
            continue
        seen.add(space_id)
        spaces.append(
            {
                "space_id": space_id,
                "level_id": _empty_to_none(read_text(session, item["object_id"], LEVEL_ID_KEY)),
                "space_display": item["space_display"],
            }
        )
    objects = []
    for rhino_id in iter_scan_targets(session, selected_only=False):
        type_id = _empty_to_none(read_text(session, rhino_id, TYPE_ID_KEY))
        record = catalog.by_type_id(type_id) if type_id else None
        objects.append(
            {
                "object_id": read_text(session, rhino_id, OBJECT_ID_KEY),
                "type_id": type_id,
                "type_category": _empty_to_none(read_text(session, rhino_id, TYPE_CATEGORY_KEY))
                or (record.type_category if record else None),
                "type_sequence": _empty_to_none(read_text(session, rhino_id, TYPE_SEQUENCE_KEY))
                or (record.type_sequence if record else None),
                "type_display_name": record.type_display_name if record else None,
                "construction_status": _empty_to_none(read_text(session, rhino_id, CONSTRUCTION_KEY)),
                "space_id": _empty_to_none(read_text(session, rhino_id, SPACE_ID_KEY)) or schema.RESERVED_SPACE_ID,
                "space_display": _empty_to_none(read_text(session, rhino_id, SPACE_DISPLAY_KEY))
                or schema.RESERVED_SPACE_ID,
                "elevation_basis": _empty_to_none(read_text(session, rhino_id, ELEVATION_BASIS_KEY)),
                "elevation_value": _as_number(read_text(session, rhino_id, ELEVATION_VALUE_KEY)),
                "elevation_display": _empty_to_none(read_text(session, rhino_id, ELEVATION_DISPLAY_KEY)),
                "remarks": _empty_to_none(read_text(session, rhino_id, REMARKS_KEY)),
                "data_revision": _as_number(read_text(session, rhino_id, DATA_REVISION_KEY)),
            }
        )
    return {
        "schema_id": schema.SCHEMA_ID,
        "schema_version": schema.SCHEMA_VERSION,
        "project_id": project_id,
        "model_unit": model_unit,
        "types": types,
        "spaces": spaces,
        "objects": objects,
        "extension": {},
    }
