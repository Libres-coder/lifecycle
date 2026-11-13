"""lifecycle threads: more than one line of work at a time.

One `docs/work/current.md` is one handoff. A project with two workstreams - the
game and its tooling, a feature and a migration - needs one per stream, plus a
way to see them together and to say who is on which.

    docs/work/threads/<slug>/current.md   that thread's handoff
    docs/work/threads/<slug>/plan.md      that thread's milestones
    docs/work/threads/<slug>/owner        "name @ 2026-11-13T20:00:00"

The flat `docs/work/current.md` stays the portfolio: what the effort as a whole
is doing now. Threads are optional; without `threads/` everything behaves as a
single line of work.
"""
import os
import re
import time

from . import thread as threadmod

THREADS_DIR = "docs/work/threads"
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,40}$")
CLAIM_HOURS = 24

CURRENT_TEMPLATE = ("# Thread: {title}\n\n## Goal\n\n\n## Done\n\n- \n\n"
                    "## Next\n\n- \n\n## Blockers\n\nNone.\n")
PLAN_TEMPLATE = "# Plan - {title}\n\n## M1 - first milestone\n\n- [ ] first task\n"


def warn(name, detail, fix):
    return {"name": name, "ok": False, "detail": detail, "fix": fix, "required": False}


def ok(name, detail):
    return {"name": name, "ok": True, "detail": detail, "required": False}


def root(repo):
    return os.path.join(repo, THREADS_DIR)


def list_threads(repo):
    d = root(repo)
    if not os.path.isdir(d):
        return []
    out = []
    for name in sorted(os.listdir(d)):
        path = os.path.join(d, name)
        if not os.path.isdir(path) or name.startswith("."):
            continue
        out.append({"slug": name, "path": path,
                    "current": os.path.join(path, "current.md"),
                    "plan": os.path.join(path, "plan.md"),
                    "owner_file": os.path.join(path, "owner")})
    return out


def owner(repo, slug):
    path = os.path.join(root(repo), slug, "owner")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()
    except OSError:
        return ""


def claim(repo, slug, who):
    t = _find(repo, slug)
    if t is None:
        return False, "no thread %r (create it with `lifecycle thread new %s`)" % (slug, slug)
    with open(t["owner_file"], "w", encoding="utf-8", newline="\n") as f:
        f.write("%s @ %s\n" % (who, time.strftime("%Y-%m-%dT%H:%M:%S")))
    return True, "%s is on %s" % (who, slug)


def release(repo, slug):
    t = _find(repo, slug)
    if t is None:
        return False, "no thread %r" % slug
    try:
        os.remove(t["owner_file"])
    except OSError:
        return True, "%s had no owner" % slug
    return True, "%s released" % slug


def _find(repo, slug):
    for t in list_threads(repo):
        if t["slug"] == slug:
            return t
    return None


def create(repo, slug, title=""):
    slug = str(slug or "").strip().lower()
    if not SLUG_RE.match(slug):
        return False, "slug must be lowercase letters, digits and dashes: %r" % slug
    d = os.path.join(root(repo), slug)
    if os.path.isdir(d):
        return False, "thread %s already exists" % slug
    os.makedirs(os.path.join(d, "log"), exist_ok=True)
    title = title or slug
    with open(os.path.join(d, "current.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(CURRENT_TEMPLATE.format(title=title))
    with open(os.path.join(d, "plan.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(PLAN_TEMPLATE.format(title=title))
    return True, "created %s/%s" % (THREADS_DIR, slug)


def _next_item(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
    except OSError:
        return ""
    body = threadmod._section_body(text, "next")
    for line in body.splitlines():
        if re.match(r"^\s*[-*]\s+\S", line):
            return line.strip()[2:].strip()
    return ""


def _plan_progress(path):
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    boxes = threadmod.CHECKBOX_RE.findall(text)
    if not boxes:
        return None
    return {"total": len(boxes), "done": len([b for b in boxes if b[0].lower() == "x"])}


def summary(repo, t):
    """One row per thread: who owns it, how far along, is its handoff current."""
    current = t["current"]
    exists = os.path.isfile(current)
    mtime = os.path.getmtime(current) if exists else 0.0
    changed = threadmod.newest_source_change(repo)
    fresh = bool(exists) and mtime and threadmod.file_change_time(repo, os.path.relpath(
        current, repo).replace("\\", "/")) >= changed - 1
    return {"slug": t["slug"], "exists": exists, "fresh": fresh,
            "owner": owner(repo, t["slug"]),
            "next": _next_item(current) if exists else "",
            "plan": _plan_progress(t["plan"]) if os.path.isfile(t["plan"]) else None,
            "mtime": mtime}


def describe(repo):
    return [summary(repo, t) for t in list_threads(repo)]


def check(repo):
    """Advisory checks for the thread set."""
    rows = list(list_threads(repo))
    if not rows:
        return []
    out = []
    missing = [r["slug"] for r in rows if not os.path.isfile(r["current"])]
    if missing:
        out.append(warn("threads:missing", "thread(s) without current.md: %s"
                        % ", ".join(missing),
                        "each thread needs its own handoff file"))
    owners = {}
    stale = []
    for r in rows:
        who = owner(repo, r["slug"])
        if not who:
            continue
        name, _, stamp = who.partition(" @ ")
        owners.setdefault(name.strip(), []).append(r["slug"])
        try:
            when = time.mktime(time.strptime(stamp.strip(), "%Y-%m-%dT%H:%M:%S"))
        except (ValueError, OverflowError):
            continue
        if (time.time() - when) / 3600 > CLAIM_HOURS:
            stale.append(r["slug"])
    shared = ["%s (%s)" % (n, ", ".join(s)) for n, s in owners.items() if len(s) > 1]
    if shared:
        out.append(warn("threads:owners", "one owner on several threads: %s"
                        % "; ".join(shared),
                        "split the work or close a thread - one agent cannot keep "
                        "two handoffs current"))
    if stale:
        out.append(warn("threads:claims", "claim(s) older than %dh: %s"
                        % (CLAIM_HOURS, ", ".join(stale)),
                        "release or refresh the claim; a stale owner hides that a "
                        "thread is free"))
    if not out:
        out.append(ok("threads", "%d thread(s)" % len(rows)))
    return out
