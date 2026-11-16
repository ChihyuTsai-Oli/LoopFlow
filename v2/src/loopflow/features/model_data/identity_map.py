# -*- coding: utf-8 -*-
"""已發布的 Rhino 物件 GUID 與 LoopFlow UUID 對照。"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from loopflow.features.dictionary.layer_paths import project_id_from_session
from loopflow.foundation.atomic_io import read_json
from loopflow.foundation.paths import resolve_registry_for_document

KEY = "identity_map_v1"


class IdentityMapError(ValueError):
    pass


def validate_map(value) -> dict:
    from loopflow.features.model_data.identity import UUID_V4_RE

    if not isinstance(value, dict) or value.get("version") != 1:
        raise IdentityMapError("已發布的物件身分對照版本無效。")
    pairs = value.get("pairs")
    used = value.get("used_uuids")
    if not isinstance(pairs, dict) or not isinstance(used, list):
        raise IdentityMapError("已發布的物件身分對照格式無效。")
    if any(not isinstance(a, str) or not a.strip() or not isinstance(b, str) or not UUID_V4_RE.fullmatch(b)
           for a, b in pairs.items()):
        raise IdentityMapError("已發布的物件身分對照含無效 GUID 或 UUID。")
    if len(set(pairs.values())) != len(pairs):
        raise IdentityMapError("已發布的物件身分對照含重複 UUID。")
    if any(not isinstance(b, str) or not UUID_V4_RE.fullmatch(b) for b in used) or len(set(used)) != len(used):
        raise IdentityMapError("已發布的物件身分對照含無效歷史 UUID。")
    if not set(pairs.values()).issubset(set(used)):
        raise IdentityMapError("已發布的物件身分對照與歷史 UUID 不一致。")
    return {"version": 1, "pairs": dict(pairs), "used_uuids": list(used)}


def load_identity_map(session) -> Optional[dict]:
    """沒有正式 Registry 時回傳 None；正式檔損壞或缺對照時停止。"""
    project_id = project_id_from_session(session)
    document_path = session.document_path() if hasattr(session, "document_path") else None
    if not document_path or not project_id:
        return None
    resolved = resolve_registry_for_document(document_path, project_id)
    if not resolved.ok:
        raise IdentityMapError(resolved.message)
    official = Path(resolved.details["registry"])
    if not official.is_file():
        return None
    loaded = read_json(official)
    if not loaded.ok:
        raise IdentityMapError("無法讀取正式 Registry：%s" % loaded.message)
    payload = loaded.details.get("payload")
    if not isinstance(payload, dict) or payload.get("project_id") != project_id:
        raise IdentityMapError("正式 Registry 的專案身分不符。")
    extension = payload.get("extension")
    if extension is None:
        return None
    if not isinstance(extension, dict):
        raise IdentityMapError("正式 Registry 的 extension 格式無效。")
    if KEY not in extension:
        return None
    mapping = validate_map(extension[KEY])
    object_ids = {item.get("object_id") for item in payload.get("objects", ()) if isinstance(item, dict)}
    if set(mapping["pairs"].values()) != object_ids:
        raise IdentityMapError("正式 Registry 物件與身分對照不一致。")
    return mapping


def snapshot_identity_map(session, previous: Optional[dict], targets) -> dict:
    from loopflow.features.model_data.identity import UUID_V4_RE
    from loopflow.foundation.usertext import OBJECT_ID_KEY, read_text

    pairs: Dict[str, str] = {}
    for rhino_id in targets:
        b = read_text(session, rhino_id, OBJECT_ID_KEY)
        if not b or not UUID_V4_RE.fullmatch(b):
            raise IdentityMapError("模型物件缺少有效的 LoopFlow UUID。")
        pairs[str(rhino_id)] = b
    if len(set(pairs.values())) != len(pairs):
        raise IdentityMapError("模型物件的 LoopFlow UUID 重複。")
    prior = previous["pairs"] if previous else {}
    for a, b in prior.items():
        if a in pairs and pairs[a] != b:
            raise IdentityMapError("物件 %s 的 LoopFlow UUID 與已發布身分不符。" % a)
    used = set(previous["used_uuids"] if previous else ())
    for a, b in pairs.items():
        if a not in prior and b in used:
            raise IdentityMapError("新物件沿用了已發布或已退役的 UUID。")
    return validate_map({"version": 1, "pairs": pairs, "used_uuids": sorted(used | set(pairs.values()))})
