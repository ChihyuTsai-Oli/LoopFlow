# -*- coding: utf-8 -*-
"""記憶體假 Rhino 文件，供純 Python 測試 snapshot／restore 與圖層同步。"""
from __future__ import annotations

import copy
from typing import Dict, List, Optional

from loopflow.foundation import results
from loopflow.platform.rhino.session import (
    apply_extract_layer_print,
    capture_snapshot,
    is_section_or_extract_layer,
    restore_snapshot,
    silence_loopflow_layers,
)
from loopflow.platform.rhino.state import DocumentSnapshot, ObjectViewState


class MemorySession:
    def __init__(self, *, model_unit: str = "Centimeters", document_text=None) -> None:
        self._objects: Dict[str, ObjectViewState] = {}
        self._object_meta: Dict[str, dict] = {}
        self._layers: Dict[str, dict] = {}
        self._curves: Dict[str, dict] = {}
        self._bboxes: Dict[str, tuple] = {}
        self._blocks: Dict[str, tuple] = {}
        self._block_names: Dict[str, str] = {}
        self._points: Dict[str, tuple] = {}
        self._texts: Dict[str, dict] = {}
        self._text_dots: Dict[str, dict] = {}
        self._document_path: Optional[str] = None
        self._clipping_planes: Dict[str, dict] = {}
        self._drawing_content_bboxes: Dict[str, tuple] = {}
        self._ray_hits: list = []
        self._layout_active = True
        self._current_layout_page: Optional[str] = None
        self._layout_details: list = []
        self._layout_pages: List[str] = []
        self._page_objects: Dict[str, List[str]] = {}
        self._layout_sizes: Dict[str, tuple] = {}
        self.clipboard_ops: List[str] = []
        self._unassigned_paper_ids: List[str] = []
        self._detail_model_points: Dict[str, tuple] = {}
        self.zoomed_layout_details: List[dict] = []
        self.zoomed_layout_objects: List[dict] = []
        self._modified = False
        self._model_unit = model_unit
        self._document_text = dict(document_text or {})
        self._next_id = 1
        self.zoomed_object_ids: List[str] = []

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
        self._block_names.pop(object_id, None)
        self._points.pop(object_id, None)
        self._texts.pop(object_id, None)
        self._text_dots.pop(object_id, None)
        self._clipping_planes.pop(object_id, None)
        for ids in self._page_objects.values():
            if object_id in ids:
                ids.remove(object_id)
        self._modified = True

    def iter_object_ids(
        self,
        *,
        include_hidden: bool = True,
        include_locked: bool = True,
        include_linked: bool = False,
    ):
        ids: List[str] = []
        for state in self._objects.values():
            if state.hidden and not include_hidden:
                continue
            if state.locked and not include_locked:
                continue
            ids.append(state.object_id)
        return tuple(ids)

    def iter_curve_ids(self):
        return tuple(self._curves)

    def get_view_state(self, object_id: str) -> Optional[ObjectViewState]:
        return self._objects.get(object_id)

    def set_view_state(self, state: ObjectViewState) -> None:
        if state.object_id not in self._objects:
            raise KeyError("未知物件：%s" % state.object_id)
        self._objects[state.object_id] = state

    def set_redraw_enabled(self, enabled: bool) -> None:
        return None

    def select_objects(self, object_ids) -> None:
        wanted = set(str(item) for item in object_ids)
        for object_id, state in list(self._objects.items()):
            selected = object_id in wanted
            if state.selected == selected:
                continue
            self._objects[object_id] = ObjectViewState(
                object_id=object_id,
                selected=selected,
                locked=state.locked,
                hidden=state.hidden,
                color=state.color,
                color_by_layer=state.color_by_layer,
            )

    def document_modified(self) -> bool:
        return self._modified

    def set_document_modified(self, value: bool) -> None:
        self._modified = bool(value)

    def document_user_text(self, key: str) -> Optional[str]:
        value = self._document_text.get(key)
        if value in (None, ""):
            return None
        return str(value)

    def set_document_user_text(self, key: str, value: str) -> None:
        if value in (None, ""):
            self._document_text.pop(key, None)
        else:
            self._document_text[key] = value
        self._modified = True

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
        silence_loopflow_layers(self, path)
        apply_extract_layer_print(self, path)
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

    def set_layer_printable(self, path: str, printable: bool) -> None:
        if path not in self._layers:
            return
        self._layers[path]["printable"] = bool(printable)
        self._modified = True

    def layer_printable(self, path: str) -> Optional[bool]:
        layer = self._layers.get(path) or {}
        value = layer.get("printable")
        if value is None:
            return None
        return bool(value)

    def set_layer_print_color(self, path: str, rgb) -> None:
        if path not in self._layers:
            return
        self._layers[path]["print_color"] = tuple(int(value) for value in rgb[:3])
        self._modified = True

    def layer_print_color(self, path: str):
        layer = self._layers.get(path) or {}
        value = layer.get("print_color")
        if value is None:
            return None
        return tuple(int(item) for item in value[:3])

    def layer_color(self, path: str):
        layer = self._layers.get(path) or {}
        return layer.get("color")

    def layer_locked(self, path: str) -> bool:
        return bool((self._layers.get(path) or {}).get("locked", False))

    def set_layer_locked(self, path: str, locked: bool) -> None:
        if path not in self._layers:
            return
        self._layers[path]["locked"] = bool(locked)
        self._modified = True

    def layer_visible(self, path: str) -> bool:
        layer = self._layers.get(path) or {}
        if "visible" not in layer:
            return True
        return bool(layer.get("visible"))

    def set_layer_visible(self, path: str, visible: bool) -> None:
        if path not in self._layers:
            return
        self._layers[path]["visible"] = bool(visible)
        self._modified = True

    def copy_object(self, object_id: str) -> Optional[str]:
        if object_id not in self._objects:
            return None
        state = self._objects[object_id]
        meta = copy.deepcopy(self._meta(object_id))
        new_id = "mem-%s" % self._next_id
        self._next_id += 1
        self.add_object(
            new_id,
            selected=False,
            locked=False,
            hidden=False,
            color=state.color,
            color_by_layer=True,
            name=meta.get("name"),
            layer=meta.get("layer"),
            user_text=meta.get("user_text"),
        )
        if object_id in self._curves:
            self._curves[new_id] = copy.deepcopy(self._curves[object_id])
        if object_id in self._bboxes:
            self._bboxes[new_id] = copy.deepcopy(self._bboxes[object_id])
        if object_id in self._points:
            self._points[new_id] = tuple(self._points[object_id])
        if object_id in self._blocks:
            self._blocks[new_id] = copy.deepcopy(self._blocks[object_id])
        if object_id in self._block_names:
            self._block_names[new_id] = self._block_names[object_id]
        if object_id in self._texts:
            self._texts[new_id] = copy.deepcopy(self._texts[object_id])
        if object_id in self._text_dots:
            self._text_dots[new_id] = copy.deepcopy(self._text_dots[object_id])
        if object_id in self._clipping_planes:
            self._clipping_planes[new_id] = copy.deepcopy(self._clipping_planes[object_id])
        return new_id

    def reset_object_to_bylayer(self, object_id: str) -> None:
        state = self._objects.get(object_id)
        if state is None:
            return
        self._objects[object_id] = ObjectViewState(
            object_id=object_id,
            selected=state.selected,
            locked=state.locked,
            hidden=state.hidden,
            color=state.color,
            color_by_layer=True,
        )

    def object_display_color(self, object_id: str):
        state = self._objects.get(object_id)
        if state is None:
            return None
        if state.color_by_layer:
            layer = self.object_layer(object_id)
            return self.layer_color(layer) if layer else state.color
        return state.color

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

    def object_user_text_keys(self, object_id: str):
        return tuple(self._meta(object_id)["user_text"].keys())

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

    def add_point(self, object_id: str, xyz=(0.0, 0.0, 0.0), *, layer: Optional[str] = None) -> None:
        if object_id not in self._objects:
            self.add_object(object_id, layer=layer)
        elif layer not in (None, ""):
            self.set_object_layer(object_id, layer)
        self._points[object_id] = tuple(float(v) for v in xyz)

    def is_point(self, object_id: str) -> bool:
        return object_id in self._points and object_id not in self._blocks

    def point_xyz(self, object_id: str):
        point = self._points.get(object_id)
        if not point:
            return None
        return tuple(float(v) for v in point)

    def layout_page_name_of(self, object_id: str) -> Optional[str]:
        for page_name, ids in self._page_objects.items():
            if object_id in ids:
                return page_name
        return None

    def add_text(
        self,
        content: str,
        point,
        *,
        layer: str,
        page_name: Optional[str] = None,
        height: float = 1.0,
    ) -> str:
        object_id = "mem-%s" % self._next_id
        self._next_id += 1
        self.add_object(object_id, layer=layer)
        xyz = tuple(float(v) for v in (point or (0.0, 0.0, 0.0)))
        self._texts[object_id] = {
            "text": str(content),
            "point": xyz,
            "height": float(height),
            "font": "Arial",
            "justification": "bottom_left",
        }
        if page_name:
            self.add_object_to_layout_page(page_name, object_id)
        return object_id

    def update_text(self, object_id: str, content: str, origin=None) -> bool:
        item = self._texts.get(object_id)
        if not item:
            return False
        item["text"] = str(content)
        if origin is not None:
            item["point"] = tuple(float(v) for v in origin)
        self._modified = True
        return True

    def text_height(self, object_id: str) -> Optional[float]:
        item = self._texts.get(object_id)
        if not item:
            return None
        return float(item.get("height") or 0.0)

    def set_text_height(self, object_id: str, height: float) -> None:
        item = self._texts.get(object_id)
        if item is None:
            return
        item["height"] = float(height)
        self._modified = True

    def text_origin(self, object_id: str):
        item = self._texts.get(object_id)
        if not item:
            return None
        return tuple(item.get("point") or ())

    def text_content(self, object_id: str) -> Optional[str]:
        item = self._texts.get(object_id)
        if not item:
            return None
        return str(item.get("text") or "")

    def document_path(self) -> Optional[str]:
        return self._document_path

    def set_document_path(self, path: Optional[str]) -> None:
        self._document_path = None if path in (None, "") else str(path)

    def set_curve(self, object_id: str, polygon, *, closed: bool = True, elevation=None) -> None:
        pts = tuple(tuple(pt) for pt in polygon)
        if elevation is None:
            if pts and len(pts[0]) >= 3:
                elevation = float(pts[0][2])
            else:
                elevation = 0.0
        self._curves[object_id] = {
            "polygon": pts,
            "closed": bool(closed),
            "elevation": float(elevation),
        }

    def is_closed_curve(self, object_id: str) -> bool:
        curve = self._curves.get(object_id)
        return bool(curve and curve["closed"] and len(curve["polygon"]) >= 3)

    def curve_polygon(self, object_id: str):
        curve = self._curves.get(object_id)
        if not curve:
            return None
        return curve["polygon"]

    def curve_elevation(self, object_id: str):
        curve = self._curves.get(object_id)
        if not curve:
            return None
        return float(curve["elevation"])

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

    def set_block(self, object_id: str, insertion, name: Optional[str] = None) -> None:
        self._blocks[object_id] = tuple(insertion)
        if name not in (None, ""):
            self._block_names[object_id] = str(name)

    def is_block_instance(self, object_id: str) -> bool:
        return object_id in self._blocks

    def block_definition_name(self, object_id: str) -> Optional[str]:
        return self._block_names.get(object_id)

    def insertion_point(self, object_id: str):
        point = self._blocks.get(object_id)
        if not point:
            return None
        return tuple(float(v) for v in point)

    def add_text_dot(self, object_id: str, text: str, point=(0.0, 0.0, 0.0)) -> None:
        if object_id not in self._objects:
            self.add_object(object_id)
        self._text_dots[object_id] = {
            "text": str(text),
            "point": tuple(float(v) for v in point),
        }

    def is_text_dot(self, object_id: str) -> bool:
        return object_id in self._text_dots

    def text_dot_text(self, object_id: str) -> Optional[str]:
        item = self._text_dots.get(object_id)
        if not item:
            return None
        text = str(item.get("text") or "").strip()
        return text or None

    def add_clipping_plane(
        self,
        object_id: str,
        *,
        name: str,
        origin=(0.0, 0.0, 0.0),
        x_axis=(1.0, 0.0, 0.0),
        y_axis=(0.0, 1.0, 0.0),
        z_axis=(0.0, 0.0, 1.0),
        section_bbox_local=(0.0, 0.0, 1.0, 1.0),
    ) -> None:
        if object_id not in self._objects:
            self.add_object(object_id, name=name)
        else:
            self.set_object_name(object_id, name)
        local = None
        if section_bbox_local is not None:
            local = tuple(float(v) for v in section_bbox_local)
        self._clipping_planes[object_id] = {
            "origin": tuple(float(v) for v in origin),
            "x_axis": tuple(float(v) for v in x_axis),
            "y_axis": tuple(float(v) for v in y_axis),
            "z_axis": tuple(float(v) for v in z_axis),
            "section_bbox_local": local,
        }

    def is_clipping_plane(self, object_id: str) -> bool:
        return object_id in self._clipping_planes

    def iter_clipping_plane_ids(self):
        return tuple(self._clipping_planes)

    def clipping_plane_plane(self, object_id: str):
        plane = self._clipping_planes.get(object_id)
        if not plane:
            return None
        return {
            "origin": plane["origin"],
            "x_axis": plane["x_axis"],
            "y_axis": plane["y_axis"],
            "z_axis": plane["z_axis"],
        }

    def clipping_plane_section_bbox_local(self, object_id: str):
        plane = self._clipping_planes.get(object_id)
        if not plane:
            return None
        box = plane.get("section_bbox_local")
        if not box or len(box) < 4:
            return None
        return tuple(float(v) for v in box)

    def drawing_content_bbox(self, frame_id: str):
        return self._drawing_content_bboxes.get(str(frame_id))

    def set_drawing_content_bbox(self, frame_id: str, box) -> None:
        self._drawing_content_bboxes[str(frame_id)] = tuple(float(v) for v in box)

    def objects_bbox(self, object_ids):
        boxes = []
        for object_id in object_ids:
            box = self.object_bbox(object_id)
            if box:
                boxes.append(box)
        if not boxes:
            return None
        return (
            min(box[0] for box in boxes),
            min(box[1] for box in boxes),
            min(box[2] for box in boxes),
            max(box[3] for box in boxes),
            max(box[4] for box in boxes),
            max(box[5] for box in boxes),
        )

    def uuid_objects_bbox_center(self):
        boxes = []
        for object_id in self.iter_object_ids(include_hidden=True, include_locked=True):
            uuid_value = (
                self.get_object_user_text(object_id, "_07_UUID")
                or self.get_object_user_text(object_id, "_12_UUID")
                or self.get_object_user_text(object_id, "lf_object_id")
            )
            if not uuid_value:
                continue
            if is_section_or_extract_layer(self.object_layer(object_id) or ""):
                continue
            box = self.object_bbox(object_id)
            if box:
                boxes.append(box)
        if not boxes:
            return None
        return (
            (min(box[0] for box in boxes) + max(box[3] for box in boxes)) * 0.5,
            (min(box[1] for box in boxes) + max(box[4] for box in boxes)) * 0.5,
            (min(box[2] for box in boxes) + max(box[5] for box in boxes)) * 0.5,
        )

    def add_closed_polyline(self, points, *, layer: str, name: str) -> str:
        object_id = "mem-%s" % self._next_id
        self._next_id += 1
        pts = [tuple(float(v) for v in pt) for pt in points]
        if len(pts) < 3:
            raise ValueError("封閉框至少需要 3 點")
        self.add_object(object_id, name=name, layer=layer)
        closed = list(pts)
        if closed[0] != closed[-1]:
            closed.append(closed[0])
        self.set_curve(object_id, closed, closed=True)
        xs = [pt[0] for pt in pts]
        ys = [pt[1] for pt in pts]
        zs = [pt[2] if len(pt) > 2 else 0.0 for pt in pts]
        self.set_bbox(
            object_id,
            (min(xs), min(ys), min(zs)),
            (max(xs), max(ys), max(zs)),
        )
        return object_id

    def set_ray_hits(self, hits) -> None:
        self._ray_hits = [dict(item) for item in hits]

    def shoot_ray_hits(self, origin, direction):
        return tuple(dict(item) for item in self._ray_hits)

    def zoom_to_object(self, object_id: str) -> None:
        self.zoomed_object_ids.append(object_id)

    def activate_layout_page(self, page_name: str) -> bool:
        name = str(page_name or "").strip()
        if name not in self._layout_pages:
            return False
        self.set_current_layout_page(name)
        return True

    def zoom_to_layout_object(self, page_name: str, object_id: str) -> None:
        self.activate_layout_page(page_name)
        self.zoomed_layout_objects.append(
            {"layout": str(page_name or ""), "object_id": str(object_id or "")}
        )

    def set_layout_active(self, value: bool) -> None:
        self._layout_active = bool(value)

    def is_layout_active(self) -> bool:
        return bool(self._layout_active)

    def set_current_layout_page(self, page_name: Optional[str]) -> None:
        name = str(page_name or "").strip() or None
        self._current_layout_page = name
        if name:
            self._layout_active = True
            if name not in self._layout_pages:
                self._layout_pages.append(name)
                self._page_objects.setdefault(name, [])

    def current_layout_page_name(self):
        if not self._layout_active:
            return None
        return self._current_layout_page

    def set_layout_details(self, items) -> None:
        self._layout_details = [dict(item) for item in items]

    def listed_layout_details(self):
        return tuple(dict(item) for item in self._layout_details)

    def set_detail_model_point(self, detail_id: str, point) -> None:
        self._detail_model_points[str(detail_id)] = tuple(float(v) for v in point)

    def detail_model_point(self, detail_id: str):
        point = self._detail_model_points.get(str(detail_id))
        if not point:
            return None
        return tuple(point)

    def zoom_to_layout_detail(self, layout: str, detail_id: str) -> None:
        self.zoomed_layout_details.append(
            {"layout": str(layout or ""), "detail_id": str(detail_id or "")}
        )

    def set_layout_pages(self, names) -> None:
        """依傳入順序設定 Layout 頁；頁序從 1 起算。"""
        self._layout_pages = [str(name) for name in names]
        for name in self._layout_pages:
            self._page_objects.setdefault(name, [])
            self._layout_sizes.setdefault(name, (297.0, 210.0))

    def add_object_to_layout_page(self, page_name: str, object_id: str) -> None:
        page = str(page_name)
        if page not in self._layout_pages:
            self._layout_pages.append(page)
            self._layout_sizes.setdefault(page, (297.0, 210.0))
        self._page_objects.setdefault(page, [])
        if object_id not in self._page_objects[page]:
            self._page_objects[page].append(object_id)

    def listed_layout_pages(self):
        return tuple(
            {"name": name, "page_number": index + 1}
            for index, name in enumerate(self._layout_pages)
        )

    def objects_on_layout_page(self, page_name: str):
        return tuple(self._page_objects.get(str(page_name), ()))

    def layout_page_size(self, page_name: str):
        size = self._layout_sizes.get(str(page_name))
        if not size:
            return None
        return (float(size[0]), float(size[1]))

    def add_layout_page(self, name: str, width: float, height: float):
        page = str(name or "").strip()
        if not page or page in self._layout_pages:
            return None
        self._layout_pages.append(page)
        self._page_objects[page] = []
        self._layout_sizes[page] = (float(width), float(height))
        self._modified = True
        return page

    def delete_layout_page(self, page_name: str) -> bool:
        page = str(page_name)
        if page not in self._layout_pages:
            return False
        for object_id in list(self._page_objects.get(page, ())):
            self.delete_object(object_id)
        self._layout_pages.remove(page)
        self._page_objects.pop(page, None)
        self._layout_sizes.pop(page, None)
        self._modified = True
        return True

    def copy_layout_page_objects(self, source_page: str, target_page: str):
        """複製頁上物件到目標頁。不使用剪貼簿。"""
        mapping = {}
        for object_id in list(self.objects_on_layout_page(source_page)):
            new_id = self.copy_object(object_id)
            if not new_id:
                continue
            mapping[str(object_id)] = new_id
            self.add_object_to_layout_page(target_page, new_id)
        return mapping

    def add_unassigned_paper_object(self, object_id: str) -> None:
        key = str(object_id)
        if key not in self._unassigned_paper_ids:
            self._unassigned_paper_ids.append(key)

    def paper_space_object_ids(self):
        ids: List[str] = []
        seen = set()
        for page_ids in self._page_objects.values():
            for object_id in page_ids:
                if object_id in seen:
                    continue
                seen.add(object_id)
                ids.append(object_id)
        for object_id in self._unassigned_paper_ids:
            if object_id in seen:
                continue
            seen.add(object_id)
            ids.append(object_id)
        return tuple(ids)

    def rename_layout_page(self, page_name: str, new_name: str) -> bool:
        old = str(page_name)
        new = str(new_name)
        if old not in self._layout_pages:
            return False
        if new != old and new in self._layout_pages:
            return False
        self._layout_pages[self._layout_pages.index(old)] = new
        self._page_objects[new] = self._page_objects.pop(old, [])
        self._modified = True
        return True

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
