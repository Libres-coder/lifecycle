# R6 the game pack checks world consistency

```
$ python -m unittest tests.test_packs.GamePackTests -v   # exit 0
test_cycle_blocks (tests.test_packs.GamePackTests) ... ok
test_duplicate_quest_id_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_bible_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_prerequisite_blocks (tests.test_packs.GamePackTests) ... ok
test_pack_detected_by_directory (tests.test_packs.GamePackTests) ... ok
test_pillars_need_three (tests.test_packs.GamePackTests) ... ok
test_unestablished_reveal_blocks (tests.test_packs.GamePackTests) ... ok
test_unknown_actor_blocks (tests.test_packs.GamePackTests) ... ok
test_valid_world_passes (tests.test_packs.GamePackTests) ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.135s

OK

```

```
$ python -m lifecycle --repo <game fixture> check --stage 2   # exit 1
stage 2 Design     FAIL
  - architecture: no architecture document
    -> write docs/design/architecture.md: components, data flow, and the trade-off you chose
  - decisions: no recorded decision
    -> projtruth decide "<choice>" --why "<reason>" for each non-obvious choice
  - game:requires: quest(s) require a quest that does not exist: q-keep -> q-missing
    -> fix the id or add the missing quest file
```

measured
