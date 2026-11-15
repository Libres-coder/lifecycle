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
act: 1
order: 20
requires: [q-prologue]
reveals: [war-started]
characters: [aria]
factions: [guild]
reveals_to:
  - borin: war-started
---
```

Then the prose: what the player does, what they learn, what changes.

## Order and knowledge

`act:` and `order:` say when the player meets the quest. The check refuses a
quest that requires one the timeline puts later - the player cannot finish a
quest before the one it needs, whatever the graph says.

`knows:` in the bible is what each character knows before the story starts;
`reveals_to:` says who learns a fact in this quest. A reveal to someone who
already knows it is reported: either the reveal is redundant or the starting
state is wrong, and both are cheap to fix now.

## The craft standard (what "good" means here)

A quest is a verb with a cost. The checks can see the graph; they cannot see
whether the quest is worth playing. This is the difference.

1. **The player does, not watches.** Every quest states the verb the player
   performs and the choice they make. "Learn about the guild" is a lecture;
   "decide who to sell the ledger to" is a quest.
2. **A choice has a cost.** If both options are fine, it is a menu, not a
   decision. Say what each choice takes away.
3. **Stakes are concrete and local.** "The city is in danger" is a premise;
   "the fisher who hid you loses the boat" is a stake.
4. **The world answers back.** Factions remember what the player did, and say
   so. A world that does not remember is a backdrop.
5. **No filler verbs.** Fetch, kill-ten and walk-here are structure; if the
   quest is only that, cut it or wrap it around a decision the player cares
   about.
6. **Show the lore through action.** A fact revealed while the player is doing
   something they care about lands; a fact delivered by a lore dump does not.
7. **Difficult material is not softened.** War, cruelty, grief and desire are
   part of the world: write them as consequences with names and bodies, not as
   set dressing and not as something the camera avoids. The limit is the rating
   and the law, not discomfort.
8. **Every quest changes the world state.** A door, a faction, a fact, a
   relationship - if nothing changes, the quest is a detour.

### Weak quest looks like

- a fetch with no decision in it;
- a stake nobody in the scene can lose;
- the same "talk to X, then Y" shape as the last four quests;
- lore delivered in a monologue, not in the middle of trouble;
- the world unchanged when it is over.

The advisory checks read the shadow of this standard: a quest with no `stakes`,
a quest under 40 words. They do not grade design. They make the empty case
visible.

## What the checks catch

- a quest requiring a quest that does not exist;
- a quest that requires a later quest (timeline inversion);
- a prerequisite loop (a quest that can never start);
- a reveal of a fact the bible never establishes;
- a reveal to a character who already knows it;
- a character or faction used in a quest but never declared.

## Shallow looks like

A wiki of names with no goals, quests described in prose with no ids, and a
timeline that exists only in the writer's head.

## Exit

`lifecycle check --stage 2` passes with the pack active - which means both
the generic design checks and these - and every quest id, fact and actor
resolves.
"""

STORY = """# Story pack - long-form narrative

A novel or a screenplay is not a product backlog, and its design document is not
an architecture. It is a world, a cast with conflicting wants, and a set of
promises made to the reader that all have to be kept - usually written out of
order.

This pack adds checks to stages 0 and 2. It applies when `docs/story/` exists.

## Answer these

1. **What is the premise in one sentence?** Who wants what, and what stands in
   the way. If it takes a paragraph, it is setting, not a premise. A premise
   that could be swapped for another story's premise has not been decided.
2. **What is the main thread?** Name it under `main_thread:`. If two threads
   compete, pick the spine and let the other run beside it. A story whose main
   thread changes every volume is an anthology of unfinished openings.
3. **What is the inciting incident?** The event that starts *every* faction and
   character at once. "The hero sees something and runs" starts only the hero;
   a real inciting incident changes what each power wants next.
4. **What question does the story ask, and who pays to answer it?** `theme:` is
   a question, not a slogan. If no character has to choose between two things
   they cannot both keep, the theme is decoration.
5. **What does the protagonist want, what do they need, and what lie do they
   believe?** Want drives the plot; need is what they actually require; the lie
   is why they cannot see it. The gap is the character arc.
6. **What is the antagonist's plan, and why does it not simply kill the hero?**
   `goal`, `plan`, `constraint`. The plan must be one that would work if the
   hero did nothing; the constraint is the structural reason the hero is alive.
   "The villain had no time" is not a constraint.
7. **What does each faction want, and what ties it to another?** `faction_wants`
   and `faction_ties` (`a -- b: reason`). Trade, debt, marriage, fear: the tie
   decides what each will sacrifice. A list of powers is a map; a network of
   interests is a plot.
8. **How many chapters does each act carry, and who is in them?** `act:` and
   `characters:` on every chapter. One chapter per act is a synopsis; a
   character who appears once and vanishes is a function.
9. **Who knows what, when?** `knows:` is the starting state; `reveals_to:` in a
   chapter updates it. A reveal to someone who already knows is a continuity
   bug the reader will feel.
10. **Which thread does each chapter advance or resolve?** A chapter that moves
    nothing is a scene looking for a book.

## Write

`docs/story/outline.md` - the heart, then the acts and threads:

```markdown
---
premise: a smuggler must return the dead king's seal before the war it can start
theme: can a lie told to protect someone survive the truth?
main_thread: the-heir
inciting_incident: the seal is found on a body in the harbor
inciting_chapter: ch-01
acts: [setup, turn, resolution]
threads: [the-heir, the-war]
---
```

`docs/story/characters.md` - characters, facts, starting knowledge, and the
network:

```markdown
---
characters: [aria, borin]
facts: [war-started, king-dead]
knows:
  - aria: war-started
