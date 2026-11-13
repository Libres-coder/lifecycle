# R1 status is computed from repository artifacts

_Run at 2026-11-13 21:29:34_

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
Ran 8 tests in 0.045s

OK

```

```
$ python -m unittest tests.test_review2.RegistryRobustnessTests -v   # exit 0
test_bom_registry_is_read (tests.test_review2.RegistryRobustnessTests) ... ok
test_malformed_registry_reports_instead_of_crashing (tests.test_review2.RegistryRobustnessTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.029s

OK

```

```
$ python -m lifecycle status   # exit 0
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
