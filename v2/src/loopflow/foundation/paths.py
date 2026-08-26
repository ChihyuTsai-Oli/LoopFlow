# -*- coding: utf-8 -*-
"""以目前 .3dm 所在資料夾解析路徑。字典與 `_LoopFlow_Config` 一律與 .3dm 同層。

LoopFlow 的設定、Registry 與 log 在 `_LoopFlow_Config/loopflow/`。
其他產品（R2B／R2O／QTY）各用自己的子資料夾，不混在一起。
"""
from __future__ import annotations
from loopflow.foundation.i18n import t

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from . import results
from .config import AppConfig, DEFAULT_CONFIG

DICTIONARY_FILENAME = "LoopFlow_Dictionary.xlsx"
CONFIG_DIR_NAME = "_LoopFlow_Config"
PRODUCT_DIR_NAME = "loopflow"
PROJECT_CONFIG_FILENAME = "LoopFlow_Project.json"
SIBLING_PRODUCT_DIR_NAMES = frozenset(
    {"loopflow", "loopflow_R2B", "loopflow_R2O", "loopflow_QTY"}
)
_FILENAME_FORBIDDEN = frozenset('\\/:*?"<>|')
REGISTRY_FILENAME = "Project_Registry.json"
REGISTRY_LOCK_FILENAME = "Project_Registry.lock"
REGISTRY_PENDING_FILENAME = "Project_Registry.pending.json"
REGISTRY_LAST_GOOD_FILENAME = "Project_Registry.last-good.json"

_EXTENDED_PATH_PREFIX = "\\\\?\\"
_EXTENDED_UNC_PREFIX = "\\\\?\\UNC\\"


def canonical_path(path: Union[str, Path]) -> Path:
    """去掉 Windows `\\\\?\\` 前綴，再做成可比較的絕對路徑。大小寫不當作不同資料夾。"""
    text = os.fspath(path).strip().strip('"')
    if text.startswith(_EXTENDED_UNC_PREFIX):
        text = "\\\\" + text[len(_EXTENDED_UNC_PREFIX) :]
    elif text.startswith(_EXTENDED_PATH_PREFIX):
        text = text[len(_EXTENDED_PATH_PREFIX) :]
    return Path(os.path.normcase(os.path.abspath(os.path.realpath(text))))


def path_relative_to_root(path: Union[str, Path], root: Union[str, Path]) -> Optional[Path]:
    """檔案是否在該資料夾內。不因大小寫或 `\\\\?\\` 前綴誤判成別的磁碟。"""
    try:
        return canonical_path(path).relative_to(canonical_path(root))
    except (ValueError, OSError):
        return None


@dataclass(frozen=True)
class ProjectPaths:
    """`.3dm` 所在資料夾即工作資料夾；三者只以相對關係綁定，換碟換機不受影響。

    `config_dir` 是 LoopFlow 產品資料夾：`_LoopFlow_Config/loopflow`。
    """

    root: Path
    document: Path
    config_dir: Path
    dictionary: Path

    def log_file(self, config: AppConfig = DEFAULT_CONFIG) -> Path:
        return self.config_dir / config.log_dir_name / config.log_filename


def shared_config_dir(root: Union[str, Path]) -> Path:
    """各產品共用的 `_LoopFlow_Config` 父資料夾。"""
    return Path(root) / CONFIG_DIR_NAME


def loopflow_config_dir(root: Union[str, Path]) -> Path:
    """LoopFlow 自己的設定／Registry／log 資料夾。"""
    return shared_config_dir(root) / PRODUCT_DIR_NAME


def _is_reserved_product_dir(name: str) -> bool:
    return name.casefold() in {item.casefold() for item in SIBLING_PRODUCT_DIR_NAMES}


