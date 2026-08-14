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

    def document_user_text(self, key: str) -> Optional[str]:
        value = self._rs.GetDocumentUserText(key)
        if value in (None, ""):
            return None
        return str(value)

    def model_unit_system(self) -> str:
        return str(self._sc.doc.ModelUnitSystem)

    def layer_paths(self):
        names = self._rs.LayerNames() or []
        return tuple(str(name) for name in names)

    def has_layer(self, path: str) -> bool:
        return bool(self._rs.IsLayer(path))

    def ensure_layer(self, path: str) -> bool:
        created = not self.has_layer(path)
        current = ""
        for index, part in enumerate(path.split("::")):
            current = part if index == 0 else current + "::" + part
            if not self._rs.IsLayer(current):
                self._rs.AddLayer(current)
        return created

    def delete_layer(self, path: str) -> None:
        if self._rs.IsLayer(path):
            self._rs.DeleteLayer(path)

    def _layer_obj(self, path: str):
        index = self._sc.doc.Layers.FindByFullPath(path, -1)
        if index < 0:
            return None
        return self._sc.doc.Layers[index]

    def get_layer_user_text(self, path: str, key: str) -> Optional[str]:
        layer = self._layer_obj(path)
        if layer is None:
            return None
        value = layer.GetUserString(key)
        if value in (None, ""):
            return None
        return str(value)

    def set_layer_user_text(self, path: str, key: str, value: str) -> None:
        layer = self._layer_obj(path)
        if layer is None:
            raise KeyError("未知圖層：%s" % path)
        layer.SetUserString(key, value)
        layer.CommitChanges()

    def object_name(self, object_id: str) -> Optional[str]:
        value = self._rs.ObjectName(object_id)
        if value in (None, ""):
            return None
        return str(value)

    def set_object_name(self, object_id: str, name: str) -> None:
        self._rs.ObjectName(object_id, name)

    def object_layer(self, object_id: str) -> Optional[str]:
        value = self._rs.ObjectLayer(object_id)
        if value in (None, ""):
            return None
        return str(value)

    def set_object_layer(self, object_id: str, path: str) -> None:
        self._rs.ObjectLayer(object_id, path)

    def get_object_user_text(self, object_id: str, key: str) -> Optional[str]:
        value = self._rs.GetUserText(object_id, key)
        if value in (None, ""):
            return None
        return str(value)

    def set_object_user_text(self, object_id: str, key: str, value: str) -> None:
        self._rs.SetUserText(object_id, key, value)

    def objects_on_layer(self, path: str):
        ids = self._rs.ObjectsByLayer(path) or []
        return tuple(str(item) for item in ids)

    def add_placeholder(self, *, layer: str, name: str) -> str:
        line_id = self._rs.AddLine((0, 0, 0), (-25, 0, 0))
        object_id = str(line_id)
        self._rs.ObjectLayer(object_id, layer)
        self._rs.ObjectName(object_id, name)
        return object_id

    def delete_object(self, object_id: str) -> None:
        self._rs.DeleteObject(object_id)

    def is_closed_curve(self, object_id: str) -> bool:
        return bool(self._rs.IsCurve(object_id) and self._rs.IsCurveClosed(object_id))

    def curve_polygon(self, object_id: str):
        if not self._rs.IsCurve(object_id):
            return None
        points = self._rs.CurvePoints(object_id) or []
        return tuple((float(pt.X), float(pt.Y)) for pt in points)

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
