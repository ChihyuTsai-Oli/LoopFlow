# -*- coding: utf-8 -*-
"""掃描／寫入 local frame、W／D／H 與 quantity。不進 Nexus 選單。"""
from __future__ import annotations

from typing import List, Mapping, Optional

from loopflow.features.dictionary.layer_paths import LAYER_TYPE_ID_KEY, to_relative_path
from loopflow.features.dictionary.loader import TypeCatalog, load_from_workfiles
from loopflow.features.dimension.frame import (
    DIM_D_KEY,
    DIM_H_KEY,
    DIM_W_KEY,
    FRAME_KEY,
    ISSUE_NO_BBOX,
    dimensions_in_frame,
    dump_frame,
    resolve_frame,
)
from loopflow.features.dimension.quantity import evaluate_quantity
from loopflow.features.model_data.identity import TYPE_ID_KEY, iter_scan_targets
from loopflow.foundation import results
from loopflow.platform.rhino.session import RhinoSession, run_guarded

COMMAND_ID = "LF_Nexus"
QUANTITY_KEY = "lf_quantity"


def _fmt(value: float) -> str:
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return ("%.6f" % value).rstrip("0").rstrip(".")


def _load_catalog(catalog: Optional[TypeCatalog], environ) -> results.Result:
    if catalog is not None:
        return results.ok("load_dictionary", "已使用注入的 Type Catalog。", details={"catalog": catalog})
    return load_from_workfiles(environ=environ)


def _type_record(session: RhinoSession, object_id: str, catalog: TypeCatalog):
    type_id = session.get_object_user_text(object_id, TYPE_ID_KEY)
    record = catalog.by_type_id(type_id) if type_id else None
    if record is None:
        layer = session.object_layer(object_id) or ""
        record = catalog.by_layer_path(to_relative_path(layer))
        if record is None:
            record = catalog.by_type_id(session.get_layer_user_text(layer, LAYER_TYPE_ID_KEY) or "")
    return record


def scan_dimensions(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    rederive: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """掃描尺寸與數量。不寫入、不猜 World bbox。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "scan_dimensions",
                "使用者取消尺寸／數量 Scan。",
                command_id=command_id,
            )
        loaded = _load_catalog(catalog, environ)
        if not loaded.ok:
            return loaded
        type_catalog = loaded.details["catalog"]
        model_unit = current.model_unit_system()
        items = []
        for object_id in iter_scan_targets(current, selected_only=selected_only):
            issues: List[str] = []
            resolved = resolve_frame(current, object_id, rederive=rederive)
            frame = resolved["frame"]
            if resolved["status"] == "block" and resolved["reason"]:
                issues.append(resolved["reason"])
            bbox = current.object_bbox(object_id)
            wdh = dimensions_in_frame(frame, bbox) if frame is not None else None
            if frame is not None and wdh is None:
                issues.append(ISSUE_NO_BBOX)
            record = _type_record(current, object_id, type_catalog)
            quantity = None
            if wdh is not None and record is not None:
                evaluated = evaluate_quantity(
                    record.measurement_rule,
                    record.estimation_unit,
                    wdh[0],
                    wdh[1],
                    wdh[2],
                    model_unit=model_unit,
                )
                quantity = evaluated["quantity"]
                issues.extend(evaluated["issues"])
            elif wdh is not None and record is None:
                issues.append("unknown_type")
            items.append(
                {
                    "rhino_id": object_id,
                    "frame": frame,
                    "frame_status": resolved["status"],
                    "reused": resolved["reused"],
                    "dimension_w": None if wdh is None else wdh[0],
                    "dimension_d": None if wdh is None else wdh[1],
                    "dimension_h": None if wdh is None else wdh[2],
                    "quantity": quantity,
                    "issues": tuple(dict.fromkeys(issues)),
                }
            )
        blocking = []
        warnings = []
        for item in items:
            for issue in item["issues"]:
                if issue in ("measurement_rule_undefined", "model_unit_not_cm", "unknown_model_unit"):
                    if issue not in warnings:
                        warnings.append(issue)
                elif issue not in blocking:
                    blocking.append(issue)
        payload = {
            "publish_ready": False,
            "items": tuple(items),
            "blocking": tuple(blocking),
            "remaining": tuple(item["rhino_id"] for item in items if item["issues"] and set(item["issues"]) - {
                "measurement_rule_undefined",
                "model_unit_not_cm",
                "unknown_model_unit",
            }),
        }
        message = "尺寸／數量 Scan 完成，%s 個物件。未寫入。不可發布。" % len(items)
        if warnings or blocking:
            return results.ok_with_warnings(
                "scan_dimensions",
                message,
                tuple(warnings + blocking),
                command_id=command_id,
                details=payload,
            )
        return results.ok("scan_dimensions", message, command_id=command_id, details=payload)

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)


def apply_dimensions(
    session: RhinoSession,
    *,
    catalog: Optional[TypeCatalog] = None,
    environ: Optional[Mapping[str, str]] = None,
    selected_only: bool = False,
    rederive: bool = False,
    cancel: bool = False,
    guarded: bool = True,
    command_id: str = COMMAND_ID,
) -> results.Result:
    """寫入 lf_local_frame、lf_dimension_*、lf_quantity。阻擋項不寫尺寸。"""

    def action(current: RhinoSession) -> results.Result:
        if cancel:
            return results.cancelled(
                "apply_dimensions",
                "使用者取消尺寸／數量 Apply。",
                command_id=command_id,
            )
        scanned = scan_dimensions(
            current,
            catalog=catalog,
            environ=environ,
            selected_only=selected_only,
            rederive=rederive,
            cancel=False,
            guarded=False,
            command_id=command_id,
        )
        if not scanned.ok:
            return scanned
        applied = []
        remaining = []
        for item in scanned.details["items"]:
            rhino_id = item["rhino_id"]
            hard = [
                issue
                for issue in item["issues"]
                if issue not in ("measurement_rule_undefined", "model_unit_not_cm", "unknown_model_unit")
            ]
            if hard or item["frame"] is None or item["dimension_w"] is None:
                remaining.append(rhino_id)
                continue
            current.set_object_user_text(rhino_id, FRAME_KEY, dump_frame(item["frame"]))
            current.set_object_user_text(rhino_id, DIM_W_KEY, _fmt(item["dimension_w"]))
            current.set_object_user_text(rhino_id, DIM_D_KEY, _fmt(item["dimension_d"]))
            current.set_object_user_text(rhino_id, DIM_H_KEY, _fmt(item["dimension_h"]))
            if item["quantity"] is None:
                current.set_object_user_text(rhino_id, QUANTITY_KEY, "-")
            else:
                current.set_object_user_text(rhino_id, QUANTITY_KEY, _fmt(item["quantity"]))
            applied.append(rhino_id)
        payload = {
            "publish_ready": False,
            "applied": tuple(applied),
            "remaining": tuple(remaining),
        }
        if remaining and not applied:
            return results.blocked(
                "apply_dimensions",
                "沒有可寫入的尺寸／數量。",
                blocking=scanned.details.get("blocking") or ("nothing_to_apply",),
                command_id=command_id,
                details=payload,
            )
        message = "已 Apply 尺寸／數量。不可發布。"
        if remaining:
            return results.ok_with_warnings(
                "apply_dimensions",
                message + " 剩餘 %s 項。" % len(remaining),
                ("remaining_dimension_work",),
                command_id=command_id,
                details=payload,
            )
        return results.ok("apply_dimensions", message, command_id=command_id, details=payload)

    if not guarded:
        return action(session)
    return run_guarded(session, action, command_id=command_id)
