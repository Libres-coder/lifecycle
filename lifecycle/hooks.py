"""lifecycle hooks: make the thread automatic instead of remembered.

Two Claude Code hooks, installed into the *project's* `.claude/settings.json`:

    PreCompact          run `lifecycle snapshot` before the context is compacted,
                        so the state is written down while it still exists
    SessionStart        run `lifecycle resume` when a session starts, resumes or
    (startup|compact|   comes back from a compaction, so the first thing in
     resume)            context is the work thread

Project-level settings, not the user's global file: they belong to the project
that has a work thread, and they do not collide with whatever manages the
global config.

The command written into the hook must actually run in the user's shell, which
is a different environment from the one that ran `hook install`. So it is built
from the interpreter that can import this package, fully quoted, and falls back
to the console script; if neither resolves, install refuses rather than writing
a hook that exits 127.
"""
import json
import os
import re
import shlex
import subprocess
import sys

SETTINGS = os.path.join(".claude", "settings.json")
# A command of ours ends at the subcommand; the legacy forms (before --hook
# existed) have nothing after it.
LEGACY = re.compile(r"lifecycle(?:\.exe)?\s+(snapshot|resume)\s*$")


def _kind(cmd):
    """Which lifecycle subcommand a hook command runs, or None if it is not ours.

    Matched on a word boundary: `~/bin/lifecycle-resume.sh` is someone else's
    script, and claiming it would also make `uninstall` delete it.
    """
    if not isinstance(cmd, str):
        return None
    tail = r"\s+(snapshot|resume|statusline)(?=[\s\"']|$)"
    m = re.search(r"(?:^|[\\/\s\"'])lifecycle(?:\.exe)?" + tail, cmd)
    if not m:
        m = re.search(r"-m\s+lifecycle" + tail, cmd)
    return m.group(1) if m else None


def _runs(python, module="lifecycle"):
    try:
        p = subprocess.run([python, "-c", "import %s" % module],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=30)
    except (OSError, subprocess.SubprocessError):
        return False
    return p.returncode == 0


def _command(args):
    """A command line that works in the user's shell, not just this process.

    The console script first, because it is portable between machines; the
    interpreter's absolute path only as a fallback, and it is machine-specific -
    a committed settings file should not carry one if it can be avoided.
    """
    import shutil
    if shutil.which("lifecycle"):
        # bare name, not the resolved path: the settings file is committed and
        # must not carry this machine's install location
        return "lifecycle %s" % args
    python = sys.executable or "python"
    if _runs(python):
        return "%s -m lifecycle %s" % (shlex.quote(python), args)
    return None


def snapshot_command():
    return _command("snapshot --hook")


def statusline_command():
    return _command("statusline")


def resume_command():
    return _command("resume --hook")


def _hooks():
    snap, resume = snapshot_command(), resume_command()
    if not snap or not resume:
        return None
    return [("PreCompact", "", snap),
            ("SessionStart", "startup|resume|compact", resume)]


def _path(repo):
    return os.path.join(repo, SETTINGS)


def load(repo):
    try:
        with open(_path(repo), encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}
    except (OSError, ValueError):
        return None                      # refuse to touch an unreadable file
    return data if isinstance(data, dict) else None


def save(repo, data):
    os.makedirs(os.path.dirname(_path(repo)), exist_ok=True)
    tmp = _path(repo) + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, _path(repo))


def _entry_commands(entry):
    return [h.get("command") for h in entry.get("hooks", [])
            if isinstance(h, dict)]


def _all_commands(hooks, event):
    """Every lifecycle command installed for an event, whatever form it took."""
    out = []
    for e in (hooks.get(event) or []):
        for c in _entry_commands(e):
            if _kind(c):
                out.append(c)
    return out


def installed(repo):
    data = load(repo)
    if data is None:
        return {}
    hooks = data.get("hooks") or {}
    return {"PreCompact": bool(_all_commands(hooks, "PreCompact")),
            "SessionStart": bool(_all_commands(hooks, "SessionStart"))}


