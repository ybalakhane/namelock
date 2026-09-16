import json
import os
import tempfile
import unittest
from pathlib import Path

from namelock.check import check_text, load_transcript
from namelock.cli import EXIT_MISMATCH, EXIT_OK, EXIT_USAGE, main

ROOT = Path(__file__).resolve().parents[1]


class TestWrongName(unittest.TestCase):
    def test_wrong_vocative_fails(self):
        text = "Okay, let me take a look. You're all set, Jordan."
        findings = check_text(text, "Alex Test")
        self.assertTrue(findings)
        self.assertEqual(findings[0].name, "Jordan")

    def test_expected_name_passes(self):
        text = "You're all set, Alex. See you Tuesday."
        self.assertEqual(check_text(text, "Alex Test"), [])

    def test_first_name_only_matches_full_expected(self):
        text = "Hi, Alex. What can I do for you?"
        self.assertEqual(check_text(text, "Alex Test"), [])

    def test_practice_name_is_not_a_person(self):
        text = "Thanks for calling Northside Dental. This is Riley."
        self.assertEqual(check_text(text, "Alex Test"), [])

    def test_day_of_week_is_not_a_person(self):
        text = "I can do Tuesday morning."
        self.assertEqual(check_text(text, "Alex Test"), [])

    def test_alias_is_allowed(self):
        text = "You're all set, Xander."
        self.assertEqual(check_text(text, "Alex", aliases=["Xander"]), [])

    def test_cli_wrong_name_exits_1(self):
        path = ROOT / "examples" / "wrong-name.txt"
        self.assertEqual(
            main([str(path), "--expect-name", "Alex Test"]),
            EXIT_MISMATCH,
        )

    def test_cli_right_name_exits_0(self):
        path = ROOT / "examples" / "right-name.txt"
        self.assertEqual(
            main([str(path), "--expect-name", "Alex Test"]),
            EXIT_OK,
        )

    def test_cli_json_transcript_uses_agent_turns_only(self):
        path = ROOT / "examples" / "call.json"
        self.assertEqual(
            main([str(path), "--expect-name", "Alex Test"]),
            EXIT_MISMATCH,
        )

    def test_missing_file_exits_2(self):
        self.assertEqual(
            main(["/no/such/file.txt", "--expect-name", "Alex"]),
            EXIT_USAGE,
        )

    def test_load_json_ignores_caller_turns(self):
        payload = {
            "turns": [
                {"speaker": "agent", "text": "Thanks for calling."},
                {"speaker": "caller", "text": "Hi, my friend Jordan told me to come in."},
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(payload, fh)
            path = fh.name
        try:
            text = load_transcript(path)
            self.assertNotIn("Jordan", text)
            self.assertEqual(check_text(text, "Alex Test"), [])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
