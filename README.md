# lifecycle

**A product is not "almost done". It is at a stage, and each stage has artifacts a stranger can check.**

`lifecycle` reads a repository and says which stages it passes, what blocks the
next one, and the one command that unblocks it. Real output on one of my own
projects:

```
$ lifecycle --repo ../projtruth status
# lifecycle (.../projtruth)
4/7 stages pass

| # | stage | state | what the stage asks |
|---|---|---|---|
| 0 | Discovery | **FAIL** | no product vision document |
| 1 | Spec | **PASS** | What exactly is promised, in a way a stranger can check? |
| 2 | Design | **FAIL** | no architecture document |
| 3 | Build | **PASS** | Does the code and its tests exist? |
| 4 | Verify | **PASS** | Is every promise backed by evidence that still holds? |
| 5 | Release | **PASS** | Is there a version, a changelog and a tag? |
| 6 | Sustain | **FAIL** | no docs/work/current.md |

## Next
Stage 0 Discovery: **vision** - no product vision document

    write docs/product/vision.md with Problem, Audience and Non-goals
```

That report is correct: projtruth has requirements, code, tests, evidence and a
release, but no vision document and no architecture doc.

## What it covers

| what a long task needs | how lifecycle answers it |
|---|---|
| where am I | seven stages computed from artifacts, not from a meeting |
| what is next | the first blocking item with the command that fixes it |
| what does "good" look like here | `lifecycle guide <stage>`: questions, shallow examples, tools |
| how far along | `docs/work/plan.md` milestones and checkbox counts |
| what happened last session | `docs/work/log/` and `lifecycle resume` |
| survive a context reset | PreCompact snapshot + SessionStart resume, installed as hooks |
| periodic summary | `lifecycle report` drafts it; three sections stay yours |
| is anyone looking critically | `docs/reviews/` note, checked for age and findings |
| is it getting too big to load | context budget for the always-loaded documents |

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
| 6 Sustain | a work thread, a journal entry, a status report, a context budget | `docs/work/`, `docs/reports/` |

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
| `lifecycle guide [stage]` | the playbook: questions to answer, what shallow looks like |
| `lifecycle init` | scaffold the work thread, plan, log/report/review directories |
| `lifecycle resume` | after a compaction or in a new session: the work thread, plan progress, journal, next blocker |
| `lifecycle report` | drafts `docs/reports/status-<date>.md` from facts it can check |
| `lifecycle snapshot` | writes the state a compaction would lose |
| `lifecycle hook install` | wires PreCompact + SessionStart into the project's `.claude/settings.json` |

## Automatic, not remembered

Skills are model-invoked: an agent under load does the task instead of choosing
a tool, which is why installed skills can go unused for weeks. Anything that
must happen every time belongs in a hook:

```bash
lifecycle hook install
```

- **PreCompact** → `lifecycle snapshot`: writes the stage state, the working
  tree, the last commits, the head of the work thread, and the transcript size
  (the only window into context size a subprocess gets).
- **SessionStart (compact|resume)** → `lifecycle resume`: the work thread, the
  last journal entries and the blocking item are the first thing in the new
  context.

Installed into the project's `.claude/settings.json`, uninstalled by the same
command, and it refuses to touch a settings file it cannot parse.

## Quality, as far as it is checkable

- `docs/reviews/*.md` - an adversarial review note; stage 6 reports it missing,
  stale, or with no findings (a first review that found nothing did not look).
- Evidence tiers: a stage where no evidence is `measured` is reported.
- `lifecycle guide` prints what a shallow stage looks like, which is the part a
  checker cannot decide.

## Long-running work

A task that outlives one context window needs three artifacts, and they are the
only ones a fresh session can read:

| file | what it holds |
|---|---|
| `docs/work/current.md` | Goal / Done / Next / Blockers - the handoff; the sections and a concrete Next are checked |
| `docs/work/plan.md` | milestones with `- [ ]` tasks - how far along the work is |
| `docs/work/log/<date>.md` | one entry per working session: what you tried, what happened |
| `docs/reports/status-<date>.md` | a periodic summary; `lifecycle report` drafts it, you fill in what went well and what did not |

Stage 6 makes these conditions: after the first release a missing or stale work
thread fails the stage, and an old journal or report is reported. Before the
first release they are warnings - a thread is good practice, not a promise you
have made to a user.

`lifecycle resume` is the command to run after a compaction or at the start of a
new session: it prints the thread, the last journal entries and the one blocking
item. What it cannot do is see your actual context window - the budget check
measures the documents the repository loads (CLAUDE.md, README, vision,
architecture, `current.md`), which is a proxy.

## What it can and cannot make an agent do

lifecycle **cannot invoke a skill, a plugin or a slash command**. It names the
right tool for the stage (`lifecycle guide <stage>`, `lifecycle suggest`) and
the agent decides whether to use it; `/compact` and `/clear` are the user's
keystrokes, not a tool call.

