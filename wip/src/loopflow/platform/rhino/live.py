# -*- coding: utf-8 -*-
"""Rhino 8 live adapter。

模組載入不 import Rhino。NX-01～04 使用的 API 已在家中 Rhino 8 驗證。
"""
from __future__ import annotations

from typing import Optional, Tuple

from loopflow.features.dimension.frame import axes_from_plane
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

    def set_layer_appearance(self, path: str, rgb, material_name: Optional[str] = None) -> None:
        if not self.has_layer(path):
            raise KeyError("未知圖層：%s" % path)
        color = rgb_tuple(rgb)
        self._rs.LayerColor(path, color)
        if not material_name or self._rhino is None:
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
        if mat_idx >= 0 and legacy_name:
            try:
                material = self._sc.doc.Materials[mat_idx]
                if material.Name != material_name:
                    material.Name = material_name
                    self._sc.doc.Materials.Modify(material, mat_idx, True)
            except Exception:
                pass
        if mat_idx == -1:
            new_mat = self._rhino.DocObjects.Material()
            new_mat.Name = material_name
            try:
                new_mat.DiffuseColor = sys_color
                new_mat.ToPhysicallyBased()
                new_mat.PhysicallyBased.BaseColor = self._rhino.Display.Color4f(sys_color)
            except Exception:
                pass
            mat_idx = self._sc.doc.Materials.Add(new_mat)
        layer.RenderMaterialIndex = mat_idx
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

    def insertion_point(self, object_id: str):
        if not self._rs.IsBlockInstance(object_id):
            return None
        point = self._rs.BlockInstanceInsertPoint(object_id)
        if point is None:
            return None
        return (float(point.X), float(point.Y), float(point.Z))

    def geometry_kind(self, object_id: str):
        rs = self._rs
        if not rs.IsObject(object_id):
            return None
        if rs.IsBlockInstance(object_id):
            return "block_instance"
        try:
            type_value = int(rs.ObjectType(object_id))
        except (TypeError, ValueError, AttributeError):
            return None
        if type_value == 1073741824:
            return "extrusion"
        if type_value == 8:
            try:
                if rs.IsSurfacePlanar(object_id):
                    return "planar_surface"
            except Exception:
                pass
        if type_value == 16:
            try:
                brep = rs.coercebrep(object_id)
                if brep is not None and getattr(brep.Faces, "Count", 0) == 1:
                    ok, plane = brep.Faces[0].TryGetPlane()
                    if ok and plane is not None:
                        return "planar_surface"
            except Exception:
                pass
        if type_value in (8, 16) and self._try_oriented_box(object_id) is not None:
            return "oriented_box"
        if type_value in (8, 16, 32):
            return "closed_box"
        if type_value == 4:
            try:
                if rs.IsCurvePlanar(object_id):
                    return "planar_curve"
            except Exception:
                pass
        return None

    def _try_oriented_box(self, object_id: str):
        rs = self._rs
        Rhino = self._rhino
        sc = self._sc
        try:
            geom = None
            try:
                guid = rs.coerceguid(object_id)
                rhobj = sc.doc.Objects.FindId(guid)
                if rhobj is not None:
                    geom = rhobj.Geometry
            except Exception:
                geom = None
            if geom is None:
                try:
                    geom = rs.coercegeometry(object_id)
                except Exception:
                    geom = None
            box = self._box_from_geometry(geom, Rhino)
            if box is None:
                brep = None
                try:
                    brep = rs.coercebrep(object_id)
                except Exception:
                    brep = None
                box = self._box_from_geometry(brep, Rhino)
            if box is None:
                return None
            plane = getattr(box, "Plane", None)
            if plane is None:
                return None
            return axes_from_plane(
                plane.Origin,
                plane.XAxis,
                plane.YAxis,
                plane.ZAxis,
                normal_is_depth=False,
            )
        except Exception:
            return None

    def _box_from_geometry(self, geom, Rhino):
        if geom is None:
            return None
        name = type(geom).__name__
        if name == "Box" and getattr(geom, "Plane", None) is not None:
            return geom
        brep = geom
        if name != "Brep":
            to_brep = getattr(geom, "ToBrep", None)
            if to_brep is None:
                return None
            try:
                brep = to_brep() if name != "Extrusion" else to_brep(True)
            except TypeError:
                try:
                    brep = to_brep()
                except Exception:
                    return None
            except Exception:
                return None
        if brep is None:
            return None
        box = self._try_get_box(brep, Rhino)
        if box is not None:
            return box
        try:
            faces = getattr(brep.Faces, "Count", 0)
            verts = getattr(brep.Vertices, "Count", 0)
            solid = bool(getattr(brep, "IsSolid", False))
        except Exception:
            return None
        if not (solid and faces == 6 and verts == 8) or Rhino is None:
            return None
        try:
            ok, plane = brep.Faces[0].TryGetPlane()
            if not ok or plane is None:
                return None
            bbox = brep.GetBoundingBox(plane)
            if bbox is None or not getattr(bbox, "IsValid", True):
                return None
            return Rhino.Geometry.Box(plane, bbox)
        except Exception:
            return None

    def _try_get_box(self, brep, Rhino):
        try:
            result = brep.TryGetBox()
        except TypeError:
            result = None
            if Rhino is not None:
                try:
                    candidate = Rhino.Geometry.Box()
                    if brep.TryGetBox(candidate) and getattr(candidate, "IsValid", True):
                        return candidate
                except Exception:
                    result = None
        except Exception:
            result = None
        if result is None or result is False:
            return None
        if isinstance(result, tuple):
            if not result:
                return None
            if len(result) >= 2 and isinstance(result[0], bool):
                if not result[0]:
                    return None
                return result[1]
            return result[0]
        if result is True:
            return None
        if getattr(result, "Plane", None) is not None:
            return result
        return None

    def derive_local_frame(self, object_id: str):
        kind = self.geometry_kind(object_id)
        method = {
            "block_instance": "block_insertion",
            "extrusion": "extrusion_base",
            "planar_curve": "unique_plane",
            "planar_surface": "unique_plane",
            "oriented_box": "oriented_box",
        }.get(kind or "")
        if method is None:
            return None
        axes = self._frame_axes(object_id, kind)
        if axes is None:
            return None
        origin, x_axis, y_axis, z_axis = axes
        return {
            "schema_id": "loopflow.local_frame",
            "schema_version": 1,
            "origin": list(origin),
            "x_axis": list(x_axis),
            "y_axis": list(y_axis),
            "z_axis": list(z_axis),
            "derivation_method": method,
        }

    def _frame_axes(self, object_id: str, kind: str):
        rs = self._rs
        Rhino = self._rhino
        try:
            if kind == "block_instance":
                origin = rs.BlockInstanceInsertPoint(object_id)
                xform = rs.BlockInstanceXform(object_id)
                if origin is None or xform is None or Rhino is None:
                    return None
                vx = Rhino.Geometry.Vector3d(1, 0, 0)
                vy = Rhino.Geometry.Vector3d(0, 1, 0)
                vz = Rhino.Geometry.Vector3d(0, 0, 1)
                vx.Transform(xform)
                vy.Transform(xform)
                vz.Transform(xform)
                if not vx.Unitize() or not vy.Unitize() or not vz.Unitize():
                    return None
                return (
                    (float(origin.X), float(origin.Y), float(origin.Z)),
                    (float(vx.X), float(vx.Y), float(vx.Z)),
                    (float(vy.X), float(vy.Y), float(vy.Z)),
                    (float(vz.X), float(vz.Y), float(vz.Z)),
                )
            if kind == "oriented_box":
                return self._try_oriented_box(object_id)
            plane = None
            if kind == "extrusion":
                geom = rs.coercegeometry(object_id)
                if geom is not None and hasattr(geom, "GetProfilePlane"):
                    plane = geom.GetProfilePlane(0.0)
            elif kind == "planar_curve":
                plane = rs.CurvePlane(object_id)
            elif kind == "planar_surface":
                try:
                    brep = rs.coercebrep(object_id)
                    if brep is not None and getattr(brep.Faces, "Count", 0) == 1:
                        ok, plane = brep.Faces[0].TryGetPlane()
                        if not ok:
                            plane = None
                except Exception:
                    plane = None
                if plane is None:
                    try:
                        plane = rs.SurfaceFrame(object_id, (0, 0))
                    except Exception:
                        plane = None
            if plane is None:
                return None
            aligned = axes_from_plane(
                plane.Origin,
                plane.XAxis,
                plane.YAxis,
                plane.ZAxis,
                normal_is_depth=kind in ("planar_curve", "planar_surface"),
            )
            if aligned is None:
                return None
            origin, x_axis, y_axis, z_axis = aligned
            return (
                (float(origin[0]), float(origin[1]), float(origin[2])),
                (float(x_axis[0]), float(x_axis[1]), float(x_axis[2])),
                (float(y_axis[0]), float(y_axis[1]), float(y_axis[2])),
                (float(z_axis[0]), float(z_axis[1]), float(z_axis[2])),
            )
        except Exception:
            return None

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
