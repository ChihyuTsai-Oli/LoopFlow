# -*- coding: utf-8 -*-
"""已登錄的 2.0 指令目錄。

入口檔名即 command ID。此表只聲明身分與實作狀態，不含業務邏輯。
已實作的指令在 `loopflow.runners` 以同一 ID 登錄 runner；尚未實作的不得標為 ready。
"""
from __future__ import annotations

from typing import Optional

# 核心主鏈；與資料契約「指令 ID」一致。2D 工具不在此列。
CORE_COMMANDS = (
    "LF_Open_Dictionary",
    "LF_Open_Dictionary_Export",
    "LF_Nexus",
    "LF_Export_Type_Layers",
    "LF_Publish_Exchange",
    "LF_Data_Viewer",
    "LF_Tagger_Grab",
    "LF_Tagger_Laser",
    "LF_Tagger_Index",
    "LF_Tagger_Layout_ID",
    "LF_TAG-O",
    "LF_Infuser_Part",
    "LF_Infuser_All",
    "LF_Anchor_Frame",
    "LF_Extract_CP",
    "LF_Duplicate_Layout",
    "LF_Catalog",
    "LF_Sync_Worksession",
)

_READY = {
    "LF_Open_Dictionary": "C02/open-dictionary",
    "LF_Open_Dictionary_Export": "C02/open-dictionary",
    "LF_Nexus": "C02/menu",
    "LF_Export_Type_Layers": "C02/NX-02-export",
    "LF_Publish_Exchange": "C02/NX-07",
    "LF_Data_Viewer": "C04",
    "LF_Tagger_Grab": "D01",
    "LF_Tagger_Laser": "D02",
    "LF_Tagger_Index": "D03",
    "LF_Tagger_Layout_ID": "D04",
    "LF_Anchor_Frame": "E01",
    "LF_Catalog": "E05",
    "LF_Infuser_Part": "D06",
    "LF_Infuser_All": "D07",
}

_COMMANDS = {
    command_id: {
        "command_id": command_id,
        "entrypoint": "%s.py" % command_id,
        "status": "not_implemented",
        "task": "pending",
    }
    for command_id in CORE_COMMANDS
}
for _command_id, _task in _READY.items():
    _COMMANDS[_command_id]["status"] = "ready"
    _COMMANDS[_command_id]["task"] = _task


def get_command(command_id: str) -> Optional[dict]:
    return _COMMANDS.get(command_id)


def list_commands():
    return tuple(_COMMANDS[cid] for cid in CORE_COMMANDS)


def ready_command_ids():
    return tuple(cid for cid in CORE_COMMANDS if _COMMANDS[cid]["status"] == "ready")
