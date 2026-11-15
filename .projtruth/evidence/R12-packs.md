# R12 packs extend the stages for non-software work

_Run at 2026-11-15 18:43:11_

```
$ python -m unittest tests.test_packs.StoryPackTests -v   # exit 0
test_a_character_seen_once_in_a_long_story_warns (tests.test_packs.StoryPackTests) ... ok
test_a_faction_tie_to_an_undeclared_faction_blocks (tests.test_packs.StoryPackTests) ... ok
test_a_major_character_who_never_appears_warns (tests.test_packs.StoryPackTests) ... ok
test_a_repeated_want_is_a_template_not_a_scene (tests.test_packs.StoryPackTests) ... ok
test_act_density_is_checked_when_chapters_declare_acts (tests.test_packs.StoryPackTests) ... ok
test_antagonist_needs_a_plan_and_a_constraint (tests.test_packs.StoryPackTests) ... ok
test_auto_detection_keeps_source_and_tests (tests.test_packs.StoryPackTests) ... ok
test_auto_detection_never_removes_a_generic_gate (tests.test_packs.StoryPackTests)
A narrative folder in a software repo must not drop architecture. ... ok
test_auto_detection_runs_every_detected_pack (tests.test_packs.StoryPackTests)
A game with a written narrative is both kinds; auto runs both. ... ok
test_chapter_cast_must_be_declared (tests.test_packs.StoryPackTests) ... ok
test_craft_flags_a_character_without_a_want (tests.test_packs.StoryPackTests) ... ok
test_craft_flags_a_quest_without_stakes (tests.test_packs.StoryPackTests) ... ok
test_craft_flags_a_summary_chapter (tests.test_packs.StoryPackTests) ... ok
test_detected_by_outline_not_an_empty_directory (tests.test_packs.StoryPackTests) ... ok
test_discovery_needs_an_outline (tests.test_packs.StoryPackTests) ... ok
test_discovery_warns_without_a_premise_or_theme (tests.test_packs.StoryPackTests) ... ok
test_discovery_warns_without_threads (tests.test_packs.StoryPackTests) ... ok
test_duplicate_order_blocks (tests.test_packs.StoryPackTests) ... ok
test_explicit_story_pack_replaces_the_software_build_checks (tests.test_packs.StoryPackTests) ... ok
test_factions_need_interests_and_ties (tests.test_packs.StoryPackTests) ... ok
test_inciting_chapter_must_exist (tests.test_packs.StoryPackTests) ... ok
test_main_thread_must_be_a_declared_thread (tests.test_packs.StoryPackTests) ... ok
test_relations_must_name_the_cast (tests.test_packs.StoryPackTests) ... ok
test_reveal_to_a_character_who_already_knows_warns (tests.test_packs.StoryPackTests) ... ok
test_scaffold_teaches_the_story_heart (tests.test_packs.StoryPackTests) ... ok
test_story_build_needs_a_draft_and_counts_it (tests.test_packs.StoryPackTests) ... ok
test_story_pack_replaces_the_generic_design_artifacts (tests.test_packs.StoryPackTests) ... ok
test_story_packs_wiring_runs_both_checks (tests.test_packs.StoryPackTests) ... ok
test_thread_resolved_before_its_last_advance_warns (tests.test_packs.StoryPackTests) ... ok
test_undeclared_pov_blocks (tests.test_packs.StoryPackTests) ... ok
test_unknown_thread_blocks_and_open_thread_warns (tests.test_packs.StoryPackTests) ... ok
test_valid_story_passes (tests.test_packs.StoryPackTests) ... ok
test_with_adds_checks_without_replacing_the_gate (tests.test_packs.StoryPackTests) ... ok
test_word_count_counts_kana_and_hangul (tests.test_packs.StoryPackTests) ... ok

----------------------------------------------------------------------
Ran 34 tests in 3.562s

OK

```

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
Ran 19 tests in 0.258s

OK

```

```
$ python -m lifecycle pack init story   # exit 0
created docs/story/outline.md
created docs/story/characters.md
created docs/story/chapters/_template.md

Next: fill the TODOs, then `lifecycle check`. The checks read these files; they do not read intention.
```

```
$ python -m lifecycle pack list   # exit 0
game   Open-world game    stages 0,2    
story  Long-form story    stages 0,2,3  active
```

```
$ two chapters both with order 10, then python -m lifecycle status   # exit 0
- story:characters:list: no characters declared
- story:order-dup: two chapters share order 10: ch-one and ch-two
```

measured
