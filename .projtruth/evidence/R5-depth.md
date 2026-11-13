# R5 depth checks flag shallow artifacts without blocking

_Run at 2026-11-14 02:56:41_

```
$ python -m unittest tests.test_packs.DepthTests -v   # exit 0
test_decision_without_why_warns (tests.test_packs.DepthTests) ... ok
test_guessed_evidence_warns (tests.test_packs.DepthTests) ... ok
test_short_vision_warns (tests.test_packs.DepthTests) ... ok
test_thin_criteria_warn (tests.test_packs.DepthTests) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.035s

OK

```

```
$ python -m lifecycle status   # WARN items never fail a stage   # exit 0
# lifecycle (D:\my_idea\lifecycle)
5/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **FAIL** | 5 requirement(s) not verified: R6, R7, R9, R11, R12 |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |
| 6 | Sustain | **WARN** | Does the work survive a context reset, and is it summarised? |

## Blocked
**Stage 4 Verify**
- evidence: 5 requirement(s) not verified: R6, R7, R9, R11, R12
  - re-run each requirement's verification and write evidence, then `projtruth report`

## Next
Stage 4 Verify: **evidence** - 5 requirement(s) not verified: R6, R7, R9, R11, R12

    re-run each requirement's verification and write evidence, then `projtruth report`

## Not blocking
- stage 6 Sustain: the last review has no findings - a review that found nothing did not look; name at least one thing you would change

_2026-11-14 02:56_
```

measured
