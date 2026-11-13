# Changelog

## [1.4.2] - 2026-11-14

### Added
- **A pack can replace a generic artifact** (`replaces`): the story pack
  stands in for `architecture` and `decisions` at stage 2, because a novel has
  no architecture document and forcing one is theatre. Its outline, cast and
  chapter checks are the design stage for that kind of work. Game and software
  projects keep the generic checks.
- **Stage 4 reads `evidence_tier`** (projtruth 1.2.2) and adds an advisory when
  every verified requirement rests on `guessed` or untiered evidence. It does
  not change any status; it makes "verified by a guess" visible to the stage
  that trusts it. A projtruth older than 1.2.2 (no field in its JSON) is
  ignored rather than misread.

## [1.4.1] - 2026-11-14

An adversarial review of the pack layer (v1.3.0-1.4.0) found 2 P1 and 6 P2;
all fixed, 121 -> 135 tests.

### Fixed
- **A repository path containing glob characters** (`Game [WIP]`) made every
  quest and chapter invisible: the glob treated `[WIP]` as a character class,
  the graph checks never ran, and the stage passed. The root is escaped now.
- **Only `_template.md` is skipped.** The code skipped every `_`-prefixed file,
  so a real `_prologue.md` disappeared - and a quest requiring it reported a
  false "requires a quest that does not exist".
- **Frontmatter quotes and comments** are parsed properly: a comment after a
  value with an apostrophe (`facts: [a, b]  # the king's death`) no longer
  becomes data, `title: "Chapter #1"` keeps its text, `threads: ["a, b"]` is
  one item, and `- "aria": "war-started"` keeps both sides intact.
- **An empty `quests/` or `chapters/` directory no longer opts a pack in** -
  and an empty `docs/game/quests/` no longer wins auto-detection over a
  complete `docs/story/`.
- **Knowledge accumulates in story order**: a second reveal of the same fact
  is reported, and `knows:` naming an undeclared character or fact fails
  instead of silently disabling the check.
- **Timeline**: a missing `act:` is warned about (a cross-act inversion used to
  be compared as if it were act 1); **threads**: a thread resolved before its
  last appearance is warned about.
- **`pack init`** refuses a path conflict before writing anything, reports a
  directory named like a file instead of "kept", and never raises.
- **Word count** includes kana and Hangul; a 300-character Japanese chapter is
  no longer "0 words".
- The story playbook's Exit now says the generic design checks still apply.

## [1.4.0] - 2026-11-14

### Added
- **Packs are now craft standards, not only structure checks.** `lifecycle
  pack guide story|game` prints what an excellent deliverable in that domain
  looks like and what weak work looks like:
  - story: concrete scenes (not summaries), conflict as the engine, difficult
    material written with weight instead of avoided, personal stakes,
    characters as wants meeting obstacles, every scene turns or reveals;
  - game: a verb with a cost, choices that take something away, a world that
    remembers, no filler verbs, lore shown through action.
- Advisory craft checks that read the declared shadow of the standard:
  a chapter without `want`/`obstacle`/`turn`, a chapter under 200 words, a
  character without a declared want/obstacle/flaw, a quest without `stakes`,
  a quest under 40 words. None of them fails a stage.
- `pack init` templates now carry those fields, so the scaffold teaches the
  standard by existing.

## [1.3.1] - 2026-11-13

### Added
- `lifecycle suggest` names the active pack when the blocking stage is 0 or 2,
  with the command that prints its playbook. A story project was being told the
  generic design questions and nothing about the pack actually checking it.
- `corpus` 0.1.3 skips `_template.md` scaffold files, so the two tools agree on
  what counts as a document.

## [1.3.0] - 2026-11-13

### Added
- **Packs for work that is not software.** `story` is the second pack: an
  outline with acts and plot threads, a cast with starting knowledge, and
  chapters with `order`/`pov`/`reveals`/`threads`/`resolves`. It catches a
  chapter out of order, a POV who is not in the cast, a thread used but never
  declared, a thread nobody resolves, and a reveal to someone who already
  knows.
