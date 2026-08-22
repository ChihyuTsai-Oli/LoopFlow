# -*- coding: utf-8 -*-
"""畫面句子表：與定稿一致；未記住語系時仍繁中。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
TOOLS = WIP / "tools"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import build_i18n_catalog  # noqa: E402
from loopflow.foundation import i18n  # noqa: E402
from loopflow.foundation import locale as locale_store  # noqa: E402


class I18nCatalogTests(unittest.TestCase):
    def setUp(self):
        self._old = os.environ.get(locale_store.PREFS_ENV)
        self._dir = tempfile.TemporaryDirectory()
        self._path = Path(self._dir.name) / "preferences.json"
        os.environ[locale_store.PREFS_ENV] = str(self._path)

    def tearDown(self):
        if self._old is None:
            os.environ.pop(locale_store.PREFS_ENV, None)
        else:
            os.environ[locale_store.PREFS_ENV] = self._old
        self._dir.cleanup()

    def test_catalog_matches_final_markdown(self):
        i18n._CACHE = None
        rows = build_i18n_catalog.build()
        existing = i18n.load_catalog()
        self.assertEqual(existing, rows)
        self.assertGreaterEqual(len(rows), 600)
        self.assertIn("nexus.033", rows)

    def test_unset_locale_stays_traditional_chinese(self):
        self.assertIsNone(locale_store.read_locale())
        self.assertEqual(i18n.current_locale(), locale_store.LOCALE_ZH_TW)
        self.assertEqual(
            i18n.t("nexus.022"),
            i18n.load_catalog()["nexus.022"]["zh-TW"],
        )

    def test_english_locale_uses_catalog_en(self):
        locale_store.write_locale(locale_store.LOCALE_EN)
        self.assertEqual(
            i18n.t("nexus.022"),
            "2  Sync Type Layers from Dictionary",
        )

    def test_apply_message_english_has_no_chinese_leftover(self):
        from loopflow.features.project.console import compose_scan_apply_message
        from loopflow.foundation import results

        locale_store.write_locale(locale_store.LOCALE_EN)
        identity = results.ok(
            "apply",
            "",
            details={"applied": list(range(46)), "count": 46},
        )
        placement = results.ok(
            "apply",
            "",
            details={"applied": ["a"], "ext": []},
        )
        message = compose_scan_apply_message("apply", identity, placement)
        self.assertEqual(
            message,
            "Updated 46 objects with ID/Type, Space/elevation. Publishing is unavailable.",
        )
        self.assertNotIn("不可發布", message)
        self.assertNotIn("、", message)

    def test_open_check_message_english(self):
        locale_store.write_locale(locale_store.LOCALE_EN)
        self.assertEqual(
            i18n.t("nexus.001"),
            i18n.load_catalog()["nexus.001"]["en"],
        )
        self.assertEqual(
            i18n.t("catalog.001"),
            i18n.load_catalog()["catalog.001"]["en"],
        )
        self.assertEqual(
            i18n.t("prompts.014"),
            i18n.load_catalog()["prompts.014"]["en"],
        )


if __name__ == "__main__":
    unittest.main()
