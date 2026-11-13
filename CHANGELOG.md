# Changelog

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
