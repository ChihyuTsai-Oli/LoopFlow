# -*- coding: utf-8 -*-
"""D08 開發輔助：全檔圖塊把舊顯示欄抄到 lf_* 後刪掉舊 key。

不是產品指令。已有的 lf_* 不覆蓋。鎖定欄若寫 x／X 會抄到 lf_lock_state
後刪舊名字；提示文字只刪不抄。責任見 `wip/docs/D08_Tag圖塊欄位.md`。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from loopflow.features.sheet.keys import (
    DRAWING_NAME_KEY,
    DRAWING_NO_KEY,
    SCALE_KEY,
    SHEET_ID_KEY,
)
from loopflow.features.tagger.keys import (
    LOCK_LEGACY_KEY,
    LOCK_STATE_KEY,
    is_legacy_lock_x,
)
from loopflow.features.tagger.templates import DEFAULT_PATH
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

STAGE = "d08_migrate_display_keys"
COMMAND_ID = "LF_D08_Migrate_Display_Keys"
FRAME_LEGACY_KEYS = frozenset(("DWG_NO", "DWG_NAME", "03-A3 Scale"))
FRAME_CANONICAL_KEYS = frozenset(
    (DRAWING_NO_KEY, DRAWING_NAME_KEY, SCALE_KEY, SHEET_ID_KEY)
)
# 1.x 圖框常順便寫 Index 欄；圖框不該有這些，只刪不抄到 lf_sheet_code。
FRAME_STRAY_KEYS = ("Category", "REF_ID", "Detail_NO")
Confirm = Callable[[Sequence[str]], bool]


def _text(value) -> Optional[str]:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def load_template_migrations(
    path: Optional[Path] = None,
) -> Tuple[Dict[str, Tuple[Tuple[str, str], ...]], frozenset]:
    """回傳 (block 名小寫 → 舊→新 key, 允許鎖定的 block 名小寫)。"""
    source = path or DEFAULT_PATH
    payload = json.loads(source.read_text(encoding="utf-8"))
    lock = str(payload.get("lock_legacy_key") or LOCK_LEGACY_KEY)
    mapping = {}
    lock_allowed = set()
    for item in payload.get("templates") or ():
        pairs = []
        seen = set()
        for field in item.get("fields") or ():
            new_key = str(field.get("usertext") or "")
            if not new_key:
                continue
            for old in field.get("legacy") or ():
                old_key = str(old)
                if not old_key or old_key == lock or old_key in seen:
                    continue
                seen.add(old_key)
                pairs.append((old_key, new_key))
        migrations = tuple(pairs)
        names = tuple(str(name) for name in (item.get("block_names") or ()))
        if item.get("lock_allowed"):
            lock_allowed.update(name.casefold() for name in names)
        for name in names:
            mapping[name.casefold()] = migrations
    return mapping, frozenset(lock_allowed)


def _frame_migrations(all_migrations: Dict[str, Tuple[Tuple[str, str], ...]]) -> Tuple[Tuple[str, str], ...]:
    return all_migrations.get("sample_frame") or (
        ("DWG_NO", DRAWING_NO_KEY),
        ("DWG_NAME", DRAWING_NAME_KEY),
        ("03-A3 Scale", SCALE_KEY),
    )


def _keys(session: RhinoSession, object_id: str) -> Tuple[str, ...]:
    getter = getattr(session, "object_user_text_keys", None)
    if not callable(getter):
        return ()
    return tuple(str(item) for item in (getter(object_id) or ()))


def _clear_key(session: RhinoSession, object_id: str, key: str) -> None:
    session.set_object_user_text(object_id, key, "")


def _is_title_frame(block_name: str, keys: set) -> bool:
    if block_name.casefold() == "sample_frame":
        return True
    return bool(keys & FRAME_LEGACY_KEYS) or bool(keys & FRAME_CANONICAL_KEYS)


def _step(object_id, block_name, old_key, new_key, copy_value) -> dict:
    return {
        "object_id": object_id,
        "block_name": block_name,
        "old_key": old_key,
        "new_key": new_key,
        "copy_value": copy_value,
    }


def plan_object(
    session: RhinoSession,
    object_id: str,
    all_migrations: Dict[str, Tuple[Tuple[str, str], ...]],
    lock_allowed_blocks: frozenset = frozenset(),
) -> List[dict]:
    """回傳此物件要抄寫／刪除的步驟。非圖塊或沒有舊顯示欄則空。"""
    if not session.is_block_instance(object_id):
        return []
    block_name = session.block_definition_name(object_id) or ""
    keys = set(_keys(session, object_id))
    migrations = all_migrations.get(block_name.casefold())
    is_frame = _is_title_frame(block_name, keys)
    if migrations is None and is_frame:
        migrations = _frame_migrations(all_migrations)
    if migrations is None:
        return []
    steps = []
    seen = set()
    for old_key, new_key in migrations:
        if old_key == LOCK_LEGACY_KEY or old_key not in keys:
            continue
        old_value = _text(session.get_object_user_text(object_id, old_key))
        new_value = _text(session.get_object_user_text(object_id, new_key))
        copy_value = old_value if new_value is None and old_value is not None else None
        steps.append(_step(object_id, block_name, old_key, new_key, copy_value))
        seen.add(old_key)
    if is_frame:
        for stray in FRAME_STRAY_KEYS:
            if stray in keys and stray not in seen:
                steps.append(_step(object_id, block_name, stray, "", None))
    if (
        block_name.casefold() in lock_allowed_blocks
        and LOCK_LEGACY_KEY in keys
        and LOCK_LEGACY_KEY not in seen
    ):
        old_value = _text(session.get_object_user_text(object_id, LOCK_LEGACY_KEY))
        new_value = _text(session.get_object_user_text(object_id, LOCK_STATE_KEY))
        copy_value = (
            old_value if new_value is None and is_legacy_lock_x(old_value) else None
        )
        steps.append(
            _step(object_id, block_name, LOCK_LEGACY_KEY, LOCK_STATE_KEY, copy_value)
        )
    return steps


def collect_steps(session: RhinoSession) -> List[dict]:
    all_migrations, lock_allowed = load_template_migrations()
    steps = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        steps.extend(plan_object(session, object_id, all_migrations, lock_allowed))
    return steps


def apply_steps(session: RhinoSession, steps: Sequence[dict]) -> None:
    for step in steps:
        object_id = step["object_id"]
        if step.get("copy_value") is not None and step.get("new_key"):
            session.set_object_user_text(object_id, step["new_key"], step["copy_value"])
        _clear_key(session, object_id, step["old_key"])


def _preview_lines(steps: Sequence[dict]) -> List[str]:
    by_object = {}
    copied = 0
    for step in steps:
        by_object.setdefault(step["object_id"], step["block_name"])
        if step.get("copy_value") is not None:
            copied += 1
    lines = [
        "將處理 %s 個圖塊上的 %s 個舊欄。" % (len(by_object), len(steps)),
        "人工值會先抄到 lf_*（已有新欄不覆蓋），然後刪掉舊名字。",
        "圖框上的 Category／REF_ID 會刪掉，不抄到 Index 欄。",
        "鎖定欄若寫 x／X 會抄到 lf_lock_state；提示文字只刪不抄。",
        "文件 metadata 與 lf_sheet_id 不碰。",
        "",
    ]
    names = sorted(set(by_object.values()))
    show = names[:12]
    lines.append("圖塊：" + "、".join(show) + (" …" if len(names) > 12 else ""))
    if copied:
        lines.append("其中 %s 欄會把舊值抄到新名字（例如比例）。" % copied)
    lines.append("")
    lines.append("確認後才寫入。取消則什麼都不改。")
    return lines


def run_migrate_block_display_keys(
    session: Optional[RhinoSession],
    *,
    confirm: Optional[Confirm] = None,
) -> results.Result:
    if session is None:
        return results.failed(STAGE, "沒有 Rhino session。", command_id=COMMAND_ID)

    def _run(current: RhinoSession) -> results.Result:
        steps = collect_steps(current)
        if not steps:
            return results.ok(STAGE, "沒有需要清除的舊顯示欄。", command_id=COMMAND_ID)
        ask = confirm
        if ask is None:
            from loopflow.platform.rhino.prompts import ask_confirm_list

            ask = lambda lines: ask_confirm_list(lines, title="清除圖塊舊欄")
        if not ask(_preview_lines(steps)):
            return results.cancelled(STAGE, "已取消，未改 UserText。", command_id=COMMAND_ID)
        apply_steps(current, steps)
        objects = {step["object_id"] for step in steps}
        copied = sum(1 for step in steps if step.get("copy_value") is not None)
        return results.ok(
            STAGE,
            "已處理 %s 個圖塊、刪除 %s 個舊欄；其中 %s 欄已把值抄到 lf_*。"
            % (len(objects), len(steps), copied),
            command_id=COMMAND_ID,
            details={"objects": len(objects), "deleted": len(steps), "copied": copied},
        )

    return run_guarded(session, _run, command_id=COMMAND_ID)
