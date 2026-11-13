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


QUEST_BODY = ("the player argues with the harbormaster, pays a price, and the "
              "harbor remembers it. ") * 5
CHAPTER_BODY = ("the harbor smelled of tar and rain and the pen ran dry. ") * 30


def quest(repo, name, qid, requires=(), reveals=(), characters=(), factions=(),
          act=1, order=10, reveals_to=(),
          stakes="the fisher who hid you loses the boat"):
    lines = ["---", "id: %s" % qid, "act: %s" % act, "order: %s" % order,
             "requires: [%s]" % ", ".join(requires),
             "reveals: [%s]" % ", ".join(reveals),
             "characters: [%s]" % ", ".join(characters),
             "factions: [%s]" % ", ".join(factions)]
    if stakes:
        lines.append("stakes: %s" % stakes)
    if reveals_to:
        lines.append("reveals_to:")
        lines.extend("  - %s" % item for item in reveals_to)
    lines.append("---")
    mk(os.path.join(repo, "docs", "game", "quests", name + ".md"),
       "\n".join(lines) + "\n\n# %s\n\n%s\n" % (qid, QUEST_BODY))


def chapter(repo, name, cid, order=10, pov="aria", reveals=(), threads=(),
            resolves=(), reveals_to=(), want="to get the boat back",
            obstacle="the harbormaster holds the writ",
            turn="she learns who signed it"):
    lines = ["---", "id: %s" % cid, "order: %s" % order]
    if pov:
        lines.append("pov: %s" % pov)
    if want:
        lines.append("want: %s" % want)
    if obstacle:
        lines.append("obstacle: %s" % obstacle)
    if turn:
        lines.append("turn: %s" % turn)
    lines += ["reveals: [%s]" % ", ".join(reveals),
              "threads: [%s]" % ", ".join(threads),
              "resolves: [%s]" % ", ".join(resolves)]
    if reveals_to:
        lines.append("reveals_to:")
        lines.extend("  - %s" % item for item in reveals_to)
    lines.append("---")
    mk(os.path.join(repo, "docs", "story", "chapters", name + ".md"),
       "\n".join(lines) + "\n\n%s\n" % CHAPTER_BODY)


