"""lifecycle report: the stage table, the blockers, and the one next action.

No state is stored. A stage passes because the repository says so right now,
not because someone ran `lifecycle pass` yesterday - a gate record that can go
stale is a gate people stop trusting.
"""
import time

STATE_MARK = {"passed": "PASS", "flagged": "WARN", "failed": "FAIL",
              "skipped": "SKIP"}


def summary(stages):
    passed = len([s for s in stages if s["state"] == "passed"])
    return passed, len(stages)


def blockers(stage):
    return [r for r in stage["results"] if r["required"] and not r["ok"]]


def next_action(stages):
    for stage in stages:
        bad = blockers(stage)
        if bad:
            return stage, bad[0]
    return None, None


def render(repo, stages):
    passed, total = summary(stages)
    pack = next((s.get("pack") for s in stages if s.get("pack")), None)
    lines = ["# lifecycle (%s)" % repo,
             "%d/%d stages pass%s" % (passed, total,
                                      ("  ·  pack: %s" % pack) if pack else ""), "",
             "| # | stage | state | what the stage asks |",
             "|---|---|---|---|"]
    for s in stages:
        detail = s["question"]
        bad = blockers(s)
        if bad:
            detail = bad[0]["detail"]
        lines.append("| %d | %s | **%s** | %s |"
                     % (s["id"], s["title"], STATE_MARK[s["state"]], detail))
    blocked = [s for s in stages if s["state"] == "failed"]
    if blocked:
        lines.append("")
        lines.append("## Blocked")
        for s in blocked:
            lines.append("**Stage %d %s**" % (s["id"], s["title"]))
            for r in blockers(s)[:4]:
                lines.append("- %s: %s" % (r["name"], r["detail"]))
                lines.append("  - %s" % r["fix"])
            if len(blockers(s)) > 4:
                lines.append("- ... and %d more" % (len(blockers(s)) - 4))
    stage, item = next_action(stages)
    lines.append("")
    if stage is None or item is None:
        flagged = [(s, r) for s in stages for r in s["results"]
                   if not r["required"] and not r["ok"]]
        if flagged:
            lines.append("Every stage passes, with %d advisory warning(s) below."
                         % len(flagged))
        else:
            lines.append("Every stage passes. The next change is a new requirement, "
                         "not a new document.")
    else:
        lines.append("## Next")
        lines.append("Stage %d %s: **%s** - %s"
                     % (stage["id"], stage["title"], item["name"], item["detail"]))
        lines.append("")
        lines.append("    " + item["fix"])
    flagged = [(s, r) for s in stages for r in s["results"]
               if not r["required"] and not r["ok"]]
    if flagged:
        lines.append("")
        lines.append("## Not blocking")
        for s, r in flagged:
            lines.append("- stage %d %s: %s - %s" % (s["id"], s["title"], r["detail"],
                                                     r["fix"]))
    lines.append("")
    lines.append("_%s_" % time.strftime("%Y-%m-%d %H:%M"))
    return "\n".join(lines)


def as_json(stages):
    return [{"id": s["id"], "key": s["key"], "title": s["title"], "state": s["state"],
             "blocking": [{"name": r["name"], "detail": r["detail"], "fix": r["fix"]}
                          for r in blockers(s)],
             "flagged": [{"name": r["name"], "detail": r["detail"], "fix": r["fix"]}
                         for r in s["results"]
                         if not r["required"] and not r["ok"]]}
            for s in stages]
