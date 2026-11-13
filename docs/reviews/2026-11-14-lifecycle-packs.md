# Review - lifecycle pack layer 1.3-1.4 (2026-11-14)

Independent adversarial review of the pack system (`v1.2.4..v1.4.0`): the
frontmatter parser, detection, game/story checks, craft checks, scaffold and
the pack CLI. It found two P1 items (three separate failure modes) and six P2;
every finding was reproduced against the installed code in a temp directory,
and all are fixed in 1.4.1.

## Findings

**P1 - a repo path with glob characters hid every pack file.** A checkout at
`...\Game [WIP]\` made `quests/**/*.md` match nothing, so the graph checks
never ran and stage 2 passed with a broken quest dependency. Fixed with
`glob.escape` on the scanned root.

**P1 - every `_`-prefixed file was treated as a template.** A real
`_prologue.md` was skipped: its quest vanished from the graph, and a quest
requiring it reported a false "does not exist". Only `_template.md` is skipped.

**P1 (same area) - quote handling corrupts legal frontmatter.** A trailing
comment containing an apostrophe became part of the last list item;
`title: "Chapter #1"` was truncated; quoted pair sides (`- "aria": "war"`)
were mangled. Comments are now cut only outside quotes, lists split only on
commas outside quotes, and a quoted span is stripped only when it wraps the
whole value.

**P2 - an empty artifact directory opted a pack in.** `mkdir docs/story/chapters`
made two stages red; worse, an empty `docs/game/quests/` won auto-detection
over a complete story pack. Detection now requires a real (non-template) file.

**P2 - knowledge state never accumulated.** Two reveals of the same fact, and
`knows:` entries naming undeclared characters or facts, were invisible.
Reveals now update state in act/order, and `knows:` is validated.

**P2 - ordering was weaker than documented.** A quest without `act:` was
silently compared as act 1; a thread resolved before its last appearance
counted as resolved. Both are warned about now.

**P2 - scaffold could raise mid-write.** A path conflict left a partial
scaffold and a traceback. Paths are validated before writing; errors are
returned, never raised.

**P2 - kana and Hangul counted as zero words.** A 300-character Japanese
chapter was reported "too short". The character ranges are extended.

**P2 - the story playbook's Exit was unreachable as written.** It now states
that the generic design checks still apply.

## Checked and found correct

Parser: empty lists, block lists, unquoted inline lists, pair values with
extra colons, Windows paths, CRLF and UTF-8 BOM. Cycle detection with duplicate
ids is already covered by the duplicate-id failure. Scaffold keeps existing
files unchanged. `--pack bogus` exits 2; `pack list` is now exempt from
`--pack` validation.
