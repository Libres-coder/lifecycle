"""lifecycle playbooks: what deep work at each stage actually looks like.

The checker can see that a document exists. It cannot see whether the thinking
behind it happened. These are the questions that separate the two, written to be
read *at the start of a stage*, not after.

`lifecycle guide` prints them. They are embedded rather than shipped as package
data so an installed CLI and a copied skill directory behave identically.
"""

DISCOVERY = """# Stage 0 - Discovery

Decide whether to build this at all, and what "worth it" means. Everything
later is downstream of this; a wrong answer here is expensive to unwind.

## Answer these before writing anything

1. **Who has the problem, concretely?** A person at a company, or a workflow you
   run yourself. Not "developers". If you cannot name the moment it hurts, stop.
2. **What do they do today instead?** A spreadsheet, a shell script, nothing.
   The alternative is your real competitor.
3. **What does it cost them?** One number: hours per week, dollars, failed
   audits. If you cannot estimate it, that is the research task.
4. **What is the smallest thing that would help?** Not the product - the first
   version someone would switch to.
5. **What will this NOT do?** Three things, written down. Scope you refuse is
   design; scope you forget is debt.
6. **How will you know it worked?** One metric and where the number comes from.
   "Users" is not a metric.
7. **What must be true for this to work?** List the assumptions, and for each,
   the cheapest way to test it this week.

## Write

- `docs/product/vision.md` - Problem, Audience, Non-goals, Success metric.
- `docs/product/research.md` - what you read or observed, with links. Every
  claim about users or alternatives needs a source or a dated observation.

## Shallow looks like

"An app that helps developers be productive, for developers, success = users."
That sentence fits every product ever built and therefore decides nothing.

## Exit

`lifecycle check --stage 0` passes, and a stranger can restate the problem
without adding information you did not give them.
"""

SPEC = """# Stage 1 - Spec

Turn the decision into promises that a stranger can check, so "done" stops being
an opinion.

## Answer these

1. For each promise: **what does the user do, and what do they observe?** The
   observable part is the acceptance criterion.
2. **What is the failure behaviour?** Bad input, empty state, timeout, offline.
   A spec without failure cases is half a spec.
3. **Which promise is v1?** Cut until the cut hurts; a smaller v1 that ships
   teaches more than a complete v1 that does not.
4. **What would make this criterion wrong?** If "works" could be argued about in
   a review, it is not a criterion.

## Write

- `.projtruth/requirements.json` - one requirement per promise, each with
  criteria of the form *action -> observable result*.
- Optional `spec.md` for the narrative the registry cannot hold: users, flows,
  and the reasoning behind the cut.

## Shallow looks like

- criteria "works", "is fast", "handles errors";
- one requirement per screen instead of per promise;
- no failure case anywhere.

## Exit

`lifecycle check --stage 1` passes, every criterion is pass/fail without a
debate, and the failure behaviour of each requirement is written down.
"""

DESIGN = """# Stage 2 - Design

Choose a shape and record why, so the next session does not re-litigate a
settled question.

## Answer these

1. **What are the components, and how does data move between them?** Boxes are
   cheap; the arrows are the design.
2. **What did you reject?** Two alternatives, and the specific reason each lost.
   A design with no rejected option is a description of the first idea.
3. **What happens when a dependency fails?** Down database, slow network, bad
   data, 100x volume. The answer is a paragraph, not a shrug.
4. **What are the invariants?** What must always be true of the data, and where
   is it enforced?
5. **Which decision is expensive to reverse?** Storage model, public API,
   authentication. Record those as decisions with reasons.

## Write

- `docs/design/architecture.md` - components, data flow, trade-offs, failure
  behaviour.
- Decisions via `projtruth decide "<choice>" --why "<reason>"` - the `why` is
  the part that saves the next session.

## Shallow looks like

A component diagram with no arrow labels, no rejected alternative, and no
failure section. It looks like design and answers none of the questions a
builder has.

## Exit

`lifecycle check --stage 2` passes, and someone who has never seen the code can
predict where a new feature goes and what it will touch.
"""

BUILD = """# Stage 3 - Build

Turn the spec into working code in slices, each of which leaves the product
runnable and provable.

## Answer these

1. **What is the smallest slice that produces an observable change?** Build that
   first, end to end, however thin.
2. **What test fails before the code exists?** If you cannot write it, the
   criterion is unclear - go back to stage 1.
3. **What did you break?** Run the suite; do not assume.
4. **What is deliberately unbuilt?** Mark it, so the next session does not think
   it was forgotten.

## Write

- code and tests, committed in slices that each leave the app working;
- `PROGRESS.md` if the work spans sessions: what is done, what is next, what is
  blocked.

## Shallow looks like

One large commit at the end, tests written after the fact, integration points
"to be wired later", and no runnable state until the last day.

## Exit

`lifecycle check --stage 3` passes, `git log` reads as a sequence of working
states, and a new contributor can run the tests from the README.
"""

