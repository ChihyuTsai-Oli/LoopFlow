# -*- coding: utf-8 -*-
"""LF_Extract_CP：把 Section 線稿複製成可編輯 Drawing。

依 1.x 顏色拆到 LoopFlow_Extract 子層，但辨識前次產出、寫 drawing_id
與來源索引，不靜默覆寫人工修改，也不解鎖無關圖層。
"""
from __future__ import annotations

import json
import uuid
from typing import Callable, Dict, List, Mapping, Optional, Sequence, Tuple

from loopflow.features.dictionary.layer_paths import project_id_from_session
from loopflow.features.drawing import keys as drawing_keys
from loopflow.features.infuser.reader import load_published_registry
from loopflow.features.view.keys import SCHEMA_ID_KEY as VIEW_SCHEMA_ID_KEY
from loopflow.features.view.keys import VIEW_ID_KEY, VIEW_SCHEMA_ID
from loopflow.features.view.register import is_view_host
from loopflow.foundation import results
from loopflow.foundation.usertext import OBJECT_ID_KEY, read_text
from loopflow.platform.rhino.session import EXTRACT_LAYER_ROOT, RhinoSession, run_guarded
from loopflow.features.tagger.binding import UUID_V4_RE, text

COMMAND_ID = "LF_Extract_CP"
STAGE = "extract_drawing"
ShowMessage = Callable[[str], None]
PickRoots = Callable[[RhinoSession, Sequence[str]], Optional[Sequence[str]]]
PickMode = Callable[[RhinoSession, Mapping], Optional[str]]


def _new_id() -> str:
    return str(uuid.uuid4())


def _norm(value) -> Optional[str]:
    raw = text(value)
    return raw.casefold() if raw else None


def _layer_kind(path: str) -> Optional[str]:
    terminal = str(path or "").rsplit("::", 1)[-1].upper()
    if "VISIBLE" in terminal:
        return drawing_keys.KIND_VISIBLE
    if "HATCH" in terminal:
        return drawing_keys.KIND_HATCH
    if "CURVE" in terminal:
        return drawing_keys.KIND_CURVE
    return None


def _is_extract_path(path: str) -> bool:
    text_path = str(path or "")
    return text_path == EXTRACT_LAYER_ROOT or text_path.startswith(EXTRACT_LAYER_ROOT + "::")


def listed_section_roots(session: RhinoSession) -> Tuple[str, ...]:
    roots = []
    for path in session.layer_paths():
        if _is_extract_path(path):
            continue
        if _layer_kind(path) is None:
            continue
        root = str(path).split("::", 1)[0]
        if str(root).startswith("//"):
            continue
        if root and root not in roots:
            roots.append(root)
    return tuple(roots)


def rgb_to_hex(rgb) -> str:
    values = tuple(int(item) for item in (rgb or (0, 0, 0))[:3])
    while len(values) < 3:
        values = values + (0,)
    return "#%02X%02X%02X" % values


def curve_layer_path(rgb) -> str:
    return drawing_keys.CURVE_LAYER_PREFIX + rgb_to_hex(rgb)


def target_layer_for(kind: str, rgb) -> str:
    if kind == drawing_keys.KIND_VISIBLE:
        return drawing_keys.LAYER_VISIBLE
    if kind == drawing_keys.KIND_HATCH:
        return drawing_keys.LAYER_HATCH
    return curve_layer_path(rgb)


def _parse_source_ids(raw) -> Tuple[str, ...]:
    cleaned = text(raw)
    if cleaned is None:
        return ()
    if cleaned.startswith("["):
        try:
            payload = json.loads(cleaned)
        except (TypeError, ValueError):
            payload = None
        if isinstance(payload, list):
            ids = []
            for item in payload:
                value = text(item)
                if value and value not in ids:
                    ids.append(value)
            return tuple(ids)
    return (cleaned,)


def source_object_ids(session: RhinoSession, object_id: str) -> Tuple[str, ...]:
    ids = []
    for key in (
        drawing_keys.SOURCE_OBJECT_IDS_KEY,
        "lf_source_object_id",
        OBJECT_ID_KEY,
        "SourceId",
    ):
        if key == OBJECT_ID_KEY:
            values = _parse_source_ids(read_text(session, object_id, OBJECT_ID_KEY))
        else:
            values = _parse_source_ids(session.get_object_user_text(object_id, key))
        for value in values:
            if value not in ids:
                ids.append(value)
        if ids:
            break
    extra = getattr(session, "clipping_drawing_source_ids", None)
    if callable(extra):
        for value in extra(object_id) or ():
            item = text(value)
            if item and item not in ids:
                ids.append(item)
    return tuple(ids)