def migrate_legacy_loopflow_config(root: Union[str, Path]) -> results.Result:
    """把 2.0.6 以前寫在 `_LoopFlow_Config` 根層的 LoopFlow 檔搬進 `loopflow/`。

    新路徑已有 `LoopFlow_Project.json` 時只認新路徑，不搬剩餘舊檔。
    不搬 `loopflow_R2B`／`loopflow_R2O`／`loopflow_QTY`。失敗不刪來源。
    """
    root_path = Path(root)
    dest = loopflow_config_dir(root_path)
    dest_json = dest / PROJECT_CONFIG_FILENAME
    if dest_json.is_file():
        return results.ok(
            "migrate_loopflow_config",
            t("paths.005"),
            details={"config_dir": dest, "migrated": False},
        )
    shared = shared_config_dir(root_path)
    if not shared.exists():
        return results.ok(
            "migrate_loopflow_config",
            t("paths.005"),
            details={"config_dir": dest, "migrated": False},
        )
    items = []
    src_json = shared / PROJECT_CONFIG_FILENAME
    if src_json.is_file():
        items.append(src_json)
    src_logs = shared / "logs"
    if src_logs.exists():
        items.append(src_logs)
    try:
        children = list(shared.iterdir())
    except OSError as exc:
        return results.failed(
            "migrate_loopflow_config",
            "無法讀取舊設定資料夾：%s" % exc,
            details={"config_dir": str(shared)},
        )
    for child in children:
        if not child.is_dir():
            continue
        if child.name.casefold() == "logs":
            continue
        if _is_reserved_product_dir(child.name):
            continue
        if (child / REGISTRY_FILENAME).is_file():
            items.append(child)
    if not items:
        return results.ok(
            "migrate_loopflow_config",
            t("paths.005"),
            details={"config_dir": dest, "migrated": False},
        )
    try:
        dest.mkdir(parents=True, exist_ok=True)
        for item in items:
            target = dest / item.name
            if target.exists():
                return results.failed(
                    "migrate_loopflow_config",
                    "無法把舊設定搬進 loopflow：目標已有同名項目 %s" % item.name,
                    details={"source": str(item), "target": str(target)},
                )
            shutil.move(str(item), str(target))
    except OSError as exc:
        return results.failed(
            "migrate_loopflow_config",
            "搬移舊設定失敗：%s" % exc,
            details={"config_dir": str(dest)},
        )
    return results.ok(
        "migrate_loopflow_config",
        t("paths.005"),
        details={"config_dir": dest, "migrated": True},
    )


def normalize_dictionary_filename(
    raw: Optional[str],
    *,
    root: Optional[Path] = None,
) -> results.Result:
    """只允許 .3dm 同一層的單一 .xlsx 檔名。可帶完整路徑，但必須落在該資料夾內。"""
    text = str(raw or "").strip().strip('"')
    if not text:
        return results.failed(
            "resolve_dictionary",
            t("paths.007"),
            details={"filename": ""},
        )
    candidate = Path(text)
    if candidate.is_absolute() or (len(text) >= 2 and text[1] == ":"):
        if root is None:
            return results.blocked(
                "resolve_dictionary",
                t("paths.013"),
                blocking=("dictionary_outside_project_folder",),
                details={"filename": text},
            )
        relative = path_relative_to_root(candidate, root)
        if relative is None:
            return results.blocked(
                "resolve_dictionary",
                "Dictionary 必須和 .3dm 放在同一個資料夾。\n選到：%s\n必須在：%s"
                % (candidate, root),
                blocking=("dictionary_outside_project_folder",),
                details={
                    "filename": candidate.name,
                    "selected": str(candidate),
                    "project_folder": str(root),
                },
            )
        if len(relative.parts) != 1:
            return results.blocked(
                "resolve_dictionary",
                t("paths.014"),
                blocking=("dictionary_not_basename",),
                details={"filename": Path(candidate).name},
            )
        name = Path(candidate).name
    else:
        normalized = text.replace("\\", "/")
        parts = Path(normalized).parts
        if ".." in parts or len(parts) != 1:
            return results.blocked(
                "resolve_dictionary",
                t("paths.015"),
                blocking=("dictionary_not_basename",),
                details={"filename": text},
            )
        name = Path(normalized).name
    if any(char in name for char in _FILENAME_FORBIDDEN):
        return results.blocked(
            "resolve_dictionary",
            "Dictionary 檔名不可含 \\ / : * ? \" < > |",
            blocking=("invalid_dictionary_filename",),
            details={"filename": name},
        )
    suffix = Path(name).suffix
    if suffix.lower() != ".xlsx":
        if suffix:
            return results.blocked(
                "resolve_dictionary",
                t("paths.016"),
                blocking=("invalid_dictionary_filename",),
                details={"filename": name},
            )
        name = name + ".xlsx"
    stem = Path(name).stem
    if stem.lower().endswith("_export") or name.lower() == "loopflow_dictionary_export.xlsx":
        return results.blocked(
            "resolve_dictionary",
            t("paths.009"),
            blocking=("export_file_not_dictionary",),
            details={"filename": name},
        )
    return results.ok(
        "resolve_dictionary",
        t("paths.003"),
        details={"filename": name},
    )


def export_dictionary_filename(official_name: str) -> str:
    stem = Path(official_name or DICTIONARY_FILENAME).stem or Path(DICTIONARY_FILENAME).stem
    return "%s_Export.xlsx" % stem


def normalize_project_id(value: Optional[str]) -> Optional[str]:
    """專案名稱＝圖層前綴＝Registry 子資料夾名。禁止空白與路徑／檔名非法字元。"""
    text = str(value or "").strip()
    if not text:
        return None
    if any(char in text for char in _FILENAME_FORBIDDEN):
        return None
    if text in (".", "..") or ".." in text.replace("\\", "/"):
        return None
    return text


