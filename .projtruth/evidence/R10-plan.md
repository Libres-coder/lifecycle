# R10 a plan makes progress visible

_Run at 2026-11-13 21:30:10_

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
test_create_claim_release (tests.test_plan.ThreadTests) ... ok
test_no_threads_is_quiet (tests.test_plan.ThreadTests) ... ok
test_shared_owner_warns (tests.test_plan.ThreadTests) ... ok
test_slug_is_validated (tests.test_plan.ThreadTests) ... ok

----------------------------------------------------------------------
Ran 14 tests in 0.411s

OK

```

```
$ python -m lifecycle resume   # includes plan progress   # exit 0
Lifecycle: stage 5 Release - no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.3.0, v0.4.0)
  fix: tag v1.2.1, or fix the version

context: 74% used


Context at 74%: fine to keep going; compact before you open a new thread.
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
- v1.0.0: plan artifact with milestone progress, `lifecycle init`, thread
  structure ch
```

```
$ python -m lifecycle status   # exit 0
# lifecycle (D:\my_idea\lifecycle)
6/7 stages pass  ·  context: 74% used

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.3.0, v0.4.0) |
| 6 | Sustain | **PASS** | Does the work survive a context reset, and is it summarised? |

## Blocked
**Stage 5 Release**
- tag: no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.
```

measured