def classify_sources(source_ids: Sequence[str]) -> Tuple[str, str, str]:
    unique = tuple(dict.fromkeys(text(item) for item in source_ids if text(item)))
    if not unique:
        return drawing_keys.STATE_UNINDEXED, "unindexed", drawing_keys.METHOD_LOOPFLOW
    if len(unique) == 1:
        method = (
            drawing_keys.METHOD_RHINO
            if UUID_V4_RE.match(unique[0].strip("{}").casefold())
            else drawing_keys.METHOD_LOOPFLOW
        )
        return drawing_keys.STATE_CURRENT, "indexed", method
    return drawing_keys.STATE_AMBIGUOUS, "ambiguous", drawing_keys.METHOD_LOOPFLOW


def listed_views(session: RhinoSession):
    views = []
    for object_id in session.iter_object_ids():
        schema = text(session.get_object_user_text(object_id, VIEW_SCHEMA_ID_KEY))
        if schema != VIEW_SCHEMA_ID and not is_view_host(session, object_id):
            continue
        view_id = text(session.get_object_user_text(object_id, VIEW_ID_KEY))
        if not view_id:
            continue
        views.append(
            {
                "frame_id": object_id,
                "view_id": view_id,
                "name": session.object_name(object_id) or "",
            }
        )
    return tuple(views)


def match_view_for_root(root: str, views: Sequence[Mapping]) -> results.Result:
    needle = _norm(root)
    if needle is None:
        return results.ok(STAGE, "沒有根圖層名。", details={"view": None})
    hits = [
        dict(view)
        for view in views
        if _norm(view.get("name")) == needle
    ]
    if len(hits) == 1:
        return results.ok(STAGE, "已對到 View。", details={"view": hits[0]})
    if len(hits) > 1:
        return results.blocked(
            STAGE,
            "剖面圖層「%s」對到兩個以上 View，已跳過，不猜測。" % root,
            ("ambiguous_view",),
            command_id=COMMAND_ID,
            details={"root": root},
        )
    return results.ok(STAGE, "沒有對到 View。", details={"view": None})


def is_drawing_element(session: RhinoSession, object_id: str) -> bool:
    schema = text(session.get_object_user_text(object_id, drawing_keys.SCHEMA_ID_KEY))
    return schema == drawing_keys.DRAWING_SCHEMA_ID


def previous_elements(
    session: RhinoSession,
    *,
    view_id: Optional[str],
    source_root: str,
) -> Tuple[str, ...]:
    found = []
    for object_id in session.iter_object_ids():
        if not is_drawing_element(session, object_id):
            continue
        layer = session.object_layer(object_id) or ""
        if not _is_extract_path(layer):
            continue
        stored_view = text(session.get_object_user_text(object_id, VIEW_ID_KEY))
        stored_root = text(
            session.get_object_user_text(object_id, drawing_keys.SOURCE_LAYER_ROOT_KEY)
        )
        if view_id and stored_view == view_id:
            found.append(object_id)
        elif not view_id and stored_root == source_root:
            found.append(object_id)
    return tuple(found)


def previous_is_modified(session: RhinoSession, object_ids: Sequence[str]) -> bool:
    for object_id in object_ids:
        state = text(
            session.get_object_user_text(object_id, drawing_keys.PROVENANCE_STATE_KEY)
        )
        status = text(
            session.get_object_user_text(object_id, drawing_keys.DRAWING_STATUS_KEY)
        )
        if state == drawing_keys.STATE_MODIFIED or status == drawing_keys.STATUS_MODIFIED:
            return True
    return False


def _snapshot_layers(session: RhinoSession):
    snapshot = {}
    locked_fn = getattr(session, "layer_locked", None)
    visible_fn = getattr(session, "layer_visible", None)
    for path in session.layer_paths():
        snapshot[path] = {
            "locked": bool(locked_fn(path)) if callable(locked_fn) else False,
            "visible": bool(visible_fn(path)) if callable(visible_fn) else True,
        }
    return snapshot


