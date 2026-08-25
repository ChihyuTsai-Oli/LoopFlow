# -*- coding: utf-8 -*-
"""產品版號與 schema_version。

未知 schema_id 或 schema_version 必須停止，不得猜測解析。
"""
from __future__ import annotations
from loopflow.foundation.i18n import t

from typing import Mapping, Optional

from . import results

PACKAGE_VERSION = "2.0.4"

SCHEMA_VERSIONS = {
    "loopflow.project": 1,
    "loopflow.dictionary": 1,
    "loopflow.object": 1,
    "loopflow.space": 1,
    "loopflow.view": 1,
    "loopflow.drawing": 1,
    "loopflow.sheet": 1,
    "loopflow.registry": 1,
    "loopflow.tag_template": 1,
    "loopflow.tag_template_set": 1,
}


def known_schema_ids():
    return tuple(SCHEMA_VERSIONS)


def check_schema(
    schema_id: str,
    schema_version: int,
    *,
    expected: Optional[Mapping[str, int]] = None,
) -> results.Result:
    table = dict(expected or SCHEMA_VERSIONS)
    if schema_id not in table:
        return results.failed(
            "check_schema",
            t("foundation.017") % schema_id,
            details={"schema_id": schema_id, "schema_version": schema_version},
        )
    current = table[schema_id]
    if schema_version != current:
        return results.failed(
            "check_schema",
            t("foundation.018")
            % (schema_id, schema_version, current),
            details={
                "schema_id": schema_id,
                "schema_version": schema_version,
                "expected_schema_version": current,
            },
        )
    return results.ok(
        "check_schema",
        "%s schema_version %s" % (schema_id, schema_version),
        details={"schema_id": schema_id, "schema_version": schema_version},
    )
