import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import depth, packs  # noqa: E402


def mk(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


BIBLE = """---
characters: [aria, borin]
factions: [guild, crown]
locations: [harbor]
facts: [war-started, king-dead]
---

# World
"""


def quest(repo, name, qid, requires=(), reveals=(), characters=(), factions=()):
    mk(os.path.join(repo, "docs", "game", "quests", name + ".md"),
       "---\nid: %s\nrequires: [%s]\nreveals: [%s]\ncharacters: [%s]\nfactions: [%s]\n---\n\n# %s\n"
       % (qid, ", ".join(requires), ", ".join(reveals), ", ".join(characters),
          ", ".join(factions), qid))


class FrontmatterTests(unittest.TestCase):
    def test_list_and_block_forms(self):
        text = "---\nid: q1\nrequires: [q0, q2]\ncharacters:\n  - aria\n  - borin\n---\n"
        fm = packs.frontmatter(text)
        self.assertEqual(fm["requires"], ["q0", "q2"])
        self.assertEqual(fm["characters"], ["aria", "borin"])

    def test_no_frontmatter(self):
        self.assertEqual(packs.frontmatter("# nothing\n"), {})


class GamePackTests(unittest.TestCase):
    def test_pack_detected_by_artifacts_not_an_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(packs.detect(tmp))
            os.makedirs(os.path.join(tmp, "docs", "game"))
            self.assertIsNone(packs.detect(tmp), "an empty docs/game must not opt in")
            mk(os.path.join(tmp, "docs", "game", "pillars.md"), "# p\n")
            self.assertEqual(packs.detect(tmp), "game")

    def test_missing_bible_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "docs", "game"))
            results = packs.game_design(tmp)
            self.assertTrue(any(not r["ok"] and r["required"] for r in results))

    def test_valid_world_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1")
            quest(tmp, "q2", "q2", requires=["q1"], reveals=["war-started"],
                  characters=["aria"], factions=["guild"])
            results = packs.game_design(tmp)
            self.assertTrue(all(r["ok"] for r in results), results)

    def test_missing_prerequisite_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1", requires=["q9"])
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any("q9" in r["detail"] for r in bad), bad)

    def test_cycle_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "a", "a", requires=["b"])
            quest(tmp, "b", "b", requires=["a"])
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any(r["name"] == "game:cycle" for r in bad), bad)

    def test_unestablished_reveal_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1", reveals=["never-established"])
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any("never-established" in r["detail"] for r in bad), bad)

    def test_unknown_actor_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1", characters=["nobody"])
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any("nobody" in r["detail"] for r in bad), bad)

    def test_duplicate_quest_id_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "one", "same")
            quest(tmp, "two", "same")
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any(r["name"] == "game:quest-id" for r in bad), bad)

    def test_pillars_need_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "pillars.md"),
               "# Pillars\n\n- one\n- two\n")
            results = packs.game_discovery(tmp)
            self.assertTrue(any(not r["ok"] for r in results))
            mk(os.path.join(tmp, "docs", "game", "pillars.md"),
               "# Pillars\n\n- one\n- two\n- three\n")
            self.assertTrue(all(r["ok"] for r in packs.game_discovery(tmp)))


class DepthTests(unittest.TestCase):
    def test_short_vision_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "product", "vision.md"),
               "# V\n\n## Problem\nx\n\n## Audience\ny\n\n## Non-goals\n- a\n- b\n")
            out = depth.vision_depth(tmp)
            self.assertTrue(any(r["name"] == "vision:depth" for r in out))
            self.assertTrue(all(not r["required"] for r in out))

    def test_thin_criteria_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".projtruth", "requirements.json"),
               '{"requirements": [{"id": "R1", "criteria": [{"id": "R1.1", "text": "works"}]}]}')
            out = depth.spec_depth(tmp)
            self.assertTrue(any("R1.1" in r["detail"] for r in out))

    def test_decision_without_why_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".projtruth", "decisions.jsonl"),
               '{"decision": "use sqlite"}\n')
            out = depth.design_depth(tmp)
            self.assertTrue(any(r["name"] == "design:why" for r in out))

    def test_guessed_evidence_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, ".projtruth", "evidence", "R1-a.md"), "guessed\n")
            out = depth.verify_depth(tmp)
            self.assertTrue(any("guessed" in r["detail"] for r in out))


if __name__ == "__main__":
    unittest.main()
