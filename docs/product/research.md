# Research

How this problem is solved today, and why the tool exists anyway.

- **AI-DLC (awslabs, 6.0k★, MIT-0)** - a stage-gated engine with 33 stages,
  artifact traceability and a statusline. Rejected as a replacement: it dictates
  the workflow and duplicates projtruth/corpus rather than reading them.
  https://github.com/awslabs/aidlc-workflows
- **sdlc-mcp (0★, MIT)** - the right primitive: `validate_artifact` returning a
  verdict and blockers. At the time of reading it was days old, its README still
  carried a `<you>` placeholder, and it validated document shape rather than
  repository state. https://github.com/Osucha/sdlc-mcp
- **spec-kit / agent-os / BMAD** - add a canonical directory for specs. They
  relocate work, they do not check that a stage produced anything.
- **verify-first, projtruth, corpus** (this workspace) - cover evidence,
  requirements and document health respectively. None answers "which stage is
  the product in", which is the gap this tool fills.
