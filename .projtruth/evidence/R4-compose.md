# R4 sibling tools compose, missing ones are advisory

```
$ python -m unittest tests.test_lifecycle.StageTests.test_verify_skips_when_tools_missing -v   # exit 0
test_verify_skips_when_tools_missing (tests.test_lifecycle.StageTests) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.007s

OK

```

```
$ python -m lifecycle status   # in an empty directory   # exit 0
# lifecycle (C:\Users\LiuDing\AppData\Local\Temp\tmpi796l25d)
1/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **FAIL** | no requirement registry |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **FAIL** | no source files found |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no CHANGELOG |

## Next
Stage 0 Discovery: **vision** - no product vision document

    write docs/product/vision.md with Problem, Audience and Non-goals

## Not blocking
- stage 5 Release: not a git repository - git init and tag the release

_2026-11-13 19:36_
```

```
$ python -m lifecycle check --stage 4   # projtruth + corpus installed   # exit 1
stage 4 Verify     FAIL
  - evidence: 1 requirement(s) not verified: R4
    -> re-run each requirement's verification and write evidence, then `projtruth report`
```

measured