That is deliberate, and it is why the hooks exist: anything that must happen
every time - recording state before a compaction, restoring the thread after one
- is a hook, and anything that needs judgement is a name in front of whoever
reads it. A tool that pretends to drive other tools is the one that silently
does nothing.

## More than one line of work

```bash
lifecycle thread new game-main --title "Main quest"
lifecycle thread claim game-main --as aria
lifecycle thread list
```

Each thread is a directory with its own `current.md`, `plan.md` and `owner`;
`status` shows the portfolio (owner, plan progress, next item, handoff current
or STALE) and `resume --thread` opens one. The flat `docs/work/current.md` stays
the portfolio for the effort as a whole.

## Deep work, not just presence

Presence is cheap to fake. `lifecycle guide` prints the questions that separate a
real stage from a filled-in template - the purpose of the stage, what you must
answer before producing anything, what to write, **what shallow looks like**, and
what done means.

```bash
lifecycle guide            # the stage that is blocking right now
lifecycle guide design
```

Some checks are **advisory** and never fail a stage: a vision under 100 words,
fewer than two non-goals, criteria too vague to test, a decision recorded without
a reason, an architecture that never mentions a trade-off or a failure, evidence
marked `guessed`. They are reported with the sentence that says what a shallow
version looks like, because taste is not a gate.

## Game pack

An open-world game's design is not an architecture document. When `docs/game/`
exists, a pack adds checks to stages 0 and 2: pillars, a world bible with
characters/factions/locations/facts, and quest files with
`id`/`requires`/`reveals`.

Real output on a game-shaped demo repository (the missing prerequisite is
deliberate):

```
$ lifecycle --repo ../game-demo status
0/6 stages pass  ·  pack: game

| 0 | Discovery | **WARN** | Why does this exist, and what will it not do? |
| 1 | Spec      | **FAIL** | no requirement registry |
| 2 | Design    | **FAIL** | no architecture document |
| 3 | Build     | **FAIL** | no source files found |
| 4 | Verify    | **WARN** | no requirements registered - nothing to verify |
| 5 | Release   | **FAIL** | no CHANGELOG |

## Blocked
**Stage 2 Design**
- architecture: no architecture document
- decisions: no recorded decision
- game:requires: quest(s) require a quest that does not exist: q-keep -> q-missing
  - fix the id or add the missing quest file
```

The checks are the ones a wiki cannot do: a prerequisite loop, a reveal of a fact
the bible never establishes, an actor used but never declared.
`lifecycle guide game` prints the full playbook.

## Design notes

- **No gate state.** A stage passes because the repository says so right now -
  there is no "passed" record to go stale. The thread files (`docs/work/`,
  `docs/reports/`, `docs/reviews/`) are yours; `init` creates them empty and
  `report` drafts one.
- **It cannot fake a pass.** `init` scaffolds empty files and `report` drafts a
  summary, but no command fills in a vision, a test or an evidence file.
- **Composes instead of replacing.** projtruth and corpus are called through
  their JSON output; either can be missing.
- **Opinionated and forkable.** Six generic stages cover a product. A game or a
  library needs different artifacts - change `lifecycle/contract.py`, see
  [references/forking.md](references/forking.md).

## Context: what this tool can and cannot see

A hook never receives the live context percentage, and no hook can trigger a
compaction - Claude Code decides that itself. What is available:

- **statusline**: its payload carries `context_window.used_percentage`. Install
  it with `lifecycle hook install` (it adds `statusLine` only when you do not
  already have one); `lifecycle statusline` records the payload to
  `.lifecycle/context.json` and renders `74% ctx` - or `74% ctx - /compact` once
  the reading is within five points of the trigger.
- **SessionStart on resume/compact**: carries `context_tokens`; `resume --hook`
  records it, so the work thread knows how full the window was.
- **PreCompact**: carries the transcript path; `snapshot` records its size.

`status` and `resume` print `context: N% used` when a recent reading exists.

Why the UI can sit at 74% without compacting: the displayed percentage is not
the quantity compaction compares against. Auto-compact fires near the model's
window minus a summary buffer, and `CLAUDE_CODE_AUTO_COMPACT_WINDOW` (or
`autoCompactWindow`) can lower the window so the two numbers diverge further.
To compact earlier, lower the trigger explicitly:

```bash
export CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=70     # 1-100, can only lower the default
```

`/compact` compacts now; `autoCompactEnabled` (or `/config`) turns auto-compact
off, and `DISABLE_COMPACT=1` turns off both.

lifecycle reads that override and moves its advice with it: with the trigger at
70, the nudge comes at 55% and "run /compact now" at 65%. Advising a compaction
at 85 when the harness compacts at 70 would be advice about the past.

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
