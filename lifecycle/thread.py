"""lifecycle thread: the artifacts that make work survive a context reset.

A long task outlives the conversation it started in. When the context is
compacted or a new session picks it up, three things decide whether the work
continues or restarts:

    docs/work/current.md    where the work stands right now (goal, done, next,
                            blockers, open questions) - the handoff
    docs/work/log/*.md      what happened, one entry per working session
    docs/reports/*.md       periodic summaries: what was done, what was not

None of these are generated for you. `lifecycle resume` reads them,
`lifecycle report` drafts the periodic one from facts it can check, and the
Sustain stage makes "the thread is up to date" a condition instead of a hope.
"""
import os
import time

from .contract import SOURCE_EXT, fail, git, ok, read, walk_files

WORK_DIR = "docs/work"
CURRENT = "docs/work/current.md"
LOG_DIR = "docs/work/log"
REPORT_DIR = "docs/reports"
DAY = 86400
JOURNAL_DAYS = 14
REPORT_DAYS = 30
CONTEXT_BUDGET_CHARS = 60000      # ~15k tokens of always-loaded project docs


def warn(name, detail, fix):
    return {"name": name, "ok": False, "detail": detail, "fix": fix, "required": False}


def _files(repo, rel_dir, suffix=".md"):
    d = os.path.join(repo, rel_dir)
    if not os.path.isdir(d):
        return []
    out = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        for f in files:
            if f.lower().endswith(suffix):
                out.append(os.path.join(root, f))
    return sorted(out)


def journal(repo):
    return _files(repo, LOG_DIR)


def reports(repo):
    return _files(repo, REPORT_DIR)


def newest_source_mtime(repo):
    newest = 0.0
    for rel in walk_files(repo):
        if os.path.splitext(rel)[1].lower() in SOURCE_EXT:
            try:
                newest = max(newest, os.path.getmtime(os.path.join(repo, rel)))
            except OSError:
                pass
    return newest


def released(repo):
    tags = git(repo, "tag")
    return bool(tags and tags.strip())


def context_load(repo):
    """Chars of the documents a session loads before any work starts."""
    files = []
    for rel in ("CLAUDE.md", "README.md", "AGENTS.md", CURRENT,
                "docs/product/vision.md", "docs/design/architecture.md"):
        p = os.path.join(repo, rel)
        if os.path.isfile(p):
            files.append(p)
    files += _files(repo, "docs/product")
    files = sorted(set(files))
    total = 0
    for p in files:
        try:
            total += os.path.getsize(p)
        except OSError:
            pass
    return total, files


def resume_text(repo, stages):
    """The handoff view: state, recent log, and the blocking item."""
    lines = []
    rel, text = read(repo, CURRENT)
    if text and text.strip():
        lines.append(text.strip())
    else:
        lines.append("No %s yet. Create it with Goal / Done / Next / Blockers - "
                     "it is what a fresh session reads first." % CURRENT)
    path, snap = latest_snapshot(repo)
    if snap:
        lines.append("")
        lines.append("## Last compaction snapshot")
        lines.append("")
        for line in snap.splitlines():
            if line.strip() and not line.startswith("#"):
                lines.append(line)
    entries = journal(repo)
    if entries:
        lines.append("")
        lines.append("## Recent journal")
        for path in entries[-3:]:
            rel = os.path.relpath(path, repo).replace("\\", "/")
            try:
                with open(path, encoding="utf-8-sig", errors="replace") as f:
                    head = [l.strip() for l in f.read().splitlines() if l.strip()][:3]
            except OSError:
                head = []
            lines.append("- `%s` - %s" % (rel, " / ".join(head) or "(empty)"))
    return "\n".join(lines)


