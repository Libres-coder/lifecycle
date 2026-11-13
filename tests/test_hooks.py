"""Tests for hooks, snapshots and the review note."""
import json
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import hooks, thread  # noqa: E402

DAY = 86400


def mk(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class HookTests(unittest.TestCase):
    def test_install_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, _ = hooks.install(tmp)
            self.assertTrue(ok)
            hooks.install(tmp)
            data = hooks.load(tmp)
            pre = data["hooks"]["PreCompact"]
            self.assertEqual(len(pre), 1)
            cmds = [h["command"] for e in pre for h in e["hooks"]]
            self.assertEqual(len([c for c in cmds if "snapshot" in c]), 1)

    def test_install_upgrades_a_pre_1_2_hook(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".claude", "settings.json"),
               '{"hooks": {"SessionStart": [{"hooks": [{"type": "command", '
               '"command": "lifecycle resume"}], "matcher": "compact|resume"}]}}\n')
            ok, msg = hooks.install(tmp)
            self.assertTrue(ok, msg)
            cmds = [h["command"] for e in hooks.load(tmp)["hooks"]["SessionStart"]
                    for h in e["hooks"]]
            self.assertTrue(any("resume --hook" in c for c in cmds), cmds)

    def test_existing_status_line_is_reported_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".claude", "settings.json"),
               '{"statusLine": {"type": "command", "command": "ccusage statusline"}}\n')
            ok, msg = hooks.install(tmp)
            self.assertTrue(ok)
            self.assertIn("left alone", msg)
            self.assertEqual(hooks.load(tmp)["statusLine"]["command"],
                             "ccusage statusline")

    def test_uninstall_leaves_a_lookalike_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".claude", "settings.json"),
               '{"hooks": {"PreCompact": [{"hooks": [{"type": "command", '
               '"command": "~/bin/lifecycle-resume.sh"}]}]}}\n')
            ok, _ = hooks.uninstall(tmp)
            self.assertTrue(ok)
            data = hooks.load(tmp)
            cmds = [h["command"] for e in data["hooks"]["PreCompact"] for h in e["hooks"]]
            self.assertEqual(cmds, ["~/bin/lifecycle-resume.sh"])

    def test_install_preserves_existing_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".claude", "settings.json"),
               '{"permissions": {"allow": ["Bash(ls:*)"]}}\n')
            hooks.install(tmp)
            data = hooks.load(tmp)
            self.assertEqual(data["permissions"]["allow"], ["Bash(ls:*)"])
            self.assertIn("PreCompact", data["hooks"])

    def test_uninstall_removes_only_ours(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".claude", "settings.json"),
               '{"hooks": {"PreCompact": [{"hooks": [{"type": "command", '
               '"command": "echo mine"}]}]}}\n')
            hooks.install(tmp)
            self.assertTrue(hooks.installed(tmp)["PreCompact"])
            hooks.uninstall(tmp)
            state = hooks.installed(tmp)
            self.assertFalse(state["PreCompact"])
            data = hooks.load(tmp)
            cmds = [h["command"] for e in data["hooks"]["PreCompact"] for h in e["hooks"]]
            self.assertEqual(cmds, ["echo mine"])

    def test_refuses_to_touch_broken_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".claude", "settings.json"), "{not json")
            ok, msg = hooks.install(tmp)
            self.assertFalse(ok)
            self.assertIn("cannot read", msg)


class SnapshotTests(unittest.TestCase):
    def test_snapshot_writes_and_prunes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, thread.SNAP_DIR)
            os.makedirs(d)
            for i in range(thread.MAX_SNAPSHOTS + 5):
                with open(os.path.join(d, "old-%03d.md" % i), "w", encoding="utf-8") as f:
                    f.write("x\n")
            path = thread.snapshot(tmp)
            self.assertTrue(os.path.exists(path))
            names = os.listdir(d)
            self.assertLessEqual(len(names), thread.MAX_SNAPSHOTS + 1)

    def test_snapshot_records_transcript_size(self):
        with tempfile.TemporaryDirectory() as tmp:
            transcript = os.path.join(tmp, "t.jsonl")
            with open(transcript, "w", encoding="utf-8") as f:
                f.write("x" * 40000)
            path = thread.snapshot(tmp, transcript=transcript, trigger="auto")
            with open(path, encoding="utf-8") as f:
                body = f.read()
            self.assertIn("transcript: ~10k tokens", body)
            self.assertIn("(auto)", body)


class ReviewNoteTests(unittest.TestCase):
    def test_missing_review_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = thread.check_review(tmp)
            self.assertTrue(any(r["name"] == "review" and not r["ok"] for r in results))

    def test_review_without_findings_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "reviews", "latest.md"), "# Review\n\nAll good.\n")
            results = thread.check_review(tmp)
            self.assertTrue(any("no findings" in r["detail"] for r in results))

    def test_fresh_review_with_findings_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "reviews", "latest.md"),
               "# Review\n\n- something to fix\n")
            results = thread.check_review(tmp)
            self.assertTrue(all(r["ok"] for r in results), results)

    def test_old_review_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "docs", "reviews", "latest.md")
            mk(p, "# Review\n\n- something\n")
            old = time.time() - (thread.REVIEW_DAYS + 5) * DAY
            os.utime(p, (old, old))
            results = thread.check_review(tmp)
            self.assertTrue(any("days old" in r["detail"] for r in results))


if __name__ == "__main__":
    unittest.main()
