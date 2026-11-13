"""lifecycle statusline: the one place Claude Code tells a program the context usage.

A hook never receives the live context percentage, but the statusline payload
does (`context_window.used_percentage`, `remaining_percentage`,
`total_input_tokens`). So `lifecycle statusline` is installed as the statusline
command: it renders a short line, and writes the payload to
`.lifecycle/context.json`, where `status` and `resume` read it.

That closes the loop the hooks cannot: before a compaction the snapshot knows
how full the window was, and during a session the agent can be told.

Reference: Claude Code statusline payload (code.claude.com/docs/en/statusline).
"""
import json
import os
import time

CTX_FILE = os.path.join(".lifecycle", "context.json")
FRESH_MINUTES = 10
WARN_PERCENT = 85


def parse(text):
    try:
        data = json.loads(text or "{}")
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    ctx = data.get("context_window") or {}
    if not isinstance(ctx, dict):
        ctx = {}
    model = data.get("model") or {}
    return {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "session": data.get("session_name") or data.get("session_id") or "",
        "model": model.get("display_name") or model.get("id") or "",
        "cwd": data.get("cwd") or "",
        "used_percentage": ctx.get("used_percentage"),
        "remaining_percentage": ctx.get("remaining_percentage"),
        "context_window_size": ctx.get("context_window_size"),
        "total_input_tokens": ctx.get("total_input_tokens"),
        "total_output_tokens": ctx.get("total_output_tokens"),
    }


def save(repo, payload):
    path = os.path.join(repo, CTX_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return path


def last(repo):
    """(payload, age_seconds) or (None, None)."""
    path = os.path.join(repo, CTX_FILE)
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        age = time.time() - os.path.getmtime(path)
    except (OSError, ValueError):
        return None, None
    return (data if isinstance(data, dict) else None), age


def staleness_line(repo):
    """One line for status/resume, or '' when nothing recent was recorded."""
    data, age = last(repo)
    if not data or data.get("used_percentage") is None:
        return ""
    mins = int(age // 60) if age is not None else 0
    if age is not None and age > FRESH_MINUTES * 60:
        return "context: %d%% (as of %d min ago - install the statusline hook to keep it current)" \
               % (data["used_percentage"], mins)
    return "context: %d%% used" % data["used_percentage"]


def render(repo):
    """The status line itself: cheap enough to run on every UI render."""
    from . import threads

    parts = []
    try:
        rows = threads.describe(repo)
    except Exception:
        rows = []
    if rows:
        active = max(rows, key=lambda r: r["mtime"] or 0)
        parts.append(active["slug"])
        if active.get("plan"):
            parts.append("%d/%d" % (active["plan"]["done"], active["plan"]["total"]))
    data, _ = last(repo)
    if data and data.get("used_percentage") is not None:
        parts.append("%d%% ctx" % data["used_percentage"])
    return " · ".join(parts) or "lifecycle"
