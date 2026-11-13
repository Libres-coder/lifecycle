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
  `~/.claude/settings.json` and the CC Switch provider. 89 tests.
- v1.2.3: the status line carries the advice (`74% ctx - /compact` within five
  points of the trigger), so the always-visible surface asks for the compaction.
- v1.2.4: independent review of the 1.2.x surface (1 P1, 7 P2, all fixed) -
  context readings sanitized on read, `hook install` reports instead of
  silently skipping, legacy hooks upgraded, no stale percentage after resume,
  thread slugs normalized. 100 tests; review note in `docs/reviews/`.
- v1.3.0: packs for work that is not software - story (outline/cast/chapters,
  POV, thread resolution) and the game pack extended with act/order timelines
  and per-character knowledge; `lifecycle pack list|init|guide`. 117 tests.
- Pre-release hardening: snapshots skip the heavy verify stage; hook commands
  fall back to `python -m lifecycle` when the console script is absent.

## Next

- Try the hooks in a real session: does `resume` after a compaction actually
  restore enough to continue, or is it noise?
- Push 1.2.2-1.2.4 (the trigger advice needs one live session to confirm).
- Game pack: timeline order and per-character knowledge (who knows what, when).

## Blockers

None.

## Open questions

- Is the context budget (60k chars) the right threshold? It is a guess until a
  real project crosses it.
- Should the journal be required before the first release, or only after?
