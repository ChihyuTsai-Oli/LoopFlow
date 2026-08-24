# -*- coding: utf-8 -*-
# Script: LF_Tagger_Laser.py (Ray-Probe Mode Tag Block Binding Tool)
# Version: v1.0
# Date: 2026-04-20
# Developer: Cursor (Claude Opus 4.7 / Sonnet 4.6)
# Environment: Rhino 8 (CPython 3.9) / Windows 10
# Synced Files: _LoopFlow_Config.py, _LF_Debug.py
# Usage: In 2D.3dm, first select a TAG_HEIGHT_* or TAG_FINISH_* tag on the Layout,
#           then click the target position inside the Detail View; the script fires a ray probe to hit a solid in 3D.3dm,
#           reads its _12_UUID, and writes it to the tag's Source_UUID field.
#           Prerequisite: Anchor Frames must exist in the 3D scene; Clipping Plane names must match Text Dots.

# ==================================================================
# Imports
# ==================================================================
import Rhino
import rhinoscriptsyntax as rs
import scriptcontext as sc

try:
    from _LoopFlow_Config import MIRROR_KEYWORDS, INVERT_Y
except Exception:
    MIRROR_KEYWORDS = ["CEILING", u"\u5929\u82b1", "RCP"]
    INVERT_Y        = True

try:
    from _LF_Debug import log_exception, DEBUG_LOG_PATH as _DEBUG_LOG_PATH
except Exception:
    log_exception  = None
    _DEBUG_LOG_PATH = "cursor_LF_debug_log.txt"

# ==================================================================
# UserText Helpers
# ==================================================================
def _get_ut_by_prefix(rh_obj, prefix, default=None):
    """依前綴搜尋物件 UserText（例如 '_04_'），避開寫死完整欄位名。
    這樣字典第二列不論是中文 `_04_ID名稱`、英文 `_04_ID Name` 或任何自訂字尾，都能抓到值。"""
    try:
        nvc = rh_obj.Attributes.GetUserStrings()
        for k in nvc.AllKeys:
            if k and k.startswith(prefix):
                v = nvc[k]
                if v is not None and str(v).strip():
                    return v
    except Exception:
        pass
    return default

# ==================================================================
# Geometry Helpers
# ==================================================================
def get_breps_from_obj(obj, xform=Rhino.Geometry.Transform.Identity):
    breps = []
    if not obj: return breps
    geom = obj.Geometry if hasattr(obj, 'Geometry') else obj
    if isinstance(geom, Rhino.Geometry.Brep):
        b = geom.Duplicate(); b.Transform(xform); breps.append(b)
    elif isinstance(geom, Rhino.Geometry.Extrusion):
        b = geom.ToBrep(False)
        if b: b.Transform(xform); breps.append(b)
    elif isinstance(obj, Rhino.DocObjects.InstanceObject):
        idef = obj.InstanceDefinition
        if idef:
            new_xform = xform * obj.InstanceXform
            for def_obj in idef.GetObjects():
                breps.extend(get_breps_from_obj(def_obj, new_xform))
    return breps

def get_hit_normal(breps, hit_pt):
    closest_dist = float('inf'); best_normal = Rhino.Geometry.Vector3d.ZAxis
    for brep in breps:
        try:
            for face in brep.Faces:
                success, u, v = face.ClosestPoint(hit_pt)
                if success:
                    cp = face.PointAt(u, v); dist = cp.DistanceTo(hit_pt)
                    if dist < closest_dist: closest_dist = dist; best_normal = face.NormalAt(u, v)
        except: pass
    return best_normal

def get_all_objects_including_linked():
    settings = Rhino.DocObjects.ObjectEnumeratorSettings()
    settings.NormalObjects = True; settings.LockedObjects = True
    settings.ReferenceObjects = True; settings.HiddenObjects = True
    return list(sc.doc.Objects.GetObjectList(settings))

def is_obj_visible(obj):
    if obj.IsHidden: return False
    lyr_idx = obj.Attributes.LayerIndex
    if lyr_idx >= 0 and not sc.doc.Layers[lyr_idx].IsVisible: return False
    return True

