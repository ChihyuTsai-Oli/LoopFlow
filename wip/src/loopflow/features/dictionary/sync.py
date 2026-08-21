# -*- coding: utf-8 -*-
"""Type layer 同步與反向差異匯出。不寫物件 instance、不覆寫正式 Dictionary。"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Set

from loopflow.features.dictionary import schema
from loopflow.features.dictionary.layer_paths import (
    LAYER_CONSTRUCTION_KEY,
    LAYER_PREFIX_3D,
    LAYER_TYPE_ID_KEY,
    color_for_layer_path,
    dna_ref_name,
    is_dw_child,
    is_exportable_type_layer,
    material_name_for_layer,
    normalize_layer_prefix,
    project_id_from_session,
    read_layer_prefix,
    system_layers,
    to_full_path,
    to_relative_path,
)
from loopflow.features.dictionary.loader import TypeCatalog, load_dictionary
from loopflow.foundation import results
from loopflow.foundation.paths import (
    DICTIONARY_FILENAME,
    export_dictionary_filename,
    normalize_dictionary_filename,
    resolve_project_folder,
)
from loopflow.foundation.project_config import (
    dictionary_filename_from_session,
    remembered_dictionary_filename,
    update_config,
)
from loopflow.platform.excel import write_table
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
EXPORT_FILENAME = "LoopFlow_Dictionary_Export.xlsx"
EXPORT_HEADERS = schema.DISPLAY_COLUMNS + ("diff_status",)


def export_hint(official_name: str = DICTIONARY_FILENAME) -> str:
    return (
        "此檔只供核對，不能當正式字典開啟，也不可覆寫 %s。"
        "藍字 added_in_rhino 合併時必須給新的 _03_ID編號，不可沿用舊圖層編號。"
        % (official_name or DICTIONARY_FILENAME)
    )


EXPORT_HINT = export_hint()
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
    prefix: str,
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
        for system_path in system_layers(prefix):
            session.ensure_layer(system_path)
            session.set_layer_appearance(system_path, color_for_layer_path(system_path, prefix))
        for record in catalog.types:
            full = to_full_path(record.layer_path, prefix)
            if is_dw_child(full, prefix):
                skipped_dw_children.append(record.layer_path)
                continue
            existed = session.has_layer(full)
            session.ensure_layer(full)
            session.set_layer_appearance(
                full,
                color_for_layer_path(full, prefix),
                material_name=material_name_for_layer(full, prefix),
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
                prefix=prefix,
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
        "layer_prefix": prefix,
        "steps_hint": "layer 已同步，可存檔。Scan／Apply／發布尚未實作。",
    }
    warnings = ()
    if skipped_dw_children:
        warnings = ("已排除 %s 個 20_DW 子圖層，不建 Type。" % len(skipped_dw_children),)
    message = "Type layer 同步完成（%s）：新建 %s、保留 %s。" % (prefix, len(created_types), len(kept_types))
    if warnings:
        return results.ok_with_warnings(
            "sync_type_layers",
            message,
            warnings,
            command_id=COMMAND_ID,
            details=payload,
        )
    return results.ok("sync_type_layers", message, command_id=COMMAND_ID, details=payload)


def _should_ask_dictionary(session: RhinoSession, root: Path) -> bool:
    """第一次尚未記住檔名，或已記住的檔不在 .3dm 同層（改名或搬走）時才問。"""
    stored = remembered_dictionary_filename(session)
    if not stored:
        return True
    return not (root / stored).is_file()


def dictionary_missing_hint(filename: str) -> str:
    """字典改名或搬走時的說明。請使用者移回，再從 .3dm 目錄選。"""
    return (
        "找不到字典 %s。請把字典移回 .3dm 所在的資料夾（字典可以改名），"
        "接著在開啟的視窗選這份專案要用的 .xlsx。" % filename
    )


def sync_type_layers(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    cancel: bool = False,
    export_path: Optional[Path] = None,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
    layer_prefix: Optional[str] = None,
    ask_prefix=None,
    dictionary_filename: Optional[str] = None,
    ask_dictionary=None,
) -> results.Result:
    """Dictionary → Rhino Type layer。既有 layer 保留資料；不寫物件 instance。"""

    def action(current: RhinoSession) -> results.Result:
        current_prefix = read_layer_prefix(current)
        stored = normalize_layer_prefix(project_id_from_session(current) or "")
        chosen = layer_prefix
        if chosen is None and callable(ask_prefix):
            chosen = ask_prefix(stored or "")
            if chosen is None:
                return results.cancelled(
                    "sync_type_layers",
                    "使用者取消輸入專案名稱。",
                    command_id=command_id,
                )
        if chosen is None:
            chosen = stored or current_prefix or LAYER_PREFIX_3D
        prefix = normalize_layer_prefix(chosen)
        if not prefix:
            return results.blocked(
                "sync_type_layers",
                "專案名稱不能空白，也不能含 : \\ / * ? \" < > |",
                blocking=("invalid_layer_prefix",),
                command_id=command_id,
            )

        resolved = resolve_project_folder(current)
        if not resolved.ok:
            return resolved
        root = resolved.details["paths"].root
        chosen_dict = dictionary_filename
        if chosen_dict is None and callable(ask_dictionary) and _should_ask_dictionary(current, root):
            chosen_dict = ask_dictionary(dictionary_filename_from_session(current))
            if chosen_dict is None:
                return results.cancelled(
                    "sync_type_layers",
                    "使用者取消選擇 Dictionary。",
                    command_id=command_id,
                )
        if chosen_dict is None:
            chosen_dict = dictionary_filename_from_session(current)
        normalized = normalize_dictionary_filename(chosen_dict, root=root)
        if not normalized.ok:
            return normalized
        filename = str(normalized.details["filename"])
        remembered = update_config(
            current,
            project_id=prefix,
            layer_prefix=prefix,
            dictionary_filename=filename,
        )
        if not remembered.ok:
            return remembered
        dictionary_file = root / filename
        type_catalog = catalog
        if type_catalog is None:
            loaded = load_dictionary(current, dictionary_filename=filename)
            if not loaded.ok:
                return loaded
            type_catalog = loaded.details["catalog"]
        return _sync_body(
            current,
            type_catalog,
            cancel=cancel,
            export_path=export_path,
            dictionary_path=dictionary_file,
            prefix=prefix,
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def _diff_rows(session: RhinoSession, catalog: TypeCatalog, prefix: str) -> List[List[str]]:
    rhino_paths = session.layer_paths()
    exportable = [path for path in rhino_paths if is_exportable_type_layer(path, rhino_paths, prefix)]
    by_rel = {to_relative_path(path, prefix): path for path in exportable}
    dict_by_rel = {
        record.layer_path: record
        for record in catalog.types
        if not is_dw_child(to_full_path(record.layer_path, prefix), prefix)
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
    prefix: str = LAYER_PREFIX_3D,
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
    rows = _diff_rows(session, catalog, prefix)
    written = write_table(target, DIFF_TITLE, DIFF_HEADERS, rows)
    if not written.ok:
        return written
    return results.ok(
        "sync_type_layers",
        "已匯出 layer 差異，未改正式 Dictionary。",
        command_id=COMMAND_ID,
        details={"filename": target.name, "row_count": len(rows)},
    )


def _blank_display_row() -> List[str]:
    return [""] * len(schema.DISPLAY_COLUMNS)


def _record_display_row(record) -> List[str]:
    values = {
        "layer_path": record.layer_path,
        "space_id": "",
        "construction_default": record.construction_default or "",
        "type_id": record.type_id,
        "type_display_name": record.type_display_name or "",
        "elevation_basis": record.elevation_basis or "",
        "elevation_value": "",
        "object_id": "",
        "remarks_default": record.remarks_default or "",
        "dimension_w": "",
        "dimension_d": "",
        "dimension_h": "",
        "estimation_unit": record.estimation_unit or "",
        "measurement_rule": record.measurement_rule or "",
        "quantity": "",
    }
    return [values.get(key) or "" for key in schema.MACHINE_KEYS]


def _dictionary_export_rows(session: RhinoSession, catalog: TypeCatalog, prefix: str) -> List[List[str]]:
    rhino_paths = session.layer_paths()
    exportable = [path for path in rhino_paths if is_exportable_type_layer(path, rhino_paths, prefix)]
    by_rel = {to_relative_path(path, prefix): path for path in exportable}
    rows = []
    seen = set()
    for record in catalog.types:
        if is_dw_child(to_full_path(record.layer_path, prefix), prefix):
            continue
        seen.add(record.layer_path)
        row = _record_display_row(record)
        full = by_rel.get(record.layer_path)
        if full is None:
            rows.append(row + ["missing_in_rhino"])
            continue
        rhino_type = session.get_layer_user_text(full, LAYER_TYPE_ID_KEY) or ""
        rhino_cons = session.get_layer_user_text(full, LAYER_CONSTRUCTION_KEY) or ""
        status = "unchanged"
        if (rhino_type and rhino_type != record.type_id) or (
            rhino_cons and rhino_cons != (record.construction_default or "")
        ):
            status = "modified"
            if rhino_type:
                row[schema.MACHINE_KEYS.index("type_id")] = rhino_type
            if rhino_cons:
                row[schema.MACHINE_KEYS.index("construction_default")] = rhino_cons
        rows.append(row + [status])
    added = []
    for relative, full in by_rel.items():
        if relative in seen:
            continue
        row = _blank_display_row()
        row[schema.MACHINE_KEYS.index("layer_path")] = relative
        row[schema.MACHINE_KEYS.index("type_id")] = session.get_layer_user_text(full, LAYER_TYPE_ID_KEY) or ""
        row[schema.MACHINE_KEYS.index("construction_default")] = (
            session.get_layer_user_text(full, LAYER_CONSTRUCTION_KEY) or ""
        )
        added.append(row + ["added_in_rhino"])
    rows.extend(added)
    return rows


def export_dictionary(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    export_path: Optional[Path] = None,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
    show_message: Optional[Callable[[str], None]] = None,
) -> results.Result:
    """在 .3dm 同資料夾新增匯出檔。不讀 Object UserText，不覆寫正式 Dictionary。"""
    filename = dictionary_filename_from_session(session)
    resolved = resolve_project_folder(session, dictionary_filename=filename)
    if not resolved.ok:
        return resolved
    dictionary_path = resolved.details["paths"].dictionary
    if catalog is None:
        loaded = load_dictionary(session, dictionary_filename=filename)
        if not loaded.ok:
            return loaded
        catalog = loaded.details["catalog"]

    def action(current: RhinoSession) -> results.Result:
        prefix = read_layer_prefix(current)
        default_export = dictionary_path.parent / export_dictionary_filename(dictionary_path.name)
        target = Path(export_path) if export_path is not None else default_export
        if target.resolve() == Path(dictionary_path).resolve():
            return results.blocked(
                "export_dictionary",
                "匯出 Type Layers 不得覆寫正式 Dictionary。",
                blocking=("overwrite_dictionary_forbidden",),
                command_id=command_id,
            )
        if not target.parent.exists():
            return results.failed(
                "export_dictionary",
                "匯出目錄不存在，不建立。",
                command_id=command_id,
            )
        rows = _dictionary_export_rows(current, catalog, prefix)
        written = write_table(
            target,
            schema.TITLE_ROW,
            EXPORT_HEADERS,
            rows,
            profile="dictionary",
            hint=export_hint(dictionary_path.name),
        )
        if not written.ok:
            return written
        message = "已在 .3dm 同資料夾匯出 %s，未改正式 Dictionary。" % target.name
        if callable(show_message):
            show_message(message)
        else:
            from loopflow.platform.rhino.prompts import show_message as live_popup

            live_popup(message)
        return results.ok(
            "export_dictionary",
            message,
            command_id=command_id,
            details={"filename": target.name, "path": str(target), "row_count": len(rows)},
        )

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)
