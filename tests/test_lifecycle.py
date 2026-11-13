import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import cli, contract, report  # noqa: E402

GIT = shutil.which("git")


def mk(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def git(repo, *args):
    env = dict(os.environ)
    env.setdefault("GIT_AUTHOR_NAME", "t")
    env.setdefault("GIT_AUTHOR_EMAIL", "t@example.com")
    env.setdefault("GIT_COMMITTER_NAME", "t")
    env.setdefault("GIT_COMMITTER_EMAIL", "t@example.com")
    subprocess.run(["git", "-C", repo] + list(args), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)


VISION = """# Vision

## Problem
Nobody can tell what is done.

## Audience
One developer shipping a small product.

## Non-goals
Not a project tracker.
"""


def make_complete(repo, version="0.1.0"):
    mk(os.path.join(repo, "docs", "product", "vision.md"), VISION)
    mk(os.path.join(repo, ".projtruth", "requirements.json"),
       json.dumps({"schema_version": 1, "requirements": [
           {"id": "R1", "title": "t", "status": "pending",
            "criteria": [{"id": "R1.1", "text": "c"}]}]}))
    mk(os.path.join(repo, ".projtruth", "decisions.jsonl"),
       '{"ts": "2026-01-01", "decision": "sqlite", "why": "single writer"}\n')
    mk(os.path.join(repo, "docs", "design", "architecture.md"), "# Architecture\n")
    mk(os.path.join(repo, "app.py"), "print('hi')\n")
    mk(os.path.join(repo, "tests", "test_app.py"), "def test_x():\n    assert True\n")
    mk(os.path.join(repo, "CHANGELOG.md"), "# Changelog\n\n## [%s] - 2026-01-01\n- x\n" % version)
    mk(os.path.join(repo, "pyproject.toml"),
       '[project]\nname = "x"\nversion = "%s"\n' % version)


class StageTests(unittest.TestCase):
    def test_vision_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(contract.check_vision(tmp)[0]["name"], "vision")
            self.assertFalse(contract.check_vision(tmp)[0]["ok"])
            mk(os.path.join(tmp, "docs", "product", "vision.md"), VISION)
            results = contract.check_vision(tmp)
            self.assertTrue(all(r["ok"] for r in results), results)

    def test_vision_missing_section_names_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "product", "vision.md"),
               "# Vision\n\n## Problem\nx\n")
            bad = [r for r in contract.check_vision(tmp) if not r["ok"]]
            self.assertTrue(any("Audience" in r["detail"] for r in bad))

    def test_spec_requires_criteria(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(contract.check_spec(tmp)[0]["ok"])
            mk(os.path.join(tmp, ".projtruth", "requirements.json"),
               json.dumps({"requirements": [{"id": "R1", "title": "t", "criteria": []}]}))
            results = contract.check_spec(tmp)
            self.assertFalse(all(r["ok"] for r in results))
            self.assertTrue(any(r["name"] == "criteria" and not r["ok"] for r in results))

    def test_design_needs_architecture_and_a_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "ARCHITECTURE.md"), "# A\n")
            results = contract.check_design(tmp)
            self.assertTrue(any(r["ok"] and r["name"] == "architecture" for r in results))
            self.assertTrue(any(not r["ok"] and r["name"] == "decisions" for r in results))

    def test_build_needs_tests(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "app.py"), "x = 1\n")
            results = contract.check_build(tmp)
            self.assertTrue(any(r["ok"] and r["name"] == "source" for r in results))
            self.assertTrue(any(not r["ok"] and r["name"] == "tests" for r in results))
            mk(os.path.join(tmp, "tests", "test_app.py"), "def test(): pass\n")
            self.assertTrue(all(r["ok"] for r in contract.check_build(tmp)))

    def test_verify_skips_when_tools_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = contract.run_json
            contract.run_json = lambda *a, **k: None
            try:
                results = contract.check_verify(tmp)
            finally:
                contract.run_json = original
            self.assertTrue(all(r.get("skipped") and not r["required"] for r in results))

    def test_verify_blocks_on_unverified_requirement(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = contract.run_json

            def fake(repo, tool, args):
                if tool == "projtruth":
                    return [{"id": "R1", "status": "verified"},
                            {"id": "R2", "status": "stale"}]
                return {"metrics": {"severity": {"incorrect": 0}}}
            contract.run_json = fake
            try:
                results = contract.check_verify(tmp)
            finally:
                contract.run_json = original
            bad = [r for r in results if r["required"] and not r["ok"]]
            self.assertEqual(len(bad), 1)
            self.assertIn("R2", bad[0]["detail"])


@unittest.skipUnless(GIT, "git not installed")
class ReleaseTests(unittest.TestCase):
    def test_release_needs_matching_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_complete(tmp)
            git(tmp, "init")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-m", "one")
            results = contract.check_release(tmp)
            self.assertTrue(any(not r["ok"] and r["name"] == "tag" for r in results))
            git(tmp, "tag", "-a", "v0.1.0", "-m", "v")
            results = contract.check_release(tmp)
            self.assertTrue(all(r["ok"] for r in results if r["required"]), results)

    def test_version_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_complete(tmp, version="0.2.0")
            git(tmp, "init")
            git(tmp, "add", "-A")
            git(tmp, "commit", "-m", "one")
            git(tmp, "tag", "-a", "v0.1.0", "-m", "v")
            bad = [r for r in contract.check_release(tmp) if not r["ok"]]
            self.assertTrue(any(r["name"] == "tag" for r in bad), bad)

    def test_changelog_must_mention_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_complete(tmp, version="0.1.0")
            mk(os.path.join(tmp, "CHANGELOG.md"), "# Changelog\n")
            bad = [r for r in contract.check_release(tmp) if not r["ok"]]
            self.assertTrue(any(r["name"] == "changelog" for r in bad))


class ReportTests(unittest.TestCase):
    def test_next_action_points_at_first_blocker(self):
        stages = [
            {"id": 0, "title": "Discovery", "question": "", "state": "failed",
             "results": [{"name": "vision", "ok": False, "required": True,
                          "detail": "no vision", "fix": "write it"}]},
            {"id": 1, "title": "Spec", "question": "", "state": "passed", "results": []},
        ]
        stage, item = report.next_action(stages)
        self.assertEqual(stage["id"], 0)
        self.assertEqual(item["name"], "vision")
        text = report.render("/tmp/x", stages)
        self.assertIn("write it", text)

    def test_all_passed_message(self):
        stages = [{"id": 0, "title": "D", "question": "", "state": "passed",
                   "results": []}]
        self.assertIn("Every stage passes", report.render("/tmp/x", stages))


class CliTests(unittest.TestCase):
    def _run(self, argv):
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            rc = cli.main(argv)
        finally:
            sys.stdout = old
        return rc, buf.getvalue()

    def test_repo_must_exist(self):
        self.assertEqual(cli.main(["--repo", "no-such-dir-xyz", "status"]), 2)

    def test_check_fails_and_names_the_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = self._run(["--repo", tmp, "check"])
            self.assertEqual(rc, 1)
            self.assertIn("Discovery", out)

    def test_check_stage_zero_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(cli.main(["--repo", tmp, "check", "--stage", "0"]), 1)
            self.assertEqual(cli.main(["--repo", tmp, "check", "--stage", "9"]), 2)

    def test_json_status_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            rc, out = self._run(["--repo", tmp, "status", "--json"])
            self.assertEqual(rc, 0)
            data = json.loads(out)
            self.assertEqual(len(data), len(contract.STAGES))
            self.assertIn("blocking", data[0])


if __name__ == "__main__":
    unittest.main()
