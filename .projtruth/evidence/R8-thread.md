# R8 the work thread survives a context reset

_Run at 2026-11-13 20:46:18_

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
test_stale_thread_blocks_after_release (tests.test_thread.SustainTests)
A commit that changes code after the thread's last commit is drift. ... ok

----------------------------------------------------------------------
Ran 9 tests in 6.279s

OK

```

```
$ python -m lifecycle resume   # exit 0
Lifecycle: stage 4 Verify - 3 requirement(s) not verified: R8, R9, R10
  fix: re-run each requirement's verification and write evidence, then `projtruth report`

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
  structure checks, compaction cadence.
- 71 tests; 10 requirements verified; 7/7 stages on this repo.
- Pre-release hardening: snapshots skip the heavy verify stage; hook commands
  fall back to `python -m lifecycle` when the console script is absent.

## Next

- Independent review of 1.0, then publish with a release note.
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
- blocked: Sustain
- working tree: 6 changed file(s)
- plan: 3/4 milestones, 9/13 tasks
- d063740 1.0 hardening: light snapshots, module fallback for hooks
- cddd690 docs: where things live, linked from CONTRIBUTING
- d0bd1ce lifecycle 1.0.0: plan, init, thread structure, cadence
    # Current work
    ## Goal
    A checkable contract for shipping a product, plus the thread that keeps a long
    task alive across context resets.
    ## Done
    - v0.2.1: six stages, depth checks, game pack, playbooks, review fixes.

## Recent journal
- `docs/work/log/2026-11-13.md` - # 2026-11-13 / ## Did / - Built the contract, the playbooks, the depth checks and the game pack.
```

```
$ python -m lifecycle report   # exit 0
wrote docs/reports/status-2026-11-13.md
```

measured
