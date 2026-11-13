# R3 no gate state is stored

```
$ python -m unittest tests.test_lifecycle.ReportTests -v   # exit 0
test_all_passed_message (tests.test_lifecycle.ReportTests) ... ok
test_next_action_points_at_first_blocker (tests.test_lifecycle.ReportTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.000s

OK

```

```
$ python -m lifecycle status   # twice, in a copy of this repo: identical=True
first run exit 0, second exit 0, outputs identical: True

# lifecycle (C:\Users\LiuDing\AppData\Local\Temp\tmp2dew19rl\demo)
3/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no recorded decision |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no CHANGELOG |

## Next
Stage 1 Spec: **requirements** - no requirement registry

    projtruth init && pro
```

```
$ rm docs/product/vision.md && python -m lifecycle status   # exit 0
# lifecycle (C:\Users\LiuDing\AppData\Local\Temp\tmp2dew19rl\demo)
2/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no recorded decision |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no CHANGELOG |

## Next
Stage 0 Discovery: **vision** - no product vision document

    write docs/product/vision.md with Prob
```

measured
