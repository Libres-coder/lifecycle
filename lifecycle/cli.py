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

from . import contract, report


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
    ap.add_argument("--repo", default=os.getcwd(),
                    help="project root (default: cwd)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status")
    p.add_argument("--json", action="store_true")
    sub.add_parser("next")
    p = sub.add_parser("check")
    p.add_argument("--stage", type=int, default=None,
                   help="assert one stage (default: every stage)")
    p.add_argument("--json", action="store_true")
    sub.add_parser("stages")

    args = ap.parse_args(argv)
    _utf8()
    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        sys.stderr.write("lifecycle: --repo is not a directory: %s\n" % repo)
        return 2

    stages = _stages(repo)

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

    if args.cmd == "stages":
        for s in contract.STAGES:
            print("%d  %-10s %s" % (s["id"], s["title"], s["question"]))
        return 0
    return 2


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
