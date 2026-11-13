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
