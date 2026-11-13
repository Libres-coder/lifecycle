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

    def test_statusline_command_records_and_prints(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = self._run(["--repo", tmp, "statusline"], json.dumps(PAYLOAD))
            self.assertEqual(rc, 0)
            self.assertIn("74% ctx", out)
            data, _ = statusline.last(tmp)
            self.assertEqual(data["used_percentage"], 74)

    def test_resume_hook_records_context_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, _ = self._run(["--repo", tmp, "resume", "--hook"],
                              '{"source": "compact", "context_tokens": 42000}')
            self.assertEqual(rc, 0)
            data, _ = statusline.last(tmp)
            self.assertEqual(data["total_input_tokens"], 42000)


if __name__ == "__main__":
    unittest.main()
