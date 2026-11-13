# R8 the work thread survives a context reset

_Run at 2026-11-13 20:28:14_

```
$ python -m unittest tests.test_thread -v   # exit 0
test_stage_six_is_registered (tests.test_thread.StageSixTests) ... ok
test_after_release_a_missing_thread_blocks (tests.test_thread.SustainTests) ... ok
test_before_release_a_missing_thread_warns (tests.test_thread.SustainTests) ... ok
test_context_budget (tests.test_thread.SustainTests) ... ok
test_fresh_thread_passes (tests.test_thread.SustainTests) ... ok
test_old_journal_warns (tests.test_thread.SustainTests) ... ok
test_report_is_drafted_from_facts (tests.test_thread.SustainTests) ... ok
test_resume_prints_state_and_journal (tests.test_thread.SustainTests) ... ok
test_stale_thread_blocks_after_release (tests.test_thread.SustainTests) ... ok

----------------------------------------------------------------------
Ran 9 tests in 3.736s

OK

```

```
$ python -m lifecycle resume   # exit 0
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
- Game pack: timeline order and per-character knowledge (who knows what, when).

## Blockers

None.

## Open questions

- Is the context budget (60k chars) the right threshold? It is a guess until a
  real project crosses it.
- Should the journal be required before the first release, or only after?

## Plan

3/4 milestones, 9/13 tasks done.

## Last compaction snapshot

- stages: 5/7 pass
- blocked: Verify, Sustain
- working tree: 24 changed file(s)
- c29bc6a docs: long-running work in the README
- 515e269 lifecycle 0.3.0: the long-running thread
- b0a75a9 lifecycle 0.2.1: review fixes
    # Current work
    ## Goal
    A checkable contract for shipping a product, plus the thread that keeps a long
    task alive across context resets.
    ## Done
    - v0.2.1: six stages, depth checks, game pack, playbooks, review fixes.

## Recent journal
- `docs/work/log/2026-11-13.md` - # 2026-11-13 / ## Did / - Built the contract, the playbooks, the depth checks and the game pack.

Lifecycle: stage 4 Verify - 3 requirement(s) not verified: R8, R9, R10
  fix: re-run each requirement's verification and write evidence, then `projtruth report`
```

```
$ python -m lifecycle report   # exit 0
wrote docs/reports/status-2026-11-13.md
```

measured
