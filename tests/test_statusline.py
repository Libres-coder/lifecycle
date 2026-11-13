"""Tests for the statusline payload, context recording and the status line."""
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import cli, statusline, threads  # noqa: E402

PAYLOAD = {
    "session_name": "demo",
    "cwd": "/tmp/x",
    "model": {"id": "claude-sonnet-5-5", "display_name": "Sonnet 5.5"},
    "context_window": {"used_percentage": 74, "remaining_percentage": 26,
                       "context_window_size": 200000,
                       "total_input_tokens": 148000, "total_output_tokens": 900},
}


class ParseTests(unittest.TestCase):
    def test_extracts_context_fields(self):
        row = statusline.parse(json.dumps(PAYLOAD))
        self.assertEqual(row["used_percentage"], 74)
        self.assertEqual(row["model"], "Sonnet 5.5")
        self.assertEqual(row["context_window_size"], 200000)

    def test_bad_payloads_do_not_raise(self):
        for text in ("", "not json", "[]", '{"context_window": 3}'):
            self.assertEqual(statusline.parse(text).get("used_percentage"), None)


class RecordTests(unittest.TestCase):
    def test_save_and_read_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))
            data, age = statusline.last(tmp)
            self.assertEqual(data["used_percentage"], 74)
            self.assertLess(age, 5)
            self.assertIn("74%", statusline.staleness_line(tmp))

    def test_old_reading_is_marked_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))
            old = time.time() - 3600
            os.utime(path, (old, old))
            self.assertIn("min ago", statusline.staleness_line(tmp))

    def test_no_reading_means_no_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(statusline.staleness_line(tmp), "")


class RenderTests(unittest.TestCase):
    def test_status_line_shows_thread_and_percent(self):
        with tempfile.TemporaryDirectory() as tmp:
            threads.create(tmp, "game-main", "Main quest")
            statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))
            line = statusline.render(tmp)
            self.assertIn("game-main", line)
            self.assertIn("74% ctx", line)

    def test_status_line_without_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(statusline.render(tmp), "lifecycle")


class BadStateTests(unittest.TestCase):
    """The state file is hand-edited and merged; a bad field is input, not a crash."""

    def _write(self, tmp, text):
        os.makedirs(os.path.join(tmp, ".lifecycle"), exist_ok=True)
        with open(os.path.join(tmp, ".lifecycle", "context.json"), "w",
                  encoding="utf-8", newline="\n") as f:
            f.write(text)

    def test_numeric_strings_are_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, '{"used_percentage": " 85 "}')
            self.assertEqual(statusline.last(tmp)[0]["used_percentage"], 85)
            self.assertIn("85%", statusline.render(tmp))

    def test_wrong_type_does_not_crash_any_consumer(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write(tmp, '{"used_percentage": "high", '
                             '"total_input_tokens": "many"}')
            data, _ = statusline.last(tmp)
            self.assertIsNone(data["used_percentage"])
            self.assertEqual(statusline.render(tmp), "lifecycle")
            self.assertEqual(statusline.staleness_line(tmp), "")
            self.assertEqual(cli._context_hint(tmp), "")


class SuggestTests(unittest.TestCase):
    def _run(self, tmp):
        import io
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            cli._suggest(tmp, [])
            return sys.stdout.getvalue()
        finally:
            sys.stdout = old

    def setUp(self):
        self._old = os.environ.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE")
        os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "60"

    def tearDown(self):
        if self._old is None:
            os.environ.pop("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", None)
        else:
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = self._old

    def test_no_reading_is_reported_as_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIn("no context reading", self._run(tmp))

    def test_a_healthy_reading_is_not_called_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            statusline.save(tmp, {"used_percentage": 30})
            text = self._run(tmp)
            self.assertNotIn("no context reading", text)
            self.assertNotIn("[context]", text)      # nothing to do


class CliTests(unittest.TestCase):
    def _run(self, argv, stdin_text=""):
        import io
        old_in, old_out = sys.stdin, sys.stdout
        sys.stdin, sys.stdout = io.StringIO(stdin_text), io.StringIO()
        try:
            rc = cli.main(argv)
            return rc, sys.stdout.getvalue()
        finally:
            sys.stdin, sys.stdout = old_in, old_out

    def test_resume_hook_is_silent_in_an_uninitialized_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = self._run(["--repo", tmp, "resume", "--hook"],
                                '{"source": "startup", "context_tokens": 1000}')
            self.assertEqual(rc, 0)
            self.assertEqual(out, "")
            self.assertFalse(os.path.exists(os.path.join(tmp, ".lifecycle")))

    def test_resume_hook_is_silent_when_only_a_context_reading_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))
            rc, out = self._run(["--repo", tmp, "resume", "--hook"],
                                '{"source": "startup"}')
            self.assertEqual(rc, 0)
            self.assertEqual(out, "", "a status line reading alone is not a project")

    def test_statusline_command_records_and_prints(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = self._run(["--repo", tmp, "statusline"], json.dumps(PAYLOAD))
            self.assertEqual(rc, 0)
            self.assertIn("74% ctx", out)
            data, _ = statusline.last(tmp)
            self.assertEqual(data["used_percentage"], 74)

    def test_resume_hook_records_context_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "docs", "work"))   # an initialized repo
            rc, _ = self._run(["--repo", tmp, "resume", "--hook"],
                              '{"source": "compact", "context_tokens": 42000}')
            self.assertEqual(rc, 0)
            data, _ = statusline.last(tmp)
            self.assertEqual(data["total_input_tokens"], 42000)

    def test_resume_hook_does_not_keep_a_stale_percentage(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "docs", "work"))
            statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))   # 74%
            rc, _ = self._run(["--repo", tmp, "resume", "--hook"],
                              '{"source": "resume", "context_tokens": 42000}')
            self.assertEqual(rc, 0)
            data, _ = statusline.last(tmp)
            self.assertEqual(data["total_input_tokens"], 42000)
            self.assertIsNone(data["used_percentage"],
                              "a token count is not a percent of the window")


