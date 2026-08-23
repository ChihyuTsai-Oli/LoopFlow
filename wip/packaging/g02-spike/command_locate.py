# -*- coding: utf-8 -*-
"""找出 loopflow 套件根（src 或 lib）。

RhinoCode 執行 yak 指令時，會把腳本拷到 `%USERPROFILE%\\.rhinocode\\stage\\`，
`__file__` 不再位於套件目錄。`PathFromName("LoopFlow")` 更新後也可能仍指向已刪的舊版路徑。
因此還要搜 Package Manager 安裝位置。指令 `.py` 必須內嵌同一份邏輯，不能在執行期 import 本檔。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Mapping, Optional

PLUGIN_ID = "e6822bb2-91ef-4bee-9564-45de3508ccfb"


def has_loopflow(root: Path) -> bool:
    try:
        return (root / "loopflow" / "bootstrap.py").is_file()
    except Exception:
        return False


def from_package_dir(package_dir: Optional[Path]) -> Optional[Path]:
    if package_dir is None:
        return None
    try:
        package_dir = Path(str(package_dir))
        if not package_dir.is_dir():
            return None
        package_dir = package_dir.resolve()
    except Exception:
        return None
    for candidate in (package_dir / "lib", package_dir / "src", package_dir):
        if has_loopflow(candidate):
            return candidate
    return None


def from_rhp(rhp: object) -> Optional[Path]:
    if not rhp:
        return None
    try:
        path = Path(str(rhp))
        if path.is_file():
            return from_package_dir(path.resolve().parent)
        return from_package_dir(path)
    except Exception:
        return None


def from_script(script_file: str) -> Optional[Path]:
    try:
        here = Path(str(script_file)).resolve()
    except Exception:
        return None
    for parent in here.parents:
        found = from_package_dir(parent)
        if found:
            return found
        for folder in ("src", "lib"):
            if has_loopflow(parent / folder):
                return parent / folder
    return None


def _version_key(name: str):
    parts = []
    for bit in name.split("."):
        try:
            parts.append((0, int(bit)))
        except ValueError:
            parts.append((1, bit))
    return parts


def from_yak_install(environ: Optional[Mapping[str, str]] = None) -> Optional[Path]:
    env = environ if environ is not None else os.environ
    roots = []
    for key in ("APPDATA", "LOCALAPPDATA"):
        base = str(env.get(key) or "").strip()
        if base:
            roots.append(
                Path(base) / "McNeel" / "Rhinoceros" / "packages" / "8.0" / "loopflow"
            )
    found = []
    for root in roots:
        try:
            if not root.is_dir():
                continue
            for version_dir in root.iterdir():
                if not version_dir.is_dir():
                    continue
                hit = from_package_dir(version_dir)
                if hit:
                    found.append((version_dir.name, hit))
        except Exception:
            continue
    if not found:
        return None
    found.sort(key=lambda item: _version_key(item[0]))
    return found[-1][1]


def resolve_loopflow_src(
    script_file: str,
    environ: Optional[Mapping[str, str]] = None,
    plugin_rhps: Iterable[object] = (),
) -> Path:
    hit = from_script(script_file)
    if hit:
        return hit
    for rhp in plugin_rhps:
        hit = from_rhp(rhp)
        if hit:
            return hit
    hit = from_yak_install(environ)
    if hit:
        return hit
    raise RuntimeError("找不到 loopflow 套件（src 或 lib）。")


def wrapper_source(official: str, dev_id: str) -> str:
    """內嵌查找邏輯的正式指令腳本。RhinoCode 執行時不會帶上本模組。"""
    return '''#! python 3
# -*- coding: utf-8 -*-
"""G02 套件登錄的正式指令 %s。開發期入口仍是 %s.py，不要改那個檔名。"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PLUGIN_ID = "e6822bb2-91ef-4bee-9564-45de3508ccfb"


def _has_loopflow(root):
    try:
        return (root / "loopflow" / "bootstrap.py").is_file()
    except Exception:
        return False


def _from_package_dir(package_dir):
    if package_dir is None:
        return None
    try:
        package_dir = Path(str(package_dir))
        if not package_dir.is_dir():
            return None
        package_dir = package_dir.resolve()
    except Exception:
        return None
    for candidate in (package_dir / "lib", package_dir / "src", package_dir):
        if _has_loopflow(candidate):
            return candidate
    return None


def _from_rhp(rhp):
    if not rhp:
        return None
    try:
        path = Path(str(rhp))
        if path.is_file():
            return _from_package_dir(path.resolve().parent)
        return _from_package_dir(path)
    except Exception:
        return None


def _from_script(script_file):
    try:
        here = Path(str(script_file)).resolve()
    except Exception:
        return None
    for parent in here.parents:
        found = _from_package_dir(parent)
        if found:
            return found
        for folder in ("src", "lib"):
            if _has_loopflow(parent / folder):
                return parent / folder
    return None


def _version_key(name):
    parts = []
    for bit in name.split("."):
        try:
            parts.append((0, int(bit)))
        except ValueError:
            parts.append((1, bit))
    return parts


def _from_yak_install():
    roots = []
    for key in ("APPDATA", "LOCALAPPDATA"):
        base = str(os.environ.get(key) or "").strip()
        if base:
            roots.append(
                Path(base) / "McNeel" / "Rhinoceros" / "packages" / "8.0" / "loopflow"
            )
    found = []
    for root in roots:
        try:
            if not root.is_dir():
                continue
            for version_dir in root.iterdir():
                if not version_dir.is_dir():
                    continue
                hit = _from_package_dir(version_dir)
                if hit:
                    found.append((version_dir.name, hit))
        except Exception:
            continue
    if not found:
        return None
    found.sort(key=lambda item: _version_key(item[0]))
    return found[-1][1]


def _plugin_rhps():
    paths = []
    try:
        import Rhino
        from System import Guid
    except Exception:
        return paths
    try:
        paths.append(Rhino.PlugIns.PlugIn.PathFromId(Guid(PLUGIN_ID)))
    except Exception:
        pass
    try:
        paths.append(Rhino.PlugIns.PlugIn.PathFromName("LoopFlow"))
    except Exception:
        pass
    return paths


def _loopflow_src():
    hit = _from_script(__file__)
    if hit:
        return hit
    for rhp in _plugin_rhps():
        hit = _from_rhp(rhp)
        if hit:
            return hit
    hit = _from_yak_install()
    if hit:
        return hit
    raise RuntimeError("找不到 loopflow 套件（src 或 lib）。")


_SRC = str(_loopflow_src())
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from loopflow.bootstrap import run_command  # noqa: E402

run_command("%s")
''' % (official, dev_id, dev_id)
