# -*- coding: utf-8 -*-
"""以目前 .3dm 所在資料夾解析路徑。字典與 `_LoopFlow_Config` 一律與 .3dm 同層。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from . import results
from .config import AppConfig, DEFAULT_CONFIG

DICTIONARY_FILENAME = "LoopFlow_Dictionary.xlsx"
CONFIG_DIR_NAME = "_LoopFlow_Config"
_FILENAME_FORBIDDEN = frozenset('\\/:*?"<>|')
REGISTRY_FILENAME = "Project_Registry.json"
REGISTRY_LOCK_FILENAME = "Project_Registry.lock"
REGISTRY_PENDING_FILENAME = "Project_Registry.pending.json"
REGISTRY_LAST_GOOD_FILENAME = "Project_Registry.last-good.json"

_UNSAVED_HINT = (
    "請先把這份檔案存成 .3dm。工作資料夾就是 .3dm 所在的資料夾；"
    "尚未存檔就沒有資料夾，無法建立設定、字典位置與 %s。" % CONFIG_DIR_NAME
)
_NO_RHINO_HINT = "目前不在 Rhino 內，無法取得 .3dm 位置。不修改檔案。"
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
    """`.3dm` 所在資料夾即工作資料夾；三者只以相對關係綁定，換碟換機不受影響。"""

    root: Path
    document: Path
    config_dir: Path
    dictionary: Path

    def log_file(self, config: AppConfig = DEFAULT_CONFIG) -> Path:
        return self.config_dir / config.log_dir_name / config.log_filename


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
            "Dictionary 檔名不能空白。",
            details={"filename": ""},
        )
    candidate = Path(text)
    if candidate.is_absolute() or (len(text) >= 2 and text[1] == ":"):
        if root is None:
            return results.blocked(
                "resolve_dictionary",
                "請只輸入檔名。完整路徑須先知道 .3dm 所在資料夾。",
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
                "Dictionary 須和 .3dm 同一層，不能放在子資料夾。",
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
                "請只輸入檔名，不可含資料夾路徑。",
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
                "Dictionary 必須是 .xlsx 檔。",
                blocking=("invalid_dictionary_filename",),
                details={"filename": name},
            )
        name = name + ".xlsx"
    stem = Path(name).stem
    if stem.lower().endswith("_export") or name.lower() == "loopflow_dictionary_export.xlsx":
        return results.blocked(
            "resolve_dictionary",
            "不能把匯出檔當正式 Dictionary。",
            blocking=("export_file_not_dictionary",),
            details={"filename": name},
        )
    return results.ok(
        "resolve_dictionary",
        "已確認 Dictionary 檔名",
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
            _UNSAVED_HINT,
            blocking=("unsaved_document",),
        )
    folder = Path(text).expanduser()
    parent = folder.parent
    if str(parent) in ("", "."):
        return results.blocked(
            "resolve_document",
            _UNSAVED_HINT,
            blocking=("unsaved_document",),
        )
    return results.ok(
        "resolve_document",
        "已確認檔案所在資料夾",
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
    """由 .3dm 位置組出工作資料夾、設定資料夾與字典路徑。不建立任何檔案。"""
    located = document_directory(document_path)
    if not located.ok:
        return located
    root = Path(located.details["document_dir"])
    filename = DICTIONARY_FILENAME
    if dictionary_filename not in (None, ""):
        normalized = normalize_dictionary_filename(dictionary_filename, root=root)
        if not normalized.ok:
            return normalized
        filename = str(normalized.details["filename"])
    paths = ProjectPaths(
        root=root,
        document=Path(located.details["document_path"]),
        config_dir=root / CONFIG_DIR_NAME,
        dictionary=root / filename,
    )
    return results.ok(
        "resolve_project_folder",
        "已解析 .3dm 工作資料夾",
        details={"paths": paths},
    )


def resolve_project_folder(session, dictionary_filename: Optional[str] = None) -> results.Result:
    """目前 Rhino 文件的工作資料夾。沒有 session 或未存檔時停止。"""
    if session is None:
        return results.failed("rhino_session", _NO_RHINO_HINT)
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
    config_dir = Path(located.details["document_dir"]) / CONFIG_DIR_NAME
    details = dict(located.details)
    details["config_dir"] = config_dir
    return results.ok(
        "resolve_config_dir",
        "已解析 %s 資料夾" % CONFIG_DIR_NAME,
        details=details,
    )


def resolve_registry_for_document(
    document_path: Optional[Union[str, Path]],
    project_id: Optional[str],
) -> results.Result:
    """Registry 在 <目前 3dm 資料夾>/_LoopFlow_Config/<專案名稱>/。"""
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
            "缺少專案名稱，停止解析 Registry。請先跑 Nexus 選單 2 填專案名稱。",
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
        "已解析 Registry 路徑",
        details={
            "project_id": pid,
            "folder": folder,
            "registry": folder / REGISTRY_FILENAME,
            "lock": folder / REGISTRY_LOCK_FILENAME,
            "pending": folder / REGISTRY_PENDING_FILENAME,
            "last_good": folder / REGISTRY_LAST_GOOD_FILENAME,
        },
    )