def report_text(repo, stages, requirements=None, corpus=None):
    """A periodic summary drafted from what is checkable, with gaps left blank."""
    stamp = time.strftime("%Y-%m-%d")
    passed = len([s for s in stages if s["state"] == "passed"])
    lines = ["# Status report - %s" % stamp, "",
             "%d/%d stages pass." % (passed, len(stages)), "",
             "## Stage state", ""]
    for s in stages:
        lines.append("- **%s** - %s" % (s["title"], s["state"]))
    if requirements is not None:
        lines += ["", "## Requirements", "",
                  "%d registered, %d verified."
                  % (len(requirements),
                     len([r for r in requirements if r.get("status") == "verified"]))]
        bad = [r for r in requirements if r.get("status") != "verified"]
        for r in bad[:10]:
            lines.append("- %s (%s) %s" % (r.get("id"), r.get("status"),
                                           r.get("title", "")))
    if corpus is not None:
        sev = (corpus.get("metrics") or {}).get("severity") or {}
        lines += ["", "## Documents", "",
                  "%d artifacts, %d incorrect, %d stale, %d noise."
                  % ((corpus.get("metrics") or {}).get("artifacts", 0),
                     sev.get("incorrect", 0), sev.get("stale", 0), sev.get("noise", 0))]
    commits = git(repo, "log", "--oneline", "-10")
    if commits:
        lines += ["", "## Recent commits", ""]
        lines += ["- %s" % c for c in commits.splitlines()]
    lines += ["", "## What went well", "", "- ", "",
              "## What did not go well", "", "- ", "",
              "## Next", "", "- ", ""]
    return "\n".join(lines)


def write_report(repo, text):
    d = os.path.join(repo, REPORT_DIR)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "status-%s.md" % time.strftime("%Y-%m-%d"))
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


SNAP_DIR = ".lifecycle/snapshots"
MAX_SNAPSHOTS = 20
REVIEW_DIR = "docs/reviews"
REVIEW_DAYS = 30


