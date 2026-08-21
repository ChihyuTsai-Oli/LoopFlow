# -*- coding: utf-8 -*-
"""以 LOOPFLOW_WORKFILES_ROOT 解析工作檔，不寫死磁碟機、不猜路徑。"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional, Union

from . import results
from .config import AppConfig, DEFAULT_CONFIG

WORKFILES_ROOT_ENV = "LOOPFLOW_WORKFILES_ROOT"
DICTIONARY_FILENAME = "LoopFlow_Dictionary.xlsx"
DICTIONARY_FILENAME_KEY = "lf_dictionary_filename"
EXCHANGE_DIR_NAME = "exchange"
_FILENAME_FORBIDDEN = frozenset('\\/:*?"<>|')
REGISTRY_FILENAME = "Project_Registry.json"
REGISTRY_LOCK_FILENAME = "Project_Registry.lock"
REGISTRY_PENDING_FILENAME = "Project_Registry.pending.json"
REGISTRY_LAST_GOOD_FILENAME = "Project_Registry.last-good.json"

_MISSING_ROOT_HINT = (
    "缺少或無效的 %s。請在本機設定該環境變數，指向既有的工作檔資料夾"
    "（見工作區根目錄的工作檔路徑說明），然後重開程式。不得猜測磁碟機，也不建立正式資料。"
    % WORKFILES_ROOT_ENV
)
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
    """檔案是否在工作檔根目錄內。不因大小寫或 `\\\\?\\` 前綴誤判成別的磁碟。"""
    try:
        return canonical_path(path).relative_to(canonical_path(root))
    except (ValueError, OSError):
        return None


@dataclass(frozen=True)
class WorkfilesPaths:
    root: Path
    dictionary: Path
    exchange_root: Path

    def log_file(self, config: AppConfig = DEFAULT_CONFIG) -> Path:
        return self.root / config.log_dir_name / config.log_filename


def _environ(environ: Optional[Mapping[str, str]] = None) -> Mapping[str, str]:
    return os.environ if environ is None else environ


def normalize_dictionary_filename(
    raw: Optional[str],
    *,
    root: Optional[Path] = None,
) -> results.Result:
    """只允許工作檔根目錄下的單一 .xlsx 檔名。可帶完整路徑，但必須落在該資料夾內。"""
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
                "請只輸入檔名。完整路徑須先有工作檔資料夾。",
                blocking=("dictionary_outside_workfiles",),
                details={"filename": text},
            )
        relative = path_relative_to_root(candidate, root)
        if relative is None:
            return results.blocked(
                "resolve_dictionary",
                "必須選工作檔資料夾內的 Excel，不能用其他磁碟或路徑。\n選到：%s\n必須在：%s"
                % (candidate, root),
                blocking=("dictionary_outside_workfiles",),
                details={
                    "filename": candidate.name,
                    "selected": str(candidate),
                    "workfiles_root": str(root),
                },
            )
        if len(relative.parts) != 1:
            return results.blocked(
                "resolve_dictionary",
                "Dictionary 須放在工作檔資料夾根目錄，不能在子資料夾。",
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


def dictionary_filename_from_session(session) -> str:
    remembered = remembered_dictionary_filename(session)
    if remembered:
        return remembered
    return DICTIONARY_FILENAME


def remembered_dictionary_filename(session) -> Optional[str]:
    """只回這份文件記住的 Dictionary 檔名。沒記住就不套預設檔名。"""
    if session is None:
        return None
    getter = getattr(session, "document_user_text", None)
    raw = getter(DICTIONARY_FILENAME_KEY) if callable(getter) else None
    if raw in (None, ""):
        return None
    normalized = normalize_dictionary_filename(raw)
    if normalized.ok:
        return str(normalized.details["filename"])
    return None


def resolve_workfiles(
    environ: Optional[Mapping[str, str]] = None,
    dictionary_filename: Optional[str] = None,
) -> results.Result:
    """解析工作檔根目錄。目錄必須已存在；不建立、不搜尋 .3dm 旁路徑。"""
    raw = (_environ(environ).get(WORKFILES_ROOT_ENV) or "").strip()
    if not raw:
        return results.failed(
            "resolve_workfiles",
            _MISSING_ROOT_HINT,
            details={"env": WORKFILES_ROOT_ENV},
        )
    root = Path(raw)
    if not root.exists() or not root.is_dir():
        return results.failed(
            "resolve_workfiles",
            _MISSING_ROOT_HINT,
            details={"env": WORKFILES_ROOT_ENV, "exists": root.exists()},
        )
    filename = DICTIONARY_FILENAME
    if dictionary_filename not in (None, ""):
        normalized = normalize_dictionary_filename(dictionary_filename, root=root)
        if not normalized.ok:
            return normalized
        filename = str(normalized.details["filename"])
    paths = WorkfilesPaths(
        root=root,
        dictionary=root / filename,
        exchange_root=root / EXCHANGE_DIR_NAME,
    )
    return results.ok(
        "resolve_workfiles",
        "已解析工作檔根目錄",
        details={"paths": paths},
    )


def dictionary_path(root: Path, filename: Optional[str] = None) -> Path:
    name = filename or DICTIONARY_FILENAME
    normalized = normalize_dictionary_filename(name, root=root)
    if normalized.ok:
        name = str(normalized.details["filename"])
    else:
        name = DICTIONARY_FILENAME
    return Path(root) / name


def normalize_project_id(value: Optional[str]) -> Optional[str]:
    """專案名稱＝圖層前綴＝exchange 資料夾名。禁止空白與路徑／檔名非法字元。"""
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
            "請先把這份檔案存成 .3dm。尚未存檔就沒有資料夾，無法建立 exchange。",
            blocking=("unsaved_document",),
        )
    folder = Path(text).expanduser()
    parent = folder.parent
    if str(parent) in ("", "."):
        return results.blocked(
            "resolve_document",
            "請先把這份檔案存成 .3dm。尚未存檔就沒有資料夾，無法建立 exchange。",
            blocking=("unsaved_document",),
        )
    return results.ok(
        "resolve_document",
        "已確認檔案所在資料夾",
        details={"document_path": folder, "document_dir": parent},
    )


def exchange_root_for_document(document_path: Optional[Union[str, Path]]) -> results.Result:
    located = document_directory(document_path)
    if not located.ok:
        return located
    root = Path(located.details["document_dir"]) / EXCHANGE_DIR_NAME
    details = dict(located.details)
    details["exchange_root"] = root
    return results.ok(
        "resolve_exchange",
        "已解析 exchange 資料夾",
        details=details,
    )


def resolve_registry_for_document(
    document_path: Optional[Union[str, Path]],
    project_id: Optional[str],
) -> results.Result:
    """Registry 在 <目前 3dm 資料夾>/exchange/<專案名稱>/。"""
    located = exchange_root_for_document(document_path)
    if not located.ok:
        return located
    resolved = registry_paths(located.details["exchange_root"], project_id or "")
    if not resolved.ok:
        return resolved
    details = dict(located.details)
    details.update(resolved.details)
    return results.ok(
        resolved.stage,
        resolved.message,
        details=details,
    )


def registry_paths(exchange_root: Path, project_id: str) -> results.Result:
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
    folder = Path(exchange_root) / pid
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
