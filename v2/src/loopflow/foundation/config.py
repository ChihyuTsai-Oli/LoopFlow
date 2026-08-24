# -*- coding: utf-8 -*-
"""可調的進階設定。

Registry 檔名、layer path、schema 與 UserText key 屬契約，不放這裡。
"""
from __future__ import annotations
from loopflow.foundation.i18n import t

from dataclasses import dataclass

from . import results


@dataclass(frozen=True)
class AppConfig:
    log_dir_name: str = "logs"
    log_filename: str = "loopflow.log"
    worksession_refresh_delay: float = 0.5


DEFAULT_CONFIG = AppConfig()


def load_config() -> results.Result:
    """目前只提供程式內建預設；尚未讀使用者覆寫檔。"""
    cfg = DEFAULT_CONFIG
    return results.ok(
        "load_config",
        t("foundation.010"),
        details={
            "log_dir_name": cfg.log_dir_name,
            "log_filename": cfg.log_filename,
            "worksession_refresh_delay": cfg.worksession_refresh_delay,
        },
    )
