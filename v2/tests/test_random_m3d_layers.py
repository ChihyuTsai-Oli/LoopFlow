# -*- coding: utf-8 -*-
"""隨機把選取物件分到 M3D 類型子圖層。"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.devtools.random_m3d_layers import (
    assign_selected_to_random_type_layers,
    type_leaf_layers,
)
from loopflow.platform.rhino.memory import MemorySession


class RandomM3DLayerTests(unittest.TestCase):
    def _session(self) -> MemorySession:
        session = MemorySession()
        session.ensure_layer("M3D::00_STR_結構::Slab.樓板")
        session.ensure_layer("M3D::00_STR_結構::Beam.樑")
        session.ensure_layer("M3D::_Data::Space_Boundaries")
        session.ensure_layer("M3D::_Data::Level_Boundaries_FFL")
        session.ensure_layer("M3D::_Data::Level_Boundaries_FL")
        return session

    def test_only_leaf_type_layers(self):
        session = self._session()
        leaves = type_leaf_layers(session)
        self.assertEqual(
            set(leaves),
            {"M3D::00_STR_結構::Slab.樓板", "M3D::00_STR_結構::Beam.樑"},
        )
        self.assertNotIn("M3D::00_STR_結構", leaves)
        self.assertNotIn("M3D::_Data::Space_Boundaries", leaves)

    def test_assigns_selected_objects(self):
        session = self._session()
        session.add_object("a", selected=True, layer="M3D")
        session.add_object("b", selected=True, layer="M3D")
        session.add_object("c", selected=False, layer="M3D")
        result = assign_selected_to_random_type_layers(session, rng=random.Random(0))
        self.assertTrue(result.ok)
        self.assertIn(session.object_layer("a"), type_leaf_layers(session))
        self.assertIn(session.object_layer("b"), type_leaf_layers(session))
        self.assertEqual(session.object_layer("c"), "M3D")

    def test_skips_dna_ref_and_system_layer_objects(self):
        session = self._session()
        session.add_object("ref", selected=True, name="DNA_REF_EX-01", layer="M3D::00_STR_結構::Slab.樓板")
        session.add_object("space", selected=True, name="客廳", layer="M3D::_Data::Space_Boundaries")
        result = assign_selected_to_random_type_layers(session, rng=random.Random(1))
        self.assertFalse(result.ok)
        self.assertEqual(session.object_layer("ref"), "M3D::00_STR_結構::Slab.樓板")
        self.assertEqual(session.object_layer("space"), "M3D::_Data::Space_Boundaries")

    def test_fails_without_selection_or_type_layers(self):
        empty = MemorySession()
        empty.ensure_layer("M3D::_Data::Space_Boundaries")
        self.assertFalse(assign_selected_to_random_type_layers(empty).ok)
        session = self._session()
        session.add_object("a", selected=False, layer="M3D")
        self.assertFalse(assign_selected_to_random_type_layers(session).ok)


if __name__ == "__main__":
    unittest.main()
