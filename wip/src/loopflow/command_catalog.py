# -*- coding: utf-8 -*-
"""已登錄的 2.0 指令目錄。

入口檔名即 command ID。此表只聲明身分與實作狀態，不含業務邏輯。
尚未建立的入口不得標為 ready。
"""
from __future__ import annotations

from typing import Optional

# 核心主鏈；與資料契約「指令 ID」一致。2D 工具不在此列。
CORE_COMMANDS = (
    "LF_Nexus",
    "LF_Dictionary_Editor",
    "LF_Data_Viewer",
    "LF_Push_3D_to_JSON",
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
    "LF_Sync_Worksession",
)

_COMMANDS = {
    command_id: {
        "command_id": command_id,
        "entrypoint": "%s.py" % command_id,
        "status": "not_implemented",
        "task": "pending",
    }
    for command_id in CORE_COMMANDS
}
_COMMANDS["LF_Nexus"]["status"] = "console"
_COMMANDS["LF_Nexus"]["task"] = "C02/NX-04"


def get_command(command_id: str) -> Optional[dict]:
    return _COMMANDS.get(command_id)


def list_commands():
    return tuple(_COMMANDS[cid] for cid in CORE_COMMANDS)
