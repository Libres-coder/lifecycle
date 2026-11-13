"""Tests for the plan artifact, thread structure, cadence and init."""
import os
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lifecycle import thread, threads  # noqa: E402

DAY = 86400


def mk(path, text):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


PLAN = """# Plan

## M1 - first
- [x] a
- [ ] b

## M2 - second
- [ ] c
"""


class PlanTests(unittest.TestCase):
    def test_parse_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, thread.PLAN), PLAN)
            ms = thread.parse_plan(tmp)
            self.assertEqual([m["title"] for m in ms], ["M1 - first", "M2 - second"])
            self.assertEqual((ms[0]["total"], ms[0]["done"]), (2, 1))
            s = thread.plan_summary(tmp)
            self.assertEqual((s["milestones"], s["tasks"], s["tasks_done"]), (2, 3, 1))

    def test_missing_plan_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertTrue(any(not r["ok"] for r in thread.check_plan(tmp)))

    def test_empty_milestone_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, thread.PLAN), "# P\n\n## M1 - nothing\n\nprose only\n")
            self.assertTrue(any("no tasks" in r["detail"] for r in thread.check_plan(tmp)))

    def test_all_done_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, thread.PLAN), "# P\n\n## M1\n- [x] a\n")
            self.assertTrue(any("checked off" in r["detail"]
                                for r in thread.check_plan(tmp)))


class ThreadStructureTests(unittest.TestCase):
    def test_missing_sections_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, thread.CURRENT), "# Current\n\n## Goal\n\nship it\n")
            out = thread.check_thread_structure(tmp)
            self.assertTrue(any("missing" in r["detail"] for r in out), out)

    def test_next_needs_a_bullet(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, thread.CURRENT),
               "# C\n\n## Goal\nx\n\n## Done\n- a\n\n## Next\n\nsoon\n\n## Blockers\nnone\n")
            out = thread.check_thread_structure(tmp)
            self.assertTrue(any(r["name"] == "thread:next" for r in out), out)

    def test_good_thread_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            mk(os.path.join(tmp, thread.CURRENT),
               "# C\n\n## Goal\nx\n\n## Done\n- a\n\n## Next\n- ship\n\n## Blockers\nnone\n")
            self.assertEqual(thread.check_thread_structure(tmp), [])


class CadenceTests(unittest.TestCase):
    def test_three_compactions_without_a_report_warn(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, thread.SNAP_DIR)
            os.makedirs(d)
            for i in range(3):
                p = os.path.join(d, "s%d.md" % i)
                with open(p, "w", encoding="utf-8") as f:
                    f.write("x\n")
                os.utime(p, (time.time() + i, time.time() + i))
            self.assertEqual(thread.cadence(tmp), 3)
            self.assertTrue(any("compaction" in r["detail"]
                                for r in thread.check_cadence(tmp)))

    def test_a_report_resets_the_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, thread.SNAP_DIR)
            os.makedirs(d)
            now = time.time()
            for i in range(3):
                p = os.path.join(d, "s%d.md" % i)
                with open(p, "w", encoding="utf-8") as f:
                    f.write("x\n")
                os.utime(p, (now - 100 + i, now - 100 + i))
            r = os.path.join(tmp, thread.REPORT_DIR, "status.md")
            mk(r, "# r\n")
            os.utime(r, (now, now))
            self.assertEqual(thread.cadence(tmp), 0)


class ThreadTests(unittest.TestCase):
    def test_create_claim_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, msg = threads.create(tmp, "game-main", "Main quest")
            self.assertTrue(ok, msg)
            self.assertIn("game-main", [t["slug"] for t in threads.list_threads(tmp)])
            ok, _ = threads.claim(tmp, "game-main", "aria")
            self.assertTrue(ok)
            self.assertTrue(threads.owner(tmp, "game-main").startswith("aria @"))
            row = threads.describe(tmp)[0]
            self.assertEqual(row["plan"]["total"], 1)
            self.assertEqual(row["next"], "", "the template has no Next item yet")
            path = os.path.join(tmp, threads.THREADS_DIR, "game-main", "current.md")
            mk(path, "# T\n\n## Next\n\n- wire the harbor quest\n")
            self.assertIn("wire the harbor quest", threads.describe(tmp)[0]["next"])
            threads.release(tmp, "game-main")
            self.assertEqual(threads.owner(tmp, "game-main"), "")

    def test_slug_is_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(threads.create(tmp, "Bad Slug!")[0])
            for name in ("nul", "CON", "com1", "lpt9"):
                ok, msg = threads.create(tmp, name)
                self.assertFalse(ok, msg)

    def test_lookups_normalize_case_and_space(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, msg = threads.create(tmp, "My-Thing", "Mixed")
            self.assertTrue(ok, msg)
            ok, msg = threads.claim(tmp, " My-Thing ", "aria")
            self.assertTrue(ok, msg)
            self.assertTrue(threads.owner(tmp, "my-thing").startswith("aria @"))
            self.assertTrue(threads.release(tmp, "MY-THING")[0])
            self.assertIsNotNone(threads._find(tmp, " My-Thing "))

    def test_shared_owner_warns(self):
        with tempfile.TemporaryDirectory() as tmp:
            threads.create(tmp, "one")
            threads.create(tmp, "two")
            threads.claim(tmp, "one", "aria")
            threads.claim(tmp, "two", "aria")
            out = threads.check(tmp)
            self.assertTrue(any("several threads" in r["detail"] for r in out), out)

    def test_no_threads_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(threads.check(tmp), [])


class ScaffoldTests(unittest.TestCase):
    def test_creates_thread_files_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            created = thread.scaffold(tmp)
            self.assertIn(thread.CURRENT, created)
            self.assertTrue(os.path.exists(os.path.join(tmp, thread.PLAN)))
            mk(os.path.join(tmp, thread.CURRENT), "# mine\n")
            thread.scaffold(tmp)
            with open(os.path.join(tmp, thread.CURRENT), encoding="utf-8") as f:
                self.assertEqual(f.read(), "# mine\n")


if __name__ == "__main__":
    unittest.main()
