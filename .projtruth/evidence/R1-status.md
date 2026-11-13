# R1 status is computed from repository artifacts

```
$ python -m unittest tests.test_lifecycle.StageTests -v   # exit 0
test_build_needs_tests (tests.test_lifecycle.StageTests) ... ok
test_design_needs_architecture_and_a_decision (tests.test_lifecycle.StageTests) ... ok
test_spec_requires_criteria (tests.test_lifecycle.StageTests) ... ok
test_verify_blocks_on_unverified_requirement (tests.test_lifecycle.StageTests) ... ok
test_verify_does_not_pass_without_requirements (tests.test_lifecycle.StageTests)
No registry is stage 1's problem; stage 4 must not claim success. ... ok
test_verify_skips_when_tools_missing (tests.test_lifecycle.StageTests) ... ok
test_vision_missing_section_names_it (tests.test_lifecycle.StageTests) ... ok
test_vision_sections (tests.test_lifecycle.StageTests) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.047s

OK

```

```
$ python -m lifecycle --repo . status   # exit 0
# lifecycle (D:\my_idea\lifecycle)
4/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **FAIL** | 3 requirement(s) not verified: R1, R3, R4 |
| 5 | Release | **FAIL** | newest tag v0.1.0 does not match version 0.2.0 |

## Blocked
**Stage 4 Verify**
- evidence: 3 requirement(s) not verified: R1, R3, R4
  - re-run each requirement's verification and write evidence, then `projtruth report`
**Stage 5 Release**
- tag: newest tag v0.1.0 does not match version 0.2.0
  - bump the version or tag 0.2.0

## Next
Stage 4 Verify: **evidence** - 3 requirement(s) not verified: R1, R3, R4

    re-run each requirement's verification and write evidence, then `projtruth report`

_2026-11-13 19:36_
```

measured
