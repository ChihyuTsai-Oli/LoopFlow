# -*- coding: utf-8 -*-
"""記憶體假 Rhino 文件，供純 Python 測試 snapshot／restore。"""
from __future__ import annotations

from typing import Dict, List, Optional

from loopflow.foundation import results
from loopflow.platform.rhino.session import capture_snapshot, restore_snapshot
from loopflow.platform.rhino.state import DocumentSnapshot, ObjectViewState


class MemorySession:
    def __init__(self, *, model_unit: str = "Centimeters", document_text=None) -> None:
        self._objects: Dict[str, ObjectViewState] = {}
        self._modified = False
        self._model_unit = model_unit
        self._document_text = dict(document_text or {})

    def add_object(
        self,
        object_id: str,
        *,
        selected: bool = False,
        locked: bool = False,
        hidden: bool = False,
        color=(0, 0, 0),
        color_by_layer: bool = True,
    ) -> ObjectViewState:
        state = ObjectViewState(
            object_id=object_id,
            selected=selected,
            locked=locked,
            hidden=hidden,
            color=tuple(color),
            color_by_layer=color_by_layer,
        )
        self._objects[object_id] = state
        self._modified = True
        return state

    def delete_object(self, object_id: str) -> None:
        self._objects.pop(object_id, None)
        self._modified = True

    def iter_object_ids(self, *, include_hidden: bool = True, include_locked: bool = True):
        ids: List[str] = []
        for state in self._objects.values():
            if state.hidden and not include_hidden:
                continue
            if state.locked and not include_locked:
                continue
            ids.append(state.object_id)
        return tuple(ids)

    def get_view_state(self, object_id: str) -> Optional[ObjectViewState]:
        return self._objects.get(object_id)

    def set_view_state(self, state: ObjectViewState) -> None:
        if state.object_id not in self._objects:
            raise KeyError("未知物件：%s" % state.object_id)
        self._objects[state.object_id] = state

    def document_modified(self) -> bool:
        return self._modified

    def set_document_modified(self, value: bool) -> None:
        self._modified = bool(value)

    def document_user_text(self, key: str) -> Optional[str]:
        value = self._document_text.get(key)
        if value in (None, ""):
            return None
        return str(value)

    def model_unit_system(self) -> str:
        return self._model_unit

    def snapshot(self) -> DocumentSnapshot:
        return capture_snapshot(self)

    def restore(
        self,
        snapshot: DocumentSnapshot,
        *,
        restore_document_modified: bool,
    ) -> results.Result:
        return restore_snapshot(
            self,
            snapshot,
            restore_document_modified=restore_document_modified,
        )
