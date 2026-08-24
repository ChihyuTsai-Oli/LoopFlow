# -*- coding: utf-8 -*-
"""驗證 Registry payload。未知核心欄、缺 EXT、尺寸欄皆阻擋。"""
from __future__ import annotations

import re
from typing import Mapping, Sequence

from loopflow.features.registry import schema
from loopflow.foundation import results
from loopflow.foundation.paths import normalize_project_id
from loopflow.foundation.version import check_schema
from loopflow.foundation.i18n import t

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
        return _blocked("invalid_%s" % label, t("registry.036") % (label, index))
    extra = tuple(key for key in item if key not in required)
    missing = tuple(key for key in required if key not in item)
    if extra:
        return _blocked(
            "unknown_%s_field" % label,
            t("registry.037") % (label, index, ", ".join(extra)),
            details={"extra": extra},
        )
    if missing:
        return _blocked(
            "missing_%s_field" % label,
            t("registry.038") % (label, index, ", ".join(missing)),
            details={"missing": missing},
        )
    return None


def validate_payload(payload) -> results.Result:
    """檢查 canonical 根欄、陣列形狀、EXT 與 objects 不得帶尺寸。"""
    if not isinstance(payload, dict):
        return _blocked("invalid_payload", t("registry.013"))
    extra = tuple(key for key in payload if key not in schema.REQUIRED_ROOT)
    if extra:
        return _blocked(
            "unknown_core_field",
            t("registry.039") % ", ".join(extra),
            details={"extra": extra},
        )
    missing = tuple(key for key in schema.REQUIRED_ROOT if key not in payload)
    if missing:
        return _blocked(
            "missing_root_field",
            t("registry.040") % ", ".join(missing),
            details={"missing": missing},
        )
    schema_id = payload.get("schema_id")
    schema_version = payload.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        return _blocked("unknown_schema_version", t("registry.026"))
    checked = check_schema(str(schema_id or ""), schema_version)
    if not checked.ok:
        reason = "unknown_schema_id" if "schema_id" in checked.message else "unknown_schema_version"
        return _blocked(reason, checked.message, details=checked.details)

    project_id = str(payload.get("project_id") or "").strip()
    if not normalize_project_id(project_id):
        return _blocked(
            "invalid_project_id",
            t("registry.027"),
        )
    revision = payload.get("registry_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        return _blocked("invalid_revision", t("registry.028"))
    if not str(payload.get("published_at") or "").strip():
        return _blocked("missing_published_at", t("registry.029"))
    if not str(payload.get("model_unit") or "").strip():
        return _blocked("missing_model_unit", t("registry.030"))
    if not isinstance(payload.get("extension"), dict):
        return _blocked("invalid_extension", t("registry.031"))

    types = payload.get("types")
    spaces = payload.get("spaces")
    objects = payload.get("objects")
    if not isinstance(types, list):
        return _blocked("invalid_types", t("registry.032"))
    if not isinstance(spaces, list):
        return _blocked("invalid_spaces", t("registry.033"))
    if not isinstance(objects, list):
        return _blocked("invalid_objects", t("registry.034"))

    type_ids = []
    for index, item in enumerate(types):
        bad = _item_keys(item, schema.TYPE_KEYS, label="types", index=index)
        if bad:
            return bad
        type_id = str(item.get("type_id") or "").strip()
        if not type_id:
            return _blocked("missing_type_id", t("registry.041") % index)
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
                return _blocked("invalid_ext_space", t("registry.042"))
            if str(item.get("space_display") or "") != schema.RESERVED_SPACE_ID:
                return _blocked("invalid_ext_space", t("registry.043"))
        elif not UUID_V4_RE.match(str(space_id or "")):
            return _blocked("invalid_space_id", t("registry.049") % index)
    if not has_ext:
        return _blocked("missing_ext_space", t("registry.035"))

    for index, item in enumerate(objects):
        if not isinstance(item, dict):
            return _blocked("invalid_objects", t("registry.044") % index)
        forbidden = tuple(key for key in schema.FORBIDDEN_OBJECT_KEYS if key in item)
        if forbidden:
            return _blocked(
                "forbidden_object_field",
                t("registry.045") % (index, ", ".join(forbidden)),
                details={"forbidden": forbidden},
            )
        bad = _item_keys(item, schema.OBJECT_KEYS, label="objects", index=index)
        if bad:
            return bad
        object_id = str(item.get("object_id") or "")
        if not UUID_V4_RE.match(object_id):
            return _blocked("invalid_object_id", t("registry.046") % index)
        type_id = str(item.get("type_id") or "").strip()
        if type_id not in type_id_set:
            return _blocked(
                "unknown_type_id",
                t("registry.047") % index,
            )
        space_id = item.get("space_id")
        if space_id != schema.RESERVED_SPACE_ID and not UUID_V4_RE.match(str(space_id or "")):
            return _blocked("invalid_space_id", t("registry.048") % index)

    return results.ok(
        "validate_registry",
        t("registry.025"),
        command_id=COMMAND_ID,
        details={
            "project_id": project_id,
            "registry_revision": revision,
            "type_count": len(types),
            "space_count": len(spaces),
            "object_count": len(objects),
        },
    )
