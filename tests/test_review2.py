"""Regressions from the independent review of lifecycle 0.2.0."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import cli, contract, packs  # noqa: E402


def mk(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


class RegistryRobustnessTests(unittest.TestCase):
    def test_malformed_registry_reports_instead_of_crashing(self):
        cases = ['{"requirements": [1]}',
                 '{"requirements": [{"title": "x"}]}',
                 '{"requirements": [{"id": "R1", "criteria": "works"}]}',
                 '[]']
        for body in cases:
            with tempfile.TemporaryDirectory() as tmp:
                mk(os.path.join(tmp, ".projtruth", "requirements.json"), body)
                results = contract.check_spec(tmp)
                self.assertTrue(results, body)
                self.assertFalse(all(r["ok"] for r in results), body)

    def test_bom_registry_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, ".projtruth", "requirements.json")
            os.makedirs(os.path.dirname(path))
            with open(path, "w", encoding="utf-8-sig", newline="\n") as f:
                f.write('{"requirements": [{"id": "R1", "criteria": [{"id": "R1.1", "text": "c"}]}]}')
            self.assertTrue(all(r["ok"] for r in contract.check_spec(tmp)))


class BuildDetectionTests(unittest.TestCase):
    def test_rust_inline_tests_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "src", "lib.rs"),
               "pub fn add() {}\n\n#[cfg(test)]\nmod tests {\n  #[test]\n  fn it_works() {}\n}\n")
            results = contract.check_build(tmp)
            self.assertTrue(all(r["ok"] for r in results), results)

    def test_dart_is_a_source_language(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "lib", "main.dart"), "void main() {}\n")
            results = contract.check_build(tmp)
            source = [r for r in results if r["name"] == "source"][0]
            self.assertTrue(source["ok"], results)

    def test_docs_spec_is_not_a_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "app.py"), "x = 1\n")
            mk(os.path.join(tmp, "docs", "spec", "openapi.yaml"), "openapi: 3\n")
            results = contract.check_build(tmp)
            tests = [r for r in results if r["name"] == "tests"][0]
            self.assertFalse(tests["ok"], "docs/spec must not count as tests")


class DesignTests(unittest.TestCase):
    def test_empty_architecture_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "design", "architecture.md"), "   \n")
            mk(os.path.join(tmp, ".projtruth", "decisions.jsonl"),
               '{"decision": "x", "why": "y"}\n')
            results = contract.check_design(tmp)
            arch = [r for r in results if r["name"] == "architecture"][0]
            self.assertFalse(arch["ok"])


class ReleaseMatchingTests(unittest.TestCase):
    def test_version_match_is_exact(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "pyproject.toml"), '[project]\nversion = "1.0.0"\n')
            mk(os.path.join(tmp, "CHANGELOG.md"), "# C\n\n## [11.0.0] - x\n- y\n")
            os.makedirs(os.path.join(tmp, ".git"))
            results = contract.check_release(tmp)
            changelog = [r for r in results if r["name"] == "changelog"][0]
            self.assertFalse(changelog["ok"], "1.0.0 must not match 11.0.0")


class GamePackDetectionTests(unittest.TestCase):
    def test_nested_quest_directory_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"),
               "---\ncharacters: [aria]\nfactions: []\nlocations: [harbor]\nfacts: []\n---\n")
            mk(os.path.join(tmp, "docs", "game", "quests", "act1", "q1.md"),
               "---\nid: q1\nrequires: [q-missing]\nreveals: []\ncharacters: [aria]\nfactions: []\n---\n")
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any("q-missing" in r["detail"] for r in bad), bad)

    def test_comments_in_frontmatter_are_stripped(self):
        fm = packs.frontmatter("---\nrequires: [q1]  # the first quest\n---\n")
        self.assertEqual(fm["requires"], ["q1"])
        fm = packs.frontmatter("---\ncharacters:\n  - aria  # hero\n---\n")
        self.assertEqual(fm["characters"], ["aria"])


class RootDiscoveryTests(unittest.TestCase):
    def test_running_from_a_subdirectory_finds_the_project(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".projtruth", "requirements.json"), "{}")
            sub = os.path.join(tmp, "src", "deep")
            os.makedirs(sub)
            self.assertEqual(os.path.normcase(cli._find_root(sub)),
                             os.path.normcase(os.path.abspath(tmp)))


if __name__ == "__main__":
    unittest.main()