# ==================================================================
# Clipping Plane Ray Origin Resolver
# ==================================================================
def get_cp_ray_origin(pt_2d_model):
    all_objs = get_all_objects_including_linked()
    clipping_planes = [{"name": rs.ObjectName(o.Id).strip().upper(), "id": o.Id, "geom": o.Geometry} 
                       for o in all_objs if isinstance(o.Geometry, Rhino.Geometry.ClippingPlaneSurface) and rs.ObjectName(o.Id)]
    
    for cp in clipping_planes:
        sec_name = cp["name"]
        container_obj = next((obj for obj in all_objs if rs.ObjectName(obj.Id) and sec_name in rs.ObjectName(obj.Id).upper() and rs.IsCurveClosed(obj.Id)), None)
        if not container_obj: continue

        c_bbox = container_obj.Geometry.GetBoundingBox(True)
        if c_bbox.Min.X <= pt_2d_model.X <= c_bbox.Max.X and c_bbox.Min.Y <= pt_2d_model.Y <= c_bbox.Max.Y:
            cp_plane = cp["geom"].Plane
            xform = Rhino.Geometry.Transform.ChangeBasis(Rhino.Geometry.Plane.WorldXY, cp_plane)
            bbox_3d_local = Rhino.Geometry.BoundingBox.Empty

            tol = sc.doc.ModelAbsoluteTolerance
            for obj in all_objs:
                if not is_obj_visible(obj): continue
                if obj.ObjectType in [Rhino.DocObjects.ObjectType.Brep, Rhino.DocObjects.ObjectType.Extrusion, Rhino.DocObjects.ObjectType.InstanceReference]:
                    breps = get_breps_from_obj(obj)
                    for b in breps:
                        success, curves, pts = Rhino.Geometry.Intersect.Intersection.BrepPlane(b, cp_plane, tol)
                        if success and curves:
                            for crv in curves:
                                crv.Transform(xform)
                                bbox_3d_local.Union(crv.GetBoundingBox(True))

            if not bbox_3d_local.IsValid: continue

            h_bbox = Rhino.Geometry.BoundingBox.Empty; c_bbox_cur = Rhino.Geometry.BoundingBox.Empty
            for obj in all_objs:
                if obj.Id == container_obj.Id or isinstance(obj.Geometry, (Rhino.Geometry.TextEntity, Rhino.Geometry.Dimension)): continue
                if isinstance(obj.Geometry, (Rhino.Geometry.Curve, Rhino.Geometry.Hatch)) and not obj.IsReference:
                    obj_bbox = obj.Geometry.GetBoundingBox(True)
                    if c_bbox.Min.X <= obj_bbox.Center.X <= c_bbox.Max.X and c_bbox.Min.Y <= obj_bbox.Center.Y <= c_bbox.Max.Y:
                        if isinstance(obj.Geometry, Rhino.Geometry.Hatch): h_bbox.Union(obj_bbox)
                        else: c_bbox_cur.Union(obj_bbox)

            bbox_2d = h_bbox if h_bbox.IsValid else c_bbox_cur
            center_2d = bbox_2d.Center; center_3d_local = bbox_3d_local.Center
            is_mirror = any(k in sec_name for k in MIRROR_KEYWORDS)
            dx = (pt_2d_model.X - center_2d.X) * (-1.0 if is_mirror else 1.0)
            dy = (pt_2d_model.Y - center_2d.Y) * (-1.0 if INVERT_Y else 1.0)
            return cp_plane, cp_plane.PointAt(center_3d_local.X + dx, center_3d_local.Y + dy), sec_name

    return None, None, None

# ==================================================================
# Ray Shoot Logic
# ==================================================================
def shoot_ray_to_model(ray_origin, cp_plane):
    ray = Rhino.Geometry.Ray3d(ray_origin, cp_plane.Normal)
    hits_log = []
    all_model_objs = get_all_objects_including_linked()
    
    for obj in all_model_objs:
        if obj.ObjectType not in [Rhino.DocObjects.ObjectType.Brep, Rhino.DocObjects.ObjectType.Extrusion, Rhino.DocObjects.ObjectType.InstanceReference]:
            continue 
            
        uuid = obj.Attributes.GetUserString("_12_UUID")
        if not uuid: continue 
        
        breps = get_breps_from_obj(obj)
        if not breps: continue
        
        hits = Rhino.Geometry.Intersect.Intersection.RayShoot(ray, breps, 1)
        if hits:
            hit_pt = hits[0]; dist = ray_origin.DistanceTo(hit_pt)
            normal = get_hit_normal(breps, hit_pt)
            dot_val = ray.Direction * normal
            
            if dot_val < -0.5: h_type = "FRONTAL"   
            elif dot_val > 0.5: h_type = "BACKFACE" 
            else: h_type = "GRAZING"   
            
            layer = sc.doc.Layers[obj.Attributes.LayerIndex].Name if obj.Attributes.LayerIndex >= 0 else "Unknown"
            hits_log.append({"dist": dist, "obj": obj, "uuid": uuid, "layer": layer, "hit_type": h_type})
                
    if not hits_log: return None, []
    
    priority = {"FRONTAL": 0, "GRAZING": 1, "BACKFACE": 2}
    hits_log.sort(key=lambda x: (priority[x["hit_type"]], x["dist"]))
    return hits_log[0]["obj"], hits_log