STORY_CHARS = """---
characters: [aria, borin]
facts: [war-started, king-dead]
knows:
  - aria: war-started
want:
  - aria: to reclaim the harbor
  - borin: to keep the guild's ledger
obstacle:
  - aria: the guild holds the deed
  - borin: the guild owns him
flaw:
  - aria: trusts the wrong people
  - borin: cannot lie to his father
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

    def test_comments_are_stripped_only_outside_quotes(self):
        text = ("---\nfacts: [a, b]  # the king's death\n"
                'title: "Chapter #1"\n---\n')
        fm = packs.frontmatter(text)
        self.assertEqual(fm["facts"], ["a", "b"])
        self.assertEqual(fm["title"], "Chapter #1")

    def test_quoted_list_items_keep_inner_commas(self):
        fm = packs.frontmatter('---\nthreads: ["a, b", c]\n---\n')
        self.assertEqual(fm["threads"], ["a, b", "c"])

    def test_quoted_pair_sides(self):
        fm = packs.frontmatter('---\nknows:\n  - "aria": "war-started"\n---\n')
        self.assertEqual(packs._start_knowledge(fm), {"aria": {"war-started"}})


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

    def test_repo_path_with_glob_characters_is_still_scanned(self):
        with tempfile.TemporaryDirectory() as base:
            repo = os.path.join(base, "Game [WIP]")
            mk(os.path.join(repo, "docs", "game", "world-bible.md"), BIBLE)
            quest(repo, "q1", "q1", requires=["ghost"])
            bad = [r for r in packs.game_design(repo) if not r["ok"] and r["required"]]
            self.assertTrue(any("ghost" in r["detail"] for r in bad), bad)

    def test_underscore_prefixed_real_file_is_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            mk(os.path.join(tmp, "docs", "game", "quests", "_prologue.md"),
               "---\nid: q-prologue\nact: 1\norder: 1\n---\n\n" + QUEST_BODY)
            quest(tmp, "q2", "q2", requires=["q-prologue"], order=20)
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertFalse(bad, bad)
            self.assertIn("q-prologue", [q["id"] for q in packs._quests(tmp)])

    def test_empty_artifact_directory_does_not_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "docs", "story", "chapters"))
            self.assertIsNone(packs.detect(tmp))
            os.makedirs(os.path.join(tmp, "docs", "game", "quests"))
            self.assertIsNone(packs.detect(tmp))

    def test_knowledge_accumulates_across_quests(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1", order=10, reveals_to=["aria:war-started"])
            quest(tmp, "q2", "q2", order=20, reveals_to=["aria:war-started"])
            out = packs.game_design(tmp)
            hit = [r for r in out if r["name"] == "game:knows-redundant"]
            self.assertTrue(hit, out)
            self.assertIn("q2", hit[0]["detail"])

    def test_knows_naming_undeclared_things_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"),
               BIBLE.replace("facts: [war-started, king-dead]",
                             "facts: [war-started, king-dead]\nknows:\n"
                             "  - ghost: war-started"))
            quest(tmp, "q1", "q1")
            bad = [r for r in packs.game_design(tmp) if not r["ok"] and r["required"]]
            self.assertTrue(any(r["name"] == "game:knows-state" for r in bad), bad)

    def test_quest_without_an_act_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            mk(os.path.join(tmp, "docs", "game", "quests", "q.md"),
               "---\nid: q\norder: 10\n---\n\n" + QUEST_BODY)
            out = packs.game_design(tmp)
            self.assertTrue(any(r["name"] == "game:timeline-act" for r in out), out)

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

    def test_craft_flags_a_summary_chapter(self):
        self.write_world()
        mk(os.path.join(self.repo, "docs", "story", "chapters", "thin.md"),
           "---\nid: ch-09\norder: 90\npov: aria\n---\n\nthey argued.\n")
        out = packs.story_craft(self.repo)
        names = {r["name"] for r in out if not r["ok"]}
        self.assertIn("story:craft-scene", names)
        self.assertIn("story:craft-thin", names)
        self.assertTrue(all(not r["required"] for r in out), "craft is advisory")

    def test_craft_flags_a_character_without_a_want(self):
        mk(os.path.join(self.repo, "docs", "story", "characters.md"),
           "---\ncharacters: [aria, borin]\nfacts: []\n"
           "want:\n  - aria: the boat\n"
           "obstacle:\n  - aria: the writ\n"
           "flaw:\n  - aria: trust\n---\n")
        out = packs.story_craft(self.repo)
        warned = [r for r in out if r["name"] == "story:craft-character"][0]
        self.assertIn("borin", warned["detail"])

    def test_craft_flags_a_quest_without_stakes(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "game", "world-bible.md"), BIBLE)
            quest(tmp, "q1", "q1", stakes="")
            out = packs.game_craft(tmp)
            self.assertTrue(any(r["name"] == "game:craft-stakes" for r in out), out)

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

    def test_thread_resolved_before_its_last_advance_warns(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir"],
                resolves=["the-heir"])
        chapter(self.repo, "two", "ch-02", order=20, threads=["the-heir"])
        out = packs.story_design(self.repo)
        self.assertTrue(any(r["name"] == "story:threads-order" for r in out), out)

    def test_word_count_counts_kana_and_hangul(self):
        self.assertGreater(packs._word_count("あ" * 300), 250)
        self.assertGreater(packs._word_count("가" * 300), 250)
        self.assertEqual(packs._word_count("---\nid: x\n---\n"), 0)

    def test_story_packs_wiring_runs_both_checks(self):
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir"],
                resolves=["the-heir"])
        chapter(self.repo, "two", "ch-02", order=20, threads=["the-war"],
                resolves=["the-war"])
        results = []
        for check in packs.PACKS["story"]["design"]:
            results.extend(check(self.repo))
        self.assertTrue(all(r["ok"] for r in results), results)

    def test_story_pack_replaces_the_generic_design_artifacts(self):
        from lifecycle import contract
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir"],
                resolves=["the-heir"])
        chapter(self.repo, "two", "ch-02", order=20, pov="borin",
                threads=["the-war"], resolves=["the-war"])
        stages = contract.evaluate(self.repo, pack="story")
        stage2 = next(s for s in stages if s["id"] == 2)
        names = [r["name"] for r in stage2["results"]]
        self.assertNotIn("architecture", names)
        self.assertNotIn("decisions", names)
        self.assertEqual(stage2["state"], "passed", stage2["results"])

    def test_auto_detection_never_removes_a_generic_gate(self):
        """A narrative folder in a software repo must not drop architecture."""
        from lifecycle import contract
        self.write_world()
        chapter(self.repo, "one", "ch-01", order=10, threads=["the-heir"],
                resolves=["the-heir"])
        chapter(self.repo, "two", "ch-02", order=20, pov="borin",
                threads=["the-war"], resolves=["the-war"])
        stages = contract.evaluate(self.repo)          # auto-detected story
        stage2 = next(s for s in stages if s["id"] == 2)
        names = [r["name"] for r in stage2["results"]]
        self.assertIn("architecture", names)
        self.assertIn("decisions", names)
        self.assertEqual(stage2["state"], "failed", stage2["results"])

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

    def test_scaffold_reports_a_path_conflict_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, "docs", "story", "chapters"), "not a directory\n")
            result, err = packs.scaffold(tmp, "story")
            self.assertIsNone(result)
            self.assertIn("not a directory", err)
            self.assertFalse(os.path.exists(os.path.join(tmp, "docs", "story",
                                                          "outline.md")))

    def test_cli_pack_commands_ignore_a_bogus_pack_flag(self):
        from lifecycle import cli
        import io
        with tempfile.TemporaryDirectory() as tmp:
            old = sys.stdout
            sys.stdout = io.StringIO()
            try:
                rc_list = cli.main(["--repo", tmp, "--pack", "bogus", "pack", "list"])
                rc_status = cli.main(["--repo", tmp, "--pack", "bogus", "status"])
            finally:
                sys.stdout = old
            self.assertEqual(rc_list, 0, "listing must not depend on --pack")
            self.assertEqual(rc_status, 2)

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
