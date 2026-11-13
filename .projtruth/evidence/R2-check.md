# R2 check exits 1 on a failing stage

_Run at 2026-11-14 03:04:43_

```
$ python -m unittest tests.test_lifecycle.CliTests -v   # exit 0
stage 0 Discovery  FAIL
  - vision: no product vision document
    -> write docs/product/vision.md with Problem, Audience and Non-goals
test_check_fails_and_names_the_stage (tests.test_lifecycle.CliTests) ... ok
test_check_stage_zero_only (tests.test_lifecycle.CliTests) ... lifecycle: no stage 9 (0-6)
ok
test_json_status_shape (tests.test_lifecycle.CliTests) ... ok
test_repo_must_exist (tests.test_lifecycle.CliTests) ... lifecycle: --repo is not a directory: D:\my_idea\lifecycle\no-such-dir-xyz
ok

----------------------------------------------------------------------
Ran 4 tests in 1.282s

OK

```

```
$ python -m lifecycle check --stage 2   # exit 0
python -m lifecycle check --stage 9   # exit 2
stage 2 Design     PASSED
lifecycle: no stage 9 (0-6)
```

measured
