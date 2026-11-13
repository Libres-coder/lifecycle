# R5 depth checks flag shallow artifacts without blocking

_Run at 2026-11-13 20:03:17_

```
$ python -m unittest tests.test_packs.DepthTests -v   # exit 0
test_decision_without_why_warns (tests.test_packs.DepthTests) ... ok
test_guessed_evidence_warns (tests.test_packs.DepthTests) ... ok
test_short_vision_warns (tests.test_packs.DepthTests) ... ok
test_thin_criteria_warn (tests.test_packs.DepthTests) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.031s

OK

```

```
$ python -m lifecycle status   # WARN items never fail a stage   # exit 0
# lifecycle (D:\my_idea\lifecycle)
6/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **FAIL** | 1 requirement(s) not verified: R7 |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |
| 6 | Sustain | **PASS** | Does the work survive a context reset, and is it summarised? |

## Blocked
**Stage 4 Verify**
- evidence: 1 requirement(s) not verified: R7
  - re-run each requirement's verification and write evidence, then `projtruth report`

## Next
Stage 4 Verify: **evidence** - 1 requirement(s) not verified: R7

    re-run each requirement's verification and write evidence, then `projtruth report`

_2026-11-13 20:03_
```

measured
