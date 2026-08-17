# -*- coding: utf-8 -*-
"""Tag 綁定。Grab 寫來源；Laser／Index／Infuser 另開任務。"""
from loopflow.features.tagger.grab import bind_tag, run_tagger_grab
from loopflow.features.tagger.templates import load_tag_templates

__all__ = ["bind_tag", "load_tag_templates", "run_tagger_grab"]
