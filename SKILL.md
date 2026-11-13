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

No gate state is stored: a stage passes because the repo says so right now, not
because someone ran a command last week. The thread files under `docs/work/` are
the project's, and `init` creates them empty.

## Use it

```bash
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

Commands:

| command | for |
|---|---|
| `lifecycle status [--json]` | the stage table and the next action |
| `lifecycle next` | one blocking item, with its fix |
| `lifecycle check [--stage N]` | CI gate: exit 1 on a failing stage |
| `lifecycle stages` | the contract: what each stage asks |
| `lifecycle guide [stage]` | the playbook for a stage: questions to answer, what shallow looks like |
| `lifecycle pack list\|init\|guide <name>` | domain packs: game, story - checks, playbook, scaffold |
| `lifecycle init` | scaffold the work thread, plan, log/report/review directories |
| `lifecycle resume` | after a compaction or in a new session: the work thread, plan progress, journal, next blocker |
| `lifecycle report` | drafts `docs/reports/status-<date>.md` from facts it can check |
| `lifecycle snapshot` | writes the state a compaction would lose (run by a hook) |
| `lifecycle hook install` | wires PreCompact + SessionStart into `.claude/settings.json` |

## Make it automatic, not remembered

An agent does not reliably choose a skill. Descriptions compete with the task in
front of it, and "I will remember to update the thread" is not a mechanism. Two
hooks are:

```bash
lifecycle hook install     # writes .claude/settings.json for this project
lifecycle hook status
```

- **PreCompact** runs `lifecycle snapshot` before the context is compacted, so
  the state is written while it still exists (it also records the transcript
  size, the only window this tool has into the context it cannot see).
- **SessionStart (compact|resume)** runs `lifecycle resume`, so the first thing
  in a fresh context is the work thread, the last journal entries and the one
  blocking item.

The hooks live in the project's `.claude/settings.json`, not the global file:
they belong to the project that has a thread, and they do not collide with
whatever manages the global config. `lifecycle hook uninstall` removes only the
entries it added. `hook install` upgrades entries written by older versions and
leaves a `statusLine` it did not write alone, saying so rather than reporting a
success that would never record a reading.

## More than one line of work

A project with two workstreams - the game and its tooling, a feature and a
migration - gets one thread per stream instead of one handoff trying to hold
both:

```bash
lifecycle thread new game-main --title "Main quest"
lifecycle thread claim game-main --as aria
lifecycle thread list
lifecycle resume --thread game-main
```

`docs/work/threads/<slug>/` holds that thread's `current.md`, `plan.md` and
`owner`. `lifecycle status` prints a portfolio table: owner, plan progress, next
item, and whether the handoff is still current. The flat `docs/work/current.md`
stays the portfolio - what the effort as a whole is doing now.

The checks report two things a team hits first: one owner whose claim is older
than a day (the thread looks busy but is not), and one owner on several threads
(nobody keeps two handoffs current). Both are warnings; a thread is not a gate.

If a user asks why a skill never fires, this is the honest answer: skills are
model-invoked, and a model under load does the task instead of choosing a tool.
Anything that must happen every time belongs in a hook or a gate, not in a
description.

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

## Long-running work

A task that outlives one context window needs three artifacts, and they are the
only ones a fresh session can read:

- `docs/work/current.md` - Goal / Done / Next / Blockers. The handoff. Stage 6
  checks the sections exist and that Next has a concrete item.
- `docs/work/plan.md` - milestones (`## M1 ...`) with `- [ ]` tasks. It is what
  makes "how far along" visible; a plan with no tasks or with every box ticked
  is reported.
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
  writing anything new;
- **every few compactions** - `lifecycle report`; three snapshots since the last
  report is reported as working from memory.

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
marked `guessed`, a verified requirement whose evidence is untiered or guessed.
They never fail a stage - taste is not a gate - but they are printed with what
a shallow version looks like.

## Packs: work that is not software

A product's stages are generic; the work inside them is not. A pack adds
domain checks to stages 0 and 2, a playbook for that kind of work, and a
scaffold for its artifacts:

