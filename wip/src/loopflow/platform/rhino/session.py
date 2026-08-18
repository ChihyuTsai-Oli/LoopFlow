# -*- coding: utf-8 -*-
"""Rhino session 契約與成功／取消／失敗的狀態還原。"""
from __future__ import annotations

import traceback
from typing import Callable, Optional, Protocol, Sequence

from loopflow.foundation import results
from loopflow.platform.rhino.state import DocumentSnapshot, ObjectViewState


class RhinoSession(Protocol):
    def iter_object_ids(
        self,
        *,
        include_hidden: bool = True,
        include_locked: bool = True,
    ) -> Sequence[str]:
        ...

    def get_view_state(self, object_id: str) -> Optional[ObjectViewState]:
        ...

    def set_view_state(self, state: ObjectViewState) -> None:
        ...

    def document_modified(self) -> bool:
        ...

    def set_document_modified(self, value: bool) -> None:
        ...

    def document_user_text(self, key: str) -> Optional[str]:
        ...

    def set_document_user_text(self, key: str, value: str) -> None:
        ...

    def model_unit_system(self) -> str:
        ...

    def layer_paths(self) -> Sequence[str]:
        ...

    def has_layer(self, path: str) -> bool:
        ...

    def ensure_layer(self, path: str) -> bool:
        ...

    def delete_layer(self, path: str) -> None:
        ...

    def get_layer_user_text(self, path: str, key: str) -> Optional[str]:
        ...

    def set_layer_user_text(self, path: str, key: str, value: str) -> None:
        ...

    def set_layer_appearance(
        self,
        path: str,
        rgb: Sequence[int],
        material_name: Optional[str] = None,
    ) -> None:
        ...

    def object_name(self, object_id: str) -> Optional[str]:
        ...

    def set_object_name(self, object_id: str, name: str) -> None:
        ...

    def object_layer(self, object_id: str) -> Optional[str]:
        ...

    def set_object_layer(self, object_id: str, path: str) -> None:
        ...

    def get_object_user_text(self, object_id: str, key: str) -> Optional[str]:
        ...

    def set_object_user_text(self, object_id: str, key: str, value: str) -> None:
        ...

    def objects_on_layer(self, path: str) -> Sequence[str]:
        ...

    def add_placeholder(self, *, layer: str, name: str) -> str:
        ...

    def delete_object(self, object_id: str) -> None:
        ...

    def is_closed_curve(self, object_id: str) -> bool:
        ...

    def curve_polygon(self, object_id: str) -> Optional[Sequence[Sequence[float]]]:
        ...

    def curve_elevation(self, object_id: str) -> Optional[float]:
        ...

    def is_model_object(self, object_id: str) -> bool:
        ...

    def object_bbox(self, object_id: str) -> Optional[Sequence[float]]:
        ...

    def is_block_instance(self, object_id: str) -> bool:
        ...

    def block_definition_name(self, object_id: str) -> Optional[str]:
        ...

    def insertion_point(self, object_id: str) -> Optional[Sequence[float]]:
        ...

    def shoot_ray_hits(self, origin, direction):
        ...

    def is_text_dot(self, object_id: str) -> bool:
        ...

    def text_dot_text(self, object_id: str) -> Optional[str]:
        ...

    def is_clipping_plane(self, object_id: str) -> bool:
        ...

    def iter_clipping_plane_ids(self) -> Sequence[str]:
        ...

    def clipping_plane_plane(self, object_id: str):
        ...

    def clipping_plane_section_bbox_local(self, object_id: str):
        ...

    def objects_bbox(self, object_ids: Sequence[str]):
        ...

    def add_closed_polyline(self, points, *, layer: str, name: str) -> str:
        ...

    def zoom_to_object(self, object_id: str) -> None:
        ...

    def is_layout_active(self) -> bool:
        ...

    def listed_layout_details(self) -> Sequence[dict]:
        ...

    def listed_layout_pages(self) -> Sequence[dict]:
        ...

    def objects_on_layout_page(self, page_name: str) -> Sequence[str]:
        ...

    def rename_layout_page(self, page_name: str, new_name: str) -> bool:
        ...

    def detail_model_point(self, detail_id: str):
        ...

    def zoom_to_layout_detail(self, layout: str, detail_id: str) -> None:
        ...

    def is_point(self, object_id: str) -> bool:
        ...

    def point_xyz(self, object_id: str):
        ...

    def layout_page_name_of(self, object_id: str) -> Optional[str]:
        ...

    def add_text(
        self,
        content: str,
        point,
        *,
        layer: str,
        page_name: Optional[str] = None,
        height: float = 1.0,
    ) -> str:
        ...

    def update_text(self, object_id: str, content: str, origin=None) -> bool:
        ...

    def document_path(self) -> Optional[str]:
        ...

    def snapshot(self) -> DocumentSnapshot:
        ...

    def restore(
        self,
        snapshot: DocumentSnapshot,
        *,
        restore_document_modified: bool,
    ) -> results.Result:
        ...