- `lifecycle pack list | init <name> | guide <name>`: what is available and
  active, a scaffold that creates the empty structure (never content), and the
  playbook. Template files (`_template.md`) are never read as data.
- Game pack: `act`/`order` on quests, so a quest that requires one the timeline
  puts later is refused; `knows:` in the bible and `reveals_to:` in a quest
  report a reveal to a character who already knows the fact.

### Fixed
- The status line writing `.lifecycle/context.json` made the SessionStart hook
  treat an unrelated folder as a lifecycle project; `resume --hook` now needs
  `docs/work/`, a snapshot history, or a registry with requirements.
- `resume` printed the stale-context sentence twice (once as the reading, once
  as the advice).

## [1.2.4] - 2026-11-13

An adversarial review of the 1.2.x surface found one P1 and six P2s; all fixed.

### Fixed
- A wrong-typed field in `.lifecycle/context.json` (a percentage as `"85"` or
  `"high"`) crashed the status line and the SessionStart hook with `TypeError`.
  Readings are now sanitized on read: numeric strings are accepted, anything
  else becomes "unknown", and no consumer sees a string where it expects a
  number.
- `resume --hook` no longer carries the previous session's percentage into a
  fresh mtime. A token count is not a percent of the window, so the percentage
  is cleared; `resume` shows no context line until the status line writes a
  real reading.
- `suggest` no longer reports "no context reading" for a healthy reading below
  the nudge threshold; the entry is simply absent.
- Thread lookups normalize case and surrounding spaces, so
  `thread claim My-Thing` finds what `thread new My-Thing` created. Reserved
  Windows device names (`nul`, `con`, `com1`, ...) are refused at creation.

### Changed
- `hook install` upgrades legacy entries it wrote before `--hook` existed
  instead of treating them as current, and says so.
- When another tool owns `statusLine`, `hook install` leaves it alone **and
  says so**, naming the command; before, it reported a successful install
  while the context reading could never happen.
- Hook commands are matched on a subcommand word boundary: a script such as
  `~/bin/lifecycle-resume.sh` is neither claimed nor removed by uninstall.

### Docs
- Corrected: SessionStart carries `context_tokens` on `resume`/`fork`, not on
  `compact`; the thread therefore records the count when present and says
  nothing when it is not.
- Noted that a reading belongs to the repository, not to a window: two
  sessions on one repository overwrite each other's number.

## [1.2.3] - 2026-11-13

### Added
- The status line carries the advice, not just the number: once the reading is
  within five points of the trigger it renders `74% ctx - /compact`. The status
  line is the one surface always in view, so the compaction is asked for there
  instead of waiting for someone to run `status`.

## [1.2.2] - 2026-11-13

### Changed
- The context advice now follows the real compaction trigger. `lifecycle`
  reads `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` and moves its warnings with it:
  the nudge at trigger − 15, "run /compact now" at trigger − 5. With the
  override at 70 that is a nudge at 55% and a warning at 65% - early enough
  for the compaction to happen on your terms instead of mid-thought. Without
  the override the default trigger (95%) keeps the old late behaviour.
- The warning names the trigger (`auto-compact fires at 70%`), so a reading
  and the advice cannot disagree silently.

## [1.2.1] - 2026-11-13

### Fixed
- The SessionStart hook printed the whole resume report in any folder the
  session opened, including ones with no lifecycle setup. `resume --hook` is now
  silent unless the repository has a work thread, a registry with requirements,
  or a `.lifecycle/` directory.

### Added
- `lifecycle suggest`: the blocking item, the tools worth using for that stage,
  and a context warning (`/compact` at 85% and above, a nudge at 70%).
- A context reading older than ten minutes is labelled stale instead of live.
- Documented what lifecycle cannot do: invoke a skill or a slash command.

## [1.2.0] - 2026-11-13

### Added
- **Context readings.** `lifecycle statusline` is a Claude Code status line
  command: it records `context_window.used_percentage` to
  `.lifecycle/context.json` and renders `74% ctx`. `status` and `resume` print
  `context: N% used`, and a reading older than ten minutes is marked.
