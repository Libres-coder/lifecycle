# R5 depth checks flag shallow artifacts without blocking

```
$ python -m unittest tests.test_packs.DepthTests -v   # exit 0
test_decision_without_why_warns (tests.test_packs.DepthTests) ... ok
test_guessed_evidence_warns (tests.test_packs.DepthTests) ... ok
test_short_vision_warns (tests.test_packs.DepthTests) ... ok
test_thin_criteria_warn (tests.test_packs.DepthTests) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.033s

OK

```

```
$ python -m lifecycle status   # WARN items never fail a stage   # exit 0
# lifecycle (D:\my_idea\lifecycle)
5/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **FAIL** | 3 requirement(s) not verified: R5, R6, R7 |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |

## Blocked
**Stage 4 Verify**
- evidence: 3 requirement(s) not verified: R5, R6, R7
  - re-run each requirement's verification and write evidence, then `projtruth report`

## Next
Stage 4 Verify: **evidence** - 3 requirement(s) not verified: R5, R6, R7

    re-run each requirement's verification and write evidence, then `projtruth report`

_2026-11-13 19:51_
```

measured
