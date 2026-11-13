# R5 depth checks flag shallow artifacts without blocking

```
$ python -m unittest tests.test_packs.DepthTests -v   # exit 0
test_decision_without_why_warns (tests.test_packs.DepthTests) ... ok
test_guessed_evidence_warns (tests.test_packs.DepthTests) ... ok
test_short_vision_warns (tests.test_packs.DepthTests) ... ok
test_thin_criteria_warn (tests.test_packs.DepthTests) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.050s

OK

```

```
$ python -m lifecycle status   # exit 0, WARN items never fail a stage
# lifecycle (D:\my_idea\lifecycle)
5/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | newest tag v0.1.0 does not match version 0.2.0 |

## Blocked
**Stage 5 Release**
- tag: newest tag v0.1.0 does not match version 0.2.0
  - bump the version or tag 0.2.0

## Next
Stage 5 Release: **tag** - newest tag v0.1.0 does not match version 0.2.0

    bump the version or tag 0.2.0

_2026-11-13 19:36_
```

measured
