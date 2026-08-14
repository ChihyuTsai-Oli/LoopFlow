# -*- coding: utf-8 -*-
"""記憶體假 Rhino 文件，供純 Python 測試 snapshot／restore 與圖層同步。"""
from __future__ import annotations

from typing import Dict, List, Optional

from loopflow.foundation import results
from loopflow.platform.rhino.session import capture_snapshot, restore_snapshot
from loopflow.platform.rhino.state import DocumentSnapshot, ObjectViewState


class MemorySession:
    def __init__(self, *, model_unit: str = "Centimeters", document_text=None) -> None:
        self._objects: Dict[str, ObjectViewState] = {}
        self._object_meta: Dict[str, dict] = {}
        self._layers: Dict[str, dict] = {}
        self._curves: Dict[str, dict] = {}
        self._bboxes: Dict[str, tuple] = {}
        self._blocks: Dict[str, tuple] = {}
        self._points: Dict[str, tuple] = {}
        self._kinds: Dict[str, str] = {}
        self._derived_frames: Dict[str, dict] = {}
        self._modified = False
        self._model_unit = model_unit
        self._document_text = dict(document_text or {})
        self._next_id = 1

    def add_object(
        self,
        object_id: str,
        *,
        selected: bool = False,
        locked: bool = False,
        hidden: bool = False,
        color=(0, 0, 0),
        color_by_layer: bool = True,
        name: Optional[str] = None,
        layer: Optional[str] = None,
        user_text=None,
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
        self._object_meta[object_id] = {
            "name": name,
            "layer": layer,
            "user_text": dict(user_text or {}),
        }
        self._modified = True
        return state

    def delete_object(self, object_id: str) -> None:
        self._objects.pop(object_id, None)
        self._object_meta.pop(object_id, None)
        self._curves.pop(object_id, None)
        self._bboxes.pop(object_id, None)
        self._blocks.pop(object_id, None)
        self._points.pop(object_id, None)
        self._kinds.pop(object_id, None)
        self._derived_frames.pop(object_id, None)
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

    def layer_paths(self):
        return tuple(self._layers)

    def has_layer(self, path: str) -> bool:
        return path in self._layers

    def ensure_layer(self, path: str) -> bool:
        created = path not in self._layers
        current = ""
        for index, part in enumerate(path.split("::")):
            current = part if index == 0 else current + "::" + part
            if current not in self._layers:
                self._layers[current] = {"user_text": {}}
                self._modified = True
        return created

    def delete_layer(self, path: str) -> None:
        self._layers.pop(path, None)
        self._modified = True

    def get_layer_user_text(self, path: str, key: str) -> Optional[str]:
        layer = self._layers.get(path)
        if not layer:
            return None
        value = layer["user_text"].get(key)
        if value in (None, ""):
            return None
        return str(value)

    def set_layer_user_text(self, path: str, key: str, value: str) -> None:
        if path not in self._layers:
            raise KeyError("未知圖層：%s" % path)
        self._layers[path]["user_text"][key] = value
        self._modified = True

    def set_layer_appearance(self, path: str, rgb, material_name: Optional[str] = None) -> None:
        if path not in self._layers:
            raise KeyError("未知圖層：%s" % path)
        self._layers[path]["color"] = tuple(int(value) for value in rgb)
        self._layers[path]["material_name"] = material_name
        self._modified = True

    def layer_color(self, path: str):
        layer = self._layers.get(path) or {}
        return layer.get("color")

    def layer_material_name(self, path: str) -> Optional[str]:
        layer = self._layers.get(path) or {}
        return layer.get("material_name")

    def _meta(self, object_id: str) -> dict:
        if object_id not in self._object_meta:
            self._object_meta[object_id] = {"name": None, "layer": None, "user_text": {}}
        return self._object_meta[object_id]

    def object_name(self, object_id: str) -> Optional[str]:
        return self._meta(object_id)["name"]

    def set_object_name(self, object_id: str, name: str) -> None:
        self._meta(object_id)["name"] = name
        self._modified = True

    def object_layer(self, object_id: str) -> Optional[str]:
        return self._meta(object_id)["layer"]

    def set_object_layer(self, object_id: str, path: str) -> None:
        self._meta(object_id)["layer"] = path
        self._modified = True

    def get_object_user_text(self, object_id: str, key: str) -> Optional[str]:
        value = self._meta(object_id)["user_text"].get(key)
        if value in (None, ""):
            return None
        return str(value)

    def set_object_user_text(self, object_id: str, key: str, value: str) -> None:
        text = self._meta(object_id)["user_text"]
        if value in (None, ""):
            text.pop(key, None)
        else:
            text[key] = value
        self._modified = True

    def objects_on_layer(self, path: str):
        return tuple(
            object_id
            for object_id, meta in self._object_meta.items()
            if meta.get("layer") == path and object_id in self._objects
        )

    def add_placeholder(self, *, layer: str, name: str) -> str:
        object_id = "mem-%s" % self._next_id
        self._next_id += 1
        self.add_object(object_id, name=name, layer=layer)
        self._points[object_id] = (0.0, 0.0, 0.0)
        return object_id

    def placeholder_point(self, object_id: str):
        return self._points.get(object_id)

    def set_curve(self, object_id: str, polygon, *, closed: bool = True) -> None:
        self._curves[object_id] = {"polygon": tuple(tuple(pt) for pt in polygon), "closed": bool(closed)}

    def is_closed_curve(self, object_id: str) -> bool:
        curve = self._curves.get(object_id)
        return bool(curve and curve["closed"] and len(curve["polygon"]) >= 3)

    def curve_polygon(self, object_id: str):
        curve = self._curves.get(object_id)
        if not curve:
            return None
        return curve["polygon"]

    def is_model_object(self, object_id: str) -> bool:
        if object_id not in self._objects or object_id in self._curves:
            return False
        name = self.object_name(object_id) or ""
        return not name.startswith("DNA_REF_")

    def set_bbox(self, object_id: str, min_xyz, max_xyz) -> None:
        self._bboxes[object_id] = (tuple(min_xyz), tuple(max_xyz))

    def object_bbox(self, object_id: str):
        box = self._bboxes.get(object_id)
        if not box:
            return None
        (x0, y0, z0), (x1, y1, z1) = box
        return (float(x0), float(y0), float(z0), float(x1), float(y1), float(z1))

    def set_block(self, object_id: str, insertion) -> None:
        self._blocks[object_id] = tuple(insertion)

    def is_block_instance(self, object_id: str) -> bool:
        return object_id in self._blocks

    def insertion_point(self, object_id: str):
        point = self._blocks.get(object_id)
        if not point:
            return None
        return tuple(float(v) for v in point)

    def set_geometry_kind(self, object_id: str, kind: str) -> None:
        self._kinds[object_id] = kind

    def set_derived_frame(self, object_id: str, frame: dict) -> None:
        self._derived_frames[object_id] = dict(frame)

    def geometry_kind(self, object_id: str):
        if object_id in self._kinds:
            return self._kinds[object_id]
        if self.is_block_instance(object_id):
            return "block_instance"
        return "closed_box"

    def derive_local_frame(self, object_id: str):
        if object_id in self._derived_frames:
            return dict(self._derived_frames[object_id])
        kind = self.geometry_kind(object_id)
        method = {
            "block_instance": "block_insertion",
            "extrusion": "extrusion_base",
            "planar_curve": "unique_plane",
            "planar_surface": "unique_plane",
            "oriented_box": "oriented_box",
        }.get(kind)
        if method is None:
            return None
        insertion = self.insertion_point(object_id) if kind == "block_instance" else None
        origin = list(insertion) if insertion else [0.0, 0.0, 0.0]
        return {
            "schema_id": "loopflow.local_frame",
            "schema_version": 1,
            "origin": origin,
            "x_axis": [1.0, 0.0, 0.0],
            "y_axis": [0.0, 1.0, 0.0],
            "z_axis": [0.0, 0.0, 1.0],
            "derivation_method": method,
        }

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
