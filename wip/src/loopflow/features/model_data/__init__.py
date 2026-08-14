# -*- coding: utf-8 -*-
"""模型資料功能。NX-03 Space；NX-04 物件 ID／Type。"""
from loopflow.features.model_data.identity import (
    apply_identity,
    rollback_identity,
    scan_identity,
    verify_identity,
)
from loopflow.features.model_data.placement import apply_placement, scan_placement
from loopflow.features.model_data.space import (
    SpaceDraft,
    drafts_from_selection,
    register_space_boundaries,
)

__all__ = [
    "SpaceDraft",
    "apply_identity",
    "apply_placement",
    "drafts_from_selection",
    "register_space_boundaries",
    "rollback_identity",
    "scan_identity",
    "scan_placement",
    "verify_identity",
]
