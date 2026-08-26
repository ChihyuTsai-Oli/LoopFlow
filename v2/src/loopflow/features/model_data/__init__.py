# -*- coding: utf-8 -*-
"""模型資料功能。NX-03 Space；NX-04 物件 ID／Type。"""
from loopflow.features.model_data.identity import (
    apply_identity,
    rollback_identity,
    scan_identity,
    strip_structure_metadata,
    verify_identity,
)
from loopflow.features.model_data.placement import apply_placement, scan_placement
from loopflow.features.model_data.space import (
    SpaceDraft,
    drafts_from_selection,
    isolate_closed_curves,
    register_level_boundaries,
    register_level_boundaries_interactive,
    register_space_boundaries,
    register_space_boundaries_interactive,
)

__all__ = [
    "SpaceDraft",
    "apply_identity",
    "apply_placement",
    "drafts_from_selection",
    "isolate_closed_curves",
    "register_level_boundaries",
    "register_level_boundaries_interactive",
    "register_space_boundaries",
    "register_space_boundaries_interactive",
    "rollback_identity",
    "scan_identity",
    "scan_placement",
    "strip_structure_metadata",
    "verify_identity",
]
