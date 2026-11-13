# R8 the work thread survives a context reset

_Run at 2026-11-13 20:03:27_

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
Ran 9 tests in 3.872s

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
- `lifecycle resume` and `lifecycle report` implemented and tested (51 tests).

## Next

- Use `lifecycle resume` in the next session before touching code.
- Publish to GitHub once the thread layer has survived one real handoff.
- Game pack: timeline order and per-character knowledge (who knows what, when).

## Blockers

None.

## Open questions

- Is the context budget (60k chars) the right threshold? It is a guess until a
  real project crosses it.
- Should the journal be required before the first release, or only after?

## Recent journal
- `docs/work/log/2026-11-13.md` - # 2026-11-13 / ## Did / - Built the contract, the playbooks, the depth checks and the game pack.

Lifecycle: every stage passes.
```

```
$ python -m lifecycle report   # exit 0
wrote docs/reports/status-2026-11-13.md
```

measured