role:
  - aria: protagonist
  - borin: antagonist
want:
  - aria: to reclaim the harbor
  - borin: to keep the guild's ledger
need:
  - aria: to be seen as herself, not as the heir
  - borin: to be forgiven by his father
lie:
  - aria: believes a lie can keep everyone safe
  - borin: believes the guild is the only order
obstacle:
  - aria: the guild holds the deed
  - borin: the guild owns him
flaw:
  - aria: trusts the wrong people
  - borin: cannot lie to his father
relations:
  - aria: borin
  - borin: aria
goal:
  - borin: to keep the guild's charter
plan:
  - borin: to marry aria into the crown's debt
constraint:
  - borin: the guild needs aria alive and publicly legitimate
faction_wants:
  - guild: keep the harbor monopoly
  - crown: tax the harbor without another war
faction_ties:
  - guild -- crown: the crown holds their charter
---
```

`docs/story/chapters/<id>.md`, one per chapter:

```markdown
---
id: ch-03
order: 30
act: turn
pov: aria
characters: [aria, borin]
reveals: [king-dead]
threads: [the-heir]
resolves: []
reveals_to:
  - borin: king-dead
---
```

## The craft standard (what "good" means here)

The checks above keep the structure honest. They cannot make a scene worth
reading; this section is the standard they stand in for.

1. **Concrete, always.** A scene happens somewhere, to a body, at a time.
   "The council discussed the war" is a summary; "the chancellor's pen ran dry
   halfway through the sentence that would have ended it" is a scene. If a
   chapter can be replaced by its own `want`/`obstacle` line, it is not written
   yet.
2. **Conflict is the engine, not a topic.** Every chapter says what the POV
   wants in this moment and what stands in the way. If nothing opposes them,
   cut the chapter or find the opposition. Never resolve the tension in the
   beat that creates it.
3. **Do not look away.** Evasion looks like cutting at the moment of violence
   or intimacy, naming the emotion instead of staging it, "passed away",
   vagueness where the story demands a specific act. Write the difficult thing
   the story is about, with the weight it deserves. Mature material - violence,
   grief, desire, sex - is written plainly and consequentially, never as a wink
   and never as decoration. The limits are the law and the audience rating, not
   the writer's comfort; inside them, evasion is a craft failure.
4. **Stakes are specific and personal.** "The kingdom falls" is a premise until
   someone the reader knows loses something they can name.
5. **Characters are contradictions.** Each wants something, something blocks
   them, and their flaw is why the block holds. A character who only reacts is
   furniture. They change, or they refuse to, and the refusal costs.
6. **Dialogue does two things.** It moves the scene and hides what the speaker
   will not say. A line that can be replaced by its literal meaning is
   exposition.
7. **Every scene turns or reveals.** If it does neither, it is atmosphere -
   seasoning, not the meal.
8. **Read it aloud.** A line passes if a person would say it and the reader
   hears the silence around it.
9. **The protagonist chooses.** A hero who is chased, rescued and chased again
   is a package the plot ships between locations. At least once per volume
   they must choose between two things they cannot both keep, and the choice
   must cost something the reader has seen them value.
10. **The antagonist is competent.** Their plan would work if the hero did
    nothing, and the reason they do not simply kill the hero is structural
    (they need the hero alive, publicly, married, blamed) - never "they had no
    time" or "they underestimated him". A villain who acts because the plot
    needs it is a plot hole with a face.
11. **Theme is paid in scenes.** The question in `theme:` is answered by a
    choice someone makes and a price someone pays. If no scene would change if
    you deleted the theme, it is a label on the cover, not the book.
12. **Networks, not lists.** Every faction wants something another faction can
    give or withhold, and every relation has a history. When a new map or
    faction appears, an old character or debt must appear with it; otherwise
    the story is widening, not deepening.

### Weak chapter looks like

- it summarises the argument instead of staging it;
- the POV wants nothing in the moment, and the prose drifts;
- the hard scene is skipped with "later that night";
- every character speaks in the author's voice;
- it ends where it began, with more words;
- the villain spares the hero for a reason the book never states;
- a character exists for one scene and then vanishes without a trace;
- the same chase, the same escape, the same "everyone thinks he knows",
  renamed for a new town.

The advisory checks read the shadow of this standard: a chapter without
`want`/`obstacle`/`turn`, a chapter under 200 words, a character without a
declared want/need/lie, a repeated want or turn across chapters, a cast that
never appears, an antagonist with no plan or constraint, factions with no wants
or ties. They do not grade prose. They make the empty case visible.

## Build

For a story the build artifact is the draft, not a source tree: chapters under
`docs/story/chapters/`, each one a scene. `lifecycle --pack story check
--stage 3` requires at least one chapter and reports the chapter and word
counts; it does not judge the prose. Do not add source files or tests to
satisfy a stage that was written for software - the pack replaces those checks
because they are not this kind of work.

## What the checks catch

- an outline with no premise, theme, main thread or inciting incident;
- a `main_thread:` that names a thread the outline never declares;
- an `inciting_chapter:` that is not a chapter file;
- a cast with no protagonist or antagonist role;
- an antagonist with no goal, plan or constraint;
- a relation or faction tie that names something undeclared;
- a cast with no relations at all, or factions with no wants or ties;
- a chapter listing a character the cast never declares;
- a declared character who never appears, or appears in only one chapter;
- a chapter whose `act:` the outline never names, or an act with fewer than
  two chapters;
- the same `want`, `obstacle` or `turn` reused across chapters (a template,
  not a scene);
- a chapter without an `order:`, or two chapters sharing one;
- a POV character who is not in the cast;
- a reveal of a fact the characters file never establishes;
- a plot thread a chapter uses but the outline never declares;
- a plot thread nobody resolves (the abandoned promise readers call a plot hole);
- a reveal to a character who already knows it.

## Shallow looks like

A cast list with no wants, chapters named "Chapter 1" with no order or POV, a
thread declared and forgotten, and a twist nobody planted. A premise that is
really a setting. A villain who waits. A new volume that adds a map and three
factions but no tie to the old ones. A cast that is a list of functions - the
healer, the informant, the love interest - with no wants that could collide.

## Exit

`lifecycle --pack story check --stage 2` passes. The pack has to be chosen
explicitly for that command: auto-detection adds the story checks but never
removes a generic gate. When it is chosen, the story documents are the design
stage - the outline, cast and chapter checks stand in for the architecture and
recorded-decision checks - and every chapter's order, POV, reveal and thread
resolves against the two documents above.
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

TOOLS = {
    "discovery": [
        ("superpowers:brainstorming", "interrogate the idea before it becomes a plan"),
        ("corpus find", "is there already a document about this problem?"),
    ],
    "spec": [
        ("projtruth", "requirements with acceptance criteria, and their evidence"),
        ("mattpocock-skills:grilling", "stress the spec with questions before building"),
    ],
    "design": [
        ("feature-dev:code-architect", "an architecture blueprint from the codebase"),
        ("graphify", "what the code actually looks like, if it already exists"),
        ("ui-ux-pro-max / tastemaker", "when the product has a screen"),
        ("inkcheck", "if the narrative is written in Ink - branch and dead-end QA"),
    ],
    "build": [
        ("superpowers:test-driven-development", "a failing test before the code"),
        ("ds-verify-loop", "edit, run, read the error, fix - until green"),
        ("code-simplifier", "after it works, before it ships"),
    ],
    "verify": [
        ("verify-first", "the evidence pipeline this stage reads"),
        ("chrome-devtools-mcp / playwright", "drive the real app in a browser"),
        ("projtruth", "verified / stale / unverified per requirement"),
    ],
    "release": [
        ("corpus", "no document finding that misleads a reader"),
        ("commit-commands", "commit, push, PR"),
        ("gh", "tag, release notes, CI"),
    ],
    "sustain": [
        ("corpus", "documents rot silently; report and consolidate"),
        ("lifecycle resume", "after every compaction"),
        ("skill-audit", "the tool collection itself accumulates"),
    ],
}

STAGES = {"discovery": DISCOVERY, "spec": SPEC, "design": DESIGN,
          "build": BUILD, "verify": VERIFY, "release": RELEASE,
          "sustain": SUSTAIN}
PACKS = {"game": GAME, "story": STORY}


def for_stage(key):
    return STAGES.get(key)


def for_pack(name):
    return PACKS.get(name)
