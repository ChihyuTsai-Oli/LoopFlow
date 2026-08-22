# -*- coding: utf-8 -*-
"""把 Registry／Sheet 資料注入 Tag 顯示欄。Part 處理當前頁，All 處理全檔。"""
from loopflow.features.infuser.all import run_infuser_all
from loopflow.features.infuser.part import infuse_page, run_infuser_part

__all__ = ["infuse_page", "run_infuser_part", "run_infuser_all"]
