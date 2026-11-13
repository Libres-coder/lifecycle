---
name: lifecycle
description: >-
  Answers where a product actually is, stage by stage - discovery, spec,
  design, build, verify, release - by checking the repository instead of asking.
  Each stage declares what it must produce (a vision with problem/audience/
  non-goals, requirements with acceptance criteria, an architecture plus a
  recorded decision, source and tests, verified evidence, a changelog with a
  matching git tag) and every gap is printed with the exact command that closes
  it. Use at the start of a project, when asked what is left before shipping,
  whether this is release-ready, or what to do next; when a project has code but
  no spec, or a spec but no evidence; before a release (阶段, 还差什么, 能不能发,
  上线前检查, 下一步做什么, 产品走到哪一步了). Not for: evidence per requirement
  (projtruth), document sprawl (corpus), code structure (graphify), or prose
  style (writing-standards, tech-doc-style-chinese).
---

# lifecycle

A product is not "almost done". It is at a stage, and each stage has artifacts a
stranger can check. `lifecycle` computes which stages this repository passes,
what is blocking the next one, and the single command that unblocks it.

It stores nothing. A stage passes because the repo says so right now, not
because someone ran a command last week.

## Use it

```bash
$ lifecycle --repo . status
# lifecycle (/path/to/repo)
4/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **PASS** | Why does this exist, and what will it not do? |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **FAIL** | no release tag |

## Next
Stage 2 Design: **architecture** - no architecture document

    write docs/design/architecture.md: components, data flow, and the trade-off you chose
```

Commands:

| command | for |
|---|---|
| `lifecycle status [--json]` | the stage table and the next action |
| `lifecycle next` | one blocking item, with its fix |
| `lifecycle check [--stage N]` | CI gate: exit 1 on a failing stage |
| `lifecycle stages` | the contract: what each stage asks |

## The contract

| stage | must produce | checked by |
|---|---|---|
| 0 Discovery | `docs/product/vision.md` with Problem, Audience, Non-goals | headings |
| 1 Spec | `.projtruth/requirements.json`, every requirement with criteria | structure |
| 2 Design | an architecture doc + at least one recorded decision | file + `decisions.jsonl` |
| 3 Build | source files and test files | file scan |
| 4 Verify | every requirement `verified`; no incorrect document finding | `projtruth report --json`, `corpus report --json` |
| 5 Release | CHANGELOG entry for the version, a matching git tag | file + `git tag` |

Stage 4's two checks are **advisory** when the sibling tool is not installed:
the stage reports WARN, not FAIL, and names the install command. A missing tool
should not look like a missing product.

## What to do with a failing stage

1. Read the blocker - it names the artifact, not the process.
2. Run the printed command, or write the artifact.
3. Re-run `lifecycle status`. When the stage passes, move to the next one.

Do not work around a gate by deleting the requirement or the changelog entry.
If a check is wrong for this product, that is a conversation with the user, not
an edit to the registry.

## Limits, stated honestly

- The contract is opinionated and generic. A game, a library and a service do
  not need identical artifacts; fork the contract rather than pretending.
- It checks that artifacts exist and are structurally sound. It cannot tell
  whether the vision is good, the architecture is wise, or the tests are
  meaningful.
- Stage 4 trusts `projtruth` and `corpus`; if neither is installed it cannot
  see requirements at all.
- Version/tag matching is textual: `v0.2.0` matches `0.2.0`, and a tag created
  before the changelog edit still counts.

Forking the contract for a different kind of product - a game, a library, a
service: [references/forking.md](references/forking.md).