- `resume --hook` records `context_tokens` from the SessionStart payload, so the
  thread knows how full the window was after a compaction.
- `hook install` adds the status line only when none is configured; `hook
  uninstall` removes it only when it is ours.
- A documentation section on what a hook can and cannot see about context, and
  how to compact earlier (`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`).

## [1.1.0] - 2026-11-13

### Added
- **Threads**: more than one line of work in one repository.
  `docs/work/threads/<slug>/` holds that thread's `current.md`, `plan.md` and
  `owner`; `lifecycle thread new|claim|release|list` manages them,
  `lifecycle resume --thread` opens one, and `status` prints a portfolio table
  (owner, plan progress, next item, handoff current or STALE).
- Two team-shaped warnings: one owner claiming several threads, and a claim
  older than 24 hours (the thread looks busy but is not).

## [1.0.0] - 2026-11-13

The first release with a stable surface: seven stages, a work thread that
survives a context reset, and hooks that make the thread automatic.

### Added
- **Plan artifact** (`docs/work/plan.md`): milestones with checkbox tasks, so
  "how far along" is visible. `status` and `resume` show milestone and task
  progress; a plan with no tasks, or with every task ticked, is reported.
- **`lifecycle init`**: scaffolds `docs/work/current.md`, `plan.md`, and the
  log / report / review directories. Never overwrites.
- **Thread structure checks**: `current.md` must have Goal, Done, Next and
  Blockers, and Next must contain a concrete item.
- **Compaction cadence**: three snapshots since the last status report is
  reported - work running on memory instead of notes.
- `resume` includes plan progress and the last compaction snapshot.

### Fixed (pre-release review)
- Release checks: any tag that normalises to the version passes (`v1.0.0`,
  `pkg@1.0.0`, `release-1.0.0`); a retained `v1.0.0-rc.1` no longer wins the
  comparison. Versions are read from `pyproject.toml`, `Cargo.toml`,
  `package.json`, `pubspec.yaml`, `build.gradle`, `setup.cfg`, `project.godot`
  and `VERSION`; with no version at all the tag check fails instead of passing.
- Thread freshness uses git commit times, so a clone or a `git pull` no longer
  makes an up-to-date thread look stale (or an abandoned one look fresh).
- A registry whose `criteria` are strings is reported, not crashed on.
- Hook commands are resolved against what actually runs: the console script when
  it is on PATH, `python -m lifecycle` otherwise, and install refuses when
  neither resolves. SessionStart now also fires on `startup`.
- `check --stage 4` fails when a registry exists and projtruth is absent.
- `report` no longer overwrites a same-day report that was edited.
- `snapshot` skips the verify stage and no longer evaluates twice; `resume`
  prints the blocker first, where bounded hook output cannot drop it.
- `## Non Goals` and `## 1. The Problem` are recognised as headings.
- Plan checkboxes inside fenced code are ignored.

### Changed
- Stage 6 now runs five checks: thread freshness, sections, plan, review note,
  cadence. Only the work thread itself (present, fresher than the code) can fail
  the stage, and only after a release; the other four are advisory - a plan, a
  review note and a cadence are good practice, not a promise to a user.

## [0.4.0] - 2026-11-13

### Added
- **Hooks** (`lifecycle hook install`): PreCompact runs `lifecycle snapshot`, so
  the state is written before the context is compacted; SessionStart
  (compact|resume) runs `lifecycle resume`, so the work thread is the first thing
  in the new context. Written into the project's `.claude/settings.json`, merged
  without clobbering, removed by `hook uninstall`.
- `lifecycle snapshot` - stage state, working tree, last commits, the head of the
  work thread, and the transcript size (the only window into context size a
  subprocess has). Keeps the newest 20 by mtime.
- **Review note check** (stage 6): `docs/reviews/*.md`, reported when missing,
  older than 30 days, or with no findings at all.
- **Toolbox per stage** in `lifecycle guide`: the tools that help there, marked
  "if installed".

