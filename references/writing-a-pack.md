# Writing a pack

A pack is a complete tool for one kind of work: novel, game, service, film,
site. This is how to add one without bending the framework - and why the
framework does not bend.

## The rule that makes types peers

The seven stages are questions, not artifacts:

| stage | the question |
|---|---|
| 0 Discovery | why does this exist, for whom, and what will it not do |
| 1 Spec | what exactly is promised, checkably |
| 2 Design | what shape does it have, and why this one |
| 3 Build | does the thing exist |
| 4 Verify | is every promise backed by evidence that still holds |
| 5 Release | can a stranger use it, and can they go back |
| 6 Sustain | can the work survive a context reset |

The built-in checks answer those questions with **software** artifacts:
architecture, source, tests. They are the software default, not a universal
law. A pack declares its own artifacts for any stage where its kind of work
differs, and may replace the built-in checks for those stages.

Replacement is **explicit only**: `lifecycle --pack story check`. Detection by
directory presence adds a pack's checks but never removes another type's gate.
A narrative folder in a software repository must not weaken its architecture
requirement, and this is a test, not a promise (`test_auto_detection_never_
removes_a_generic_gate`).

A project can also be more than one kind: `--with <pack>` adds the second
pack's checks with its replacements disabled. A game that also has a written
narrative uses `--pack game --with story` - quests and architecture at once.

## What a pack contains

```python
PACKS = {
    "story": {
        "title": "Long-form story",
        "stages": (0, 2, 3),            # stages whose checks this pack adds
        "playbook": "story.md",          # what deep work looks like, and the craft standard
        "discovery": [story_discovery],  # checks appended to stage 0
        "design": [story_design, story_craft],
        "build": [story_build],
        "replaces": {"design": ["architecture", "decisions"],
                     "build": ["source", "tests"]},
    },
}
```

1. **Detection** - `packs.detect(repo)` returns the pack name when its
   artifacts exist (a real file, not an empty directory, not a template).
   First match wins; `--pack` says which one the checks follow.
2. **Checks** - one function per stage, returning result dicts from
   `contract.ok/fail/warn`. Blocking failures are for contradictions a reader
   cannot resolve (a quest requiring a missing quest); taste and length are
   `warn`. The stage's generic checks run first; `replaces` removes the named
   ones when the pack is explicit.
3. **Playbook** - in `playbooks.py`: the questions to answer, what to write,
   what shallow looks like, the craft standard, and the exit condition. This is
   the part a checker cannot do; write it as the standard, not as a summary.
4. **Scaffold** - `packs.TEMPLATES[name]` maps paths to starter text. `pack
   init` writes only what does not exist, refuses path conflicts before
   writing, and never fills content. Template files are named `_template.md`
   and are skipped by every check.

## Checklist before merging a pack

- [ ] Detection requires a real artifact; an empty directory opts out.
- [ ] Every blocking failure has a concrete contradiction behind it.
- [ ] Every advisory finding says what shallow work looks like.
- [ ] `replaces` names only checks that make no sense for this kind of work,
      and the playbook says so in its exit condition.
- [ ] `pack init` creates the structure and does not overwrite.
- [ ] Tests: valid work passes; each failure mode has a test; auto-detection
      keeps the generic gate; explicit selection replaces it.
- [ ] `docs/reviews/` gets a note for anything that claims to check quality.

## Types that are not here yet

- **service**: SLO and error budget, runbook, rollback path - replaces nothing
  at stage 2 (a service has an architecture) and adds to stages 5 and 6.
- **film/video**: build = renders and edit timeline; verify = screening notes
  with timecodes; release = export specs (resolution, subtitles, loudness).
- **site/content**: accessibility checklist, performance budget, event schema;
  a site is software, so this pack adds rather than replaces.

The framework does not change for these. If it has to, the pack is wrong or
the stage question is.
