# R5 depth checks flag shallow artifacts without blocking

_Run at 2026-11-13 21:29:46_

```
$ python -m unittest tests.test_packs.DepthTests -v   # exit 0
test_decision_without_why_warns (tests.test_packs.DepthTests) ... ok
test_guessed_evidence_warns (tests.test_packs.DepthTests) ... ok
test_short_vision_warns (tests.test_packs.DepthTests) ... ok
test_thin_criteria_warn (tests.test_packs.DepthTests) ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.029s

OK

```

```
$ python -m lifecycle status   # WARN items never fail a stage   # exit 0
# lifecycle (D:\my_idea\lifecycle)
6/7 stages pass  ·  context: 74% used

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.3.0, v0.4.0) |
| 6 | Sustain | **PASS** | Does the work survive a context reset, and is it summarised? |

## Blocked
**Stage 5 Release**
- tag: no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.3.0, v0.4.0)
  - tag v1.2.1, or fix the version

## Next
Stage 5 Release: **tag** - no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.3.0, v0.4.0)

    tag v1.2.1, or fix the version

_2026-11-13 21:29_
```

measured
