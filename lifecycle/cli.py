"""lifecycle CLI.

  lifecycle status [--json]        where the project is, stage by stage
  lifecycle next                   the one blocking thing, with the command to fix it
  lifecycle check [--stage N]      exit 1 on a failing stage (all stages by default)
  lifecycle stages                 the contract: what each stage requires

Exit codes: 0 ok, 1 a stage fails, 2 usage.
"""
import argparse
import json
import os
import sys

from . import contract, hooks, packs, playbooks, report, statusline, thread, threads


def _context_hint(repo):
    data, age = statusline.last(repo)
    pct = (data or {}).get("used_percentage")
    if pct is None:
        return ""
    if age is not None and age > statusline.FRESH_MINUTES * 60:
        return ("last context reading was %d min ago (%d%%); it is not live - "
                "the status line is what keeps it current" % (age // 60, pct))
    trigger = statusline.trigger()
    nudge, warn = statusline.thresholds(trigger)
    if not statusline.auto_enabled():
        if pct >= nudge:
            return ("Context at %d%%; auto-compact is disabled, so nothing will "
                    "shrink this window by itself: run /compact when this step "
                    "ends - afterwards `lifecycle resume` brings the thread back."
                    % pct)
        return ""
    if pct >= warn:
        return ("Context at %d%% (auto-compact fires at %d%%): run /compact now - "
                "afterwards `lifecycle resume` brings the thread back. "
                "A snapshot is written first, so nothing is lost."
                % (pct, trigger))
    if pct >= nudge:
        return ("Context at %d%%: fine for the current step; run /compact before "
                "starting a new thread (auto-compact fires at %d%%)."
                % (pct, trigger))
    return ""


def _initialized(repo):
    """Has this repository actually been set up? A SessionStart hook runs in
    whatever folder the session opened, and nagging there is noise. An empty
    .projtruth/ left by a probe does not count."""
    if os.path.exists(os.path.join(repo, "docs", "work")):
        return True
    if os.path.isdir(os.path.join(repo, ".lifecycle", "snapshots")):
        return True
    req = os.path.join(repo, ".projtruth", "requirements.json")
    try:
        import json as _json
        with open(req, encoding="utf-8-sig") as f:
            data = _json.load(f)
        return bool(isinstance(data, dict) and data.get("requirements"))
    except (OSError, ValueError):
        return False


def _find_root(start):
    """Running `lifecycle` from src/ should find the project, not fail on docs/."""
    path = os.path.abspath(start)
    while True:
        if any(os.path.exists(os.path.join(path, m))
               for m in (".git", ".projtruth", ".lifecycle")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return os.path.abspath(start)
        path = parent


def _utf8():
    rec = getattr(sys.stdout, "reconfigure", None)
    if rec:
        try:
            rec(encoding="utf-8")
        except Exception:
            pass


def _stages(repo):
    return contract.evaluate(repo)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="lifecycle")
    ap.add_argument("--repo", default=None,
                    help="project root (default: nearest ancestor with .git or "
                         ".projtruth, else cwd)")
    ap.add_argument("--pack", default="auto",
                    help="domain pack: auto (detect), game, story, or none")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    sub.add_parser("statusline")
    p = sub.add_parser("status")
    p.add_argument("--json", action="store_true")
    sub.add_parser("next")
    sub.add_parser("suggest")
    p = sub.add_parser("check")
    p.add_argument("--stage", type=int, default=None,
                   help="assert one stage (default: every stage)")
    p.add_argument("--json", action="store_true")
    sub.add_parser("stages")
    p = sub.add_parser("resume")
    p.add_argument("--thread", default=None, help="resume one named thread")
    p.add_argument("--hook", action="store_true",
                   help="read the hook payload from stdin (records context_tokens)")
    p = sub.add_parser("thread")
    p.add_argument("action", choices=["new", "claim", "release", "list"])
    p.add_argument("slug", nargs="?")
    p.add_argument("--title", default="")
    p.add_argument("--as", dest="who", default="")
    sub.add_parser("report")
    p = sub.add_parser("snapshot")
    p.add_argument("--hook", action="store_true",
                   help="read the hook payload from stdin and stay silent")
    p = sub.add_parser("hook")
    p.add_argument("action", choices=["install", "uninstall", "status"])
    p = sub.add_parser("guide")
    p.add_argument("stage", nargs="?",
                   help="stage number or name, or a pack name (game, story); "
                        "default: the stage that is blocking")
    p = sub.add_parser("pack")
    p.add_argument("action", choices=["list", "init", "guide"])
    p.add_argument("name", nargs="?")

    args = ap.parse_args(argv)
    _utf8()
    repo = os.path.abspath(args.repo) if args.repo else _find_root(os.getcwd())
    if not os.path.isdir(repo):
        sys.stderr.write("lifecycle: --repo is not a directory: %s\n" % repo)
        return 2

    if args.cmd == "init":
        created = thread.scaffold(repo)
        if created:
            print("created: %s" % ", ".join(created))
        else:
            print("already initialized")
        print("")
        print("Next: fill docs/work/current.md (Goal / Done / Next / Blockers), "
              "then `lifecycle hook install`.")
        return 0

    if args.cmd == "pack":
        # Before evaluation: `pack list` must work even when --pack names a pack
        # that does not exist - listing is how you find that out.
        return _pack(repo, args)

    try:
        stages = contract.evaluate(repo, args.pack)
    except ValueError as e:
        sys.stderr.write("lifecycle: %s" % e)
        sys.stderr.write("\n")
        return 2

    if args.cmd == "status":
        if args.json:
            print(json.dumps(report.as_json(stages), ensure_ascii=False, indent=2))
        else:
            print(report.render(repo, stages, threads=threads.describe(repo),
                                context=statusline.staleness_line(repo)))
        return 0

    if args.cmd == "next":
        stage, item = report.next_action(stages)
        if stage is None or item is None:
            print("Every stage passes - nothing is blocking.")
            return 0
        print("stage %d %s: %s" % (stage["id"], stage["title"], item["detail"]))
        print("  fix: %s" % item["fix"])
        return 0

    if args.cmd == "check":
        return _check(stages, args)

    if args.cmd == "suggest":
        return _suggest(repo, stages)

    if args.cmd == "thread":
        return _thread(repo, args)

    if args.cmd == "resume":
        if getattr(args, "hook", False) and not _initialized(repo):
            return 0                    # a hook in an unrelated folder must be quiet
        if getattr(args, "hook", False):
            try:
                payload = json.loads(sys.stdin.read() or "{}")
            except ValueError:
                payload = {}
            tokens = payload.get("context_tokens")
            if isinstance(tokens, int) and not isinstance(tokens, bool) and tokens > 0:
                prev, _ = statusline.last(repo)
                row = dict(prev or {})
                row.update({"at": __import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
                            "session": payload.get("session_id") or row.get("session", ""),
                            "total_input_tokens": tokens,
                            "source": payload.get("source") or ""})
                # A token count says nothing about how full the window is, and a
                # new session is not the one the old percentage was measured in.
                # Keeping it would show yesterday's 94% as today's reading.
                row["used_percentage"] = None
                row["remaining_percentage"] = None
                statusline.save(repo, row)
        if getattr(args, "thread", None):
            t = threads._find(repo, args.thread)
            if t is None:
                sys.stderr.write("lifecycle: no thread %r" % args.thread)
                sys.stderr.write(chr(10))
                return 2
            rel = os.path.relpath(t["current"], repo).replace("\\", "/")
            _, text = thread.read(repo, rel)
            print(text.strip() if text else "(%s is empty)" % rel)
            return 0
        stage, item = report.next_action(stages)
        if stage is not None and item is not None:
            print("Lifecycle: stage %d %s - %s" % (stage["id"], stage["title"],
                                                   item["detail"]))
            print("  fix: %s" % item["fix"])
            print("")
        ctx = statusline.staleness_line(repo)
        if ctx:
            print(ctx)
            print("")
        hint = _context_hint(repo)
        if hint and not (ctx and "min ago" in ctx):   # the stale line already said it
            print("")
            print(hint)
        print(thread.resume_text(repo, stages))
        rows = threads.describe(repo)
        if rows:
            print("")
            print("## Threads")
            for t in rows:
                plan = ("%d/%d tasks" % (t["plan"]["done"], t["plan"]["total"])
                        if t["plan"] else "no plan")
                print("- **%s** (%s) - %s - next: %s"
                      % (t["slug"], t["owner"].split(" @ ")[0] or "unclaimed",
                         plan, t["next"] or "nothing named"))
        return 0

    if args.cmd == "report":
        reqs = contract.run_json(repo, "projtruth", ["report", "--json"])
        docs = contract.run_json(repo, "corpus", ["report", "--json"])
        text = thread.report_text(repo, stages, requirements=reqs, corpus=docs)
        path = thread.write_report(repo, text)
        print("wrote %s" % os.path.relpath(path, repo).replace("\\", "/"))
        return 0

    if args.cmd == "statusline":
        payload = statusline.parse(sys.stdin.read())
        if payload.get("used_percentage") is not None:
            statusline.save(repo, payload)
        print(statusline.render(repo))
        return 0

    if args.cmd == "snapshot":
        transcript, trigger = None, ""
        if args.hook:
            try:
                payload = json.loads(sys.stdin.read() or "{}")
            except ValueError:
                payload = {}
            transcript = payload.get("transcript_path")
            trigger = payload.get("trigger") or payload.get("source") or ""
        path = thread.snapshot(repo, transcript=transcript, trigger=trigger)
        if not args.hook:
            print("wrote %s" % os.path.relpath(path, repo).replace("\\", "/"))
        return 0

    if args.cmd == "hook":
        if args.action == "status":
            print(hooks.status(repo))
            return 0
        ok, msg = (hooks.install(repo) if args.action == "install"
                   else hooks.uninstall(repo))
        print(msg)
        return 0 if ok else 1

    if args.cmd == "guide":
        return _guide(stages, args)

    if args.cmd == "stages":
        for s in contract.STAGES:
            print("%d  %-10s %s" % (s["id"], s["title"], s["question"]))
        return 0
    return 2


def _suggest(repo, stages):
    """The three things worth doing now: unblock, tool, and context hygiene.

    Advice, not dispatch: lifecycle cannot call a skill or a slash command. It
    can put the right name in front of whoever reads this.
    """
    out = []
    stage, item = report.next_action(stages)
    if stage is not None and item is not None:
        out.append(("unblock", "stage %d %s: %s" % (stage["id"], stage["title"],
                                                    item["detail"]), item["fix"]))
    if stage is not None:
        tools = playbooks.TOOLS.get(stage["key"]) or []
        for name, why in tools[:2]:
            out.append(("tool", "%s - %s" % (name, why),
                        "use it if installed; `lifecycle guide %s` explains why" %
                        stage["key"]))
    pack = next((s.get("pack") for s in stages if s.get("pack")), None)
    if pack and stage is not None and stage["id"] in (0, 2):
        out.append(("pack", "pack %s is active: the stage checks below are the "
                    "generic ones, and this kind of work has its own" % pack,
                    "lifecycle pack guide %s" % pack))
    data, _ = statusline.last(repo)
    if (data or {}).get("used_percentage") is None:
        out.append(("context",
                    "no context reading recorded; `lifecycle hook install` adds the "
                    "status line that records it", "lifecycle hook install"))
    else:
        hint = _context_hint(repo)
        if hint:
            stale = "is not live" in hint
            out.append(("context", hint,
                        "lifecycle hook status" if stale else "/compact"))
    print("What to do now")
    for kind, what, how in out:
        print("")
        print("  [%s] %s" % (kind, what))
        print("         %s" % how)
    return 0


def _thread(repo, args):
    if args.action == "list":
        rows = threads.describe(repo)
        if not rows:
            print("No threads. `lifecycle thread new <slug>` starts one.")
            return 0
        for t in rows:
            plan = ("%d/%d" % (t["plan"]["done"], t["plan"]["total"])
                    if t["plan"] else "-")
            print("%-20s owner=%-12s plan=%-6s %s  %s"
                  % (t["slug"], (t["owner"].split(" @ ")[0] or "-"), plan,
                     "current" if t["fresh"] else "STALE", t["next"]))
        return 0
    if not args.slug:
        sys.stderr.write("lifecycle: thread %s needs a slug" % args.action)
        sys.stderr.write(chr(10))
        return 2
    if args.action == "new":
        ok, msg = threads.create(repo, args.slug, args.title)
    elif args.action == "claim":
        if not args.who:
            sys.stderr.write("lifecycle: claim needs --as <name>")
            sys.stderr.write(chr(10))
            return 2
        ok, msg = threads.claim(repo, args.slug, args.who)
    else:
        ok, msg = threads.release(repo, args.slug)
    print(msg)
    return 0 if ok else 1


def _pack(repo, args):
    """list the packs, print one's playbook, or write its empty structure."""
    name = (args.name or "").strip().lower()
    if args.action == "list":
        active = packs.detect(repo)
        for key in sorted(packs.PACKS):
            spec = packs.PACKS[key]
            print("%-6s %-18s stages %-6s %s"
                  % (key, spec.get("title", ""),
                     ",".join(str(s) for s in spec.get("stages", ())),
                     "active" if key == active else ""))
        return 0
    if not name:
        sys.stderr.write("lifecycle: pack %s needs a name (%s)\n"
                         % (args.action, ", ".join(sorted(packs.PACKS))))
        return 2
    if name not in packs.PACKS:
        sys.stderr.write("lifecycle: unknown pack %r (have: %s)\n"
                         % (name, ", ".join(sorted(packs.PACKS))))
        return 2
    if args.action == "guide":
        print(playbooks.for_pack(name) or "")
        return 0
    result, err = packs.scaffold(repo, name)
    if err:
        sys.stderr.write("lifecycle: %s\n" % err)
        return 1
    for rel in result["created"]:
        print("created %s" % rel)
    for rel in result["kept"]:
        print("kept    %s (exists)" % rel)
    print("")
    print("Next: fill the TODOs, then `lifecycle check`. The checks read these "
          "files; they do not read intention.")
    return 0


def _guide(stages, args):
    want = (args.stage or "").strip().lower()
    pack = playbooks.for_pack(want)
    if pack:
        print(pack)
        return 0
    if want:
        chosen = None
        for s in stages:
            if want == s["key"] or want == str(s["id"]):
                chosen = s
        if chosen is None:
            sys.stderr.write("lifecycle: no stage or pack named %r" % want)
            sys.stderr.write("\n")
            return 2
    else:
        chosen = None
        for s in stages:
            if s["state"] == "failed":
                chosen = s
                break
        if chosen is None:
            print("Every stage passes. `lifecycle guide <stage>` reads any stage's "
                  "playbook; `lifecycle stages` lists them.")
            return 0
    text = playbooks.for_stage(chosen["key"])
    if not text:
        sys.stderr.write("lifecycle: no playbook for %s" % chosen["key"])
        sys.stderr.write("\n")
        return 2
    print(text)
    tools = playbooks.TOOLS.get(chosen["key"]) or []
    if tools:
        print("")
        print("## Tools that help (if installed)")
        print("")
        for name, why in tools:
            print("- `%s` - %s" % (name, why))
    pack_name = next((s.get("pack") for s in stages if s.get("pack")), None)
    pack_text = playbooks.for_pack(pack_name) if pack_name else None
    if pack_text:
        print("")
        print("---")
        print("")
        print(pack_text)
    return 0


def _check(stages, args):
    if args.stage is not None:
        chosen = [s for s in stages if s["id"] == args.stage]
        if not chosen:
            sys.stderr.write("lifecycle: no stage %d (0-%d)\n"
                             % (args.stage, len(contract.STAGES) - 1))
            return 2
    else:
        chosen = stages
    failing = [s for s in chosen if s["state"] == "failed"]
    if args.json:
        print(json.dumps(report.as_json(chosen), ensure_ascii=False, indent=2))
    else:
        for s in chosen:
            bad = report.blockers(s)
            if not bad:
                print("stage %d %-10s %s" % (s["id"], s["title"], s["state"].upper()))
                continue
            print("stage %d %-10s FAIL" % (s["id"], s["title"]))
            for r in bad:
                print("  - %s: %s" % (r["name"], r["detail"]))
                print("    -> %s" % r["fix"])
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