def capture_snapshot(session: RhinoSession) -> DocumentSnapshot:
    states = []
    for object_id in session.iter_object_ids(include_hidden=True, include_locked=True):
        name = session.object_name(object_id) or ""
        if name.startswith("DNA_REF_"):
            continue
        state = session.get_view_state(object_id)
        if state is not None:
            states.append(state)
    return DocumentSnapshot(objects=tuple(states), document_modified=session.document_modified())


def restore_snapshot(
    session: RhinoSession,
    snapshot: DocumentSnapshot,
    *,
    restore_document_modified: bool,
) -> results.Result:
    redraw = getattr(session, "set_redraw_enabled", None)
    if callable(redraw):
        redraw(False)
    try:
        missing = []
        for state in snapshot.objects:
            current = session.get_view_state(state.object_id)
            if current is None:
                missing.append(state.object_id)
                continue
            if current == state:
                continue
            session.set_view_state(state)
        if restore_document_modified:
            session.set_document_modified(snapshot.document_modified)
    finally:
        if callable(redraw):
            redraw(True)
    if missing:
        return results.failed(
            "restore",
            "還原時找不到 %s 個快照物件，其餘狀態已寫回。" % len(missing),
            blocking=tuple(missing),
        )
    return results.ok("restore", "已還原 Rhino 視圖狀態")


def run_guarded(
    session: RhinoSession,
    action: Callable[[RhinoSession], results.Result],
    *,
    command_id: Optional[str] = None,
) -> results.Result:
    """執行動作後還原選取／鎖定／顯示／顏色。

    成功：保留文件 modified（指令可能已寫入資料）；允許刪除快照中的物件
    （例如 Refresh 精準刪舊目錄文字再重建）。
    取消、失敗、例外：連 modified 一併還原。
    """
    try:
        snapshot = capture_snapshot(session)
    except Exception as exc:
        return results.failed(
            "guarded_run",
            "建立快照時發生例外。\n%s" % exc,
            command_id=command_id,
            details={"exception": repr(exc), "traceback": traceback.format_exc()},
        )
    try:
        outcome = action(session)
    except Exception as exc:
        restore_snapshot(session, snapshot, restore_document_modified=True)
        return results.failed(
            "guarded_run",
            "執行中發生例外，已還原 Rhino 狀態。\n%s" % exc,
            command_id=command_id,
            details={"exception": repr(exc), "traceback": traceback.format_exc()},
        )
    if not isinstance(outcome, results.Result):
        restore_snapshot(session, snapshot, restore_document_modified=True)
        return results.failed(
            "guarded_run",
            "指令未回傳 Result，已還原 Rhino 狀態。",
            command_id=command_id,
        )
    restored = restore_snapshot(
        session,
        snapshot,
        restore_document_modified=not outcome.ok,
    )
    if not restored.ok and not outcome.ok:
        return results.failed(
            "restore",
            restored.message,
            command_id=command_id,
            blocking=restored.blocking,
            details={"action_status": outcome.status},
        )
    return outcome