class TriggerTests(unittest.TestCase):
    """The advice must arrive before the thing it warns about."""

    def setUp(self):
        self._old = os.environ.get("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE")
        os.environ.pop("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", None)

    def tearDown(self):
        if self._old is None:
            os.environ.pop("CLAUDE_AUTOCOMPACT_PCT_OVERRIDE", None)
        else:
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = self._old

    def test_override_lowers_the_trigger(self):
        os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "70"
        self.assertEqual(statusline.trigger(), 70)
        self.assertEqual(statusline.thresholds(), (55, 65))

    def test_unreadable_override_keeps_the_default(self):
        os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "soon"
        self.assertEqual(statusline.trigger(), statusline.DEFAULT_TRIGGER)
        for bad in ("0", "-3", "500"):
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = bad
            self.assertTrue(1 <= statusline.trigger() <= 99)

    def test_override_parsing(self):
        for raw, want in ((" 70 ", 70), ("70.5", 70), ("0100", 99), ("0", 1),
                          ("70%", statusline.DEFAULT_TRIGGER), ("", statusline.DEFAULT_TRIGGER)):
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = raw
            self.assertEqual(statusline.trigger(), want, raw)

    def test_boundary_values_are_inclusive(self):
        os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "60"   # warn 55, nudge 45
        with tempfile.TemporaryDirectory() as tmp:
            statusline.save(tmp, {"used_percentage": 55})
            self.assertIn("/compact", statusline.render(tmp))
            self.assertIn("/compact", cli._context_hint(tmp))
            statusline.save(tmp, {"used_percentage": 54})
            self.assertNotIn("/compact", statusline.render(tmp))
            self.assertNotIn("/compact now", cli._context_hint(tmp))
            statusline.save(tmp, {"used_percentage": 45})
            self.assertIn("fine for the current step", cli._context_hint(tmp))

    def test_hint_follows_the_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))  # 74%
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "70"
            self.assertIn("/compact", cli._context_hint(tmp))
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "95"
            self.assertEqual(cli._context_hint(tmp), "")

    def test_status_line_asks_for_a_compaction_before_the_trigger(self):
        with tempfile.TemporaryDirectory() as tmp:
            statusline.save(tmp, statusline.parse(json.dumps(PAYLOAD)))  # 74%
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "70"
            self.assertIn("/compact", statusline.render(tmp))
            os.environ["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] = "95"
            self.assertNotIn("/compact", statusline.render(tmp))


if __name__ == "__main__":
    unittest.main()
