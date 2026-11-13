# R4 sibling tools compose, missing ones are advisory

```
$ python -m unittest tests.test_lifecycle.StageTests.test_verify_skips_when_tools_missing -v   # exit 0
test_verify_skips_when_tools_missing (tests.test_lifecycle.StageTests) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.009s

OK

```

```
$ python -m lifecycle status   # in an empty directory   # exit 1
D:\python_39\python.exe: No module named lifecycle
```

```
$ python -m lifecycle check --stage 4   # with projtruth+corpus installed   # exit 1
stage 4 Verify     FAIL
  - evidence: 1 requirement(s) not verified: R4
    -> re-run each requirement's verification and write evidence, then `projtruth report`
```

measured
