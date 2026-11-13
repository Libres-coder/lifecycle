# R3 no gate state is stored

_Run at 2026-11-14 03:11:44_

```
$ python -m unittest tests.test_lifecycle.ReportTests -v   # exit 0
test_all_passed_message (tests.test_lifecycle.ReportTests) ... ok
test_next_action_points_at_first_blocker (tests.test_lifecycle.ReportTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK

```

```
$ python -m lifecycle status   # twice, in a copy of this repo
identical: False (exit 0, 0)

# lifecycle (C:\Users\LiuDing)
1/7 stages pass  ·  pack: story

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no characters declared |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **WARN** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no CHANGELOG |
| 6 | Sustain | **WARN** | Do
```

```
$ rm docs/product/vision.md && python -m lifecycle status   # exit 0
# lifecycle (C:\Users\LiuDing)
1/7 stages pass  ·  pack: story

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no characters declared |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **WARN** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no CHANGELOG |
| 6 | Sustain | **WARN** | Do
```

measured
