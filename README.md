# lifecycle

**A product is not "almost done". It is at a stage, and each stage has artifacts a stranger can check.**

`lifecycle` reads a repository and says which stages it passes, what blocks the
next one, and the one command that unblocks it. Real output on one of my own
projects:

```
$ lifecycle --repo ../projtruth status
# lifecycle (.../projtruth)
4/6 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |

## Next
Stage 0 Discovery: **vision** - no product vision document

    write docs/product/vision.md with Problem, Audience and Non-goals
```

That report is correct: projtruth has requirements, code, tests, evidence and a
release, but no vision document and no architecture doc.

## Why

An agent declares a product done because the code compiles. The missing pieces -
vision, acceptance criteria, design decisions, evidence, release notes - are
each somebody's job, and nothing says which of them exist. Status meetings ask;
this reads the repository.

Existing options either replace your workflow with a fixed 33-stage framework
(AI-DLC) or are prototypes that validate document shape rather than repository
state (sdlc-mcp). This one is small, stateless, and reads whatever you already
use.

## The contract

| stage | must produce | checked by |
|---|---|---|
| 0 Discovery | `docs/product/vision.md` with Problem, Audience, Non-goals | headings |
| 1 Spec | `.projtruth/requirements.json`, every requirement with criteria | structure |
| 2 Design | an architecture doc + at least one recorded decision | file + `decisions.jsonl` |
| 3 Build | source files and test files | file scan |
| 4 Verify | every requirement `verified`; no incorrect document finding | `projtruth report --json`, `corpus report --json` |
| 5 Release | CHANGELOG entry for the version, a matching git tag | file + `git tag` |

When projtruth or corpus is not installed, stage 4 reports **WARN** with the
install command instead of FAIL. A missing tool is not a missing product.

## Install

Standard library only, Python 3.8+.

```bash
pip install git+https://github.com/Libres-coder/lifecycle
```

As a Claude Code skill:

```bash
git clone https://github.com/Libres-coder/lifecycle ~/.claude/skills/lifecycle
pip install ~/.claude/skills/lifecycle     # or PYTHONPATH=~/.claude/skills/lifecycle
```

## Commands

| command | for |
|---|---|
| `lifecycle status [--json]` | the stage table and the next action |
| `lifecycle next` | one blocking item, with its fix |
| `lifecycle check [--stage N]` | CI gate: exit 1 on a failing stage |
| `lifecycle stages` | the contract: what each stage asks |

## Design notes

- **No stored state.** A stage passes because the repository says so right now.
  A pass record that can go stale is a gate people stop trusting.
- **Read-only.** It never creates the artifacts it asks for, so it cannot
  manufacture a pass.
- **Composes instead of replacing.** projtruth and corpus are called through
  their JSON output; either can be missing.
- **Opinionated and forkable.** Six generic stages cover a product. A game or a
  library needs different artifacts - change `lifecycle/contract.py`, see
  [references/forking.md](references/forking.md).

## What it does not do

- It does not judge quality: a vision can exist and be bad.
- It does not run tests, verify requirements, or read documents - it asks
  projtruth and corpus, when they are there.
- It does not enforce anything by itself: add `lifecycle check` to CI.
- Version/tag matching is textual; `v0.2.0` matches `0.2.0`.

## Related

- [projtruth](https://github.com/Libres-coder/projtruth) - requirements and evidence.
- [corpus](https://github.com/Libres-coder/corpus) - document sprawl, duplicates, stale docs.
- [verify-first](https://github.com/Libres-coder/verify-first) - the pipeline that produces the evidence.

## License

MIT
