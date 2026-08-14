# -*- coding: utf-8 -*-
"""Rhino 8 live adapter。

模組載入不 import Rhino。實機 API 對應尚未在 Rhino 8 驗證，呼叫端必須接受這個限制。
"""
from __future__ import annotations

from typing import Optional, Tuple

from loopflow.foundation import results
from loopflow.platform.rhino.session import capture_snapshot, restore_snapshot
from loopflow.platform.rhino.state import DocumentSnapshot, ObjectViewState

LIVE_VERIFIED_IN_RHINO = False
COLOR_SOURCE_BY_LAYER = 0
COLOR_SOURCE_BY_OBJECT = 1


def _load_rhino() -> Tuple[Optional[tuple], Optional[str]]:
    try:
        import Rhino  # type: ignore
        import rhinoscriptsyntax as rs  # type: ignore
        import scriptcontext as sc  # type: ignore
    except ImportError as exc:
        return None, "目前不在 Rhino 內：%s" % exc
    return (Rhino, rs, sc), None


def open_session() -> results.Result:
    loaded, error = _load_rhino()
    if loaded is None:
        return results.failed("rhino_session", error or "無法載入 Rhino")
    _Rhino, rs, sc = loaded
    if sc.doc is None:
        return results.failed("rhino_session", "沒有作用中的 Rhino 文件")
    session = LiveSession(rs, sc)
    return results.ok(
        "rhino_session",
        "已連接 Rhino 文件。live adapter 尚未實機驗證。",
        warnings=("live_adapter_unverified",),
        details={"session": session, "verified": LIVE_VERIFIED_IN_RHINO},
    )


class LiveSession:
    def __init__(self, rs, sc) -> None:
        self._rs = rs
        self._sc = sc

    def iter_object_ids(self, *, include_hidden: bool = True, include_locked: bool = True):
        ids = []
        seen = set()
        groups = [self._rs.AllObjects() or []]
        if include_hidden:
            groups.append(self._rs.HiddenObjects() or [])
        if include_locked:
            groups.append(self._rs.LockedObjects() or [])
        for group in groups:
            for object_id in group:
                key = str(object_id)
                if key in seen:
                    continue
                seen.add(key)
                ids.append(key)
        if not include_hidden or not include_locked:
            filtered = []
            for object_id in ids:
                state = self.get_view_state(object_id)
                if state is None:
                    continue
                if state.hidden and not include_hidden:
                    continue
                if state.locked and not include_locked:
                    continue
                filtered.append(object_id)
            return tuple(filtered)
        return tuple(ids)

    def get_view_state(self, object_id: str) -> Optional[ObjectViewState]:
        rs = self._rs
        if not rs.IsObject(object_id):
            return None
        color = rs.ObjectColor(object_id)
        rgb = (int(color.R), int(color.G), int(color.B)) if color is not None else (0, 0, 0)
        source = rs.ObjectColorSource(object_id)
        return ObjectViewState(
            object_id=str(object_id),
            selected=bool(rs.IsObjectSelected(object_id)),
            locked=bool(rs.IsObjectLocked(object_id)),
            hidden=bool(rs.IsObjectHidden(object_id)),
            color=rgb,
            color_by_layer=source == COLOR_SOURCE_BY_LAYER,
        )

    def set_view_state(self, state: ObjectViewState) -> None:
        rs = self._rs
        object_id = state.object_id
        if rs.IsObjectHidden(object_id):
            rs.ShowObject(object_id)
        if rs.IsObjectLocked(object_id):
            rs.UnlockObject(object_id)
        if state.color_by_layer:
            rs.ObjectColorSource(object_id, COLOR_SOURCE_BY_LAYER)
        else:
            rs.ObjectColorSource(object_id, COLOR_SOURCE_BY_OBJECT)
            rs.ObjectColor(object_id, state.color)
        if state.selected:
            rs.SelectObject(object_id)
        else:
            rs.UnselectObject(object_id)
        if state.hidden:
            rs.HideObject(object_id)
        if state.locked:
            rs.LockObject(object_id)

    def document_modified(self) -> bool:
        return bool(self._sc.doc.Modified)

    def set_document_modified(self, value: bool) -> None:
        self._sc.doc.Modified = bool(value)

    def snapshot(self) -> DocumentSnapshot:
        return capture_snapshot(self)

    def restore(
        self,
        snapshot: DocumentSnapshot,
        *,
        restore_document_modified: bool,
    ) -> results.Result:
        self._rs.UnselectAllObjects()
        return restore_snapshot(
            self,
            snapshot,
            restore_document_modified=restore_document_modified,
        )
