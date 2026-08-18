# -*- coding: utf-8 -*-
"""Tag 綁定。Grab／Laser 寫來源；Index 寫目標 View；Infuser 另開任務。

Layout ID 在 `layout_id` 模組，不在此套件入口轉出，以免與 Sheet metadata 循環 import。
"""
from loopflow.features.tagger.grab import bind_tag, run_tagger_grab
from loopflow.features.tagger.index import bind_index_view, run_tagger_index
from loopflow.features.tagger.laser import bind_laser_hit, run_tagger_laser
from loopflow.features.tagger.templates import load_tag_templates

__all__ = [
    "bind_index_view",
    "bind_laser_hit",
    "bind_tag",
    "load_tag_templates",
    "run_tagger_grab",
    "run_tagger_index",
    "run_tagger_laser",
]
