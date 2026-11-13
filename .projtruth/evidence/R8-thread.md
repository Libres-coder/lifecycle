# R8 the work thread survives a context reset

_Run at 2026-11-13 21:49:36_

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
Ran 9 tests in 5.926s

OK

```

```
$ python -m lifecycle resume   # exit 0
Lifecycle: stage 4 Verify - 1 requirement(s) not verified: R11
  fix: re-run each requirement's verification and write evidence, then `projtruth report`

context: 58% used


Context at 58%: fine for the current step; run /compact before starting a new thread (auto-compact fires at 70%).
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
- Pre-release review fixed: tag matching, version discovery, commit-time
  freshness, hook command resolution, criteria validation, report overwrite.
- v1.1.0: threads (per-thread handoff/plan/owner, portfolio table,
  `resume --thread`, stale-claim and shared-owner warnings).
- v1.2.0: context readings via the statusline payload; `resume --hook` records
  session-start tokens; docs on why 74% does not compact.
- v1.2.1: hook stays silent outside an initialized repo; `lifecycle suggest`
  names the tool and the compaction advice.
- v1.2.2: the advice follows the real trigger - `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`
  moves the nudge to trigger−15 and `/compact now` to trigger−5 (55/65 when the
  trigger is 70). The machine override is installed at 70% in both
  `~/.claude/settings.json` and the CC Switch provider. 88 tests.
- Pre-release hardening: snapshots skip the heavy verify stage; hook commands
  fall back to `python -m lifecycle` when the console script is absent.

## Next

- Independent review of the 1.x surface (threads, statusline, trigger advice).
- Try the hooks in a real session: does `resume` after a compaction actually
  restore enough to continue, or is it noise?
- Publish 1.2.2 once the trigger advice has been seen in a live session.
- Game pack: timeline order and per-character knowledge (who knows what, when).

## Blockers

None.

## Open questions

- Is the context budget (60k chars) the right threshold? It is a guess until a
  real project crosses it.
- Should the journal be required before the first release, or only after?

## Plan

4/6 milestones, 18/20 tasks done.

## Last compaction snapshot

- stages: 5/7 pass
- blocked: Sustain
- working tree: 10 changed file(s)
- plan: 4/5 milestones, 15/17 tasks
- context: 74% (as of 12 min ago - install the statusline hook to keep it current)
- d2415a0 lifecycle 1.2.2: context advice follows the real compaction trigger
- 8718453 lifecycle 1.2.1: quiet hook, suggest, context warning
- 2c3e0d6 lifecycle 1.2.0: context readings
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
