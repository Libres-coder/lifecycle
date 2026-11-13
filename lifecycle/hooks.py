"""lifecycle hooks: make the thread automatic instead of remembered.

Two Claude Code hooks, installed into the *project's* `.claude/settings.json`:

    PreCompact      run `lifecycle snapshot` before the context is compacted,
                    so the state is written down while it still exists
    SessionStart    run `lifecycle resume` when a session starts or resumes, so
    (compact|resume) the first thing in context is the work thread

Project-level settings, not the user's global file: they belong to the project
that has a work thread, and they do not collide with whatever manages the
global config.
"""
import json
import os

SETTINGS = os.path.join(".claude", "settings.json")
SNAPSHOT_CMD = "lifecycle snapshot --hook"
RESUME_CMD = "lifecycle resume"
SNAPSHOT_CMD_MODULE = "python -m lifecycle snapshot --hook"
RESUME_CMD_MODULE = "python -m lifecycle resume"


def _commands():
    """Prefer the console script; fall back to -m when only the module exists."""
    import shutil as _shutil
    if _shutil.which("lifecycle"):
        return SNAPSHOT_CMD, RESUME_CMD
    return SNAPSHOT_CMD_MODULE, RESUME_CMD_MODULE
HOOKS = [("PreCompact", "", SNAPSHOT_CMD),
         ("SessionStart", "compact|resume", RESUME_CMD)]


def _hooks():
    snap, resume = _commands()
    return [("PreCompact", "", snap), ("SessionStart", "compact|resume", resume)]


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


def installed(repo):
    data = load(repo)
    if data is None:
        return {}
    hooks = data.get("hooks") or {}
    out = {}
    for event, _matcher, cmd in _hooks():
        out[event] = any(cmd in _entry_commands(e) for e in hooks.get(event, []))
    return out


def install(repo):
    data = load(repo)
    if data is None:
        return False, "cannot read %s - fix the JSON first" % SETTINGS
    hooks = data.setdefault("hooks", {})
    added = []
    for event, matcher, cmd in _hooks():
        entries = hooks.setdefault(event, [])
        if any(cmd in _entry_commands(e) for e in entries):
            continue
        entry = {"hooks": [{"type": "command", "command": cmd}]}
        if matcher:
            entry["matcher"] = matcher
        entries.append(entry)
        added.append("%s -> %s" % (event, cmd))
    if not added:
        return True, "already installed in %s" % SETTINGS
    save(repo, data)
    return True, "installed in %s: %s" % (SETTINGS, "; ".join(added))


def uninstall(repo):
    data = load(repo)
    if data is None:
        return False, "cannot read %s" % SETTINGS
    hooks = data.get("hooks") or {}
    removed = []
    for event, _matcher, cmd in _hooks():
        entries = hooks.get(event) or []
        keep = []
        for e in entries:
            cmds = _entry_commands(e)
            if cmd in cmds:
                removed.append("%s -> %s" % (event, cmd))
                rest = [h for h in e.get("hooks", []) if h.get("command") != cmd]
                if rest:
                    e = dict(e, hooks=rest)
                    keep.append(e)
                continue
            keep.append(e)
        if keep:
            hooks[event] = keep
        else:
            hooks.pop(event, None)
    if not removed:
        return True, "nothing to remove from %s" % SETTINGS
    if not hooks:
        data.pop("hooks", None)
    save(repo, data)
    return True, "removed from %s: %s" % (SETTINGS, "; ".join(removed))


def status(repo):
    state = installed(repo)
    if load(repo) is None:
        return "cannot read %s" % SETTINGS
    if not any(state.values()):
        return "not installed (%s)" % SETTINGS
    return ", ".join("%s: %s" % (e, "on" if state.get(e) else "off")
                     for e, _m, _c in _hooks()) + " (%s)" % SETTINGS
