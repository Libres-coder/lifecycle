# R8 the work thread survives a context reset

_Run at 2026-11-15 18:46:39_

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
Ran 9 tests in 6.245s

OK

```

```
$ python -m lifecycle resume   # exit 0
Lifecycle: stage 4 Verify - 1 requirement(s) not verified: R12
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
- v1.3.1: `suggest` names the active pack at stages 0/2; corpus 0.1.3 skips
  `_template.md` scaffold files so the two tools agree on what a document is.
  118 tests.
- v1.4.0: packs carry a craft standard, not only structure - story (concrete
  scenes, conflict engine, no evasion, stakes, contradictions) and game (verb
  with a cost, choices, a world that remembers), plus advisory craft checks on
  declared `want`/`obstacle`/`turn`/`stakes` and length. 121 tests.
- v1.4.1: independent review of the pack layer (2 P1, 6 P2, all fixed) - glob
  escaping, only `_template.md` skipped, quote/comment parsing, detection,
  knowledge accumulation, timeline/thread ordering, scaffold errors, CJK word
  count. 135 tests; review note in `docs/reviews/`.
- v1.4.2: packs may replace generic artifacts (story stands in for
  architecture/decisions); stage 4 reads `evidence_tier` and warns when
  verified requirements rest on guesses or untiered evidence. 138 tests.
- v1.4.3: replacement is explicit-only - auto-detected packs add checks and
  never remove a gate, so a story folder in a software repo cannot weaken its
  own architecture requirement. 139 tests.
- v1.4.4: kinds of work are peers - a pack may replace checks at any stage;
  story replaces stage 3's source/tests with `story:draft` (chapter and word
  counts). End-to-end contract test with the installed siblings pins the JSON
  lifecycle reads; `references/writing-a-pack.md` documents how to add a type.
- v1.4.5: fixed root finding - a stray `.projtruth/` or `.lifecycle/` in an
  ancestor hijacked subdirectories (found in a game dry run); home and drive
  root are never roots now. README.zh-CN brought up to 1.4.x. 147 tests.
- v1.4.6: `--with <pack>` - a project can be more than one kind of work (a game
  with a written narrative keeps architecture, source and tests while its story
  checks run); the secondary pack adds, never replaces. CI installs the sibling
  tools so the cross-tool contract runs on Linux, and dogfoods stage 4. 148
  tests.
- v1.4.7: auto-detection runs every kind of work present, not just the first -
  a game+story project gets both check sets and the table says `pack:
  game+story`; replacement still belongs to an explicit primary. 149 tests.
- v1.5.0: story checks the heart, not only the graph - premise, theme, main
  thread, inciting incident; protagonist want/need/lie; antagonist
  goal/plan/constraint; faction wants/ties; act density, per-chapter cast,
  and repeated beats. Driven by a real outline that was wide and empty. 162
  tests.
- Pre-release hardening: snapshots skip the heavy verify stage; hook commands
  fall back to `python -m lifecycle` when the console script is absent.

## Next

- Use it on a real long task (not a demo) and see whether `resume` after a
  compaction restores enough to continue, and whether `--with` matches how the
  work actually spans kinds (game + its tooling, app + its docs).
- Calibrate the 60k context budget against that real project.
- Add a pack only when a real project needs it (service, film, site).

## Blockers

None.

## Open questions

- Is the context budget (60k chars) the right threshold? It is a guess until a
  real project crosses it.
- Should the journal be required before the first release, or only after?

## Plan

4/7 milestones, 22/25 tasks done.

## Last compaction snapshot

- stages: 6/7 pass
- blocked: none
- working tree: 11 changed file(s)
- plan: 4/7 milestones, 22/25 tasks
- 71a7982 lifecycle 1.5.0: the story pack checks the heart and the network
- 53116df evidence: regenerate for 1.4.7 (12/12 verified)
- ceb12c2 lifecycle 1.4.7: auto-detection runs every kind of work present
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
wrote docs/reports/status-2026-11-15.md
```

measured