### Fixed
- Snapshot pruning sorted by filename; a file whose name did not start with a
  timestamp could delete the snapshot just written.

## [0.3.0] - 2026-11-13

### Added
- **Stage 6 Sustain**: the long-running thread. `docs/work/current.md` (goal,
  done, next, blockers), a session journal in `docs/work/log/`, periodic status
  reports in `docs/reports/`, and a context budget for the documents a session
  loads before any work starts. After the first release a missing or stale work
  thread fails the stage; before it, it warns.
- `lifecycle resume` - after a compaction or in a new session: the work thread,
  the last journal entries and the one blocking item.
- `lifecycle report` - drafts `docs/reports/status-<date>.md` from facts it can
  check (stage state, requirements, document findings, recent commits), leaving
  three sections blank for the human: what went well, what did not, what next.
- A Sustain playbook with the cadence: every session, every stage, every couple
  of weeks, every compaction.

### Fixed
- Evidence regenerated with identical bytes looked stale forever, because git
  sees no change; the evidence files now stamp their run time.

## [0.2.1] - 2026-11-13

### Fixed
- A malformed `requirements.json` (entries that are not objects, `criteria` as a
  string, a top-level list) crashed `status` with a traceback. It is now a
  reported finding, and a BOM'd registry is read.
- Build stage misclassified whole ecosystems: Rust falls back to inline
  `#[cfg(test)]` tests, Dart and a dozen other extensions count as source, and
  `docs/spec/openapi.yaml` no longer counts as a test file.
- An empty architecture document passed the design stage.
- Release matching was substring-based: version `1.0.0` matched tag `v11.0.0`.
  Versions and tags are normalised and compared exactly; `Cargo.toml` is read.
- Release depth checks no longer miss an empty changelog entry.
- The game pack activated on an empty `docs/game/` directory and turned two
  stages red. It now requires pillars, a bible or a quests directory.
- Nested quest directories (`quests/act1/q.md`) were ignored.
- Frontmatter comments (`requires: [q1]  # note`) corrupted ids.
- Vision headings with numbering or articles (`## 1. The Problem`) failed.
- `run_json` put the scanned repository on PYTHONPATH, so a repository under
  review could execute code when its status was requested. Only installed tools
  run now.
- Running `lifecycle` from a subdirectory failed every document stage; it now
  walks up to the nearest `.git` / `.projtruth`.

### Changed
- An unknown `--pack` exits 2 instead of silently disabling checks.
- `guide` appends the pack playbook when a pack is active, and the game
  playbook's exit line now says both generic and pack checks must pass.

## [0.2.0] - 2026-11-13

### Added
- `lifecycle guide [stage]` - the playbook for a stage: purpose, the questions
  you must answer before producing anything, what to write, what shallow looks
  like, and what done means. Six stage playbooks plus the game pack.
- Advisory depth checks: a vision under 100 words, fewer than two non-goals,
  criteria too vague to test, a decision without a reason, an architecture with
  no trade-off or failure section, evidence marked `guessed`. They never fail a
  stage; they print what a shallow version looks like.
- The `game` pack, applied when `docs/game/` exists: pillars, a world bible
  (characters/factions/locations/facts) and quest files with
  `requires`/`reveals`. Checks: unknown prerequisite, prerequisite loop, a
  reveal the bible never establishes, an actor never declared, duplicate quest
  id.
- `status` prints every blocker per failing stage, not just the first.
- `--pack auto|game|none`.

### Fixed
- Stage 4 passed on a repository with no requirements at all ("0 requirements
  verified"). It is now advisory: no registry is stage 1's problem.

## [0.1.0] - 2026-11-13

### Added
- Six-stage contract: discovery, spec, design, build, verify, release. Each
  stage declares the artifacts it requires and every gap is printed with the
  command that closes it.
- `status` / `next` / `check [--stage N]` / `stages`, with `--json`.
- Stage 4 calls projtruth and corpus when they are present (executable or
  checkout via `-m` + PYTHONPATH) and reports WARN with the install command when
  they are not.
- No stored state: a stage passes because the repository says so now.
- 16 tests.