def document_directory(document_path: Optional[Union[str, Path]]) -> results.Result:
    """已存檔的 .3dm 所在資料夾。未存檔不猜測、不建檔。"""
    text = str(document_path or "").strip()
    if not text:
        return results.blocked(
            "resolve_document",
            t("paths.002") % CONFIG_DIR_NAME,
            blocking=("unsaved_document",),
        )
    folder = Path(text).expanduser()
    parent = folder.parent
    if str(parent) in ("", "."):
        return results.blocked(
            "resolve_document",
            t("paths.002") % CONFIG_DIR_NAME,
            blocking=("unsaved_document",),
        )
    return results.ok(
        "resolve_document",
        t("paths.004"),
        details={"document_path": folder, "document_dir": parent},
    )


def document_path_of(session) -> Optional[str]:
    getter = getattr(session, "document_path", None) if session is not None else None
    if not callable(getter):
        return None
    return getter()


def project_paths_for_document(
    document_path: Optional[Union[str, Path]],
    dictionary_filename: Optional[str] = None,
) -> results.Result:
    """由 .3dm 位置組出工作資料夾、LoopFlow 設定資料夾與字典路徑。

    空專案不建檔。若 `_LoopFlow_Config` 根層還有舊的 LoopFlow 設定／Registry，會搬進 `loopflow/`。
    """
    located = document_directory(document_path)
    if not located.ok:
        return located
    root = Path(located.details["document_dir"])
    migrated = migrate_legacy_loopflow_config(root)
    if not migrated.ok:
        return migrated
    filename = DICTIONARY_FILENAME
    if dictionary_filename not in (None, ""):
        normalized = normalize_dictionary_filename(dictionary_filename, root=root)
        if not normalized.ok:
            return normalized
        filename = str(normalized.details["filename"])
    paths = ProjectPaths(
        root=root,
        document=Path(located.details["document_path"]),
        config_dir=loopflow_config_dir(root),
        dictionary=root / filename,
    )
    return results.ok(
        "resolve_project_folder",
        t("paths.005"),
        details={"paths": paths},
    )


def resolve_project_folder(session, dictionary_filename: Optional[str] = None) -> results.Result:
    """目前 Rhino 文件的工作資料夾。沒有 session 或未存檔時停止。"""
    if session is None:
        return results.failed("rhino_session", t("paths.001"))
    return project_paths_for_document(
        document_path_of(session),
        dictionary_filename=dictionary_filename,
    )


def dictionary_path(root: Path, filename: Optional[str] = None) -> Path:
    name = filename or DICTIONARY_FILENAME
    normalized = normalize_dictionary_filename(name, root=root)
    if normalized.ok:
        name = str(normalized.details["filename"])
    else:
        name = DICTIONARY_FILENAME
    return Path(root) / name


def config_dir_for_document(document_path: Optional[Union[str, Path]]) -> results.Result:
    located = document_directory(document_path)
    if not located.ok:
        return located
    root = Path(located.details["document_dir"])
    migrated = migrate_legacy_loopflow_config(root)
    if not migrated.ok:
        return migrated
    config_dir = loopflow_config_dir(root)
    details = dict(located.details)
    details["config_dir"] = config_dir
    details["migrated"] = bool(migrated.details.get("migrated"))
    return results.ok(
        "resolve_config_dir",
        t("paths.010") % ("%s\\%s" % (CONFIG_DIR_NAME, PRODUCT_DIR_NAME)),
        details=details,
    )


def resolve_registry_for_document(
    document_path: Optional[Union[str, Path]],
    project_id: Optional[str],
) -> results.Result:
    """Registry 在 <目前 3dm 資料夾>/_LoopFlow_Config/loopflow/<專案名稱>/。"""
    located = config_dir_for_document(document_path)
    if not located.ok:
        return located
    resolved = registry_paths(located.details["config_dir"], project_id or "")
    if not resolved.ok:
        return resolved
    details = dict(located.details)
    details.update(resolved.details)
    return results.ok(
        resolved.stage,
        resolved.message,
        details=details,
    )


def registry_paths(config_dir: Path, project_id: str) -> results.Result:
    raw = str(project_id or "").strip()
    if not raw:
        return results.failed(
            "resolve_registry",
            t("paths.011"),
        )
    pid = normalize_project_id(raw)
    if pid is None:
        return results.blocked(
            "resolve_registry",
            "專案名稱不可含 \\ / : * ? \" < > |，也不可當資料夾路徑。",
            blocking=("invalid_project_id",),
            details={"project_id": raw},
        )
    folder = Path(config_dir) / pid
    return results.ok(
        "resolve_registry",
        t("paths.006"),
        details={
            "project_id": pid,
            "folder": folder,
            "registry": folder / REGISTRY_FILENAME,
            "lock": folder / REGISTRY_LOCK_FILENAME,
            "pending": folder / REGISTRY_PENDING_FILENAME,
            "last_good": folder / REGISTRY_LAST_GOOD_FILENAME,
        },
    )
