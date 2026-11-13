"""lifecycle thread: the artifacts that make work survive a context reset.

A long task outlives the conversation it started in. When the context is
compacted or a new session picks it up, what decides whether the work continues
or restarts is what was written down:

    docs/work/current.md    where the work stands now: goal, done, next, blockers
    docs/work/plan.md       milestones and tasks, so "how far along" is visible
    docs/work/log/*.md      what happened, one entry per working session
    docs/reports/*.md       periodic summaries: what was done, what was not
    docs/reviews/*.md       what someone tried to break, and what broke

None of these are generated for you. `lifecycle resume` reads them,
`lifecycle report` drafts the periodic one from facts it can check, and the
Sustain stage makes "the thread is up to date" a condition instead of a hope.
"""
import os
import re
import time

from .contract import SOURCE_EXT, fail, git, headings, ok, read, walk_files

WORK_DIR = "docs/work"
CURRENT = "docs/work/current.md"
PLAN = "docs/work/plan.md"
LOG_DIR = "docs/work/log"
REPORT_DIR = "docs/reports"
REVIEW_DIR = "docs/reviews"
SNAP_DIR = ".lifecycle/snapshots"
DAY = 86400
JOURNAL_DAYS = 14
REPORT_DAYS = 30
REVIEW_DAYS = 30
MAX_SNAPSHOTS = 20
CONTEXT_BUDGET_CHARS = 60000      # ~15k tokens of always-loaded project docs
THREAD_SECTIONS = ("goal", "done", "next", "blockers")
CHECKBOX_RE = re.compile(r"^\s*[-*]\s+\[([ xX])\]\s+(.+)$", re.MULTILINE)


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


def snapshots(repo):
    return _files(repo, SNAP_DIR)


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


def _section_body(text, name):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = re.match(r"^#{1,3}\s+(.+)$", line)
        if m and m.group(1).strip().lower().startswith(name):
            start = i + 1
            continue
        if start is not None and re.match(r"^#{1,3}\s+", line):
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else ""


def _bullets(text):
    return [l for l in text.splitlines() if re.match(r"^\s*[-*]\s+\S", l)]


# -- plan ------------------------------------------------------------------

def parse_plan(repo):
    """[{title, total, done}] from the checkboxes under each '## ' milestone."""
    rel, text = read(repo, PLAN)
    if not text:
        return None
    milestones = []
    for part in re.split(r"^##\s+", text, flags=re.MULTILINE)[1:]:
        lines = part.splitlines()
        body = "\n".join(lines[1:])
        boxes = CHECKBOX_RE.findall(body)
        milestones.append({"title": lines[0].strip(), "total": len(boxes),
                           "done": len([b for b in boxes if b[0].lower() == "x"])})
    return milestones


def plan_summary(repo):
    ms = parse_plan(repo)
    if not ms:
        return None
    return {"milestones": len(ms),
            "milestones_done": len([m for m in ms if m["total"] and m["done"] == m["total"]]),
            "tasks": sum(m["total"] for m in ms),
            "tasks_done": sum(m["done"] for m in ms)}


def check_plan(repo):
    """Stage 6: is there a plan a fresh session can see progress against?"""
    ms = parse_plan(repo)
    if ms is None:
        return [warn("plan", "no %s" % PLAN,
                     "a long task needs milestones and checkboxes, or 'how far "
                     "along' is an opinion")]
    if not ms:
        return [warn("plan", "the plan has no milestones",
                     "one '## ' heading per milestone, '- [ ]' per task")]
    out = [ok("plan", "%d milestone(s), %d task(s)"
              % (len(ms), sum(m["total"] for m in ms)))]
    empty = [m["title"] for m in ms if not m["total"]]
    if empty:
        out.append(warn("plan", "milestone(s) with no tasks: %s"
                        % ", ".join(empty[:3]),
                        "a milestone without tasks cannot be started or finished"))
    summary = plan_summary(repo)
    if summary and summary["tasks"] and summary["tasks_done"] == summary["tasks"]:
        out.append(warn("plan", "every task is checked off",
                        "release it or add the next milestone - an empty plan is "
                        "how a long task quietly ends"))
    return out


# -- the handoff -----------------------------------------------------------

def check_thread_structure(repo):
    """Stage 6: the handoff must be usable, not merely present."""
    rel, text = read(repo, CURRENT)
    if not text or not text.strip():
        return []
    have = headings(text)
    out = []
    missing = [s for s in THREAD_SECTIONS
               if not any(h.startswith(s) for h in have)]
    if missing:
        out.append(warn("thread:sections",
                        "%s is missing %s" % (CURRENT, ", ".join(missing)),
                        "a handoff without Next is a diary, not a handoff"))
    nxt = _section_body(text, "next")
    if nxt and not _bullets(nxt):
        out.append(warn("thread:next", "the Next section has no concrete item",
                        "name the next action, with a verb"))
    return out


