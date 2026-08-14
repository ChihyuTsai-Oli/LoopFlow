# -*- coding: utf-8 -*-
"""Type layer 同步與反向差異匯出。不寫物件 instance、不覆寫正式 Dictionary。"""
from __future__ import annotations

from pathlib import Path
from typing import List, Mapping, Optional, Set

from loopflow.features.dictionary.layer_paths import (
    LAYER_CONSTRUCTION_KEY,
    LAYER_TYPE_ID_KEY,
    SYSTEM_LAYERS,
    color_for_layer_path,
    dna_ref_name,
    is_dw_child,
    is_exportable_type_layer,
    material_name_for_layer,
    to_full_path,
    to_relative_path,
)
from loopflow.features.dictionary.loader import TypeCatalog, load_from_workfiles
from loopflow.foundation import results
from loopflow.foundation.paths import DICTIONARY_FILENAME, resolve_workfiles
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
DIFF_HEADERS = (
    "__Rhino Layer",
    "type_id",
    "construction_default",
    "diff_status",
)
DIFF_TITLE = "LoopFlow layer diff v2.0"


def _rollback(session: RhinoSession, layers_before: Set[str], objects_before: Set[str]) -> None:
    for object_id in session.iter_object_ids():
        if object_id not in objects_before:
            session.delete_object(object_id)
    extras = sorted(
        set(session.layer_paths()) - layers_before,
        key=lambda path: path.count("::"),
        reverse=True,
    )
    for path in extras:
        session.delete_layer(path)


def _ensure_dna_ref(session: RhinoSession, layer_path: str, type_id: str) -> None:
    wanted = dna_ref_name(type_id)
    for object_id in session.objects_on_layer(layer_path):
        name = session.object_name(object_id) or ""
        if name.startswith("DNA_REF_"):
            session.delete_object(object_id)
    session.add_placeholder(layer=layer_path, name=wanted)


def _sync_body(
    session: RhinoSession,
    catalog: TypeCatalog,
    *,
    cancel: bool,
    export_path: Optional[Path],
    dictionary_path: Path,
) -> results.Result:
    if cancel:
        return results.cancelled(
            "sync_type_layers",
            "使用者取消 Type layer 同步。",
            command_id=COMMAND_ID,
        )
    layers_before = set(session.layer_paths())
    objects_before = set(session.iter_object_ids())
    skipped_dw_children = []
    created_types = []
    kept_types = []
    try:
        for system_path in SYSTEM_LAYERS:
            session.ensure_layer(system_path)
            session.set_layer_appearance(system_path, color_for_layer_path(system_path))
        for record in catalog.types:
            full = to_full_path(record.layer_path)
            if is_dw_child(full):
                skipped_dw_children.append(record.layer_path)
                continue
            existed = session.has_layer(full)
            session.ensure_layer(full)
            session.set_layer_appearance(
                full,
                color_for_layer_path(full),
                material_name=material_name_for_layer(full),
            )
            if not existed:
                if record.construction_default:
                    session.set_layer_user_text(full, LAYER_CONSTRUCTION_KEY, record.construction_default)
                session.set_layer_user_text(full, LAYER_TYPE_ID_KEY, record.type_id)
                created_types.append(record.type_id)
            else:
                kept_types.append(record.type_id)
            _ensure_dna_ref(session, full, record.type_id)
        if export_path is not None:
            exported = export_layer_diff(
                session,
                catalog,
                export_path,
                dictionary_path=dictionary_path,
            )
            if not exported.ok:
                _rollback(session, layers_before, objects_before)
                return exported
    except Exception as exc:
        _rollback(session, layers_before, objects_before)
        return results.failed(
            "sync_type_layers",
            "Type layer 同步失敗，已還原本次新增圖層與參考線。",
            command_id=COMMAND_ID,
            details={"exception": repr(exc)},
        )

    payload = {
        "created_type_ids": tuple(created_types),
        "kept_type_ids": tuple(kept_types),
        "skipped_dw_children": tuple(skipped_dw_children),
        "created_layer_count": len(created_types),
        "steps_hint": "layer 已同步，可存檔。Scan／Apply／發布尚未實作。",
    }
    warnings = ()
    if skipped_dw_children:
        warnings = ("已排除 %s 個 20_DW 子圖層，不建 Type。" % len(skipped_dw_children),)
    message = "Type layer 同步完成：新建 %s、保留 %s。" % (len(created_types), len(kept_types))
    if warnings:
        return results.ok_with_warnings(
            "sync_type_layers",
            message,
            warnings,
            command_id=COMMAND_ID,
            details=payload,
        )
    return results.ok("sync_type_layers", message, command_id=COMMAND_ID, details=payload)


