# R4 sibling tools compose, missing ones are advisory

_Run at 2026-11-14 03:53:46_

```
$ python -m unittest tests.test_lifecycle.StageTests.test_verify_skips_when_tools_missing -v   # exit 0
test_verify_skips_when_tools_missing (tests.test_lifecycle.StageTests) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.007s

OK

```

```
$ python -m unittest tests.test_lifecycle.StageTests.test_verify_does_not_pass_without_requirements -v   # exit 0
test_verify_does_not_pass_without_requirements (tests.test_lifecycle.StageTests)
No registry is stage 1's problem; stage 4 must not claim success. ... ok

----------------------------------------------------------------------
Ran 1 test in 0.007s

OK

```

```
$ python -m lifecycle status   # in an empty directory   # exit 0
# lifecycle (C:\Users\LiuDing\AppData\Local\Temp\tmpqcsep5m1)
0/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **FAIL** | no source files found |
| 4 | Verify | **WARN** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no CHANGELOG |
| 6 | Sustain | **WARN** | Does the work survive a context reset, and is it summarised? |

## Blocked
**Stage 0 Discovery**
- vision: no product vision document
  - write docs/product/vision.md with Problem, Audience and Non-goals
**Stage 1 Spec**
- requirements: no requirement registry
  - projtruth init && projtruth import-spec spec.md (or write .projtruth/requirements.json)
**Stage 2 Design**
- architecture: no architecture document
  - write docs/design/architecture.md: components, data flow, and the trade-off you chose
- decisions: no recorded decision
  - projtruth decide "<choice>" --why "<reason>" for each non-obvious choice
**Stage 3 Build**
- source: no source files found
  - build the thing, or point lifecycle at the right --repo
- tests: no test files found
  - add tests before claiming the build stage is done
**Stage 5 Release**
- changelog: no CHANGELOG
  - write CHANGELOG.md - what changed, for whom

## Next
Stage 0 Discovery: **vision** - no product vision document

    write docs/product/vision.md with Problem, Audience and Non-goals

## Not blocking
- stage 4 Verify: no requirements registered - nothing to verify - stage 1 comes first: add requirements with criteria
- stage 5 Release: not a git repository - git init and tag the release
- stage 6 Sustain: no docs/work/current.md yet - create docs/work/current.md: Goal / Done / Next / Blockers
- stage 6 Sustain: no journal entries - one file per working session in docs/work/log/: what you tried, what happened, what is next
- stage 6 Sustain: no status report yet - `lifecycle report` writes one with the stage state and the open questions
- stage 6 Sustain: no docs/work/plan.md - a long task needs milestones and checkboxes, or 'how far along' is an opinion
- stage 6 Sustain: no review note in docs/reviews/ - record an adversarial review: what you tried to break, what broke, what you decided to live with

_2026-11-14 03:53_
```

```
$ python -m lifecycle check --stage 4   # exit 1
stage 4 Verify     FAIL
  - evidence: 4 requirement(s) not verified: R7, R9, R11, R12
    -> re-run each requirement's verification and write evidence, then `projtruth report`
```

measured
