# -*- coding: utf-8 -*-
"""把選取物件隨機分到專案 M3D 的類型子圖層。僅供測試，不是產品指令。"""
from __future__ import annotations

import random
from typing import Optional, Sequence

from loopflow.features.dictionary.layer_paths import (
    DNA_REF_PREFIX,
    is_exportable_type_layer,
    is_system_layer,
    read_layer_prefix,
)
from loopflow.foundation import results
from loopflow.platform.rhino.session import run_guarded
from loopflow.platform.rhino.state import ObjectViewState

STAGE = "test_random_layers"


def type_leaf_layers(session) -> Sequence[str]:
    prefix = read_layer_prefix(session)
    paths = tuple(session.layer_paths())
    return tuple(
        path for path in paths
        if is_exportable_type_layer(path, paths, prefix)
    )


def selected_object_ids(session) -> Sequence[str]:
    ids = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        state = session.get_view_state(object_id)
        if state is not None and state.selected:
            ids.append(object_id)
    return tuple(ids)


def _skip_reason(session, object_id: str, prefix: str) -> Optional[str]:
    name = session.object_name(object_id) or ""
    if name.startswith(DNA_REF_PREFIX):
        return "dna_ref"
    layer = session.object_layer(object_id) or ""
    if is_system_layer(layer, prefix):
        return "system_layer"
    return None


def _set_layer_keeping_lock(session, object_id: str, path: str) -> None:
    state = session.get_view_state(object_id)
    if state is not None and state.locked:
        session.set_view_state(
            ObjectViewState(
                object_id=state.object_id,
                selected=state.selected,
                locked=False,
                hidden=state.hidden,
                color=state.color,
                color_by_layer=state.color_by_layer,
            )
        )
    session.set_object_layer(object_id, path)


def assign_selected_to_random_type_layers(session, rng: Optional[random.Random] = None) -> results.Result:
    prefix = read_layer_prefix(session)
    targets = type_leaf_layers(session)
    if not targets:
        return results.failed(
            STAGE,
            "沒有可用的 M3D 類型子圖層。請先用 Nexus 選單 2 同步 Type Layers。",
        )
    chosen = selected_object_ids(session)
    if not chosen:
        return results.failed(STAGE, "請先選取要分配的物件。")

    roller = rng or random.Random()
    assigned = []
    skipped = []
    for object_id in chosen:
        reason = _skip_reason(session, object_id, prefix)
        if reason:
            skipped.append(object_id)
            continue
        target = roller.choice(targets)
        _set_layer_keeping_lock(session, object_id, target)
        assigned.append((object_id, target))

    if not assigned:
        return results.failed(
            STAGE,
            "選取的物件都是系統層或 DNA_REF_，沒有分配。",
            details={"skipped": skipped, "targets": targets},
        )
    samples = "、".join(path.rsplit("::", 1)[-1] for _, path in assigned[:8])
    extra = "…" if len(assigned) > 8 else ""
    message = "已把 %s 個選取物件隨機分到 %s 個類型圖層（例如 %s%s）。" % (
        len(assigned),
        len(targets),
        samples,
        extra,
    )
    if skipped:
        message += " 略過 %s 個系統層／DNA_REF_。" % len(skipped)
    return results.ok(
        STAGE,
        message,
        details={
            "assigned": assigned,
            "skipped": skipped,
            "targets": targets,
            "prefix": prefix,
        },
    )


def run(session) -> results.Result:
    def _action(current):
        return assign_selected_to_random_type_layers(current)

    return run_guarded(session, _action)
