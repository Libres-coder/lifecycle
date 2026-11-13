# R3 no gate state is stored

_Run at 2026-11-14 03:53:41_

```
$ python -m unittest tests.test_lifecycle.ReportTests -v   # exit 0
test_all_passed_message (tests.test_lifecycle.ReportTests) ... ok
test_next_action_points_at_first_blocker (tests.test_lifecycle.ReportTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.001s

OK

```

```
$ python -m lifecycle status   # twice, in a copy of this repo
identical: True (exit 0, 0)

# lifecycle (C:\Users\LiuDing\AppData\Local\Temp\tmpqmorakp2\demo)
3/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no recorded decision |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **WARN** | Is every promise backed by evidence that still holds? |
| 5 | Release | **WARN** | Is ther
```

```
$ rm docs/product/vision.md && python -m lifecycle status   # exit 0
# lifecycle (C:\Users\LiuDing\AppData\Local\Temp\tmpqmorakp2\demo)
2/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no recorded decision |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **WARN** | Is every promise backed by evidence that still holds? |
| 5 | Release | **WARN** | Is there a version, a chan
```

measured