def sync_type_layers(
    session: RhinoSession,
    *,
    environ: Optional[Mapping[str, str]] = None,
    catalog: Optional[TypeCatalog] = None,
    cancel: bool = False,
    export_path: Optional[Path] = None,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """Dictionary → Rhino Type layer。既有 layer 保留資料；不寫物件 instance。"""
    if catalog is None:
        loaded = load_from_workfiles(environ=environ)
        if not loaded.ok:
            return loaded
        catalog = loaded.details["catalog"]
        dictionary_path = resolve_workfiles(environ=environ).details["paths"].dictionary
    else:
        workfiles = resolve_workfiles(environ=environ)
        dictionary_path = workfiles.details["paths"].dictionary if workfiles.ok else Path(DICTIONARY_FILENAME)

    def action(current: RhinoSession) -> results.Result:
        return _sync_body(
            current,
            catalog,
            cancel=cancel,
            export_path=export_path,
            dictionary_path=dictionary_path,
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def _diff_rows(session: RhinoSession, catalog: TypeCatalog) -> List[List[str]]:
    rhino_paths = session.layer_paths()
    exportable = [path for path in rhino_paths if is_exportable_type_layer(path, rhino_paths)]
    by_rel = {to_relative_path(path): path for path in exportable}
    dict_by_rel = {
        record.layer_path: record
        for record in catalog.types
        if not is_dw_child(to_full_path(record.layer_path))
    }
    rows = []
    seen = set()
    for relative, record in dict_by_rel.items():
        seen.add(relative)
        full = by_rel.get(relative)
        if full is None:
            rows.append([relative, record.type_id, record.construction_default or "", "missing_in_rhino"])
            continue
        rhino_type = session.get_layer_user_text(full, LAYER_TYPE_ID_KEY)
        rhino_cons = session.get_layer_user_text(full, LAYER_CONSTRUCTION_KEY)
        status = "unchanged"
        if (rhino_type and rhino_type != record.type_id) or (
            rhino_cons and rhino_cons != (record.construction_default or "")
        ):
            status = "modified"
        rows.append([relative, record.type_id, record.construction_default or "", status])
    for relative, full in by_rel.items():
        if relative in seen:
            continue
        rows.append(
            [
                relative,
                session.get_layer_user_text(full, LAYER_TYPE_ID_KEY) or "",
                session.get_layer_user_text(full, LAYER_CONSTRUCTION_KEY) or "",
                "added_in_rhino",
            ]
        )
    return rows


def export_layer_diff(
    session: RhinoSession,
    catalog: TypeCatalog,
    export_path: Path,
    *,
    dictionary_path: Path,
) -> results.Result:
    """匯出獨立比較用 xlsx。不讀 Object UserText，不覆寫正式 Dictionary。"""
    target = Path(export_path)
    if target.resolve() == Path(dictionary_path).resolve():
        return results.blocked(
            "sync_type_layers",
            "反向匯出不得覆寫正式 Dictionary。",
            blocking=("overwrite_dictionary_forbidden",),
            command_id=COMMAND_ID,
        )
    if not target.parent.exists():
        return results.failed(
            "sync_type_layers",
            "匯出目錄不存在，不建立。",
            command_id=COMMAND_ID,
        )
    rows = _diff_rows(session, catalog)
    written = write_table(target, DIFF_TITLE, DIFF_HEADERS, rows)
    if not written.ok:
        return written
    return results.ok(
        "sync_type_layers",
        "已匯出 layer 差異，未改正式 Dictionary。",
        command_id=COMMAND_ID,
        details={"filename": target.name, "row_count": len(rows)},
    )
