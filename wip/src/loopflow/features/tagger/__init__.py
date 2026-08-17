# -*- coding: utf-8 -*-
"""Tag 綁定。Grab／Laser 寫來源；Index／Infuser 另開任務。"""
from loopflow.features.tagger.grab import bind_tag, run_tagger_grab
from loopflow.features.tagger.laser import bind_laser_hit, run_tagger_laser
from loopflow.features.tagger.templates import load_tag_templates

__all__ = [
    "bind_laser_hit",
    "bind_tag",
    "load_tag_templates",
    "run_tagger_grab",
    "run_tagger_laser",
]