VERIFY = """# Stage 4 - Verify

Replace "it works" with evidence someone else can re-run.

## Answer these

1. **For each criterion, what did you actually run?** The command, not the idea
   of the command.
2. **What tier is this evidence?** `measured` (real run, real output),
   `inferred` (read from code or logs), `guessed` (assumption). Guessed is a
   note to yourself, not proof.
3. **What is the negative case?** Bad input, empty list, timeout, permission
   denied. A happy path alone proves very little.
4. **Would this pass on a fresh clone?** If the evidence depends on your local
   state, it is not evidence.

## Write

- one evidence file per criterion (or per requirement when one run covers it),
  named `R<n>.<i>-<slug>.md`, containing the command, its real output in a
  fenced block, and the tier word.
- `projtruth report` must show the requirement as `verified`.

## Shallow looks like

A screenshot with no command, "tested manually", evidence written before the run,
or evidence for the happy path only.

## Exit

`lifecycle check --stage 4` passes; every requirement is `verified` and its
evidence is newer than the code it covers.
"""

RELEASE = """# Stage 5 - Release

Make it usable by someone who was not in the room.

## Answer these

1. **What changed for the user?** Not for the codebase - for the person who has
   to decide whether to upgrade.
2. **How do they upgrade, and how do they roll back?** A release without a
   rollback path is a bet.
3. **What is known broken?** Name it; a known issue costs less trust than a
   surprise.
4. **What does the tag point at?** A version that matches the changelog, on a
   commit that was tested.

## Write

- `CHANGELOG.md` entry for the version - user-facing bullets, not a commit list;
- a git tag matching the version;
- release notes that say what changed, what broke and how to go back.

## Shallow looks like

A changelog that lists commits, a tag that does not match the version, or a
release with no mention of what is known broken.

## Exit

`lifecycle check --stage 5` passes, and a user can decide whether to upgrade
from the notes alone.
"""

GAME = """# Game pack - long-arc design

An open-world game's design is not an architecture document. It is a world that
has to stay consistent while hundreds of scenes are written out of order.

This pack adds checks to stages 0 and 2. It applies when `docs/game/` exists.

## Answer these

1. **What are the three pillars?** The experiences the game sells, each with how
   the player feels it. Every later decision is tested against these.
2. **Who wants what?** Characters and factions with goals that conflict. A
   faction with no goal is scenery.
3. **What facts are true in this world?** The lore a quest may reveal. If it is
   not in the bible, it does not exist.
4. **What must happen before what?** The quest graph. Which quests gate which,
   and what the player can do out of order.
5. **What does each quest reveal?** A reveal of a fact nobody established is a
   plot hole the player will find.
6. **What happens if the player skips ahead?** The answer is either a gate or a
   branch; "they probably won't" is neither.

## Write

`docs/game/pillars.md` - three bullets.

`docs/game/world-bible.md` with frontmatter lists:

```markdown
---
characters: [aria, borin]
factions: [guild, crown]
locations: [harbor, keep]
facts: [war-started, king-dead]
---
```

`docs/game/quests/<id>.md`, one per quest:

```markdown
---
id: q-harbor-arrival
requires: [q-prologue]
reveals: [war-started]
characters: [aria]
factions: [guild]
---
```

Then the prose: what the player does, what they learn, what changes.

## What the checks catch

- a quest requiring a quest that does not exist;
- a prerequisite loop (a quest that can never start);
- a reveal of a fact the bible never establishes;
- a character or faction used in a quest but never declared.

## Shallow looks like

A wiki of names with no goals, quests described in prose with no ids, and a
timeline that exists only in the writer's head.

## Exit

`lifecycle check --stage 2` passes with the pack active - which means both
the generic design checks and these - and every quest id, fact and actor
resolves.
"""

SUSTAIN = """# Stage 6 - Sustain

A long task outlives the conversation it started in. When the context is
compacted, or a new session picks the work up, what survives is what was written
down - not what was said.

## The cadence

**Every working session, before you stop:**

1. Update `docs/work/current.md` - Goal, Done, Next, Blockers. It is the file a
   fresh session reads first; if it is wrong, the next session repeats work.
2. Add one entry to `docs/work/log/YYYY-MM-DD.md` - what you tried, what
   happened, what surprised you. A compacted context cannot recover this.

**Every stage transition:** `lifecycle report` drafts `docs/reports/status-<date>.md`
from facts it can check (stage state, requirements, document findings, commits).
Fill in the three sections it leaves blank - what went well, what did not, what
is next. A stage that ends without that sentence is a stage nobody learned from.

**Every couple of weeks:** `corpus report --noise` and `corpus find` before
writing anything new. Documents are the part of the thread that rots silently.

**When the context is compacted:** run `lifecycle resume`. It prints the work
thread, the last journal entries and the one blocking item - the state you would
otherwise have to rebuild from the transcript.

## Answer these

1. If this session ended now, what would the next one get wrong? That is what
   belongs in `current.md`.
2. What did you learn that is not in the code or the docs? That is the journal.
3. What did you promise at the start of the stage, and what actually happened?
   That is the report.
4. Is the always-loaded set still small enough to start a session with? Detail
   belongs in a reference file, not in the file every session reads.

## Shallow looks like

A `current.md` that says "working on it", a journal written once, a report that
lists commits, and a `CLAUDE.md` that has grown into the project's whole
documentation.

## Exit

`lifecycle check --stage 6` passes: the work thread exists, it is newer than the
code it describes, and there is a journal entry and a report from this cycle.
"""

STAGES = {"discovery": DISCOVERY, "spec": SPEC, "design": DESIGN,
          "build": BUILD, "verify": VERIFY, "release": RELEASE,
          "sustain": SUSTAIN}
PACKS = {"game": GAME}


def for_stage(key):
    return STAGES.get(key)


def for_pack(name):
    return PACKS.get(name)
