# R10 a plan makes progress visible

_Run at 2026-11-13 20:28:22_

```
$ python -m unittest tests.test_plan -v   # exit 0
test_a_report_resets_the_count (tests.test_plan.CadenceTests) ... ok
test_three_compactions_without_a_report_warn (tests.test_plan.CadenceTests) ... ok
test_all_done_warns (tests.test_plan.PlanTests) ... ok
test_empty_milestone_warns (tests.test_plan.PlanTests) ... ok
test_missing_plan_warns (tests.test_plan.PlanTests) ... ok
test_parse_and_summary (tests.test_plan.PlanTests) ... ok
test_creates_thread_files_and_never_overwrites (tests.test_plan.ScaffoldTests) ... ok
test_good_thread_is_quiet (tests.test_plan.ThreadStructureTests) ... ok
test_missing_sections_warn (tests.test_plan.ThreadStructureTests) ... ok
test_next_needs_a_bullet (tests.test_plan.ThreadStructureTests) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.096s

OK

```

```
$ python -m lifecycle resume   # includes plan progress   # exit 0
# Current work

## Goal

A checkable contract for shipping a product, plus the thread that keeps a long
task alive across context resets.

## Done

- v0.2.1: six stages, depth checks, game pack, playbooks, review fixes.
- v0.3.0: stage 6 Sustain - work thread, journal, status reports, context budget.
- v0.4.0: PreCompact/SessionStart hooks (`lifecycle hook install`), snapshots
  that record the transcript size, a review-note check, and a per-stage toolbox
  in `guide`.
- 61 tests; 7/7 stages on this repo; v0.4.0 tagged.

## Next

- Finish M4: init on an empty repo, docs pass, review, publish 1.0.
- Try the hooks in a real session: does `resume` after a compaction actually
  restore enough to continue, or is it noise?
- Publish to GitHub once the thread layer has survived one real handoff.

```

```
$ python -m lifecycle status   # exit 0
# lifecycle (D:\my_idea\lifecycle)
5/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **FAIL** | 1 requirement(s) not verified: R10 |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |
| 6 | Sustain | **FAIL** | code changed after docs/work/current.md |

## Blocked
**Stage 4 Verify**
- evidence: 1 requirement(s) not verified: R10
  - re-run each requirement's verification and write evidence, then `projtruth report`
**Stage 6 Sustain**
- thread:fre
```

measured