def transcript_tokens(path):
    """Rough size of a session transcript, in tokens. The only window into the
    context the harness never shows a subprocess."""
    try:
        return max(1, os.path.getsize(path) // 4)
    except (OSError, TypeError):
        return 0


def snapshot(repo, transcript=None, trigger=""):
    """Write the state a compaction is about to destroy. Called by a hook.

    Cheap by design: a compaction must never be delayed by bookkeeping.
    """
    from . import contract as contractmod

    stages = contractmod.evaluate(repo)
    blocked = [s for s in stages if s["state"] == "failed"]
    passed = len([s for s in stages if s["state"] == "passed"])
    status = git(repo, "status", "--porcelain") or ""
    changed = len([l for l in status.splitlines() if l.strip()])
    commits = (git(repo, "log", "--oneline", "-3") or "").strip()
    tokens = transcript_tokens(transcript)
    stamp = time.strftime("%Y-%m-%d %H:%M")
    lines = ["# Snapshot %s%s" % (stamp, (" (%s)" % trigger) if trigger else ""), "",
             "- stages: %d/%d pass" % (passed, len(stages)),
             "- blocked: %s" % (", ".join(s["title"] for s in blocked) or "none"),
             "- working tree: %d changed file(s)" % changed]
    if tokens:
        lines.append("- transcript: ~%dk tokens" % (tokens // 1000))
    if commits:
        lines += ["", "## Last commits", ""]
        lines += ["- %s" % c for c in commits.splitlines()]
    _, current = read(repo, CURRENT)
    if current and current.strip():
        head = [l for l in current.strip().splitlines() if l.strip()][:6]
        lines += ["", "## Work thread (head)", ""] + ["    " + h for h in head]
    d = os.path.join(repo, SNAP_DIR)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, time.strftime("%Y-%m-%dT%H%M%S") + ".md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    _prune(d)
    return path


def _prune(d):
    """Keep the newest MAX_SNAPSHOTS by mtime - names sort by timestamp, but a
    test or a copied file can break that, and deleting the file just written is
    the one failure that matters."""
    try:
        files = [os.path.join(d, n) for n in os.listdir(d)]
        files.sort(key=os.path.getmtime)
    except OSError:
        return
    for path in files[:-MAX_SNAPSHOTS] if len(files) > MAX_SNAPSHOTS else []:
        try:
            os.remove(path)
        except OSError:
            pass


def latest_snapshot(repo):
    d = os.path.join(repo, SNAP_DIR)
    if not os.path.isdir(d):
        return None, None
    files = sorted(os.listdir(d))
    if not files:
        return None, None
    path = os.path.join(d, files[-1])
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return path, f.read()
    except OSError:
        return None, None


def check_review(repo):
    """Stage 6: has anyone looked at this critically, recently?

    A review note cannot prove quality - but a project that never records one
    has not looked, and a review with no findings on a first pass is a
    rubber stamp. Both are checkable; the quality itself is not.
    """
    files = _files(repo, REVIEW_DIR)
    if not files:
        return [warn("review", "no review note in %s/" % REVIEW_DIR,
                     "record an adversarial review per stage: what you tried to "
                     "break, what broke, what you decided to live with")]
    newest = max(files, key=os.path.getmtime)
    age = (time.time() - os.path.getmtime(newest)) / DAY
    if age > REVIEW_DAYS:
        return [warn("review", "the last review is %d days old" % int(age),
                     "review the thing you have now, not the thing you had a "
                     "month ago")]
    try:
        with open(newest, encoding="utf-8", errors="replace") as f:
            body = f.read()
    except OSError:
        body = ""
    findings = [l for l in body.splitlines() if l.strip().startswith("- ")]
    if not findings:
        return [warn("review", "the last review has no findings",
                     "a review that found nothing did not look; name at least one "
                     "thing you would change")]
    return [ok("review", "%d finding(s) in %s" % (len(findings),
                                                 os.path.relpath(newest, repo).replace("\\", "/")))]


def check_sustain(repo):
    """Stage 6: is the long-running thread actually being maintained?

    Blocking only after the first release - before that, a work thread is good
    practice, not a promise you have made to a user.
    """
    out = []
    live = released(repo)
    rel, text = read(repo, CURRENT)
    if not text or not text.strip():
        out.append(fail("thread", "no %s" % CURRENT,
                        "write it: Goal, Done, Next, Blockers - the file a fresh "
                        "session reads before touching anything")
                   if live else
                   warn("thread", "no %s yet" % CURRENT,
                        "create docs/work/current.md: Goal / Done / Next / Blockers"))
    else:
        changed = newest_source_mtime(repo)
        try:
            current_mtime = os.path.getmtime(os.path.join(repo, CURRENT))
        except OSError:
            current_mtime = 0
        if changed > current_mtime + 1:
            out.append(fail("thread:fresh", "code changed after %s" % CURRENT,
                            "update the work thread: what changed, what is next")
                       if live else
                       warn("thread:fresh", "code changed after the work thread",
                            "update docs/work/current.md before handing off"))
        else:
            out.append(ok("thread", CURRENT))
    entries = journal(repo)
    if not entries:
        out.append(warn("thread:journal", "no journal entries",
                        "one file per working session in docs/work/log/: what you "
                        "tried, what happened, what is next"))
    else:
        newest = max(os.path.getmtime(p) for p in entries)
        age = (time.time() - newest) / DAY
        if age > JOURNAL_DAYS:
            out.append(warn("thread:journal",
                            "the last journal entry is %d days old" % int(age),
                            "write one entry per working session - it is what a "
                            "compacted context cannot recover"))
        else:
            out.append(ok("thread:journal", "%d entry(ies)" % len(entries)))
    reps = reports(repo)
    if reps:
        newest = max(os.path.getmtime(p) for p in reps)
        age = (time.time() - newest) / DAY
        if age > REPORT_DAYS:
            out.append(warn("thread:report",
                            "the last status report is %d days old" % int(age),
                            "`lifecycle report` drafts one from the facts"))
        else:
            out.append(ok("thread:report", "%d report(s)" % len(reps)))
    else:
        out.append(warn("thread:report", "no status report yet",
                        "`lifecycle report` writes one with the stage state and the "
                        "open questions"))
    chars, files = context_load(repo)
    if chars > CONTEXT_BUDGET_CHARS:
        out.append(warn("thread:context",
                        "%d chars (~%dk tokens) load before any work starts"
                        % (chars, chars // 4000),
                        "move detail out of the always-loaded docs into references; "
                        "`corpus find` shows what already covers it"))
    else:
        out.append(ok("thread:context", "~%dk tokens of project docs" % (chars // 4000)))
    return out
