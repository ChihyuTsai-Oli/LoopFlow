# -*- coding: utf-8 -*-
"""Rhino 8 live adapter。

模組載入不 import Rhino。NX-01～04 使用的 API 已在家中 Rhino 8 驗證。
"""
from __future__ import annotations

from typing import Optional, Tuple

from loopflow.foundation import results
from loopflow.platform.rhino.session import (
    apply_extract_layer_print,
    capture_snapshot,
    is_section_cut_layer,
    is_section_or_extract_layer,
    restore_snapshot,
    silence_loopflow_layers,
)
from loopflow.platform.rhino.state import DocumentSnapshot, ObjectViewState

LIVE_VERIFIED_IN_RHINO = True
COLOR_SOURCE_BY_LAYER = 0
COLOR_SOURCE_BY_OBJECT = 1
# 對齊 1.x VALID_GEOM_TYPES，並納入 SubD。不呼叫可能不存在的 rs.IsExtrusion。
MODEL_OBJECT_TYPE_VALUES = frozenset(
    (
        8,  # Surface
        16,  # Brep
        32,  # Mesh
        4096,  # Instance
        262144,  # SubD
        1073741824,  # Extrusion
    )
)


def rgb_tuple(color) -> Tuple[int, int, int]:
    """把 Rhino／.NET 顏色或 (r,g,b) 轉成整數 RGB。"""
    if color is None:
        return (0, 0, 0)
    if isinstance(color, (tuple, list)) and len(color) >= 3:
        return (int(color[0]), int(color[1]), int(color[2]))
    red = getattr(color, "R", None)
    green = getattr(color, "G", None)
    blue = getattr(color, "B", None)
    if red is not None and green is not None and blue is not None:
        return (int(red), int(green), int(blue))
    return (0, 0, 0)


def _xy_point(point) -> Optional[Tuple[float, float]]:
    if point is None:
        return None
    if hasattr(point, "X"):
        return (float(point.X), float(point.Y))
    try:
        return (float(point[0]), float(point[1]))
    except (TypeError, IndexError, ValueError):
        return None


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
    session = LiveSession(rs, sc, _Rhino)
    if LIVE_VERIFIED_IN_RHINO:
        return results.ok(
            "rhino_session",
            "已連接 Rhino 文件。",
            details={"session": session, "verified": True},
        )
    return results.ok(
        "rhino_session",
        "已連接 Rhino 文件。live adapter 尚未實機驗證。",
        warnings=("live_adapter_unverified",),
        details={"session": session, "verified": False},
    )


