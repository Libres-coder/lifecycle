"""End-to-end: a complete software repository passes every stage.

This is the contract test between lifecycle and its siblings. It uses the
installed projtruth and corpus exactly as a user would, so a change to either
tool's JSON fails here instead of in the field. Skipped when a sibling is not
installed.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import contract  # noqa: E402

GIT = shutil.which("git")
PROJTRUTH = shutil.which("projtruth")
CORPUS = shutil.which("corpus")
TODAY = time.strftime("%Y-%m-%d")


def mk(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout or "") + (p.stderr or "")


@unittest.skipUnless(GIT and PROJTRUTH and CORPUS,
                     "needs git, projtruth and corpus installed")
class FullStackTests(unittest.TestCase):
    def _build(self, tmp):
        mk(os.path.join(tmp, "docs", "product", "vision.md"),
           "# Vision\n\n## Problem\n\n"
           + "A concrete problem statement with a named moment it hurts. " * 8
           + "\n\n## Audience\n\nSolo developers maintaining small tools. "
             "They feel it every release.\n"
           "\n## Non-goals\n\n- not a hosted service\n- not a marketplace\n"
           "\nSuccess metric: minutes saved per release, from the journal.\n")
        mk(os.path.join(tmp, "app.py"), "def add(a, b):\n    return a + b\n")
        mk(os.path.join(tmp, "test_app.py"),
           "from app import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n")
        mk(os.path.join(tmp, "docs", "design", "architecture.md"),
           "# Architecture\n\n## Components\n\none function, one test.\n\n"
           "## Trade-off\n\nno abstraction yet - the failure mode is a missing "
           "validation, handled at the call site.\n")
        mk(os.path.join(tmp, "pyproject.toml"),
           '[project]\nname = "demo"\nversion = "1.0.0"\n')
        mk(os.path.join(tmp, "CHANGELOG.md"),
           "# Changelog\n\n## [1.0.0] - %s\n\n- first release\n" % TODAY)
        mk(os.path.join(tmp, ".projtruth", "evidence", "R1-ok.md"),
           "# R1\n\n```\n$ python -m unittest test_app\nOK\n```\n\nmeasured\n")
        mk(os.path.join(tmp, "docs", "work", "current.md"),
           "# Current\n\n## Goal\n\nship the adder.\n\n## Done\n\n- built it\n"
           "\n## Next\n\n- publish v1.0.0\n\n## Blockers\n\nNone.\n")
        mk(os.path.join(tmp, "docs", "work", "log", TODAY + ".md"),
           "# Journal\n\n- built the adder and its test.\n")
        mk(os.path.join(tmp, "docs", "reports", "status-%s.md" % TODAY),
           "# Status\n\nall stages green.\n")
        mk(os.path.join(tmp, "docs", "reviews", TODAY + "-review.md"),
           "# Review\n\n## Findings\n\n- the input validation is missing\n")

        for args in (["init"], ["req-add", "R1", "adds two numbers",
                                "R1.1 returns the sum", "--files", "app.py"],
                     ["decide", "no abstraction", "--why",
                      "one function, no seam yet"]):
            rc, out = run([PROJTRUTH, "--repo", tmp] + args, tmp)
            self.assertEqual(rc, 0, "%s failed: %s" % (args, out))

        for args in (["init", "-q"], ["config", "user.email", "t@example.com"],
                     ["config", "user.name", "t"], ["add", "-A"],
                     ["commit", "-qm", "init"], ["tag", "v1.0.0"]):
            rc, out = run([GIT] + args, tmp)
            self.assertEqual(rc, 0, "git %s failed: %s" % (args, out))

    def test_a_complete_repository_has_no_blocking_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._build(tmp)
            stages = contract.evaluate(tmp)
            failed = [(s["id"], [r for r in s["results"]
                                 if r["required"] and not r["ok"]])
                      for s in stages if s["state"] == "failed"]
            self.assertEqual(failed, [], failed)

    def test_the_sibling_json_contracts_are_what_lifecycle_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._build(tmp)
            reqs = contract.run_json(tmp, "projtruth", ["report", "--json"])
            self.assertTrue(reqs, "projtruth JSON is empty")
            self.assertEqual(reqs[0]["status"], "verified", reqs[0])
            self.assertIn("evidence_tier", reqs[0])
            docs = contract.run_json(tmp, "corpus", ["report", "--json"])
            severity = (docs.get("metrics") or {}).get("severity") or {}
            self.assertEqual(severity.get("incorrect", 0), 0, docs)


if __name__ == "__main__":
    unittest.main()
