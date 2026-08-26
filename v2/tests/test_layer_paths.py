# -*- coding: utf-8 -*-
"""結構層辨認：相對路徑第一段代號 00_STR，不用 type_category。"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.dictionary.layer_paths import is_structure_layer, to_full_path


class StructureLayerTests(unittest.TestCase):
    def test_group_and_children(self):
        self.assertTrue(is_structure_layer(to_full_path("00_STR_結構")))
        self.assertTrue(is_structure_layer(to_full_path("00_STR_結構::Beam.樑")))
        self.assertTrue(is_structure_layer(to_full_path("00_STR_Structure::Beam")))
        self.assertTrue(is_structure_layer("M3D::00_STR"))

    def test_other_groups_are_not_structure(self):
        self.assertFalse(is_structure_layer(to_full_path("02_Wall_牆面::_Partition_Lightweight.輕隔間")))
        self.assertFalse(is_structure_layer(to_full_path("01_Ceiling_天花::Paint.油漆")))
        self.assertFalse(is_structure_layer("Default"))
        self.assertFalse(is_structure_layer(""))


if __name__ == "__main__":
    unittest.main()