def _restore_layers(session: RhinoSession, snapshot: Mapping[str, Mapping]) -> None:
    locked_fn = getattr(session, "set_layer_locked", None)
    visible_fn = getattr(session, "set_layer_visible", None)
    for path, state in snapshot.items():
        if not session.has_layer(path):
            continue
        if callable(locked_fn):
            locked_fn(path, bool(state.get("locked")))
        if callable(visible_fn):
            visible_fn(path, bool(state.get("visible")))


def _clear_object_user_text(session: RhinoSession, object_id: str) -> None:
    keys_fn = getattr(session, "object_user_text_keys", None)
    if not callable(keys_fn):
        return
    for key in tuple(keys_fn(object_id) or ()):
        session.set_object_user_text(object_id, str(key), "")


def _ensure_extract_layer(session: RhinoSession, path: str, rgb=None) -> None:
    session.ensure_layer(path)
    if rgb is not None:
        setter = getattr(session, "set_layer_appearance", None)
        if callable(setter):
            setter(path, rgb)


def _registry_revision(session: RhinoSession):
    project_id = project_id_from_session(session)
    loaded = load_published_registry(
        project_id,
        document_path=session.document_path() if hasattr(session, "document_path") else None,
        command_id=COMMAND_ID,
    )
    if not loaded.ok:
        return None
    return loaded.details.get("registry_revision")


def _write_element(
    session: RhinoSession,
    object_id: str,
    *,
    drawing_id: str,
    view_id: Optional[str],
    source_root: str,
    revision,
    source_ids: Sequence[str],
    state: str,
    method: str,
) -> None:
    session.set_object_user_text(object_id, drawing_keys.SCHEMA_ID_KEY, drawing_keys.DRAWING_SCHEMA_ID)
    session.set_object_user_text(
        object_id, drawing_keys.SCHEMA_VERSION_KEY, drawing_keys.DRAWING_SCHEMA_VERSION
    )
    session.set_object_user_text(object_id, drawing_keys.DRAWING_ID_KEY, drawing_id)
    session.set_object_user_text(object_id, drawing_keys.DRAWING_ELEMENT_ID_KEY, _new_id())
    session.set_object_user_text(object_id, drawing_keys.SOURCE_LAYER_ROOT_KEY, source_root)
    session.set_object_user_text(object_id, drawing_keys.DRAWING_STATUS_KEY, drawing_keys.STATUS_GENERATED)
    session.set_object_user_text(object_id, drawing_keys.PROVENANCE_STATE_KEY, state)
    session.set_object_user_text(object_id, drawing_keys.PROVENANCE_METHOD_KEY, method)
    session.set_object_user_text(
        object_id,
        drawing_keys.SOURCE_OBJECT_IDS_KEY,
        json.dumps(list(source_ids), ensure_ascii=False),
    )
    if view_id:
        session.set_object_user_text(object_id, VIEW_ID_KEY, view_id)
    if revision not in (None, ""):
        session.set_object_user_text(object_id, drawing_keys.SOURCE_REVISION_KEY, str(revision))


