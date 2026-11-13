# Architecture

Three layers, no state.

```
contract.py   stage definitions; each check reads the repo and returns results
thread.py     the handoff: current.md, plan, journal, reports, reviews, snapshots
threads.py    more than one line of work: per-thread handoff, plan, owner
depth.py      advisory checks for shallow artifacts
packs.py      domain checks (game) attached to existing stages
report.py     the stage table, the threads table, the blockers, the next action
cli.py        status / next / check / stages / resume / report / snapshot / hook
```

A check returns `{name, ok, detail, fix, required}`. A stage passes when no
required check fails. Nothing is written to disk, so there is no gate record to
go stale: re-running after an edit recomputes the answer.

Sibling tools (projtruth, corpus) are invoked as subprocesses with `--json`,
only when they are installed: the scanned repository is never put on
`PYTHONPATH`, so auditing a repository cannot execute its code. When a tool is
absent the check is advisory, not a failure.

## Trade-offs

- **Recompute over store.** Slower, but a stored pass is a claim that can drift
  from reality.
- **Opinionated stages over configurable ones.** Six generic stages cover a
  product; a project that needs different gates forks the contract.
- **It cannot manufacture a pass.** `init` writes empty templates and `report`
  drafts a summary; nothing fills in a vision, a test or an evidence file.
