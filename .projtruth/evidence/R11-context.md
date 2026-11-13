# R11 context usage is recorded when the harness exposes it

_Run at 2026-11-13 21:30:17_

```
$ python -m unittest tests.test_statusline -v   # exit 0
test_resume_hook_is_silent_in_an_uninitialized_folder (tests.test_statusline.CliTests) ... ok
test_resume_hook_records_context_tokens (tests.test_statusline.CliTests) ... ok
test_statusline_command_records_and_prints (tests.test_statusline.CliTests) ... ok
test_bad_payloads_do_not_raise (tests.test_statusline.ParseTests) ... ok
test_extracts_context_fields (tests.test_statusline.ParseTests) ... ok
test_no_reading_means_no_line (tests.test_statusline.RecordTests) ... ok
test_old_reading_is_marked_stale (tests.test_statusline.RecordTests) ... ok
test_save_and_read_back (tests.test_statusline.RecordTests) ... ok
test_status_line_shows_thread_and_percent (tests.test_statusline.RenderTests) ... ok
test_status_line_without_anything (tests.test_statusline.RenderTests) ... ok

----------------------------------------------------------------------
Ran 10 tests in 1.345s

OK

```

```
$ printf '{"context_window":{"used_percentage":74}}' | python -m lifecycle statusline   # exit 0
recorded; status now prints: ['6/7 stages pass  ·  context: 74% used']
```

```
$ printf '{"source":"compact","context_tokens":42000}' | python -m lifecycle resume --hook   # exit 0
Lifecycle: stage 5 Release - no tag matches version 1.2.1 (tags: v0.1.0, v0.2.0, v0.2.1, v0.3.0, v0.4.0)
```

measured
