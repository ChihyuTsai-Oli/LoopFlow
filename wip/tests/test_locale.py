# -*- coding: utf-8 -*-
"""這台電腦的介面語系：第一次詢問、LFLanguage、不寫進 .3dm。"""
from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

WIP = Path(__file__).resolve().parents[1]
SRC = WIP / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loopflow.features.document.language import (
    COMMAND_ID,
    ensure_locale,
    parse_locale_choice,
    run_language,
    saved_message,
)
from loopflow.foundation import locale as locale_store


class LocalePreferenceTests(unittest.TestCase):
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

    def test_missing_file_is_unset(self):
        self.assertIsNone(locale_store.read_locale())

    def test_write_and_read_roundtrip(self):
        path = locale_store.write_locale(locale_store.LOCALE_EN)
        self.assertEqual(path, self._path)
        self.assertEqual(locale_store.read_locale(), locale_store.LOCALE_EN)
        text = path.read_text(encoding="utf-8")
        self.assertIn('"locale": "en"', text)
        self.assertNotIn(".3dm", text)

    def test_unknown_value_is_unset(self):
        self._path.write_text('{"locale": "ja"}\n', encoding="utf-8")
        self.assertIsNone(locale_store.read_locale())

    def test_parse_labels(self):
        self.assertEqual(parse_locale_choice("繁中"), locale_store.LOCALE_ZH_TW)
        self.assertEqual(parse_locale_choice("English"), locale_store.LOCALE_EN)
        self.assertEqual(parse_locale_choice("zh-TW"), locale_store.LOCALE_ZH_TW)
        self.assertIsNone(parse_locale_choice(None))
        self.assertIsNone(parse_locale_choice("取消"))

    def test_ensure_skips_when_already_set(self):
        locale_store.write_locale(locale_store.LOCALE_ZH_TW)
        asked = []

        def ask():
            asked.append(1)
            return locale_store.LOCALE_EN

        self.assertIsNone(ensure_locale(ask=ask))
        self.assertEqual(asked, [])
        self.assertEqual(locale_store.read_locale(), locale_store.LOCALE_ZH_TW)

    def test_ensure_asks_once_and_remembers(self):
        result = ensure_locale(ask=lambda: "English")
        self.assertIsNone(result)
        self.assertEqual(locale_store.read_locale(), locale_store.LOCALE_EN)

    def test_ensure_cancel_does_not_save(self):
        result = ensure_locale(ask=lambda: None)
        self.assertFalse(result.ok)
        self.assertEqual(result.status, "cancelled")
        self.assertIn("尚未記住", result.message)
        self.assertIsNone(locale_store.read_locale())

    def test_ensure_without_ui_does_not_block(self):
        def ask():
            raise ImportError("no rhino")

        self.assertIsNone(ensure_locale(ask=ask))
        self.assertIsNone(locale_store.read_locale())

    def test_switch_command_saves(self):
        result = run_language(ask=lambda: "繁中")
        self.assertTrue(result.ok)
        self.assertEqual(result.command_id, COMMAND_ID)
        self.assertEqual(result.details["locale"], locale_store.LOCALE_ZH_TW)
        self.assertEqual(result.message, saved_message(locale_store.LOCALE_ZH_TW))
        self.assertEqual(locale_store.read_locale(), locale_store.LOCALE_ZH_TW)

    def test_switch_cancel(self):
        result = run_language(ask=lambda: None)
        self.assertEqual(result.status, "cancelled")
        self.assertIn("已取消切換", result.message)
        self.assertIsNone(locale_store.read_locale())


if __name__ == "__main__":
    unittest.main()
