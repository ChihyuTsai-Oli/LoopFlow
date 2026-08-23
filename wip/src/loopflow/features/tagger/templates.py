# -*- coding: utf-8 -*-
"""載入 Tag template manifest。Grab／Laser／Index 共用此查找。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

from loopflow.foundation import results
from loopflow.foundation.version import check_schema
from loopflow.foundation.i18n import t
from loopflow.foundation.templates import source_search_roots

SCHEMA_ID = "loopflow.tag_template_set"
FIXTURE_PATH = (
    Path(__file__).resolve().parents[4] / "fixtures" / "schema" / "tag_templates.json"
)


@dataclass(frozen=True)
class TagField:
    """manifest 顯示欄。Duplicate 依 `clear_on_duplicate` 清除、寫空白或保留。"""

    key: str
    usertext: str
    owner: str = ""
    clear_on_duplicate: bool = False


@dataclass(frozen=True)
class TagTemplate:
    template_id: str
    family: str
    role: str
    block_names: Tuple[str, ...]
    binding_modes: Tuple[str, ...]
    lock_allowed: bool
    source_block_name_pattern: Optional[str] = None
    default_lock_state: Optional[bool] = None
    fields: Tuple[TagField, ...] = ()


@dataclass(frozen=True)
class TagTemplateSet:
    schema_id: str
    schema_version: int
    templates: Tuple[TagTemplate, ...]

    def by_block_name(self, block_name: str) -> Optional[TagTemplate]:
        """以 Block 定義名查找。不分大小寫，以對齊現行 Tag_Blocks.3dm（Tag_Height_Grab）。"""
        name = (block_name or "").strip()
        if not name:
            return None
        folded = name.casefold()
        for template in self.templates:
            for known in template.block_names:
                if known.casefold() == folded:
                    return template
        return None


def resolve_tag_templates_path() -> Optional[Path]:
    """已裝套件讀 templates\\tag_templates.json；開發期讀 wip\\fixtures。"""
    candidates = [root / "tag_templates.json" for root in source_search_roots()]
    candidates.append(FIXTURE_PATH)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def load_tag_templates(path: Optional[Path] = None) -> results.Result:
    """讀 10 份 Tag template manifest。未知版本停止。"""
    source = path if path is not None else resolve_tag_templates_path()
    if source is None or not source.is_file():
        return results.failed(
            "check_schema",
            t("other.005") % "tag_templates.json",
            details={"path": str(source) if source is not None else ""},
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
            t("other.006") % (schema_id, SCHEMA_ID),
            details={"schema_id": schema_id},
        )
    templates = []
    for item in payload.get("templates") or ():
        lock_allowed = bool(item.get("lock_allowed"))
        raw_lock = item.get("default_lock_state")
        default_lock = bool(raw_lock) if lock_allowed and raw_lock is not None else (
            False if lock_allowed else None
        )
        fields = tuple(
            TagField(
                key=str(field.get("key") or ""),
                usertext=str(field.get("usertext") or ""),
                owner=str(field.get("owner") or ""),
                clear_on_duplicate=bool(field.get("clear_on_duplicate")),
            )
            for field in (item.get("fields") or ())
            if field.get("usertext")
        )
        templates.append(
            TagTemplate(
                template_id=str(item["template_id"]),
                family=str(item.get("family") or ""),
                role=str(item.get("role") or ""),
                block_names=tuple(item.get("block_names") or ()),
                binding_modes=tuple(item.get("binding_modes") or ()),
                lock_allowed=lock_allowed,
                source_block_name_pattern=item.get("source_block_name_pattern"),
                default_lock_state=default_lock,
                fields=fields,
            )
        )
    catalog = TagTemplateSet(
        schema_id=SCHEMA_ID,
        schema_version=int(schema_version),
        templates=tuple(templates),
    )
    return results.ok(
        "check_schema",
        t("other.004") % len(catalog.templates),
        details={"catalog": catalog, "count": len(catalog.templates)},
    )
