# Review - lifecycle 0.2.0 (2026-11-13)

An independent adversarial review of the code, before the Sustain stage existed.
Kept as the project's first review note: what was found, and what was accepted.

## Findings

- P0 malformed `requirements.json` crashed `status` with a traceback instead of
  reporting it.
- P0 the build stage misclassified whole ecosystems: Rust tests written inline
  (`#[cfg(test)]`) counted as no tests; Dart was not a known source extension.
  Conversely `docs/spec/openapi.yaml` counted as a test file, so a project with
  no tests passed.
- P1 an empty `architecture.md` passed the design stage.
- P1 version matching was substring-based: `1.0.0` matched tag `v11.0.0`.
- P1 `run_json` put the scanned repository on `PYTHONPATH`, so a repository under
  review could execute code when its status was requested.
- P1 the game pack activated on an empty `docs/game/` directory, turning two
  stages red for a project that had not opted in.
- P1 nested quest directories were not scanned.
- P1 frontmatter comments (`requires: [q1]  # note`) corrupted ids.
- P1 vision headings with numbering or articles (`## 1. The Problem`) failed.
- P2 the "every stage passes" line also appeared when stages only had warnings.

All fixed in 0.2.1, except the two decisions below.

## What was accepted, not fixed

- **Depth checks are text heuristics.** "Trade-off" and "failure" are matched by
  regex. A thoughtful document that says "we rejected X because Y" passes; a
  careless one that names the words passes too. Accepted because the alternative
  is judging prose, which this tool cannot do.
- **The context budget is a guess.** 60k characters of always-loaded docs is a
  threshold with no measurement behind it. It will be revisited when a real
  project crosses it.

## What this review could not check

Whether the stages are the right stages. A reviewer can find bugs in a contract;
only using it on real work finds out whether the contract asks for the right
things.
