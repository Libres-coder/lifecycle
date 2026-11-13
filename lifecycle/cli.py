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

from . import contract, hooks, playbooks, report, thread


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
                    help="domain pack: auto (detect), game, or none")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init")
    p = sub.add_parser("status")
    p.add_argument("--json", action="store_true")
    sub.add_parser("next")
    p = sub.add_parser("check")
    p.add_argument("--stage", type=int, default=None,
                   help="assert one stage (default: every stage)")
    p.add_argument("--json", action="store_true")
    sub.add_parser("stages")
    sub.add_parser("resume")
    sub.add_parser("report")
    p = sub.add_parser("snapshot")
    p.add_argument("--hook", action="store_true",
                   help="read the hook payload from stdin and stay silent")
    p = sub.add_parser("hook")
    p.add_argument("action", choices=["install", "uninstall", "status"])
    p = sub.add_parser("guide")
    p.add_argument("stage", nargs="?",
                   help="stage number or name, or a pack name (game); default: "
                        "the stage that is blocking")

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
            print(report.render(repo, stages))
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

    if args.cmd == "resume":
        print(thread.resume_text(repo, stages))
        stage, item = report.next_action(stages)
        print("")
        if stage is None or item is None:
            print("Lifecycle: every stage passes.")
        else:
            print("Lifecycle: stage %d %s - %s" % (stage["id"], stage["title"],
                                                   item["detail"]))
            print("  fix: %s" % item["fix"])
        return 0

    if args.cmd == "report":
        reqs = contract.run_json(repo, "projtruth", ["report", "--json"])
        docs = contract.run_json(repo, "corpus", ["report", "--json"])
        text = thread.report_text(repo, stages, requirements=reqs, corpus=docs)
        path = thread.write_report(repo, text)
        print("wrote %s" % os.path.relpath(path, repo).replace("\\", "/"))
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
