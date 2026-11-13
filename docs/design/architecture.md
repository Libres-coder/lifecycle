# Architecture

Three layers, no state.

```
contract.py   stage definitions; each check reads the repo and returns results
report.py     the stage table, the blockers, the one next action
cli.py        status / next / check / stages
```

A check returns `{name, ok, detail, fix, required}`. A stage passes when no
required check fails. Nothing is written to disk, so there is no gate record to
go stale: re-running after an edit recomputes the answer.

Sibling tools (projtruth, corpus) are invoked as subprocesses with `--json` and
`PYTHONPATH` set to the scanned repo, so a checkout works as well as an
installed package. When they are absent the check is advisory, not a failure.

## Trade-offs

- **Recompute over store.** Slower, but a stored pass is a claim that can drift
  from reality.
- **Opinionated stages over configurable ones.** Six generic stages cover a
  product; a project that needs different gates forks the contract.
- **Read-only.** It never creates the artifacts it asks for, so it cannot
  manufacture a pass.