```bash
lifecycle pack list          # what is available, and which one is active
lifecycle pack init game     # write the empty structure (never content)
lifecycle pack guide story   # the playbook for that kind of work
```

Packs are opt-in by presence, and the first match wins (`--pack story` says
which one the checks follow). **Kinds of work are peers**: the generic
seven-stage checks are the software default, not a universal law. A pack
declares its own artifacts for any stage it differs in - the story pack stands
in for the architecture and decision checks at stage 2 and for the source/test
checks at stage 3, because a novel's design is its outline, cast and chapters
and its build artifact is the draft. **Each pack is a complete tool**:
structure checks, a craft standard (what an excellent deliverable in that
domain looks like, and what weak work looks like), advisory checks that make
the empty case visible, and a scaffold that teaches the fields by existing.
Any replacement applies **only when the pack is chosen explicitly**
(`--pack story`); auto-detection adds checks but never removes another type's
gate, so a narrative folder inside a software repository cannot weaken its own
design stage.

**game** (`docs/game/`) - pillars, a world bible with characters/factions/
locations/facts, and quest files with `id`, `act`, `order`, `requires`,
`reveals`, `reveals_to`, `characters`, `factions`. The checks are the ones a
wiki cannot do: a quest requiring a quest that does not exist, a quest that
requires one the timeline puts later, a prerequisite loop, a reveal of a fact
the bible never establishes, a reveal to a character who already knows it.

**story** (`docs/story/`) - an outline with acts and the plot threads the
reader is promised, a cast file with starting knowledge, and chapters with
`order`, `pov`, `reveals`, `threads`, `resolves`. The checks catch a chapter
out of order, a POV who is not in the cast, a thread used but never declared,
a thread nobody resolves, and a reveal to someone who already knows.

Both are narrative structure that has to stay consistent while scenes are
written out of order - which is why the checks are graph checks, not
spell-check. `lifecycle guide <pack>` prints the full playbook; the shared
`pack init` templates are named `_template.md` and are never read as data.

The playbook is also the **craft standard**: for story, a scene happens to a
body in a place, conflict is the engine, difficult material is written with
weight instead of avoided, stakes are personal and specific, characters are
wants meeting obstacles. For game, a quest is a verb with a cost, choices take
something away, and the world remembers. Advisory checks read the declared
shadow of that standard - a chapter without `want`/`obstacle`/`turn` or under
200 words, a quest without `stakes` - and never fail a stage.

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

## Quality, as far as it is checkable

The checks can see that a review happened, not whether it was good:

- `docs/reviews/*.md` - an adversarial review note. Stage 6 reports one that is
  missing, older than 30 days, or that has no findings at all: a review that
  found nothing on a first pass did not look.
- Evidence tiers (`measured` / `inferred` / `guessed`) say how each proof was
  obtained; a stage where nothing is `measured` is reported.
- `lifecycle guide <stage>` prints what a shallow version of the stage looks
  like - the judgement the checker cannot make.

## Context: what this tool can and cannot see

A hook never receives the live context percentage, and no hook can trigger a
compaction - Claude Code decides that itself. What is available:

- **statusline**: its payload carries `context_window.used_percentage`. Install
  it with `lifecycle hook install` (it adds `statusLine` only when you do not
  already have one); `lifecycle statusline` records the payload to
  `.lifecycle/context.json` and renders `74% ctx` - or `74% ctx - /compact` once
  the reading is within five points of the trigger.
- **SessionStart on resume/fork**: carries `context_tokens`; `resume --hook`
  records it and clears the previous percentage, which described a window this
  session no longer has. On `compact` the harness sends no token count, so the
  hook records nothing and the old reading stays honestly stale.
- **PreCompact**: carries the transcript path; `snapshot` records its size.

`status` and `resume` print `context: N% used` when a recent reading exists. A
reading belongs to the repository, not to a window: two sessions on one repo
overwrite each other's number, and only the stale label separates them.

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