class LiveSession:
    def __init__(self, rs, sc, rhino=None) -> None:
        self._rs = rs
        self._sc = sc
        self._rhino = rhino

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

    def iter_curve_ids(self):
        rs = self._rs
        ids = []
        seen = set()
        groups = [rs.ObjectsByType(4) or []]
        try:
            groups.append(rs.HiddenObjects() or [])
            groups.append(rs.LockedObjects() or [])
        except Exception:
            pass
        for group in groups:
            for object_id in group:
                key = str(object_id)
                if key in seen:
                    continue
                if not rs.IsCurve(object_id):
                    continue
                seen.add(key)
                ids.append(key)
        return tuple(ids)

    def get_view_state(self, object_id: str) -> Optional[ObjectViewState]:
        rs = self._rs
        if not rs.IsObject(object_id):
            return None
        rgb = rgb_tuple(rs.ObjectColor(object_id))
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

    def set_redraw_enabled(self, enabled: bool) -> None:
        try:
            self._rs.EnableRedraw(bool(enabled))
        except Exception:
            pass

    def select_objects(self, object_ids) -> None:
        rs = self._rs
        ids = [str(item) for item in object_ids]
        self.set_redraw_enabled(False)
        try:
            rs.UnselectAllObjects()
            if not ids:
                return
            selected = False
            try:
                selected = bool(rs.SelectObjects(ids))
            except Exception:
                selected = False
            if not selected:
                for object_id in ids:
                    try:
                        rs.SelectObject(object_id)
                    except Exception:
                        pass
        finally:
            self.set_redraw_enabled(True)
            self._redraw_views()

    def document_modified(self) -> bool:
        return bool(self._sc.doc.Modified)

    def set_document_modified(self, value: bool) -> None:
        self._sc.doc.Modified = bool(value)

    def document_user_text(self, key: str) -> Optional[str]:
        value = self._rs.GetDocumentUserText(key)
        if value in (None, ""):
            return None
        return str(value)

    def set_document_user_text(self, key: str, value: str) -> None:
        # 不帶 value 呼叫即刪除該鍵；環境設定搬進專案設定檔後要能清掉舊鍵。
        if value in (None, ""):
            self._rs.SetDocumentUserText(key)
            return
        self._rs.SetDocumentUserText(key, value)

    def model_unit_system(self) -> str:
        return str(self._sc.doc.ModelUnitSystem)

    def layer_paths(self):
        names = self._rs.LayerNames() or []
        return tuple(str(name) for name in names)

    def has_layer(self, path: str) -> bool:
        return bool(self._rs.IsLayer(path))

    def ensure_layer(self, path: str) -> bool:
        created = not self.has_layer(path)
        parent_path = None
        current = ""
        for index, part in enumerate(path.split("::")):
            current = part if index == 0 else current + "::" + part
            if not self._rs.IsLayer(current):
                if parent_path:
                    self._rs.AddLayer(part, parent=parent_path)
                else:
                    self._rs.AddLayer(part)
            parent_path = current
        silence_loopflow_layers(self, path)
        apply_extract_layer_print(self, path)
        return created

    def delete_layer(self, path: str) -> None:
        if self._rs.IsLayer(path):
            self._rs.DeleteLayer(path)

    def _unset_layer_index(self) -> int:
        rhino = self._rhino
        value = getattr(getattr(rhino, "RhinoMath", None), "UnsetIntIndex", None)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                pass
        return -2147483648

    def _layer_obj(self, path: str):
        index = self._layer_index(path)
        if index < 0:
            return None
        return self._sc.doc.Layers[index]

    def _layer_index(self, path: str) -> int:
        """對齊 rhinoscriptsyntax.__getlayer：FindByFullPath 要用 UnsetIntIndex。"""
        layers = self._sc.doc.Layers
        wanted = str(path)
        unset = self._unset_layer_index()
        try:
            index = layers.FindByFullPath(wanted, unset)
            if index is not None and int(index) != unset and int(index) >= 0:
                return int(index)
        except Exception:
            pass
        try:
            layer_id = self._rs.LayerId(wanted)
            if layer_id:
                found = self._sc.doc.Layers.FindId(layer_id)
                if found is not None and not getattr(found, "IsDeleted", False):
                    return int(found.Index)
        except Exception:
            pass
        if "::" not in wanted:
            try:
                layer = layers.FindName(wanted)
                if layer is not None and not getattr(layer, "IsDeleted", False):
                    return int(layer.Index)
            except Exception:
                pass
        try:
            for layer in layers:
                if getattr(layer, "IsDeleted", False):
                    continue
                full = str(getattr(layer, "FullPath", "") or "")
                if full == wanted:
                    return int(layer.Index)
        except Exception:
            pass
        return -1

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

    def set_layer_printable(self, path: str, printable: bool) -> None:
        """關掉圖層面板的列印。畫面上看的是列印寬度「No Print」，即 PlotWeight = -1。

        這與改圖層顏色同一條路：rs.LayerPrintWidth 存在，且用 __getlayer 找層。
        PlotEnabled 單獨改時，Print 欄通常不會動。
        """
        if not self.has_layer(path):
            return
        width = 0.0 if printable else -1.0
        try:
            self._rs.LayerPrintWidth(path, width)
        except Exception:
            pass
        layer = self._layer_obj(path)
        if layer is not None:
            try:
                layer.PlotWeight = width
            except Exception:
                pass
            try:
                layer.PlotEnabled = bool(printable)
            except Exception:
                pass
            try:
                commit = getattr(layer, "CommitChanges", None)
                if callable(commit):
                    commit()
            except Exception:
                pass
        try:
            self._sc.doc.Views.RedrawEnabled = True
        except Exception:
            pass
        self._redraw_views()

    def set_layer_print_color(self, path: str, rgb) -> None:
        if not self.has_layer(path):
            return
        color = rgb_tuple(rgb)
        try:
            self._rs.LayerPrintColor(path, color)
        except Exception:
            pass
        layer = self._layer_obj(path)
        if layer is not None:
            try:
                import System  # type: ignore

                layer.PlotColor = System.Drawing.Color.FromArgb(color[0], color[1], color[2])
            except Exception:
                try:
                    layer.PlotColor = color
                except Exception:
                    pass
            try:
                commit = getattr(layer, "CommitChanges", None)
                if callable(commit):
                    commit()
            except Exception:
                pass
        self._redraw_views()

    def layer_print_color(self, path: str):
        if not self.has_layer(path):
            return None
        try:
            color = self._rs.LayerPrintColor(path)
            if color is not None:
                return rgb_tuple(color)
        except Exception:
            pass
        layer = self._layer_obj(path)
        if layer is None:
            return None
        try:
            return rgb_tuple(getattr(layer, "PlotColor", None))
        except Exception:
            return None

    def layer_printable(self, path: str) -> Optional[bool]:
        if not self.has_layer(path):
            return None
        try:
            width = self._rs.LayerPrintWidth(path)
            if width is not None and float(width) < 0:
                return False
        except Exception:
            pass
        layer = self._layer_obj(path)
        if layer is None:
            return None
        try:
            weight = float(getattr(layer, "PlotWeight", 0) or 0)
            if weight < 0:
                return False
        except Exception:
            pass
        return bool(getattr(layer, "PlotEnabled", True))

    def set_layer_appearance(self, path: str, rgb, material_name: Optional[str] = None) -> None:
        if not self.has_layer(path):
            raise KeyError("未知圖層：%s" % path)
        color = rgb_tuple(rgb)
        self._rs.LayerColor(path, color)
        if not material_name or self._rhino is None:
            self._redraw_views()
            return
        layer = self._layer_obj(path)
        if layer is None:
            return
        try:
            import System  # type: ignore

            sys_color = System.Drawing.Color.FromArgb(color[0], color[1], color[2])
        except Exception:
            sys_color = color
        mat_idx = -1
        legacy_name = "M3D::" + material_name if not str(material_name).startswith("M3D::") else None
        for material in self._sc.doc.Materials:
            if getattr(material, "IsDeleted", False):
                continue
            if material.Name == material_name:
                mat_idx = material.Index
                break
            if legacy_name and material.Name == legacy_name and mat_idx == -1:
                mat_idx = material.Index
        if mat_idx >= 0:
            try:
                material = self._sc.doc.Materials[mat_idx]
                if legacy_name and material.Name != material_name:
                    material.Name = material_name
                    self._sc.doc.Materials.Modify(material, mat_idx, True)
            except Exception:
                pass
        if mat_idx == -1:
            new_mat = self._rhino.DocObjects.Material()
            new_mat.Name = material_name
            try:
                new_mat.DiffuseColor = sys_color
            except Exception:
                pass
            mat_idx = self._sc.doc.Materials.Add(new_mat)
            if mat_idx >= 0:
                try:
                    material = self._sc.doc.Materials[mat_idx]
                    self._apply_material_color(material, mat_idx, sys_color, color)
                except Exception:
                    pass
        layer.RenderMaterialIndex = mat_idx
        layer.CommitChanges()
        self._redraw_views()

    def _apply_material_color(self, material, mat_idx, sys_color, color) -> None:
        try:
            material.DiffuseColor = sys_color
        except Exception:
            pass
        try:
            pbr = getattr(material, "PhysicallyBased", None)
            if pbr is not None:
                color4f = self._color4f(color)
                if color4f is not None:
                    pbr.BaseColor = color4f
        except Exception:
            pass
        try:
            render_mat = getattr(material, "RenderMaterial", None)
            if render_mat is not None:
                change = getattr(getattr(self._rhino, "Render", None), "RenderContent", None)
                contexts = getattr(change, "ChangeContexts", None) if change is not None else None
                context = getattr(contexts, "Program", None)
                if context is not None and hasattr(render_mat, "BeginChange"):
                    render_mat.BeginChange(context)
                    try:
                        color4f = self._color4f(color)
                        if color4f is not None and hasattr(render_mat, "SetParameter"):
                            render_mat.SetParameter("pbr-base-color", color4f)
                    finally:
                        render_mat.EndChange()
        except Exception:
            pass
        self._sc.doc.Materials.Modify(material, mat_idx, True)

    def _color4f(self, color):
        try:
            display = getattr(self._rhino, "Display", None)
            color4f = getattr(display, "Color4f", None)
            if color4f is None:
                return None
            return color4f(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, 1.0)
        except Exception:
            return None

    def _redraw_views(self) -> None:
        try:
            self._sc.doc.Views.Redraw()
        except Exception:
            try:
                self._rs.Redraw()
            except Exception:
                pass

    def zoom_to_object(self, object_id: str) -> None:
        box = self.object_bbox(object_id)
        if not box:
            return
        pad_x = max((box[3] - box[0]) * 0.2, 1.0)
        pad_y = max((box[4] - box[1]) * 0.2, 1.0)
        pad_z = max((box[5] - box[2]) * 0.2, 1.0)
        corners = (
            (box[0] - pad_x, box[1] - pad_y, box[2] - pad_z),
            (box[3] + pad_x, box[4] + pad_y, box[5] + pad_z),
        )
        try:
            self._rs.ZoomBoundingBox(corners, None, False)
        except Exception:
            pass
        self._redraw_views()

    def activate_layout_page(self, page_name: str) -> bool:
        page = self._page_view(page_name)
        if page is None:
            return False
        try:
            self._sc.doc.Views.ActiveView = page
            page.SetPageAsActive()
        except Exception:
            return False
        self._redraw_views()
        return True

    def zoom_to_layout_object(self, page_name: str, object_id: str) -> None:
        """切到該 Layout 並拉近 Tag，但留出圖框周圍，不放到滿畫面。"""
        if not self.activate_layout_page(page_name):
            return
        page = self._page_view(page_name)
        try:
            self._rs.UnselectAllObjects()
            self._rs.SelectObject(object_id)
        except Exception:
            pass
        box = self.object_bbox(object_id)
        if box:
            cx = (box[0] + box[3]) / 2.0
            cy = (box[1] + box[4]) / 2.0
            cz = (box[2] + box[5]) / 2.0
            tag_w = max(box[3] - box[0], 1.0)
            tag_h = max(box[4] - box[1], 1.0)
            page_w = 0.0
            page_h = 0.0
            if page is not None:
                try:
                    page_w = float(getattr(page, "PageWidth", 0) or 0)
                    page_h = float(getattr(page, "PageHeight", 0) or 0)
                except Exception:
                    page_w = page_h = 0.0
            half_w = max(tag_w * 4.0, page_w * 0.22 if page_w else tag_w * 8.0)
            half_h = max(tag_h * 4.0, page_h * 0.22 if page_h else tag_h * 8.0)
            corners = (
                (cx - half_w, cy - half_h, cz - 1.0),
                (cx + half_w, cy + half_h, cz + 1.0),
            )
            try:
                self._rs.ZoomBoundingBox(corners, None, False)
            except Exception:
                try:
                    if page is not None:
                        page.MainViewport.ZoomExtentsSelected()
                        page.MainViewport.Magnify(0.4, False)
                except Exception:
                    pass
        else:
            try:
                if page is not None:
                    page.MainViewport.ZoomExtentsSelected()
                    page.MainViewport.Magnify(0.4, False)
            except Exception:
                pass
        self._redraw_views()

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

    def copy_object(self, object_id: str) -> Optional[str]:
        copied = self._rs.CopyObject(object_id)
        if not copied:
            return None
        return str(copied)

    def reset_object_to_bylayer(self, object_id: str) -> None:
        try:
            self._rs.ObjectColorSource(object_id, 0)
            self._rs.ObjectLinetypeSource(object_id, 0)
            self._rs.ObjectPrintColorSource(object_id, 0)
            self._rs.ObjectPrintWidthSource(object_id, 0)
        except Exception:
            pass

    def object_display_color(self, object_id: str):
        try:
            source = self._rs.ObjectColorSource(object_id)
            if source == 0:
                layer = self.object_layer(object_id)
                if layer:
                    color = self._rs.LayerColor(layer)
                    if color is not None:
                        return rgb_tuple(color)
            color = self._rs.ObjectColor(object_id)
            if color is not None:
                return rgb_tuple(color)
        except Exception:
            return None
        return None

    def object_color_by_layer(self, object_id: str) -> bool:
        try:
            return int(self._rs.ObjectColorSource(object_id)) == COLOR_SOURCE_BY_LAYER
        except Exception:
            return True

    def set_object_color(self, object_id: str, rgb) -> None:
        try:
            self._rs.ObjectColorSource(object_id, COLOR_SOURCE_BY_OBJECT)
            self._rs.ObjectColor(
                object_id,
                (int(rgb[0]), int(rgb[1]), int(rgb[2])),
            )
        except Exception:
            pass

    def layer_locked(self, path: str) -> bool:
        try:
            return bool(self._rs.IsLayerLocked(path))
        except Exception:
            return False

    def set_layer_locked(self, path: str, locked: bool) -> None:
        if not self.has_layer(path):
            return
        try:
            self._rs.LayerLocked(path, bool(locked))
        except Exception:
            pass

    def layer_visible(self, path: str) -> bool:
        try:
            return bool(self._rs.IsLayerVisible(path))
        except Exception:
            return True

    def set_layer_visible(self, path: str, visible: bool) -> None:
        if not self.has_layer(path):
            return
        try:
            self._rs.LayerVisible(path, bool(visible), True)
        except Exception:
            pass

    def get_object_user_text(self, object_id: str, key: str) -> Optional[str]:
        value = self._rs.GetUserText(object_id, key)
        if value in (None, ""):
            return None
        return str(value)

    def object_user_text_keys(self, object_id: str):
        keys = self._rs.GetUserText(object_id)
        if not keys:
            return ()
        return tuple(str(item) for item in keys)

    def set_object_user_text(self, object_id: str, key: str, value: str) -> None:
        if value in (None, ""):
            self._rs.SetUserText(object_id, key)
            return
        self._rs.SetUserText(object_id, key, value)

    def redraw(self) -> None:
        self._rs.Redraw()

    def objects_on_layer(self, path: str):
        if not self.has_layer(path):
            return ()
        try:
            ids = self._rs.ObjectsByLayer(path) or []
        except ValueError:
            return ()
        return tuple(str(item) for item in ids)

    def add_placeholder(self, *, layer: str, name: str) -> str:
        point_id = self._rs.AddPoint((0, 0, 0))
        object_id = str(point_id)
        self._rs.ObjectLayer(object_id, layer)
        self._rs.ObjectName(object_id, name)
        return object_id

    def delete_object(self, object_id: str) -> None:
        self._rs.DeleteObject(object_id)

    def is_point(self, object_id: str) -> bool:
        return bool(self._rs.IsPoint(object_id))

    def point_xyz(self, object_id: str):
        if not self.is_point(object_id):
            return None
        point = self._rs.PointCoordinates(object_id)
        if not point:
            return None
        return (float(point[0]), float(point[1]), float(point[2]))

    def layout_page_name_of(self, object_id: str) -> Optional[str]:
        obj = self._rhino_object(object_id)
        if obj is None:
            return None
        viewport_id = obj.Attributes.ViewportId
        try:
            import System  # type: ignore

            if viewport_id == System.Guid.Empty:
                return None
        except Exception:
            pass
        for page in self._ordered_page_views():
            if viewport_id in self._layout_viewport_ids(page):
                name = str(getattr(page, "PageName", "") or "")
                return name or None
        return None

    def add_text(
        self,
        content: str,
        point,
        *,
        layer: str,
        page_name: Optional[str] = None,
        height: float = 1.0,
        font: Optional[str] = None,
    ) -> str:
        xyz = (
            float(point[0]),
            float(point[1]),
            float(point[2]) if point is not None and len(point) > 2 else 0.0,
        )
        font_name = str(font or "Arial")
        text_id = self._rs.AddText(
            str(content),
            xyz,
            float(height),
            font_name,
            0,
            1 | 65536,  # Left + Bottom，左下角對齊定位點
        )
        if not text_id:
            raise RuntimeError("無法建立目錄文字")
        object_id = str(text_id)
        if layer:
            self.ensure_layer(layer)
            self.set_object_layer(object_id, layer)
        self._set_text_origin(object_id, xyz)
        if page_name:
            page = self._page_view(page_name)
            obj = self._rhino_object(object_id)
            if page is not None and obj is not None:
                obj.Attributes.ViewportId = page.MainViewport.Id
                try:
                    obj.Attributes.Space = self._rhino.DocObjects.ActiveSpace.PageSpace
                except Exception:
                    pass
                obj.CommitChanges()
        return object_id

    def _set_text_origin(self, object_id: str, origin) -> None:
        obj = self._rhino_object(object_id)
        geom = getattr(obj, "Geometry", None) if obj is not None else None
        if geom is None or self._rhino is None:
            return
        try:
            plane = geom.Plane
            plane.Origin = self._rhino.Geometry.Point3d(
                float(origin[0]),
                float(origin[1]),
                float(origin[2]) if origin is not None and len(origin) > 2 else 0.0,
            )
            geom.Plane = plane
            geom.Justification = self._rhino.Geometry.TextJustification.BottomLeft
            self._sc.doc.Objects.Replace(obj.Id, geom)
        except Exception:
            pass

    def update_text(self, object_id: str, content: str, origin=None) -> bool:
        obj = self._rhino_object(object_id)
        geom = getattr(obj, "Geometry", None) if obj is not None else None
        if geom is None:
            return False
        try:
            if hasattr(geom, "PlainText"):
                geom.PlainText = str(content)
            elif hasattr(geom, "Text"):
                geom.Text = str(content)
            else:
                return False
            if origin is not None:
                plane = geom.Plane
                plane.Origin = self._rhino.Geometry.Point3d(
                    float(origin[0]),
                    float(origin[1]),
                    float(origin[2]) if len(origin) > 2 else 0.0,
                )
                geom.Plane = plane
                try:
                    geom.Justification = self._rhino.Geometry.TextJustification.BottomLeft
                except Exception:
                    pass
            return bool(self._sc.doc.Objects.Replace(obj.Id, geom))
        except Exception:
            return False

    def text_font(self, object_id: str) -> Optional[str]:
        try:
            value = self._rs.TextObjectFont(object_id)
            if value not in (None, ""):
                return str(value)
        except Exception:
            pass
        obj = self._rhino_object(object_id)
        geom = getattr(obj, "Geometry", None) if obj is not None else None
        font = getattr(geom, "Font", None)
        for attr in ("FaceName", "FamilyName", "LogfontName"):
            value = getattr(font, attr, None)
            if value not in (None, ""):
                return str(value)
        return None

    def set_text_font(self, object_id: str, font: str) -> None:
        name = str(font or "").strip()
        if not name:
            return
        try:
            self._rs.TextObjectFont(object_id, name)
        except Exception:
            pass

    def text_height(self, object_id: str) -> Optional[float]:
        try:
            value = self._rs.TextObjectHeight(object_id)
            if value is not None:
                return float(value)
        except Exception:
            pass
        obj = self._rhino_object(object_id)
        geom = getattr(obj, "Geometry", None) if obj is not None else None
        for attr in ("TextHeight", "Height"):
            value = getattr(geom, attr, None)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    continue
        return None

    def set_text_height(self, object_id: str, height: float) -> None:
        try:
            self._rs.TextObjectHeight(object_id, float(height))
        except Exception:
            pass

    def document_path(self) -> Optional[str]:
        path = getattr(self._sc.doc, "Path", None) or ""
        return str(path) if path else None

    def is_closed_curve(self, object_id: str) -> bool:
        return bool(self._rs.IsCurve(object_id) and self._rs.IsCurveClosed(object_id))

    def curve_polygon(self, object_id: str):
        rs = self._rs
        if not rs.IsCurve(object_id):
            return None
        points = []
        curve = None
        try:
            curve = rs.coercecurve(object_id)
        except Exception:
            curve = None
        if curve is not None:
            try:
                ok, polyline = curve.TryGetPolyline()
                if ok and polyline:
                    points = [_xy_point(pt) for pt in polyline]
            except Exception:
                points = []
            if len([pt for pt in points if pt is not None]) < 3:
                try:
                    params = curve.DivideByCount(32, True)
                    if params:
                        points = [_xy_point(curve.PointAt(t)) for t in params]
                except Exception:
                    points = []
        if len([pt for pt in points if pt is not None]) < 3:
            raw = rs.CurvePoints(object_id) or []
            points = [_xy_point(pt) for pt in raw]
        cleaned = tuple(pt for pt in points if pt is not None)
        if len(cleaned) < 3:
            return None
        return cleaned

    def curve_elevation(self, object_id: str):
        rs = self._rs
        if not rs.IsCurve(object_id):
            return None
        point = None
        try:
            point = rs.CurveStartPoint(object_id)
        except Exception:
            point = None
        if point is None:
            raw = rs.CurvePoints(object_id) or []
            if not raw:
                return None
            point = raw[0]
        try:
            return float(point.Z)
        except AttributeError:
            try:
                return float(point[2])
            except (TypeError, IndexError, ValueError):
                return None

    def is_model_object(self, object_id: str) -> bool:
        rs = self._rs
        if not rs.IsObject(object_id):
            return False
        name = rs.ObjectName(object_id) or ""
        if str(name).startswith("DNA_REF_"):
            return False
        try:
            type_value = int(rs.ObjectType(object_id))
        except (TypeError, ValueError, AttributeError):
            return False
        return type_value in MODEL_OBJECT_TYPE_VALUES

    def object_bbox(self, object_id: str):
        try:
            box = self._rs.BoundingBox(object_id)
        except Exception:
            return None
        if not box:
            return None
        xs = [float(pt.X) for pt in box]
        ys = [float(pt.Y) for pt in box]
        zs = [float(pt.Z) for pt in box]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def is_block_instance(self, object_id: str) -> bool:
        return bool(self._rs.IsBlockInstance(object_id))

    def block_definition_name(self, object_id: str) -> Optional[str]:
        if not self._rs.IsBlockInstance(object_id):
            return None
        value = self._rs.BlockInstanceName(object_id)
        if value in (None, ""):
            return None
        return str(value)

    def insertion_point(self, object_id: str):
        if not self._rs.IsBlockInstance(object_id):
            return None
        point = self._rs.BlockInstanceInsertPoint(object_id)
        if point is None:
            return None
        return (float(point.X), float(point.Y), float(point.Z))

    def _rhino_object(self, object_id: str):
        rhino = self._rhino
        if rhino is None:
            return None
        try:
            guid = self._rs.coerceguid(object_id)
        except Exception:
            return None
        try:
            return self._sc.doc.Objects.FindId(guid)
        except Exception:
            return None

    def _iter_rhino_objects(self, *, include_linked: bool = True):
        rhino = self._rhino
        if rhino is None:
            return ()
        settings = rhino.DocObjects.ObjectEnumeratorSettings()
        settings.NormalObjects = True
        settings.LockedObjects = True
        settings.HiddenObjects = True
        settings.ReferenceObjects = bool(include_linked)
        try:
            return tuple(self._sc.doc.Objects.GetObjectList(settings))
        except Exception:
            return ()

    def is_text_dot(self, object_id: str) -> bool:
        try:
            return bool(self._rs.IsTextDot(object_id))
        except Exception:
            return False

    def text_dot_text(self, object_id: str) -> Optional[str]:
        if not self.is_text_dot(object_id):
            return None
        try:
            value = self._rs.TextDotText(object_id)
        except Exception:
            return None
        if value in (None, ""):
            return None
        text = str(value).strip()
        return text or None

    def is_clipping_plane(self, object_id: str) -> bool:
        rhino = self._rhino
        obj = self._rhino_object(object_id)
        if rhino is None or obj is None:
            return False
        return isinstance(obj.Geometry, rhino.Geometry.ClippingPlaneSurface)

    def iter_clipping_plane_ids(self):
        rhino = self._rhino
        if rhino is None:
            return ()
        ids = []
        for obj in self._iter_rhino_objects(include_linked=True):
            if isinstance(getattr(obj, "Geometry", None), rhino.Geometry.ClippingPlaneSurface):
                ids.append(str(obj.Id))
        return tuple(ids)

    def clipping_plane_plane(self, object_id: str):
        obj = self._rhino_object(object_id)
        geom = getattr(obj, "Geometry", None) if obj is not None else None
        plane = getattr(geom, "Plane", None)
        if plane is None:
            return None
        origin = plane.Origin
        x_axis = plane.XAxis
        y_axis = plane.YAxis
        z_axis = plane.ZAxis
        return {
            "origin": (float(origin.X), float(origin.Y), float(origin.Z)),
            "x_axis": (float(x_axis.X), float(x_axis.Y), float(x_axis.Z)),
            "y_axis": (float(y_axis.X), float(y_axis.Y), float(y_axis.Z)),
            "z_axis": (float(z_axis.X), float(z_axis.Y), float(z_axis.Z)),
        }

    def _object_uuid_text(self, obj):
        if obj is None:
            return None
        try:
            attrs = obj.Attributes
        except Exception:
            return None
        for key in ("_07_UUID", "_12_UUID", "lf_object_id"):
            try:
                value = attrs.GetUserString(key)
            except Exception:
                value = None
            if value and str(value).strip():
                return str(value).strip()
        return None

    def _object_layer_path(self, obj):
        try:
            layer_index = getattr(obj.Attributes, "LayerIndex", -1)
            if layer_index >= 0:
                layer = self._sc.doc.Layers[layer_index]
                return str(layer.FullPath or layer.Name or "")
        except Exception:
            return ""
        return ""

    def uuid_objects_bbox_center(self):
        """帶 UUID 的 3D 模型 bbox 中心（含 worksession；不含剖面／Extract 線稿）。"""
        xs, ys, zs = [], [], []
        for obj in self._iter_rhino_objects(include_linked=True):
            if not self._object_uuid_text(obj):
                continue
            if is_section_or_extract_layer(self._object_layer_path(obj)):
                continue
            geom = getattr(obj, "Geometry", None)
            if geom is None:
                continue
            try:
                box = geom.GetBoundingBox(True)
            except Exception:
                continue
            if box is None or not getattr(box, "IsValid", False):
                continue
            xs.extend((float(box.Min.X), float(box.Max.X)))
            ys.extend((float(box.Min.Y), float(box.Max.Y)))
            zs.extend((float(box.Min.Z), float(box.Max.Z)))
        if not xs:
            return None
        return (
            (min(xs) + max(xs)) * 0.5,
            (min(ys) + max(ys)) * 0.5,
            (min(zs) + max(zs)) * 0.5,
        )

    def _breps_from_obj(self, obj, xform=None):
        rhino = self._rhino
        if rhino is None or obj is None:
            return []
        if xform is None:
            xform = rhino.Geometry.Transform.Identity
        breps = []
        geom = obj.Geometry if hasattr(obj, "Geometry") else obj
        if isinstance(geom, rhino.Geometry.Brep):
            brep = geom.Duplicate()
            brep.Transform(xform)
            breps.append(brep)
        elif isinstance(geom, rhino.Geometry.Extrusion):
            brep = geom.ToBrep(False)
            if brep:
                brep.Transform(xform)
                breps.append(brep)
        elif isinstance(geom, rhino.Geometry.ClippingPlaneSurface):
            pass
        elif isinstance(geom, rhino.Geometry.Surface):
            brep = None
            try:
                brep = geom.ToBrep()
            except Exception:
                brep = None
            if brep:
                brep.Transform(xform)
                breps.append(brep)
        elif isinstance(obj, rhino.DocObjects.InstanceObject):
            definition = obj.InstanceDefinition
            if definition:
                nested = xform * obj.InstanceXform
                for child in definition.GetObjects():
                    breps.extend(self._breps_from_obj(child, nested))
        return breps

    def _meshes_from_obj(self, obj, xform=None):
        rhino = self._rhino
        if rhino is None or obj is None:
            return []
        if xform is None:
            xform = rhino.Geometry.Transform.Identity
        meshes = []
        geom = obj.Geometry if hasattr(obj, "Geometry") else obj
        if isinstance(geom, rhino.Geometry.Mesh):
            mesh = geom.Duplicate()
            mesh.Transform(xform)
            meshes.append(mesh)
        elif hasattr(rhino.Geometry, "SubD") and isinstance(geom, rhino.Geometry.SubD):
            mesh = None
            try:
                create = getattr(rhino.Geometry.Mesh, "CreateFromSubD", None)
                if callable(create):
                    mesh = create(geom, 0)
                elif hasattr(geom, "ToMesh"):
                    mesh = geom.ToMesh()
            except Exception:
                mesh = None
            if mesh:
                mesh.Transform(xform)
                meshes.append(mesh)
        elif isinstance(obj, rhino.DocObjects.InstanceObject):
            definition = obj.InstanceDefinition
            if definition:
                nested = xform * obj.InstanceXform
                for child in definition.GetObjects():
                    meshes.extend(self._meshes_from_obj(child, nested))
        return meshes

    def clipping_plane_section_bbox_local(self, object_id: str):
        """把 3D 模型與 CP 的交線轉到 CP 局部座標，回傳 2D bbox。"""
        rhino = self._rhino
        obj = self._rhino_object(object_id)
        geom = getattr(obj, "Geometry", None) if obj is not None else None
        if rhino is None or not isinstance(geom, rhino.Geometry.ClippingPlaneSurface):
            return None
        cp_plane = geom.Plane
        to_local = rhino.Geometry.Transform.ChangeBasis(rhino.Geometry.Plane.WorldXY, cp_plane)
        box = rhino.Geometry.BoundingBox.Empty
        tol = self._sc.doc.ModelAbsoluteTolerance
        for item in self._iter_rhino_objects(include_linked=True):
            if getattr(item, "IsHidden", False):
                continue
            if is_section_or_extract_layer(self._object_layer_path(item)):
                continue
            layer_index = getattr(item.Attributes, "LayerIndex", -1)
            if layer_index >= 0 and not self._sc.doc.Layers[layer_index].IsVisible:
                continue
            for brep in self._breps_from_obj(item):
                try:
                    success, curves, _pts = rhino.Geometry.Intersect.Intersection.BrepPlane(
                        brep, cp_plane, tol
                    )
                except Exception:
                    continue
                if not success or not curves:
                    continue
                for curve in curves:
                    curve.Transform(to_local)
                    box.Union(curve.GetBoundingBox(True))
            for mesh in self._meshes_from_obj(item):
                try:
                    polylines = rhino.Geometry.Intersect.Intersection.MeshPlane(mesh, cp_plane)
                except Exception:
                    continue
                if not polylines:
                    continue
                for polyline in polylines:
                    try:
                        for index in range(len(polyline)):
                            point = rhino.Geometry.Point3d(polyline[index])
                            point.Transform(to_local)
                            box.Union(point)
                    except Exception:
                        continue
        if not box.IsValid:
            return None
        return (
            float(box.Min.X),
            float(box.Min.Y),
            float(box.Max.X),
            float(box.Max.Y),
            float(box.Min.Z),
            float(box.Max.Z),
        )

    def drawing_content_bbox(self, frame_id: str):
        """框內剖面 Hatch／Curve 的 bbox。不含外框、文字、標註，也不含 Visible 背景。"""
        rhino = self._rhino
        frame_box = self.object_bbox(frame_id)
        if rhino is None or not frame_box:
            return None
        cut_box = rhino.Geometry.BoundingBox.Empty
        hatch_box = rhino.Geometry.BoundingBox.Empty
        curve_box = rhino.Geometry.BoundingBox.Empty
        annotation = getattr(rhino.Geometry, "AnnotationBase", None)
        for item in self._iter_rhino_objects(include_linked=False):
            if str(item.Id) == str(frame_id):
                continue
            if getattr(item, "IsReference", False):
                continue
            geom = getattr(item, "Geometry", None)
            if geom is None:
                continue
            if isinstance(geom, (rhino.Geometry.TextEntity, rhino.Geometry.TextDot)):
                continue
            if annotation is not None and isinstance(geom, annotation):
                continue
            is_hatch = isinstance(geom, rhino.Geometry.Hatch)
            is_curve = isinstance(geom, rhino.Geometry.Curve)
            if not is_hatch and not is_curve:
                continue
            path = self._object_layer_path(item)
            terminal = str(path or "").rsplit("::", 1)[-1].upper()
            if "VISIBLE" in terminal:
                continue
            try:
                item_box = geom.GetBoundingBox(True)
            except Exception:
                continue
            if item_box is None or not getattr(item_box, "IsValid", False):
                continue
            center = item_box.Center
            if not (
                frame_box[0] - 1e-9 <= float(center.X) <= frame_box[3] + 1e-9
                and frame_box[1] - 1e-9 <= float(center.Y) <= frame_box[4] + 1e-9
            ):
                continue
            if is_section_cut_layer(path):
                cut_box.Union(item_box)
            if is_hatch:
                hatch_box.Union(item_box)
            else:
                curve_box.Union(item_box)
        chosen = cut_box if cut_box.IsValid else (hatch_box if hatch_box.IsValid else curve_box)
        if not chosen.IsValid:
            return None
        return (
            float(chosen.Min.X),
            float(chosen.Min.Y),
            float(chosen.Min.Z),
            float(chosen.Max.X),
            float(chosen.Max.Y),
            float(chosen.Max.Z),
        )

    def objects_bbox(self, object_ids):
        ids = [item for item in object_ids if item]
        if not ids:
            return None
        try:
            box = self._rs.BoundingBox(list(ids))
        except Exception:
            box = None
        if not box:
            boxes = []
            for object_id in ids:
                item = self.object_bbox(object_id)
                if item:
                    boxes.append(item)
            if not boxes:
                return None
            return (
                min(item[0] for item in boxes),
                min(item[1] for item in boxes),
                min(item[2] for item in boxes),
                max(item[3] for item in boxes),
                max(item[4] for item in boxes),
                max(item[5] for item in boxes),
            )
        xs = [float(pt.X) for pt in box]
        ys = [float(pt.Y) for pt in box]
        zs = [float(pt.Z) for pt in box]
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def add_closed_polyline(self, points, *, layer: str, name: str) -> str:
        pts = [tuple(pt) for pt in points]
        if len(pts) < 3:
            raise ValueError("封閉框至少需要 3 點")
        if pts[0] != pts[-1]:
            pts = pts + [pts[0]]
        object_id = str(self._rs.AddPolyline(pts))
        self.ensure_layer(layer)
        self._rs.ObjectLayer(object_id, layer)
        self._rs.ObjectName(object_id, name)
        self._rs.ObjectColorSource(object_id, COLOR_SOURCE_BY_LAYER)
        try:
            self._rs.ObjectPrintWidthSource(object_id, 0)
            self._rs.ObjectPrintColorSource(object_id, 0)
        except Exception:
            pass
        return object_id

    def _first_model_view(self):
        rhino = self._rhino
        if rhino is None:
            return None
        for view in self._sc.doc.Views:
            if not isinstance(view, rhino.Display.RhinoPageView):
                return view
        return None

    def _enter_model_space_for_add(self):
        """Layout 上 Add 一定進圖紙，Space 屬性無效。暫時進 Detail 或模型視圖；回傳還原函式。"""
        rhino = self._rhino
        doc = self._sc.doc
        previous = doc.Views.ActiveView
        if rhino is None or not isinstance(previous, rhino.Display.RhinoPageView):
            return lambda: None
        page = previous
        details = tuple(page.GetDetailViews() or ())
        if details:
            page.SetActiveDetail(details[0].Id)

            def restore_detail() -> None:
                page.SetPageAsActive()

            return restore_detail
        model_view = self._first_model_view()
        if model_view is None:
            return lambda: None
        doc.Views.ActiveView = model_view

        def restore_view() -> None:
            doc.Views.ActiveView = previous
            page.SetPageAsActive()

        return restore_view

    def draw_laser_debug_ray(self, plane_point, start, end) -> None:
        """測試用：清掉舊線後，把射線畫進 3D 模型空間（不要畫在 Layout 上）。"""
        rhino = self._rhino
        layer = "LoopFlow::Debug_Laser"
        self.ensure_layer(layer)
        self.set_layer_appearance(layer, (255, 0, 255))
        if rhino is None:
            return
        layer_index = self._layer_index(layer)
        if layer_index < 0:
            return
        layer_obj = self._sc.doc.Layers[layer_index]
        try:
            old_objects = self._sc.doc.Objects.FindByLayer(layer_obj) or ()
        except Exception:
            old_objects = ()
        for obj in tuple(old_objects):
            try:
                self._sc.doc.Objects.Delete(obj, True)
            except Exception:
                pass

        def _model_attrs(name):
            attrs = rhino.DocObjects.ObjectAttributes()
            attrs.LayerIndex = layer_index
            attrs.Name = name
            attrs.ColorSource = rhino.DocObjects.ObjectColorSource.ColorFromLayer
            try:
                attrs.Space = rhino.DocObjects.ActiveSpace.ModelSpace
            except Exception:
                pass
            return attrs

        start_pt = rhino.Geometry.Point3d(float(start[0]), float(start[1]), float(start[2]))
        end_pt = rhino.Geometry.Point3d(float(end[0]), float(end[1]), float(end[2]))
        plane_pt = rhino.Geometry.Point3d(
            float(plane_point[0]), float(plane_point[1]), float(plane_point[2])
        )
        restore = lambda: None
        try:
            self.set_redraw_enabled(False)
            restore = self._enter_model_space_for_add()
            self._sc.doc.Objects.AddLine(start_pt, end_pt, _model_attrs("Laser_Ray"))
            self._sc.doc.Objects.AddPoint(plane_pt, _model_attrs("Laser_Plane"))
        finally:
            try:
                restore()
            except Exception:
                pass
            self.set_redraw_enabled(True)
            try:
                self._sc.doc.Views.Redraw()
            except Exception:
                pass

    def _hit_normal(self, breps, hit_pt):
        rhino = self._rhino
        closest = float("inf")
        best = None
        if rhino is None:
            return None
        for brep in breps:
            try:
                for face in brep.Faces:
                    success, u, v = face.ClosestPoint(hit_pt)
                    if not success:
                        continue
                    closest_pt = face.PointAt(u, v)
                    dist = closest_pt.DistanceTo(hit_pt)
                    if dist < closest:
                        closest = dist
                        best = face.NormalAt(u, v)
            except Exception:
                continue
        return best

    def _mesh_hit_normal(self, mesh, hit_pt):
        if mesh is None or hit_pt is None:
            return None
        try:
            mp = mesh.ClosestMeshPoint(hit_pt, 0.0)
        except Exception:
            mp = None
        if mp is None:
            return None
        try:
            normals = mesh.FaceNormals
            if getattr(normals, "Count", 0) == 0:
                mesh.FaceNormals.ComputeFaceNormals()
                normals = mesh.FaceNormals
            return normals[mp.FaceIndex]
        except Exception:
            return None

    def _hit_type_from_normal(self, ray, normal):
        hit_type = "GRAZING"
        if normal is None:
            return hit_type
        try:
            dot_val = ray.Direction * normal
        except Exception:
            dot_val = 0.0
        if dot_val < -0.5:
            return "FRONTAL"
        if dot_val > 0.5:
            return "BACKFACE"
        return hit_type

    def shoot_ray_hits(self, origin, direction):
        """沿方向射線，回傳帶 UUID 的命中（含 worksession 連結檔）。"""
        rhino = self._rhino
        if rhino is None:
            return ()
        ray = rhino.Geometry.Ray3d(
            rhino.Geometry.Point3d(float(origin[0]), float(origin[1]), float(origin[2])),
            rhino.Geometry.Vector3d(float(direction[0]), float(direction[1]), float(direction[2])),
        )
        hits = []
        for obj in self._iter_rhino_objects(include_linked=True):
            if getattr(obj, "IsHidden", False):
                continue
            layer_index = getattr(obj.Attributes, "LayerIndex", -1)
            if layer_index >= 0 and not self._sc.doc.Layers[layer_index].IsVisible:
                continue
            object_id = str(obj.Id)
            if not self._object_uuid_text(obj):
                continue
            hit_pt = None
            normal = None
            breps = self._breps_from_obj(obj)
            if breps:
                try:
                    shot = rhino.Geometry.Intersect.Intersection.RayShoot(ray, breps, 1)
                except Exception:
                    shot = None
                if shot:
                    hit_pt = shot[0]
                    normal = self._hit_normal(breps, hit_pt)
            if hit_pt is None:
                for mesh in self._meshes_from_obj(obj):
                    try:
                        t = rhino.Geometry.Intersect.Intersection.MeshRay(mesh, ray)
                    except Exception:
                        t = -1.0
                    if t is None or float(t) < 0:
                        continue
                    hit_pt = ray.PointAt(float(t))
                    normal = self._mesh_hit_normal(mesh, hit_pt)
                    break
            if hit_pt is None:
                continue
            dist = rhino.Geometry.Point3d(
                float(origin[0]), float(origin[1]), float(origin[2])
            ).DistanceTo(hit_pt)
            hit_type = self._hit_type_from_normal(ray, normal)
            layer = ""
            if layer_index >= 0:
                try:
                    layer = str(self._sc.doc.Layers[layer_index].FullPath or self._sc.doc.Layers[layer_index].Name)
                except Exception:
                    layer = ""
            name = ""
            try:
                name = str(obj.Attributes.Name or "")
            except Exception:
                name = ""
            hits.append(
                {
                    "object_id": object_id,
                    "dist": float(dist),
                    "hit_type": hit_type,
                    "layer": layer,
                    "name": name,
                }
            )
        return tuple(hits)

    def is_layout_active(self) -> bool:
        rhino = self._rhino
        if rhino is None:
            return False
        view = self._sc.doc.Views.ActiveView
        return isinstance(view, rhino.Display.RhinoPageView)

    def current_layout_page_name(self):
        rhino = self._rhino
        if rhino is None:
            return None
        view = self._sc.doc.Views.ActiveView
        if not isinstance(view, rhino.Display.RhinoPageView):
            return None
        name = str(getattr(view, "PageName", None) or "").strip()
        return name or None

    def listed_layout_details(self):
        rhino = self._rhino
        if rhino is None:
            return ()
        items = []
        for page in self._ordered_page_views():
            details = page.GetDetailViews() or ()
            for detail in details:
                name = getattr(detail, "Name", None)
                items.append(
                    {
                        "layout": str(getattr(page, "PageName", None) or ""),
                        "page_number": int(getattr(page, "PageNumber", 0) or 0),
                        "detail_id": str(detail.Id),
                        "dv_name": str(name or ""),
                    }
                )
        return tuple(items)

    def _ordered_page_views(self):
        pages = self._sc.doc.Views.GetPageViews() or ()
        return sorted(pages, key=lambda page: int(getattr(page, "PageNumber", 0) or 0))

    def _page_view(self, page_name: str):
        target = str(page_name or "")
        for page in self._ordered_page_views():
            if str(getattr(page, "PageName", "") or "") == target:
                return page
        return None

    def listed_layout_pages(self):
        if self._rhino is None:
            return ()
        return tuple(
            {
                "name": str(getattr(page, "PageName", None) or ""),
                "page_number": int(getattr(page, "PageNumber", 0) or 0),
            }
            for page in self._ordered_page_views()
        )

    def _layout_viewport_ids(self, page):
        """紙空間＋此頁所有 Detail 視窗。標在圖上的 Tag 屬於 Detail，不是頁 MainViewport。"""
        ids = set()
        for attr in ("Id",):
            pid = getattr(page, attr, None)
            if pid is not None:
                ids.add(pid)
        try:
            ids.add(page.MainViewport.Id)
        except Exception:
            pass
        try:
            ids.add(page.ActiveViewport.Id)
        except Exception:
            pass
        details = ()
        try:
            details = page.GetDetailViews() or ()
        except Exception:
            details = ()
        for detail in details:
            for attr in ("Viewport", "MainViewport"):
                viewport = getattr(detail, attr, None)
                if viewport is None:
                    continue
                vid = getattr(viewport, "Id", None)
                if vid is not None:
                    ids.add(vid)
            did = getattr(detail, "Id", None)
            if did is not None:
                ids.add(did)
        return ids

    def objects_on_layout_page(self, page_name: str):
        if self._rhino is None:
            return ()
        page = self._page_view(page_name)
        if page is None:
            return ()
        viewport_ids = self._layout_viewport_ids(page)
        try:
            import System  # type: ignore

            viewport_ids.discard(System.Guid.Empty)
        except Exception:
            pass
        page_space = getattr(
            getattr(self._rhino, "DocObjects", None), "ActiveSpace", None
        )
        page_space = getattr(page_space, "PageSpace", None)
        ids = []
        seen = set()

        def add(obj) -> None:
            if obj is None:
                return
            try:
                if page_space is not None:
                    space = obj.Attributes.Space
                    if space is not None and space != page_space:
                        return
            except Exception:
                pass
            try:
                if obj.Attributes.ViewportId not in viewport_ids:
                    return
            except Exception:
                return
            key = str(obj.Id)
            if key in seen:
                return
            seen.add(key)
            ids.append(key)

        try:
            refs = self._sc.doc.Objects.FindByObjectType(
                self._rhino.DocObjects.ObjectType.InstanceReference
            )
            for obj in refs or ():
                add(obj)
        except Exception:
            pass
        for obj in self._iter_rhino_objects():
            add(obj)
        return tuple(ids)

    def paper_space_object_ids(self):
        """所有紙空間物件，含 ViewportId 為空、對不到任一 Layout 視窗者。"""
        rhino = self._rhino
        if rhino is None:
            return ()
        page_space = getattr(
            getattr(rhino, "DocObjects", None), "ActiveSpace", None
        )
        page_space = getattr(page_space, "PageSpace", None)
        ids = []
        seen = set()
        for obj in self._iter_rhino_objects(include_linked=True):
            if obj is None:
                continue
            try:
                if page_space is not None:
                    space = obj.Attributes.Space
                    if space is not None and space != page_space:
                        continue
            except Exception:
                continue
            key = str(obj.Id)
            if key in seen:
                continue
            seen.add(key)
            ids.append(key)
        return tuple(ids)

    def rename_layout_page(self, page_name: str, new_name: str) -> bool:
        if self._rhino is None:
            return False
        page = self._page_view(page_name)
        if page is None:
            return False
        target = str(new_name or "")
        if not target:
            return False
        if target == str(getattr(page, "PageName", "") or ""):
            return True
        if self._page_view(target) is not None:
            return False
        try:
            page.PageName = target
        except Exception:
            return False
        return True

    def layout_page_size(self, page_name: str):
        page = self._page_view(page_name)
        if page is None:
            return None
        try:
            return (float(page.PageWidth), float(page.PageHeight))
        except Exception:
            return None

    def add_layout_page(self, name: str, width: float, height: float):
        """新增 Layout 頁並刪掉 Rhino 預設 Detail。不使用剪貼簿。"""
        title = str(name or "").strip()
        if not title or self._page_view(title) is not None:
            return None
        try:
            page = self._sc.doc.Views.AddPageView(title, float(width), float(height))
        except Exception:
            page = None
        if page is None:
            return None
        self._delete_default_details(page)
        self._redraw_views()
        return str(getattr(page, "PageName", None) or title)

    def delete_layout_page(self, page_name: str) -> bool:
        title = str(page_name or "")
        if not title:
            return False
        try:
            deleted = self._rs.DeleteLayout(title)
        except Exception:
            deleted = False
        if deleted:
            self._redraw_views()
        return bool(deleted)

    def copy_layout_page_objects(self, source_page: str, target_page: str):
        """以 Rhino API 複製頁物件到目標頁，含 Detail 視窗對應。不碰系統剪貼簿。"""
        source = self._page_view(source_page)
        target = self._page_view(target_page)
        if source is None or target is None:
            return {}
        try:
            source_main = source.MainViewport.Id
            target_main = target.MainViewport.Id
        except Exception:
            return {}
        vp_map = {source_main: target_main}
        try:
            vp_map[source.Id] = target.Id
        except Exception:
            pass
        detail_type = getattr(getattr(self._rhino, "DocObjects", None), "DetailViewObject", None)
        source_ids = list(self.objects_on_layout_page(source_page))
        details = []
        others = []
        for object_id in source_ids:
            obj = self._rhino_object(object_id)
            if detail_type is not None and obj is not None and isinstance(obj, detail_type):
                details.append(object_id)
            else:
                others.append(object_id)
        mapping = {}
        for object_id in details:
            old_obj = self._rhino_object(object_id)
            old_vp = self._detail_viewport_guid(old_obj)
            new_id = self._duplicate_to_viewport(object_id, target_main)
            if not new_id:
                continue
            mapping[str(object_id)] = new_id
            new_obj = self._rhino_object(new_id)
            new_vp = self._detail_viewport_guid(new_obj)
            if old_vp is not None and new_vp is not None:
                vp_map[old_vp] = new_vp
            if old_obj is not None and new_obj is not None:
                try:
                    vp_map[old_obj.Id] = new_obj.Id
                except Exception:
                    pass
        for object_id in others:
            obj = self._rhino_object(object_id)
            old_vp = None
            if obj is not None:
                try:
                    old_vp = obj.Attributes.ViewportId
                except Exception:
                    old_vp = None
            new_vp = vp_map.get(old_vp, target_main)
            new_id = self._duplicate_to_viewport(object_id, new_vp)
            if new_id:
                mapping[str(object_id)] = new_id
        try:
            self._rs.UnselectAllObjects()
        except Exception:
            pass
        self._redraw_views()
        return mapping

    def _delete_default_details(self, page) -> None:
        detail_type = getattr(getattr(self._rhino, "DocObjects", None), "DetailViewObject", None)
        if page is None or detail_type is None:
            return
        try:
            page_vp = page.MainViewport.Id
        except Exception:
            return
        to_delete = []
        for obj in self._iter_rhino_objects(include_linked=False):
            if obj is None or not isinstance(obj, detail_type):
                continue
            try:
                if obj.Attributes.ViewportId != page_vp:
                    continue
            except Exception:
                continue
            to_delete.append(obj.Id)
        for oid in to_delete:
            try:
                self._sc.doc.Objects.Delete(oid, True)
            except Exception:
                pass

    def _detail_viewport_guid(self, obj):
        if obj is None:
            return None
        for name in ("Viewport", "MainViewport"):
            viewport = getattr(obj, name, None)
            if viewport is None:
                continue
            vid = getattr(viewport, "Id", None)
            if vid is not None:
                return vid
        return None

    def _duplicate_to_viewport(self, object_id: str, viewport_id):
        copied = self._rs.CopyObject(object_id)
        if not copied:
            return None
        obj = self._rhino_object(copied)
        if obj is None or viewport_id is None:
            return str(copied)
        try:
            obj.Attributes.ViewportId = viewport_id
            space = getattr(getattr(self._rhino, "DocObjects", None), "ActiveSpace", None)
            page_space = getattr(space, "PageSpace", None)
            if page_space is not None:
                obj.Attributes.Space = page_space
            obj.CommitChanges()
        except Exception:
            pass
        return str(copied)

    def detail_model_point(self, detail_id: str):
        obj = self._rhino_object(detail_id)
        if obj is None:
            return None
        geom = getattr(obj, "Geometry", None)
        try:
            box = geom.GetBoundingBox(True) if geom is not None else None
        except Exception:
            box = None
        if box is not None:
            try:
                center = box.Center
                xform = getattr(obj, "PageToWorldTransform", None)
                if xform is not None:
                    center.Transform(xform)
                return (float(center.X), float(center.Y), float(center.Z))
            except Exception:
                pass
        viewport = getattr(obj, "Viewport", None)
        target = getattr(viewport, "CameraTarget", None) if viewport is not None else None
        if target is None:
            return None
        try:
            return (float(target.X), float(target.Y), float(target.Z))
        except Exception:
            return None

    def zoom_to_layout_detail(self, layout: str, detail_id: str) -> None:
        rhino = self._rhino
        if rhino is None or not detail_id:
            return
        page = self._page_view(layout)
        if page is None:
            return
        self._sc.doc.Views.ActiveView = page
        page.SetPageAsActive()
        try:
            self._rs.UnselectAllObjects()
            self._rs.SelectObject(detail_id)
            page.MainViewport.ZoomExtentsSelected()
            page.MainViewport.Magnify(0.8, False)
        except Exception:
            pass
        self._redraw_views()

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
