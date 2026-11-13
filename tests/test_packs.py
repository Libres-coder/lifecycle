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

BIBLE_KNOWS = BIBLE.replace("facts: [war-started, king-dead]",
                            "facts: [war-started, king-dead]\nknows:\n  - aria: war-started")


def quest(repo, name, qid, requires=(), reveals=(), characters=(), factions=(),
          act=1, order=10, reveals_to=()):
    lines = ["---", "id: %s" % qid, "act: %s" % act, "order: %s" % order,
             "requires: [%s]" % ", ".join(requires),
             "reveals: [%s]" % ", ".join(reveals),
             "characters: [%s]" % ", ".join(characters),
             "factions: [%s]" % ", ".join(factions)]
    if reveals_to:
        lines.append("reveals_to:")
        lines.extend("  - %s" % item for item in reveals_to)
    lines.append("---")
    mk(os.path.join(repo, "docs", "game", "quests", name + ".md"),
       "\n".join(lines) + "\n\n# %s\n" % qid)


def chapter(repo, name, cid, order=10, pov="aria", reveals=(), threads=(),
            resolves=(), reveals_to=()):
    lines = ["---", "id: %s" % cid, "order: %s" % order]
    if pov:
        lines.append("pov: %s" % pov)
    lines += ["reveals: [%s]" % ", ".join(reveals),
              "threads: [%s]" % ", ".join(threads),
              "resolves: [%s]" % ", ".join(resolves)]
    if reveals_to:
        lines.append("reveals_to:")
        lines.extend("  - %s" % item for item in reveals_to)
    lines.append("---")
    mk(os.path.join(repo, "docs", "story", "chapters", name + ".md"),
       "\n".join(lines) + "\n\nprose\n")


STORY_CHARS = """---
characters: [aria, borin]
facts: [war-started, king-dead]
knows:
  - aria: war-started
---
"""

STORY_OUTLINE = """---
acts: [setup, turn, resolution]
threads: [the-heir, the-war]
---

# Outline
"""


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

    def test_timeline_inversion_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "early", "early", requires=["late"], order=10)
            quest(tmp, "late", "late", order=20)
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any(r["name"] == "game:timeline-order" for r in bad), bad)

    def test_missing_order_warns_not_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            mk(os.path.join(tmp, "docs", "game", "quests", "q.md"),
               "---\nid: q\n---\n")
            out = packs.game_design(tmp)
            timeline = [r for r in out if r["name"] == "game:timeline"]
            self.assertTrue(timeline and not timeline[0]["ok"], out)
            self.assertFalse(timeline[0]["required"])

    def test_reveal_to_someone_who_already_knows_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE_KNOWS)
            quest(tmp, "q1", "q1", reveals_to=["aria:war-started"])
            out = packs.game_design(tmp)
            self.assertTrue(any(r["name"] == "game:knows-redundant" for r in out), out)
            self.assertTrue(all(r["ok"] for r in out if r["required"]), out)

    def test_reveal_to_unknown_fact_or_actor_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1", reveals_to=["aria:never", "nobody:war-started"])
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            names = {r["name"] for r in bad}
            self.assertIn("game:knows-fact", names)
            self.assertIn("game:knows-actor", names)

    def test_pillars_need_three(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "pillars.md"),
               "# Pillars\n\n- one\n- two\n")
            results = packs.game_discovery(tmp)
            self.assertTrue(any(not r["ok"] for r in results))
            mk(os.path.join(tmp, "docs", "game", "pillars.md"),
               "# Pillars\n\n- one\n- two\n- three\n")
            self.assertTrue(all(r["ok"] for r in packs.game_discovery(tmp)))


class StoryPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def write_world(self):
        mk(os.path.join(self.repo, "docs", "story", "outline.md"), STORY_OUTLINE)
        mk(os.path.join(self.repo, "docs", "story", "characters.md"), STORY_CHARS)

    def test_detected_by_outline_not_an_empty_directory(self):
        os.makedirs(os.path.join(self.repo, "docs", "story"))
        self.assertIsNone(packs.detect(self.repo))
        mk(os.path.join(self.repo, "docs", "story", "outline.md"), STORY_OUTLINE)
        self.assertEqual(packs.detect(self.repo), "story")

    def test_discovery_needs_an_outline(self):
        bad = [r for r in packs.story_discovery(self.repo) if not r["ok"]]
        self.assertTrue(bad)
        mk(os.path.join(self.repo, "docs", "story", "outline.md"), STORY_OUTLINE)
        self.assertTrue(all(r["ok"] for r in packs.story_discovery(self.repo)))

    def test_discovery_warns_without_threads(self):
        mk(os.path.join(self.repo, "docs", "story", "outline.md"),
           "---\nacts: [one, two]\n---\n")
        out = packs.story_discovery(self.repo)
        self.assertTrue(any(r["name"] == "story:threads" for r in out), out)

    def test_valid_story_passes(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir"],
                resolves=["the-heir"])
        chapter(self.repo, "two", "ch-02", order=20, pov="borin",
                threads=["the-war"], resolves=["the-war"], reveals=["king-dead"])
        out = packs.story_design(self.repo)
        self.assertTrue(all(r["ok"] for r in out), out)

    def test_duplicate_order_blocks(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10)
        chapter(self.repo, "two", "ch-02", order=10)
        bad = [r for r in packs.story_design(self.repo) if not r["ok"] and r["required"]]
        self.assertTrue(any(r["name"] == "story:order-dup" for r in bad), bad)

    def test_undeclared_pov_blocks(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", pov="stranger")
        bad = [r for r in packs.story_design(self.repo) if not r["ok"] and r["required"]]
        self.assertTrue(any(r["name"] == "story:pov" for r in bad), bad)

    def test_unknown_thread_blocks_and_open_thread_warns(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir", "ghost"])
        out = packs.story_design(self.repo)
        names = {r["name"] for r in out if not r["ok"]}
        self.assertIn("story:threads-unknown", names)
        self.assertIn("story:threads-open", names)
        open_thread = [r for r in out if r["name"] == "story:threads-open"][0]
        self.assertFalse(open_thread["required"])

    def test_reveal_to_a_character_who_already_knows_warns(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir"],
                resolves=["the-heir"], reveals_to=["aria:war-started"])
        out = packs.story_design(self.repo)
        self.assertTrue(any(r["name"] == "story:knows-redundant" for r in out), out)


class ScaffoldTests(unittest.TestCase):
    def test_pack_init_creates_structure_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, err = packs.scaffold(tmp, "story")
            self.assertIsNone(err)
            self.assertIn("docs/story/outline.md", result["created"])
            before = os.path.getmtime(os.path.join(tmp, "docs", "story", "outline.md"))
            result2, _ = packs.scaffold(tmp, "story")
            self.assertEqual(result2["created"], [])
            self.assertEqual(os.path.getmtime(
                os.path.join(tmp, "docs", "story", "outline.md")), before)

    def test_templates_are_not_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            packs.scaffold(tmp, "game")
            self.assertEqual(packs._quests(tmp), [])
            out = packs.game_design(tmp)
            self.assertTrue(any(r["name"] == "game:quests" for r in out), out)

    def test_unknown_pack_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            result, err = packs.scaffold(tmp, "nope")
            self.assertIsNone(result)
            self.assertIn("unknown pack", err)

    def test_suggest_names_the_active_pack(self):
        from lifecycle import cli
        import io
        with tempfile.TemporaryDirectory() as tmp:
            packs.scaffold(tmp, "story")
            old = sys.stdout
            sys.stdout = io.StringIO()
            try:
                rc = cli.main(["--repo", tmp, "suggest"])
                out = sys.stdout.getvalue()
            finally:
                sys.stdout = old
            self.assertEqual(rc, 0)
            self.assertIn("pack guide story", out)

    def test_cli_pack_list_and_init(self):
        from lifecycle import cli
        import io
        with tempfile.TemporaryDirectory() as tmp:
            old = sys.stdout
            sys.stdout = io.StringIO()
            try:
                rc = cli.main(["--repo", tmp, "pack", "list"])
                listing = sys.stdout.getvalue()
                rc2 = cli.main(["--repo", tmp, "pack", "init", "game"])
                init_out = sys.stdout.getvalue()
            finally:
                sys.stdout = old
            self.assertEqual(rc, 0)
            self.assertIn("game", listing)
            self.assertIn("story", listing)
            self.assertEqual(rc2, 0)
            self.assertIn("docs/game/pillars.md", init_out)
            self.assertTrue(os.path.isfile(os.path.join(tmp, "docs", "game", "pillars.md")))


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