def install(repo):
    hooks_spec = _hooks()
    if hooks_spec is None:
        return False, ("cannot build a hook command that runs here: the package "
                       "is not importable by %s and no `lifecycle` script is on "
                       "PATH - install it first" % (sys.executable or "python"))
    data = load(repo)
    if data is None:
        return False, "cannot read %s - fix the JSON first" % SETTINGS
    hooks = data.setdefault("hooks", {})
    added, warnings = [], []
    for event, matcher, cmd in hooks_spec:
        entries = hooks.setdefault(event, [])
        ours = [(e, h) for e in entries
                for h in e.get("hooks", []) if isinstance(h, dict)]
        ours = [(e, h) for e, h in ours if _kind(h.get("command"))]
        if ours:
            upgraded = False
            for _, h in ours:
                if LEGACY.match(h.get("command") or "") \
                        and _kind(h["command"]) == _kind(cmd):
                    h["command"] = cmd      # the pre-1.2.0 form knows nothing of --hook
                    upgraded = True
            if upgraded:
                added.append("%s -> upgraded to %s" % (event, cmd))
            continue                     # one lifecycle entry per event is enough
        entry = {"hooks": [{"type": "command", "command": cmd}]}
        if matcher:
            entry["matcher"] = matcher
        entries.append(entry)
        added.append("%s -> %s" % (event, cmd))
    sl = statusline_command()
    if sl:
        current = data.get("statusLine")
        cur_cmd = (current or {}).get("command") if isinstance(current, dict) else None
        if current is None:
            data["statusLine"] = {"type": "command", "command": sl}
            added.append("statusLine -> %s" % sl)
        elif _kind(cur_cmd) != "statusline":
            warnings.append(
                "statusLine left alone - it is already %r; the context reading "
                "needs `lifecycle statusline` to run, so add that to the existing "
                "command or remove it" % (cur_cmd,))
    if not added and not warnings:
        return True, "already installed in %s" % SETTINGS
    if added:
        save(repo, data)
    msg = ("installed in %s: %s" % (SETTINGS, "; ".join(added)) if added
           else "no hook changed in %s" % SETTINGS)
    if warnings:
        msg += ". Warning: " + " ".join(warnings)
    return True, msg


def uninstall(repo):
    data = load(repo)
    if data is None:
        return False, "cannot read %s" % SETTINGS
    hooks = data.get("hooks") or {}
    removed = []
    for event in ("PreCompact", "SessionStart"):
        entries = hooks.get(event) or []
        keep = []
        for e in entries:
            ours = [h.get("command") for h in e.get("hooks", [])
                    if isinstance(h, dict) and _kind(h.get("command"))]
            if not ours:
                keep.append(e)
                continue
            removed.append("%s -> %s" % (event, ", ".join(ours)))
            rest = [h for h in e.get("hooks", [])
                    if not (isinstance(h, dict) and _kind(h.get("command")))]
            if rest:
                keep.append(dict(e, hooks=rest))
        if keep:
            hooks[event] = keep
        else:
            hooks.pop(event, None)
    sl = data.get("statusLine")
    if isinstance(sl, dict) and _kind(sl.get("command")) == "statusline":
        data.pop("statusLine", None)
        removed.append("statusLine")
    if not removed:
        return True, "nothing to remove from %s" % SETTINGS
    if not hooks:
        data.pop("hooks", None)
    save(repo, data)
    return True, "removed from %s: %s" % (SETTINGS, "; ".join(removed))


def status(repo):
    if load(repo) is None:
        return "cannot read %s" % SETTINGS
    state = installed(repo)
    if not any(state.values()):
        return "not installed (%s)" % SETTINGS
    sl_data = (load(repo) or {}).get("statusLine")
    sl = "on" if isinstance(sl_data, dict) and _kind(sl_data.get("command")) == "statusline" else "off"
    return ", ".join(["%s: %s" % (e, "on" if state.get(e) else "off")
                      for e in ("PreCompact", "SessionStart")] + ["statusLine: " + sl])         + " (%s)" % SETTINGS
