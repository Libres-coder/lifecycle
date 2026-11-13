"""Tests for the long-running thread: handoff, journal, reports, budget."""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import contract, thread  # noqa: E402

GIT = shutil.which("git")
DAY = 86400


def mk(path, text, mtime=None):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    if mtime:
        os.utime(path, (mtime, mtime))


def by_name(results, name):
    return [r for r in results if r["name"] == name][0]


@unittest.skipUnless(GIT, "git not installed")
class SustainTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name
        self._git("init")

    def tearDown(self):
        self.tmp.cleanup()

    def _git(self, *args, **kw):
        env = dict(os.environ)
        env.setdefault("GIT_AUTHOR_NAME", "t")
        env.setdefault("GIT_AUTHOR_EMAIL", "t@example.com")
        env.setdefault("GIT_COMMITTER_NAME", "t")
        env.setdefault("GIT_COMMITTER_EMAIL", "t@example.com")
        date = kw.get("date")
        if date:
            env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = date
        subprocess.run(["git", "-C", self.repo] + list(args), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    def _release(self):
        mk(os.path.join(self.repo, "app.py"), "x = 1\n")
        self._git("add", "-A")
        self._git("commit", "-m", "one")
        self._git("tag", "-a", "v0.1.0", "-m", "v")

    def test_before_release_a_missing_thread_warns(self):
        results = thread.check_sustain(self.repo)
        thread_res = by_name(results, "thread")
        self.assertFalse(thread_res["ok"])
        self.assertFalse(thread_res["required"], "not blocking before a release")

    def test_after_release_a_missing_thread_blocks(self):
        self._release()
        results = thread.check_sustain(self.repo)
        thread_res = by_name(results, "thread")
        self.assertTrue(thread_res["required"], thread_res)

    def test_stale_thread_blocks_after_release(self):
        """A commit that changes code after the thread's last commit is drift."""
        self._release()
        mk(os.path.join(self.repo, "docs", "work", "current.md"), "# c\n")
        self._git("add", "-A")
        self._git("commit", "-m", "thread", date="2026-01-01T00:00:00+0000")
        mk(os.path.join(self.repo, "app.py"), "x = 2\n")
        self._git("add", "-A")
        self._git("commit", "-m", "code moves on", date="2026-01-02T00:00:00+0000")
        results = thread.check_sustain(self.repo)
        fresh = by_name(results, "thread:fresh")
        self.assertTrue(fresh["required"])
        self.assertFalse(fresh["ok"])

    def test_fresh_thread_passes(self):
        self._release()
        mk(os.path.join(self.repo, "docs", "work", "current.md"), "# c\n")
        results = thread.check_sustain(self.repo)
        self.assertTrue(by_name(results, "thread")["ok"])

    def test_old_journal_warns(self):
        self._release()
        mk(os.path.join(self.repo, "docs", "work", "current.md"), "# c\n")
        mk(os.path.join(self.repo, "docs", "work", "log", "old.md"), "# old\n",
           mtime=time.time() - 40 * DAY)
        results = thread.check_sustain(self.repo)
        entry = by_name(results, "thread:journal")
        self.assertFalse(entry["ok"])
        self.assertFalse(entry["required"])

    def test_context_budget(self):
        self._release()
        mk(os.path.join(self.repo, "docs", "work", "current.md"), "# c\n")
        mk(os.path.join(self.repo, "CLAUDE.md"), "x" * (thread.CONTEXT_BUDGET_CHARS + 10))
        results = thread.check_sustain(self.repo)
        budget = by_name(results, "thread:context")
        self.assertFalse(budget["ok"])
        self.assertFalse(budget["required"])

    def test_resume_prints_state_and_journal(self):
        mk(os.path.join(self.repo, "docs", "work", "current.md"),
           "# Current\n\n## Next\n\n- ship it\n")
        mk(os.path.join(self.repo, "docs", "work", "log", "2026-01-01.md"),
           "# Day\n\nDid a thing.\n")
        text = thread.resume_text(self.repo, [])
        self.assertIn("ship it", text)
        self.assertIn("Did a thing", text)

    def test_report_is_drafted_from_facts(self):
        self._release()
        stages = [{"id": 0, "title": "Discovery", "state": "passed", "results": []}]
        text = thread.report_text(self.repo, stages,
                                  requirements=[{"id": "R1", "status": "verified"},
                                                {"id": "R2", "status": "stale"}],
                                  corpus={"metrics": {"artifacts": 3,
                                                      "severity": {"incorrect": 1}}})
        self.assertIn("1/1 stages pass", text)
        self.assertIn("R2 (stale)", text)
        self.assertIn("1 incorrect", text)
        self.assertIn("What went well", text)
        path = thread.write_report(self.repo, text)
        self.assertTrue(os.path.exists(path))
        self.assertIn("docs/reports", path.replace("\\", "/"))


class StageSixTests(unittest.TestCase):
    def test_stage_six_is_registered(self):
        self.assertEqual([s["key"] for s in contract.STAGES][-1], "sustain")
        self.assertEqual(len(contract.STAGES), 7)


if __name__ == "__main__":
    unittest.main()
