# -*- coding: utf-8 -*-
"""載入 Tag template manifest。Laser／Index 共用此查找，不在此實作那些指令。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from loopflow.foundation import results
from loopflow.foundation.version import check_schema

SCHEMA_ID = "loopflow.tag_template_set"
DEFAULT_PATH = (
    Path(__file__).resolve().parents[4] / "fixtures" / "schema" / "tag_templates.json"
)


@dataclass(frozen=True)
class TagTemplate:
    template_id: str
    family: str
    role: str
    block_names: Tuple[str, ...]
    binding_modes: Tuple[str, ...]
    lock_allowed: bool
    source_block_name_pattern: Optional[str] = None


@dataclass(frozen=True)
class TagTemplateSet:
    schema_id: str
    schema_version: int
    templates: Tuple[TagTemplate, ...]

    def by_block_name(self, block_name: str) -> Optional[TagTemplate]:
        name = (block_name or "").strip()
        if not name:
            return None
        for template in self.templates:
            if name in template.block_names:
                return template
        return None


def load_tag_templates(path: Optional[Path] = None) -> results.Result:
    """讀 fixtures 的 10 份 manifest。未知版本停止。"""
    source = path or DEFAULT_PATH
    if not source.is_file():
        return results.failed(
            "check_schema",
            "找不到 Tag template manifest：%s" % source.name,
            details={"path": str(source)},
        )
    payload = json.loads(source.read_text(encoding="utf-8"))
    schema_id = payload.get("schema_id")
    schema_version = payload.get("schema_version")
    checked = check_schema(str(schema_id or ""), int(schema_version or 0))
    if not checked.ok:
        return checked
    if schema_id != SCHEMA_ID:
        return results.failed(
            "check_schema",
            "未知 schema_id：%s。應為 %s。已停止，不猜測解析。" % (schema_id, SCHEMA_ID),
            details={"schema_id": schema_id},
        )
    templates = []
    for item in payload.get("templates") or ():
        templates.append(
            TagTemplate(
                template_id=str(item["template_id"]),
                family=str(item.get("family") or ""),
                role=str(item.get("role") or ""),
                block_names=tuple(item.get("block_names") or ()),
                binding_modes=tuple(item.get("binding_modes") or ()),
                lock_allowed=bool(item.get("lock_allowed")),
                source_block_name_pattern=item.get("source_block_name_pattern"),
            )
        )
    catalog = TagTemplateSet(
        schema_id=SCHEMA_ID,
        schema_version=int(schema_version),
        templates=tuple(templates),
    )
    return results.ok(
        "check_schema",
        "已載入 %s 份 Tag template。" % len(catalog.templates),
        details={"catalog": catalog, "count": len(catalog.templates)},
    )
