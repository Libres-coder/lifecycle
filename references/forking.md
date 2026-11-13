# Forking the contract

The six stages are a default, not a law. A game, a library and a hosted service
do not need identical artifacts. Change the contract in one file:
`lifecycle/contract.py`.

## Add a stage

1. Write `check_<name>(repo)` returning a list of results built with `ok()`,
   `fail()` or `skip()`.
2. Append `{"id": N, "key": ..., "title": ..., "question": ..., "checks": [...]}`
   to `STAGES`. Ids must stay contiguous - `check --stage N` uses them.
3. A check that reads another tool must degrade to `skip()` when that tool is
   absent, never to `fail()`: a missing tool is not a missing product.

## Change what a stage requires

Edit the existing check. Two rules keep the gate trustworthy:

- **Checkable from the repository.** If a human cannot verify it by looking at
  files, it is a checklist item, not a gate.
- **Never fail a healthy repository.** A check that fires on projects that are
  fine will be disabled, and then the whole contract is disabled with it.

## Examples that fit a game

| stage | artifact worth requiring |
|---|---|
| discovery | `docs/game/pillars.md` - the three experiences the game sells |
| design | `docs/game/world-bible.md` + a quest graph with prerequisites |
| build | a playable build path, not just source files |
| verify | a playtest note per milestone, with what the player actually did |
| release | store page copy + build hash + known-issues list |

These are deliberately not in the default contract: a library would fail all of
them, and a contract that fails everything teaches people to ignore contracts.