def resume_text(repo, stages):
    """The handoff view: state, last compaction, recent log."""
    lines = []
    rel, text = read(repo, CURRENT)
    if text and text.strip():
        lines.append(text.strip())
    else:
        lines.append("No %s yet. Create it with Goal / Done / Next / Blockers - "
                     "it is what a fresh session reads first." % CURRENT)
    summary = plan_summary(repo)
    if summary:
        lines.append("")
        lines.append("## Plan")
        lines.append("")
        lines.append("%d/%d milestones, %d/%d tasks done."
                     % (summary["milestones_done"], summary["milestones"],
                        summary["tasks_done"], summary["tasks"]))
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
    """A periodic summary drafted from what is checkable, gaps left blank."""
    stamp = time.strftime("%Y-%m-%d")
    passed = len([s for s in stages if s["state"] == "passed"])
    summary = plan_summary(repo)
    lines = ["# Status report - %s" % stamp, "",
             "%d/%d stages pass." % (passed, len(stages))]
    if summary:
        lines.append("%d/%d milestones, %d/%d tasks done."
                     % (summary["milestones_done"], summary["milestones"],
                        summary["tasks_done"], summary["tasks"]))
    lines += ["", "## Stage state", ""]
    for s in stages:
        lines.append("- **%s** - %s" % (s["title"], s["state"]))
    if requirements:
        lines += ["", "## Requirements", "",
                  "%d registered, %d verified."
                  % (len(requirements),
                     len([r for r in requirements if r.get("status") == "verified"]))]
        for r in [r for r in requirements if r.get("status") != "verified"][:10]:
            lines.append("- %s (%s) %s" % (r.get("id"), r.get("status"),
                                           r.get("title", "")))
    if corpus:
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


# -- compaction ------------------------------------------------------------

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
    lines = ["# Snapshot %s%s" % (time.strftime("%Y-%m-%d %H:%M"),
                                 (" (%s)" % trigger) if trigger else ""), "",
             "- stages: %d/%d pass" % (passed, len(stages)),
             "- blocked: %s" % (", ".join(s["title"] for s in blocked) or "none"),
             "- working tree: %d changed file(s)" % changed]
    summary = plan_summary(repo)
    if summary:
        lines.append("- plan: %d/%d milestones, %d/%d tasks"
                     % (summary["milestones_done"], summary["milestones"],
                        summary["tasks_done"], summary["tasks"]))
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
    """Keep the newest MAX_SNAPSHOTS by mtime - deleting the file just written
    is the one failure that matters."""
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
    snaps = snapshots(repo)
    if not snaps:
        return None, None
    path = max(snaps, key=os.path.getmtime)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return path, f.read()
    except OSError:
        return None, None


def cadence(repo):
    """Compactions since the last written report: work running on memory."""
    snaps = snapshots(repo)
    reps = reports(repo)
    if not snaps:
        return 0
    if not reps:
        return len(snaps)
    newest_report = max(os.path.getmtime(p) for p in reps)
    return len([p for p in snaps if os.path.getmtime(p) > newest_report])


def check_cadence(repo):
    n = cadence(repo)
    if n >= 3:
        return [warn("cadence", "%d compaction(s) since the last status report" % n,
                     "`lifecycle report` - what happened in those sessions is "
                     "already gone")]
    if n:
        return [ok("cadence", "%d compaction(s) since the last report" % n)]
    return []


# -- stage 6 ---------------------------------------------------------------

def check_review(repo):
    """A review note cannot prove quality - but a project that never records one
    has not looked, and a first review with no findings is a rubber stamp."""
    files = _files(repo, REVIEW_DIR)
    if not files:
        return [warn("review", "no review note in %s/" % REVIEW_DIR,
                     "record an adversarial review: what you tried to break, what "
                     "broke, what you decided to live with")]
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
    findings = _bullets(body)
    if not findings:
        return [warn("review", "the last review has no findings",
                     "a review that found nothing did not look; name at least one "
                     "thing you would change")]
    return [ok("review", "%d finding(s) in %s"
               % (len(findings), os.path.relpath(newest, repo).replace("\\", "/")))]


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
    chars, _ = context_load(repo)
    if chars > CONTEXT_BUDGET_CHARS:
        out.append(warn("thread:context",
                        "%d chars (~%dk tokens) load before any work starts"
                        % (chars, chars // 4000),
                        "move detail out of the always-loaded docs into references; "
                        "`corpus find` shows what already covers it"))
    else:
        out.append(ok("thread:context", "~%dk tokens of project docs" % (chars // 4000)))
    return out


def scaffold(repo):
    """Create the thread files a long task needs. Never overwrites."""
    created = []
    templates = {
        CURRENT: ("# Current work\n\n## Goal\n\n\n## Done\n\n- \n\n"
                  "## Next\n\n- \n\n## Blockers\n\nNone.\n"),
        PLAN: ("# Plan\n\n## M1 - first milestone\n\n- [ ] first task\n"
               "- [ ] second task\n"),
    }
    for rel, text in templates.items():
        path = os.path.join(repo, rel)
        if os.path.exists(path):
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        created.append(rel)
    for d in (LOG_DIR, REPORT_DIR, REVIEW_DIR, SNAP_DIR):
        path = os.path.join(repo, d)
        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)
            created.append(d + "/")
    return created