def extract_root(
    session: RhinoSession,
    root: str,
    *,
    mode: str,
    views: Sequence[Mapping],
    revision,
) -> results.Result:
    matched = match_view_for_root(root, views)
    if not matched.ok:
        return matched
    view = (matched.details or {}).get("view")
    view_id = text((view or {}).get("view_id"))
    previous = previous_elements(session, view_id=view_id, source_root=root)
    drawing_id = None
    if previous:
        drawing_id = text(
            session.get_object_user_text(previous[0], drawing_keys.DRAWING_ID_KEY)
        )
        if mode == drawing_keys.MODE_SKIP:
            return results.ok(
                STAGE,
                "已略過「%s」的前次產出。" % root,
                command_id=COMMAND_ID,
                details={"root": root, "mode": mode, "copied": 0, "coverage": {}},
            )
        if mode == drawing_keys.MODE_REPLACE:
            if previous_is_modified(session, previous):
                return results.blocked(
                    STAGE,
                    "「%s」的 Drawing 已人工修改，不會覆蓋。若要另存一版請選新增。" % root,
                    ("modified_drawing",),
                    command_id=COMMAND_ID,
                    details={"root": root},
                )
            for object_id in previous:
                session.delete_object(object_id)
        elif mode == drawing_keys.MODE_ADD:
            drawing_id = _new_id()
        else:
            return results.blocked(
                STAGE,
                "未知的重跑選項。",
                ("invalid_mode",),
                command_id=COMMAND_ID,
            )
    if not drawing_id:
        drawing_id = _new_id()

    _ensure_extract_layer(session, EXTRACT_LAYER_ROOT)
    _ensure_extract_layer(session, drawing_keys.LAYER_VISIBLE, drawing_keys.COLOR_VISIBLE)
    _ensure_extract_layer(session, drawing_keys.LAYER_HATCH, drawing_keys.COLOR_HATCH)

    copied = 0
    coverage = {"indexed": 0, "unindexed": 0, "ambiguous": 0}
    prefix = root + "::"
    for path in session.layer_paths():
        if path != root and not str(path).startswith(prefix):
            continue
        kind = _layer_kind(path)
        if kind is None:
            continue
        for object_id in session.objects_on_layer(path):
            color = None
            color_fn = getattr(session, "object_display_color", None)
            if callable(color_fn):
                color = color_fn(object_id)
            if not color:
                color = getattr(session, "layer_color", lambda _path: None)(path)
            target = target_layer_for(kind, color)
            if kind == drawing_keys.KIND_CURVE:
                _ensure_extract_layer(session, target, color)
            copier = getattr(session, "copy_object", None)
            if not callable(copier):
                return results.failed(
                    STAGE,
                    "此 Rhino session 不能複製物件。",
                    command_id=COMMAND_ID,
                )
            new_id = copier(object_id)
            if not new_id:
                continue
            source_ids = source_object_ids(session, object_id)
            session.set_object_layer(new_id, target)
            reset = getattr(session, "reset_object_to_bylayer", None)
            if callable(reset):
                reset(new_id)
            _clear_object_user_text(session, new_id)
            state, bucket, method = classify_sources(source_ids)
            coverage[bucket] = coverage.get(bucket, 0) + 1
            _write_element(
                session,
                new_id,
                drawing_id=drawing_id,
                view_id=view_id,
                source_root=root,
                revision=revision,
                source_ids=source_ids,
                state=state,
                method=method,
            )
            copied += 1

    return results.ok(
        STAGE,
        "已抽出「%s」%s 個物件。" % (root, copied),
        command_id=COMMAND_ID,
        details={
            "root": root,
            "view_id": view_id,
            "drawing_id": drawing_id,
            "mode": mode,
            "copied": copied,
            "coverage": coverage,
        },
    )


def extract_drawings(
    session: RhinoSession,
    roots: Sequence[str],
    *,
    mode: str = drawing_keys.MODE_REPLACE,
    revision=None,
) -> results.Result:
    views = listed_views(session)
    notes = []
    total = {"copied": 0, "indexed": 0, "unindexed": 0, "ambiguous": 0, "skipped": 0}
    drawings = []
    for root in roots:
        outcome = extract_root(
            session, root, mode=mode, views=views, revision=revision
        )
        if not outcome.ok:
            return outcome
        details = outcome.details or {}
        copied = int(details.get("copied") or 0)
        total["copied"] += copied
        coverage = details.get("coverage") or {}
        for key in ("indexed", "unindexed", "ambiguous"):
            total[key] += int(coverage.get(key) or 0)
        if details.get("mode") == drawing_keys.MODE_SKIP:
            total["skipped"] += 1
        drawings.append(details)
        notes.append(outcome.message)
    incomplete = (total["unindexed"] + total["ambiguous"]) > 0
    return results.ok(
        STAGE,
        "抽出完成：複製 %s 個物件。" % total["copied"],
        command_id=COMMAND_ID,
        details={
            "counts": total,
            "drawings": drawings,
            "notes": notes,
            "coverage_incomplete": incomplete,
        },
    )


def _default_pick_roots(session: RhinoSession, roots: Sequence[str]) -> Optional[Sequence[str]]:
    from loopflow.platform.rhino.prompts import ask_checklist

    return ask_checklist(
        list(roots),
        "勾選要抽出的剖面圖層（可複選）：",
        "抽出可編輯線稿",
    )


def _default_pick_mode(_session: RhinoSession, info: Mapping) -> Optional[str]:
    from loopflow.platform.rhino.prompts import ask_popup_choice

    labels = [label for label, _mode in drawing_keys.MODE_LABELS]
    chosen = ask_popup_choice(
        "「%s」已有前次抽出。請選取代、新增或略過。" % info.get("root"),
        labels,
        "辨識前次產出",
    )
    if chosen is None:
        return None
    for label, mode in drawing_keys.MODE_LABELS:
        if chosen == label:
            return mode
    return None


