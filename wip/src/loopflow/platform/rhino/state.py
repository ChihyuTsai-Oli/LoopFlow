# -*- coding: utf-8 -*-
"""Rhino 文件視圖狀態：選取、鎖定、隱藏、顏色。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

Color = Tuple[int, int, int]


@dataclass(frozen=True)
class ObjectViewState:
    object_id: str
    selected: bool
    locked: bool
    hidden: bool
    color: Color
    color_by_layer: bool


@dataclass(frozen=True)
class DocumentSnapshot:
    objects: Tuple[ObjectViewState, ...]
    document_modified: bool

    def object_ids(self):
        return tuple(item.object_id for item in self.objects)

    def get(self, object_id: str) -> Optional[ObjectViewState]:
        for item in self.objects:
            if item.object_id == object_id:
                return item
        return None
