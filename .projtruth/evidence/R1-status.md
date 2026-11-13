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
Ran 8 tests in 0.037s

OK

```

```
$ python -m unittest tests.test_review2.RegistryRobustnessTests -v   # exit 0
test_bom_registry_is_read (tests.test_review2.RegistryRobustnessTests) ... ok
test_malformed_registry_reports_instead_of_crashing (tests.test_review2.RegistryRobustnessTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.030s

OK

```

```
$ python -m lifecycle status   # exit 0
# lifecycle (D:\my_idea\lifecycle)
5/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **PASS** | How is it built, and why this way? |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **FAIL** | 7 requirement(s) not verified: R1, R2, R3, R4, R5, R6 |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |

## Blocked
**Stage 4 Verify**
- evidence: 7 requirement(s) not verified: R1, R2, R3, R4, R5, R6
  - re-run each requirement's verification and write evidence, then `projtruth report`

## Next
Stage 4 Verify: **evidence** - 7 requirement(s) not verified: R1, R2, R3, R4, R5, R6

    re-run each requirement's verification and write evidence, then `projtruth report`

_2026-11-13 19:51_
```

measured