# ==================================================================
# Binding Runner
# ==================================================================
def run_tagger_laser():
    try:
        print(u"\n" + "="*30)
        print(u"LF_Tagger_Laser v6.1 started...")
        print(u"="*30)

        page_view = sc.doc.Views.ActiveView
        if not isinstance(page_view, Rhino.Display.RhinoPageView):
            rs.MessageBox(u" Please run in Layout space!", 48)
            return

        tag_id = rs.GetObject(u"1. Select the tag to bind (Tag Block)", rs.filter.instance)
        if not tag_id:
            return

        keys = rs.GetUserText(tag_id)
        if keys:
            for k in keys:
                if "LOCK" in k.upper() or u"NoUpdate" in k:
                    val = rs.GetUserText(tag_id, k)
                    if val and val.strip().upper() == "X":
                        rs.MessageBox(u" This tag is locked (NoUpdate=X)!\n\nTo re-bind the probe, please clear that attribute value first.", 48, u"Tag Locked")
                        rs.UnselectAllObjects()
                        return

        blk_name_raw = rs.BlockInstanceName(tag_id) or ""
        blk_name = blk_name_raw.upper()
        if "GRAB" in blk_name or blk_name in ["TAG_DW", "TAG_ITEM"]:
            rs.MessageBox(u"This tag ({}) is Grab-only!\n\nPlease use 'LF_Tagger_Grab' to handle it.".format(blk_name_raw), 48, u"Wrong Script")
            rs.UnselectAllObjects()
            return

        rh_tag = sc.doc.Objects.FindId(tag_id)

        target_pt_page = rs.GetPoint(u"2. Click inside the DV (fire 3D ray probe)")
        if not target_pt_page: rs.UnselectAllObjects(); return

        detail_obj = next((d for d in page_view.GetDetailViews() if d.Geometry.GetBoundingBox(True).Contains(target_pt_page)), None)
        if not detail_obj:
            print(u" [!] Cancelled: click position is outside all Detail Views.")
            rs.UnselectAllObjects(); return

        model_pt_2d = Rhino.Geometry.Point3d(target_pt_page)
        model_pt_2d.Transform(detail_obj.PageToWorldTransform)

        print(u" Firing ray probe, searching for 3D objects...")
        cp_plane, ray_origin, sec_name = get_cp_ray_origin(model_pt_2d)

        if not cp_plane:
            rs.MessageBox(u" Cannot locate!\n\nNo matching Clipping Plane or 2D Anchor Frame found.", 48)
            rs.UnselectAllObjects(); return
    
        hit_obj, hits_log = shoot_ray_to_model(ray_origin, cp_plane)

        if not hit_obj:
            rs.MessageBox(u" Ray missed!\n\nThe ray did not hit any 3D target with a UUID.\nPlease confirm that a solid model exists behind that position.", 48)
            rs.UnselectAllObjects(); return

        valid_hits = [h for h in hits_log if h["hit_type"] == "FRONTAL"] or hits_log
        cluster = [h for h in valid_hits if h["dist"] <= valid_hits[0]["dist"] + 200.0]
        final_hit_obj = cluster[0]["obj"]
    
        if len(cluster) > 1:
            items = [u"[{}] {} (dist:{:.1f})".format(h['layer'].split('::')[-1], _get_ut_by_prefix(h['obj'], '_04_', u'Unknown'), h['dist']) for h in cluster]
            sel_str = rs.ListBox(items, u"Multiple overlapping 3D objects detected – select the annotation target:", u"Precise Lock")
            if sel_str: final_hit_obj = cluster[items.index(sel_str)]["obj"]

        hit_uuid = final_hit_obj.Attributes.GetUserString("_12_UUID")
        rh_tag.Attributes.SetUserString("Source_UUID", hit_uuid.strip())
    
        rh_tag.CommitChanges()
        sc.doc.Views.Redraw()
    
        id_name = _get_ut_by_prefix(final_hit_obj, "_04_", u"Unknown")
        id_num  = _get_ut_by_prefix(final_hit_obj, "_03_", u"Unknown")
    
        print(u" Ray probe binding successful!")
        print(u"  └─ Target: [{}] {}".format(id_num, id_name))
        print(u"  └─ UUID: {}".format(hit_uuid.strip()))

        rs.UnselectAllObjects()

    except Exception as e:
        if log_exception:
            print(log_exception(u"LF_Tagger_Laser.run_tagger_laser", e))
        rs.MessageBox(u" Laser binding encountered an unexpected error.\n\nSee debug log: {}".format(_DEBUG_LOG_PATH), 16)

if __name__ == "__main__":
    run_tagger_laser()