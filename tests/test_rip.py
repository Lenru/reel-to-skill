"""Offline checks for the metadata handling in rip.py. No network, no Whisper.

Run from the repo root: python -m unittest
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from rip import describe, read_meta  # noqa: E402


class ReadMeta(unittest.TestCase):
    def test_missing_info_json_gives_empty_dict(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(read_meta(Path(d)), {})

    def test_reads_info_json(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "source.info.json").write_text(
                json.dumps({"description": "hello", "uploader": "someone"}),
                encoding="utf-8")
            meta = read_meta(Path(d))
            self.assertEqual(meta["description"], "hello")
            self.assertEqual(meta["uploader"], "someone")


class Describe(unittest.TestCase):
    def test_uploader_wins_over_channel(self):
        self.assertEqual(describe({"uploader": "a", "channel": "b"})[0], "a")

    def test_falls_back_to_channel(self):
        self.assertEqual(describe({"uploader": None, "channel": "b"})[0], "b")

    def test_null_fields_become_empty_strings(self):
        self.assertEqual(
            describe({"title": None, "description": None}), ("", "", ""))

    def test_strips_whitespace(self):
        _, title, caption = describe({"title": " t \n", "description": "\n c "})
        self.assertEqual((title, caption), ("t", "c"))


if __name__ == "__main__":
    unittest.main()
