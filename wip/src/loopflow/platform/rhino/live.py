# -*- coding: utf-8 -*-
"""Rhino 8 live adapter。

模組載入不 import Rhino。NX-01～04 使用的 API 已在家中 Rhino 8 驗證。
"""
from __future__ import annotations

from typing import Optional, Tuple

from loopflow.foundation import results
from loopflow.platform.rhino.session import capture_snapshot, restore_snapshot
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
        elif isinstance(obj, rhino.DocObjects.InstanceObject):
            definition = obj.InstanceDefinition
            if definition:
                nested = xform * obj.InstanceXform
                for child in definition.GetObjects():
                    breps.extend(self._breps_from_obj(child, nested))
        return breps

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
            uuid_value = (
                obj.Attributes.GetUserString("_07_UUID")
                or obj.Attributes.GetUserString("_12_UUID")
                or obj.Attributes.GetUserString("lf_object_id")
            )
            if not uuid_value or not str(uuid_value).strip():
                continue
            breps = self._breps_from_obj(obj)
            if not breps:
                continue
            try:
                shot = rhino.Geometry.Intersect.Intersection.RayShoot(ray, breps, 1)
            except Exception:
                continue
            if not shot:
                continue
            hit_pt = shot[0]
            dist = rhino.Geometry.Point3d(
                float(origin[0]), float(origin[1]), float(origin[2])
            ).DistanceTo(hit_pt)
            normal = self._hit_normal(breps, hit_pt)
            hit_type = "GRAZING"
            if normal is not None:
                try:
                    dot_val = ray.Direction * normal
                except Exception:
                    dot_val = 0.0
                if dot_val < -0.5:
                    hit_type = "FRONTAL"
                elif dot_val > 0.5:
                    hit_type = "BACKFACE"
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

    def listed_layout_details(self):
        rhino = self._rhino
        if rhino is None:
            return ()
        items = []
        pages = self._sc.doc.Views.GetPageViews() or ()
        ordered = sorted(pages, key=lambda page: int(getattr(page, "PageNumber", 0) or 0))
        for page in ordered:
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
        page_name = str(layout or "")
        for page in self._sc.doc.Views.GetPageViews() or ():
            if str(getattr(page, "PageName", "") or "") != page_name:
                continue
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
            return

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