def _summary(details: Mapping) -> str:
    counts = details.get("counts") or {}
    lines = [
        "已抽出可編輯線稿。",
        "複製 %s 個物件到 %s。"
        % (counts.get("copied", 0), EXTRACT_LAYER_ROOT),
        "來源索引：唯一 %s、無法辨識 %s、多來源 %s。"
        % (
            counts.get("indexed", 0),
            counts.get("unindexed", 0),
            counts.get("ambiguous", 0),
        ),
    ]
    if details.get("coverage_incomplete"):
        lines.append("索引不完整仍已產出，不阻擋。")
    if counts.get("skipped"):
        lines.append("略過 %s 個已有產出的剖面。" % counts.get("skipped"))
    return "\n".join(lines)


def run_extract_cp(
    session: RhinoSession,
    *,
    pick_roots: Optional[PickRoots] = None,
    pick_mode: Optional[PickMode] = None,
    show_message: Optional[ShowMessage] = None,
) -> results.Result:
    if session is None:
        return results.failed(STAGE, "沒有 Rhino session。", command_id=COMMAND_ID)

    def _action(current: RhinoSession) -> results.Result:
        if current.is_layout_active():
            return results.blocked(
                STAGE,
                "請在 2D 模型空間執行 Extract，不要在 Layout 頁。",
                ("layout_active",),
                command_id=COMMAND_ID,
            )
        roots = listed_section_roots(current)
        if not roots:
            return results.blocked(
                STAGE,
                "找不到 Clipping Drawing 的 Visible／Hatch／Curve 圖層。",
                ("missing_section_layers",),
                command_id=COMMAND_ID,
            )
        picker = pick_roots or _default_pick_roots
        selected = picker(current, roots)
        if selected is None:
            return results.cancelled(STAGE, "已取消抽出。", command_id=COMMAND_ID)
        wanted = [name for name in selected if name in roots]
        if not wanted:
            return results.cancelled(STAGE, "沒有勾選剖面圖層。", command_id=COMMAND_ID)

        views = listed_views(current)
        modes = {}
        chooser = pick_mode or _default_pick_mode
        for root in wanted:
            matched = match_view_for_root(root, views)
            if not matched.ok:
                return matched
            view = (matched.details or {}).get("view")
            view_id = text((view or {}).get("view_id"))
            previous = previous_elements(current, view_id=view_id, source_root=root)
            if not previous:
                modes[root] = drawing_keys.MODE_ADD
                continue
            chosen = chooser(
                current,
                {
                    "root": root,
                    "view_id": view_id,
                    "count": len(previous),
                    "modified": previous_is_modified(current, previous),
                },
            )
            if chosen is None:
                return results.cancelled(STAGE, "已取消抽出。", command_id=COMMAND_ID)
            modes[root] = chosen

        layer_snapshot = _snapshot_layers(current)
        revision = _registry_revision(current)
        copied_total = {
            "copied": 0,
            "indexed": 0,
            "unindexed": 0,
            "ambiguous": 0,
            "skipped": 0,
        }
        drawings = []
        try:
            for root in wanted:
                outcome = extract_root(
                    current,
                    root,
                    mode=modes[root],
                    views=views,
                    revision=revision,
                )
                if not outcome.ok:
                    return outcome
                details = outcome.details or {}
                copied_total["copied"] += int(details.get("copied") or 0)
                coverage = details.get("coverage") or {}
                for key in ("indexed", "unindexed", "ambiguous"):
                    copied_total[key] += int(coverage.get(key) or 0)
                if details.get("mode") == drawing_keys.MODE_SKIP:
                    copied_total["skipped"] += 1
                drawings.append(details)
        finally:
            _restore_layers(current, layer_snapshot)

        incomplete = (copied_total["unindexed"] + copied_total["ambiguous"]) > 0
        payload = {
            "counts": copied_total,
            "drawings": drawings,
            "coverage_incomplete": incomplete,
        }
        message = _summary(payload)
        if callable(show_message):
            show_message(message)
        return results.ok(STAGE, message, command_id=COMMAND_ID, details=payload)

    return run_guarded(session, _action, command_id=COMMAND_ID)
