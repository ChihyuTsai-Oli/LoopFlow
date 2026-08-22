# -*- coding: utf-8 -*-
"""Tag 健康外觀：過期橘色「!」、斷連紅色「?」。塗色須在 run_guarded 之後。"""
from __future__ import annotations

from typing import Optional, Sequence, Tuple

from loopflow.features.tagger.keys import HEALTH_STATE_KEY, HEALTH_STATE_BROKEN, HEALTH_STATE_STALE
from loopflow.platform.rhino.state import ObjectViewState

STALE_MARK = "!"
BROKEN_MARK = "?"
COLOR_STALE_RGB = (0xEA, 0x93, 0x28)
COLOR_BROKEN_RGB = (0xD8, 0x1C, 0x1C)
MODE_STALE = "stale"
MODE_BROKEN = "broken"
MODE_CLEAR = "clear"
AppearanceJob = Tuple[str, Tuple[str, ...], str]


def is_broken(session, tag_id: str) -> bool:
    raw = session.get_object_user_text(tag_id, HEALTH_STATE_KEY)
    return str(raw or "").strip().casefold() == HEALTH_STATE_BROKEN


def clear_health_state(session, tag_id: str) -> None:
    session.set_object_user_text(tag_id, HEALTH_STATE_KEY, "")


def paint_object(session, object_id: str, rgb=None, *, by_layer: bool) -> None:
    state = session.get_view_state(object_id)
    if state is None:
        return
    session.set_view_state(
        ObjectViewState(
            object_id=state.object_id,
            selected=state.selected,
            locked=state.locked,
            hidden=state.hidden,
            color=tuple(rgb) if rgb is not None else state.color,
            color_by_layer=by_layer,
        )
    )


def apply_tag_health(
    session,
    tag_id: str,
    keys: Sequence[str],
    mode: str,
) -> None:
    """寫顯示欄與 lf_health_state，並塗物件色。"""
    if mode == MODE_STALE:
        for key in keys:
            session.set_object_user_text(tag_id, key, STALE_MARK)
        session.set_object_user_text(tag_id, HEALTH_STATE_KEY, HEALTH_STATE_STALE)
        paint_object(session, tag_id, COLOR_STALE_RGB, by_layer=False)
        return
    if mode == MODE_BROKEN:
        for key in keys:
            session.set_object_user_text(tag_id, key, BROKEN_MARK)
        session.set_object_user_text(tag_id, HEALTH_STATE_KEY, HEALTH_STATE_BROKEN)
        paint_object(session, tag_id, COLOR_BROKEN_RGB, by_layer=False)
        return
    clear_health_state(session, tag_id)
    paint_object(session, tag_id, by_layer=True)


def queue_appearance(
    cache: dict,
    tag_id: str,
    keys: Sequence[str],
    mode: str,
) -> None:
    jobs = cache.setdefault("appearances", [])
    jobs.append((str(tag_id), tuple(keys), mode))


def apply_queued_appearances(session, jobs: Optional[Sequence[AppearanceJob]]) -> None:
    for tag_id, keys, mode in jobs or ():
        apply_tag_health(session, tag_id, keys, mode)
