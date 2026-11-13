# R9 hooks make the thread automatic

_Run at 2026-11-13 21:49:43_

```
$ python -m unittest tests.test_hooks -v   # exit 0
test_install_is_idempotent (tests.test_hooks.HookTests) ... ok
test_install_preserves_existing_settings (tests.test_hooks.HookTests) ... ok
test_refuses_to_touch_broken_json (tests.test_hooks.HookTests) ... ok
test_uninstall_removes_only_ours (tests.test_hooks.HookTests) ... ok
test_fresh_review_with_findings_passes (tests.test_hooks.ReviewNoteTests) ... ok
test_missing_review_warns (tests.test_hooks.ReviewNoteTests) ... ok
test_old_review_warns (tests.test_hooks.ReviewNoteTests) ... ok
test_review_without_findings_warns (tests.test_hooks.ReviewNoteTests) ... ok
test_snapshot_records_transcript_size (tests.test_hooks.SnapshotTests) ... ok
test_snapshot_writes_and_prunes (tests.test_hooks.SnapshotTests) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.798s

OK

```

```
$ python -m lifecycle hook status   # exit 0
PreCompact: on, SessionStart: on, statusLine: on (.claude\settings.json)
```

```
$ printf '{"trigger":"manual"}' | python -m lifecycle snapshot   # exit 0
wrote .lifecycle/snapshots/2026-11-13T214942.md
```

measured
