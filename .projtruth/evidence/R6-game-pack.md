# R6 the game pack checks world consistency

_Run at 2026-11-15 18:46:10_

```
$ python -m unittest tests.test_packs.GamePackTests -v   # exit 0
test_cycle_blocks (tests.test_packs.GamePackTests) ... ok
test_duplicate_quest_id_blocks (tests.test_packs.GamePackTests) ... ok
test_empty_artifact_directory_does_not_opt_in (tests.test_packs.GamePackTests) ... ok
test_knowledge_accumulates_across_quests (tests.test_packs.GamePackTests) ... ok
test_knows_naming_undeclared_things_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_bible_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_order_warns_not_blocks (tests.test_packs.GamePackTests) ... ok
test_missing_prerequisite_blocks (tests.test_packs.GamePackTests) ... ok
test_pack_detected_by_artifacts_not_an_empty_directory (tests.test_packs.GamePackTests) ... ok
test_pillars_need_three (tests.test_packs.GamePackTests) ... ok
test_quest_without_an_act_warns (tests.test_packs.GamePackTests) ... ok
test_repo_path_with_glob_characters_is_still_scanned (tests.test_packs.GamePackTests) ... ok
test_reveal_to_someone_who_already_knows_warns (tests.test_packs.GamePackTests) ... ok
test_reveal_to_unknown_fact_or_actor_blocks (tests.test_packs.GamePackTests) ... ok
test_timeline_inversion_blocks (tests.test_packs.GamePackTests) ... ok
test_underscore_prefixed_real_file_is_data (tests.test_packs.GamePackTests) ... ok
test_unestablished_reveal_blocks (tests.test_packs.GamePackTests) ... ok
test_unknown_actor_blocks (tests.test_packs.GamePackTests) ... ok
test_valid_world_passes (tests.test_packs.GamePackTests) ... ok

----------------------------------------------------------------------
Ran 19 tests in 0.237s

OK

```

```
$ python -m unittest tests.test_review2.GamePackDetectionTests -v   # exit 0
test_comments_in_frontmatter_are_stripped (tests.test_review2.GamePackDetectionTests) ... ok
test_nested_quest_directory_is_scanned (tests.test_review2.GamePackDetectionTests) ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.021s

OK

```

measured
