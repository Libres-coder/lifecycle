# R11 context usage is recorded when the harness exposes it

_Run at 2026-11-13 23:38:27_

```
$ python -m unittest tests.test_statusline -v   # exit 0
test_numeric_strings_are_accepted (tests.test_statusline.BadStateTests) ... ok
test_wrong_type_does_not_crash_any_consumer (tests.test_statusline.BadStateTests) ... ok
test_resume_hook_does_not_keep_a_stale_percentage (tests.test_statusline.CliTests) ... ok
test_resume_hook_is_silent_in_an_uninitialized_folder (tests.test_statusline.CliTests) ... ok
test_resume_hook_is_silent_when_only_a_context_reading_exists (tests.test_statusline.CliTests) ... ok
test_resume_hook_records_context_tokens (tests.test_statusline.CliTests) ... ok
test_statusline_command_records_and_prints (tests.test_statusline.CliTests) ... ok
test_bad_payloads_do_not_raise (tests.test_statusline.ParseTests) ... ok
test_extracts_context_fields (tests.test_statusline.ParseTests) ... ok
test_no_reading_means_no_line (tests.test_statusline.RecordTests) ... ok
test_old_reading_is_marked_stale (tests.test_statusline.RecordTests) ... ok
test_save_and_read_back (tests.test_statusline.RecordTests) ... ok
test_status_line_shows_thread_and_percent (tests.test_statusline.RenderTests) ... ok
test_status_line_without_anything (tests.test_statusline.RenderTests) ... ok
test_a_healthy_reading_is_not_called_missing (tests.test_statusline.SuggestTests) ... ok
test_no_reading_is_reported_as_missing (tests.test_statusline.SuggestTests) ... ok
test_boundary_values_are_inclusive (tests.test_statusline.TriggerTests) ... ok
test_hint_follows_the_trigger (tests.test_statusline.TriggerTests) ... ok
test_override_lowers_the_trigger (tests.test_statusline.TriggerTests) ... ok
test_override_parsing (tests.test_statusline.TriggerTests) ... ok
test_status_line_asks_for_a_compaction_before_the_trigger (tests.test_statusline.TriggerTests) ... ok
test_unreadable_override_keeps_the_default (tests.test_statusline.TriggerTests) ... ok

----------------------------------------------------------------------
Ran 22 tests in 2.366s

OK

```

```
$ printf '{"context_window":{"used_percentage":74}}' | python -m lifecycle statusline   # exit 0
recorded; status now prints: []
```

```
$ printf '{"source":"compact","context_tokens":42000}' | python -m lifecycle resume --hook   # exit 0
Lifecycle: stage 4 Verify - 2 requirement(s) not verified: R11, R12
```

measured
