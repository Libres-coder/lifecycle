---
name: lifecycle
description: >-
  Keeps a long-running product effort organised - across stages and across
  sessions. Checks the repository for what each stage must produce (a vision
  with problem/audience/non-goals, requirements with acceptance criteria, an
  architecture plus a recorded decision, source and tests, verified evidence, a
  changelog with a matching tag) and for the work thread that survives a context
  reset (docs/work/current.md, a session journal, periodic status reports, a
  context budget). Every gap is printed with the command that closes it, and
  `guide` prints the questions that separate real work from a filled-in
  template. Use when asked where the project is, what is left before shipping,
  whether it is release-ready, what to do next, or to summarise progress (阶段,
  还差什么, 能不能发, 上线前检查, 下一步做什么, 长线, 跨会话, 上下文压缩,
  阶段汇报, 进度总结, 接着上次继续). Not for: evidence per requirement
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

Commands:

| command | for |
|---|---|
| `lifecycle status [--json]` | the stage table and the next action |
| `lifecycle next` | one blocking item, with its fix |
| `lifecycle check [--stage N]` | CI gate: exit 1 on a failing stage |
| `lifecycle stages` | the contract: what each stage asks |
| `lifecycle guide [stage]` | the playbook for a stage: questions to answer, what shallow looks like |
| `lifecycle resume` | after a compaction or in a new session: the work thread, recent journal, next blocker |
| `lifecycle report` | drafts `docs/reports/status-<date>.md` from facts it can check |

## Long-running work

A task that outlives one context window needs three artifacts, and they are the
only ones a fresh session can read:

- `docs/work/current.md` - Goal / Done / Next / Blockers. The handoff.
- `docs/work/log/<date>.md` - one entry per working session: what you tried, what
  happened, what surprised you.
- `docs/reports/status-<date>.md` - a periodic summary written by
  `lifecycle report`, with three sections left blank for you: what went well,
  what did not, what is next.

Stage 6 (Sustain) makes these conditions rather than habits: after the first
release, a missing or stale work thread fails the stage, and a journal entry or
report older than its window is reported. Before the first release they are
warnings - a thread is good practice, not a promise you have made to a user.

The cadence, in one line each:

- **before you stop a session** - update `current.md`, append a journal entry;
- **when a stage ends** - `lifecycle report`, then fill in the three sections;
- **when the context is compacted** - `lifecycle resume`;
- **every couple of weeks** - `corpus report --noise` and `corpus find` before
  writing anything new.

What it cannot do: see your actual context window. The context check measures
the documents the repository loads before work starts (CLAUDE.md, README, the
vision, the architecture, `current.md`); it is a proxy, and the real decision to
compact is still yours.

## Deep work, not just presence

Presence is cheap to fake. `lifecycle guide` prints the questions that separate a
real stage from a filled-in template - run it when you *start* a stage:

```bash
lifecycle guide            # the stage that is currently blocking
lifecycle guide design     # or a named one
```

Each playbook has the same shape: the purpose of the stage, the questions you
must answer before producing anything, what to write, what shallow looks like,
and what "done" means. Read the "shallow looks like" section first - it is the
one that catches you.

The `guide` is advice; the checks are the gate. They disagree on purpose: the
guide asks for thinking, the checks can only see artifacts.

## Advisory checks

Some checks are advisory (WARN): a vision under 100 words, fewer than two
non-goals, criteria too vague to test ("works"), a decision recorded without a
reason, architecture that never mentions a trade-off or a failure, evidence
marked `guessed`. They never fail a stage - taste is not a gate - but they are
printed with what a shallow version looks like.

## Game pack

An open-world game's design is not an architecture document. With
`docs/game/` present, a pack adds checks to stages 0 and 2:

- `docs/game/pillars.md` - three pillars;
- `docs/game/world-bible.md` - frontmatter lists of characters, factions,
  locations and facts;
- `docs/game/quests/<id>.md` - frontmatter `id`, `requires`, `reveals`,
  `characters`, `factions`.

The checks are the ones a wiki cannot do: a quest requiring a quest that does
not exist, a prerequisite loop, a reveal of a fact the bible never establishes,
an actor used but never declared. `lifecycle guide game` prints the full
playbook.

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
