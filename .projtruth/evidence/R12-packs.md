# R12 packs extend the stages for non-software work

_Run at 2026-11-13 23:38:30_

```
$ python -m unittest tests.test_packs.StoryPackTests -v   # exit 0
test_detected_by_outline_not_an_empty_directory (tests.test_packs.StoryPackTests) ... ok
test_discovery_needs_an_outline (tests.test_packs.StoryPackTests) ... ok
test_discovery_warns_without_threads (tests.test_packs.StoryPackTests) ... ok
test_duplicate_order_blocks (tests.test_packs.StoryPackTests) ... ok
test_reveal_to_a_character_who_already_knows_warns (tests.test_packs.StoryPackTests) ... ok
test_undeclared_pov_blocks (tests.test_packs.StoryPackTests) ... ok
test_unknown_thread_blocks_and_open_thread_warns (tests.test_packs.StoryPackTests) ... ok
test_valid_story_passes (tests.test_packs.StoryPackTests) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.098s

OK

```

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
Ran 13 tests in 0.122s

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
story  Long-form story    stages 0,2    active
```

```
$ two chapters both with order 10, then python -m lifecycle status   # exit 0
- story:characters:list: no characters declared
- story:order-dup: two chapters share order 10: ch-one and ch-two
```

measured
