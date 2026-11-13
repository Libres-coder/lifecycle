# R6 the game pack checks world consistency

_Run at 2026-11-13 23:37:43_

```
$ python -m unittest tests.test_packs.GamePackTests -v   # exit 0
test_cycle_blocks (tests.test_packs.GamePackTests) ... ok
test_duplicate_quest_id_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_bible_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_order_warns_not_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_prerequisite_blocks (tests.test_packs.GamePackTests) ... ok
test_pack_detected_by_artifacts_not_an_empty_directory (tests.test_packs.GamePackTests) ... ok
test_pillars_need_three (tests.test_packs.GamePackTests) ... ok
test_reveal_to_someone_who_already_knows_warns (tests.test_packs.GamePackTests) ... ok
test_reveal_to_unknown_fact_or_actor_blocks (tests.test_packs.GamePackTests) ... ok
test_timeline_inversion_blocks (tests.test_packs.GamePackTests) ... ok
test_unestablished_reveal_blocks (tests.test_packs.GamePackTests) ... ok
test_unknown_actor_blocks (tests.test_packs.GamePackTests) ... ok
test_valid_world_passes (tests.test_packs.GamePackTests) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.131s

OK

```

```
$ python -m unittest tests.test_review2.GamePackDetectionTests -v   # exit 0
test_comments_in_frontmatter_are_stripped (tests.test_review2.GamePackDetectionTests) ... ok
test_nested_quest_directory_is_scanned (tests.test_review2.GamePackDetectionTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.017s

OK

```

measured
