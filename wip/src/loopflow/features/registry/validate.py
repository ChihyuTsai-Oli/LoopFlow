# -*- coding: utf-8 -*-
"""驗證 Registry payload。未知核心欄、缺 EXT、尺寸欄皆阻擋。"""
from __future__ import annotations

import re
from typing import Mapping, Sequence

from loopflow.features.registry import schema
from loopflow.foundation import results
from loopflow.foundation.version import check_schema

UUID_V4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)
COMMAND_ID = schema.COMMAND_ID


def _blocked(reason: str, message: str, **kwargs) -> results.Result:
    return results.blocked(
        "validate_registry",
        message,
        blocking=(reason,),
        command_id=COMMAND_ID,
        **kwargs,
    )


def _item_keys(item: Mapping, required: Sequence[str], *, label: str, index: int):
    if not isinstance(item, dict):
        return _blocked("invalid_%s" % label, "%s[%s] 必須是 object。" % (label, index))
    extra = tuple(key for key in item if key not in required)
    missing = tuple(key for key in required if key not in item)
    if extra:
        return _blocked(
            "unknown_%s_field" % label,
            "%s[%s] 含未知核心欄：%s。" % (label, index, ", ".join(extra)),
            details={"extra": extra},
        )
    if missing:
        return _blocked(
            "missing_%s_field" % label,
            "%s[%s] 缺少核心欄：%s。" % (label, index, ", ".join(missing)),
            details={"missing": missing},
        )
    return None


def validate_payload(payload) -> results.Result:
    """檢查 canonical 根欄、陣列形狀、EXT 與 objects 不得帶尺寸。"""
    if not isinstance(payload, dict):
        return _blocked("invalid_payload", "Registry payload 必須是 object。")
    extra = tuple(key for key in payload if key not in schema.REQUIRED_ROOT)
    if extra:
        return _blocked(
            "unknown_core_field",
            "Registry 含未知核心欄：%s。非核心資料只放 extension。" % ", ".join(extra),
            details={"extra": extra},
        )
    missing = tuple(key for key in schema.REQUIRED_ROOT if key not in payload)
    if missing:
        return _blocked(
            "missing_root_field",
            "Registry 缺少核心欄：%s。" % ", ".join(missing),
            details={"missing": missing},
        )
    schema_id = payload.get("schema_id")
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        return _blocked("unknown_schema_version", "schema_version 必須是整數。")
    checked = check_schema(str(schema_id or ""), schema_version)
    if not checked.ok:
        reason = "unknown_schema_id" if "schema_id" in checked.message else "unknown_schema_version"
        return _blocked(reason, checked.message, details=checked.details)

    project_id = str(payload.get("project_id") or "").strip()
    if not UUID_V4_RE.match(project_id):
        return _blocked("invalid_project_id", "project_id 必須是小寫 UUID v4。")
    revision = payload.get("registry_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        return _blocked("invalid_revision", "registry_revision 必須是從 1 起的正整數。")
    if not str(payload.get("published_at") or "").strip():
        return _blocked("missing_published_at", "缺少 published_at。")
    if not str(payload.get("model_unit") or "").strip():
        return _blocked("missing_model_unit", "缺少 model_unit。")
    if not isinstance(payload.get("extension"), dict):
        return _blocked("invalid_extension", "extension 必須是 object。")

    types = payload.get("types")
    spaces = payload.get("spaces")
    objects = payload.get("objects")
    if not isinstance(types, list):
        return _blocked("invalid_types", "types 必須是陣列。")
    if not isinstance(spaces, list):
        return _blocked("invalid_spaces", "spaces 必須是陣列。")
    if not isinstance(objects, list):
        return _blocked("invalid_objects", "objects 必須是陣列。")

    type_ids = []
    for index, item in enumerate(types):
        bad = _item_keys(item, schema.TYPE_KEYS, label="types", index=index)
        if bad:
            return bad
        type_id = str(item.get("type_id") or "").strip()
        if not type_id:
            return _blocked("missing_type_id", "types[%s] 缺少 type_id。" % index)
        type_ids.append(type_id)
    type_id_set = set(type_ids)

    has_ext = False
    for index, item in enumerate(spaces):
        bad = _item_keys(item, schema.SPACE_KEYS, label="spaces", index=index)
        if bad:
            return bad
        space_id = item.get("space_id")
        if space_id == schema.RESERVED_SPACE_ID:
            has_ext = True
            if item.get("level_id") not in (None, ""):
                return _blocked("invalid_ext_space", "EXT 的 level_id 必須為 null。")
            if str(item.get("space_display") or "") != schema.RESERVED_SPACE_ID:
                return _blocked("invalid_ext_space", "EXT 的 space_display 必須為 EXT。")
        elif not UUID_V4_RE.match(str(space_id or "")):
            return _blocked("invalid_space_id", "spaces[%s] 的 space_id 必須是 UUID 或 EXT。" % index)
    if not has_ext:
        return _blocked("missing_ext_space", "spaces[] 必須含保留列 EXT。")

    for index, item in enumerate(objects):
        if not isinstance(item, dict):
            return _blocked("invalid_objects", "objects[%s] 必須是 object。" % index)
        forbidden = tuple(key for key in schema.FORBIDDEN_OBJECT_KEYS if key in item)
        if forbidden:
            return _blocked(
                "forbidden_object_field",
                "objects[%s] 不得含尺寸／數量欄：%s。" % (index, ", ".join(forbidden)),
                details={"forbidden": forbidden},
            )
        bad = _item_keys(item, schema.OBJECT_KEYS, label="objects", index=index)
        if bad:
            return bad
        object_id = str(item.get("object_id") or "")
        if not UUID_V4_RE.match(object_id):
            return _blocked("invalid_object_id", "objects[%s] 的 object_id 必須是小寫 UUID v4。" % index)
        type_id = str(item.get("type_id") or "").strip()
        if type_id not in type_id_set:
            return _blocked(
                "unknown_type_id",
                "objects[%s] 的 type_id 不在本 revision 的 types[]。" % index,
            )
        space_id = item.get("space_id")
        if space_id != schema.RESERVED_SPACE_ID and not UUID_V4_RE.match(str(space_id or "")):
            return _blocked("invalid_space_id", "objects[%s] 的 space_id 必須是 UUID 或 EXT。" % index)

    return results.ok(
        "validate_registry",
        "Registry payload 通過驗證",
        command_id=COMMAND_ID,
        details={
            "project_id": project_id,
            "registry_revision": revision,
            "type_count": len(types),
            "space_count": len(spaces),
            "object_count": len(objects),
        },
    )
