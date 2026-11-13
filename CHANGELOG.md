# Changelog

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
