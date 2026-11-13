"""Regenerate this repository's own evidence from real runs.

    python scripts/gen_evidence.py

Each requirement's evidence is the command and its actual output. Run it after
changing lifecycle code - the evidence is what the Verify stage reads, and stale
evidence is meant to fail.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args, cwd=ROOT, stdin=None):
    p = subprocess.run([sys.executable, "-m", "lifecycle"] + args, cwd=cwd,
                       input=stdin, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()


def tests(cls):
    p = subprocess.run([sys.executable, "-m", "unittest", cls, "-v"], cwd=ROOT,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return ("python -m unittest %s -v   # exit %d" % (cls, p.returncode),
            (p.stdout or "") + (p.stderr or ""))


def write(name, title, blocks):
    parts = ["# " + title, "", "_Run at %s_" % time.strftime("%Y-%m-%d %H:%M:%S"), ""]
    for cmd, out in blocks:
        parts += ["```", "$ " + cmd, out, "```", ""]
    parts.append("measured")
    path = os.path.join(ROOT, ".projtruth", "evidence", name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(parts) + "\n")
    print("wrote", name)


def main():
    rc, status = run(["status"])
    write("R1-status.md", "R1 status is computed from repository artifacts",
          [tests("tests.test_lifecycle.StageTests"),
           tests("tests.test_review2.RegistryRobustnessTests"),
           ("python -m lifecycle status   # exit %d" % rc, status)])

    rc1, check = run(["check", "--stage", "2"])
    rc2, bad = run(["check", "--stage", "9"])
    write("R2-check.md", "R2 check exits 1 on a failing stage",
          [tests("tests.test_lifecycle.CliTests"),
           ("python -m lifecycle check --stage 2   # exit %d\n"
            "python -m lifecycle check --stage 9   # exit %d" % (rc1, rc2),
            check + "\n" + bad)])

    with tempfile.TemporaryDirectory() as tmp:
        demo = os.path.join(tmp, "demo")
        shutil.copytree(ROOT, demo, ignore=shutil.ignore_patterns(
            ".git", "__pycache__", ".projtruth", ".corpus", ".lifecycle"))
        a_rc, a = run(["status"], cwd=demo)
        b_rc, b = run(["status"], cwd=demo)
        same = a == b
        os.remove(os.path.join(demo, "docs", "product", "vision.md"))
        c_rc, c = run(["status"], cwd=demo)
    write("R3-stateless.md", "R3 no gate state is stored",
          [tests("tests.test_lifecycle.ReportTests"),
           ("python -m lifecycle status   # twice, in a copy of this repo",
            "identical: %s (exit %d, %d)\n\n%s" % (same, a_rc, b_rc, a[:500])),
           ("rm docs/product/vision.md && python -m lifecycle status   # exit %d" % c_rc,
            c[:500])])

    with tempfile.TemporaryDirectory() as tmp:
        rc4, empty = run(["status"], cwd=tmp)
    rc5, here = run(["check", "--stage", "4"])
    write("R4-compose.md", "R4 sibling tools compose, missing ones are advisory",
          [tests("tests.test_lifecycle.StageTests.test_verify_skips_when_tools_missing"),
           tests("tests.test_lifecycle.StageTests.test_verify_does_not_pass_without_requirements"),
           ("python -m lifecycle status   # in an empty directory   # exit %d" % rc4, empty),
           ("python -m lifecycle check --stage 4   # exit %d" % rc5, here)])

    rc6, warns = run(["status"])
    write("R5-depth.md", "R5 depth checks flag shallow artifacts without blocking",
          [tests("tests.test_packs.DepthTests"),
           ("python -m lifecycle status   # WARN items never fail a stage   # exit %d" % rc6,
            warns)])

    write("R6-game-pack.md", "R6 the game pack checks world consistency",
          [tests("tests.test_packs.GamePackTests"),
           tests("tests.test_review2.GamePackDetectionTests")])

    rc7, g1 = run(["guide", "design"])
    rc8, g2 = run(["guide", "game"])
    write("R7-guide.md", "R7 guide prints the playbook for the blocking stage",
          [("python -m lifecycle guide design   # exit %d" % rc7, g1[:700]),
           ("python -m lifecycle guide game   # exit %d" % rc8, g2[:500])])

    rc9, res = run(["resume"])
    rc10, rep = run(["report"])
    write("R8-thread.md", "R8 the work thread survives a context reset",
          [tests("tests.test_thread"),
           ("python -m lifecycle resume   # exit %d" % rc9, res),
           ("python -m lifecycle report   # exit %d" % rc10, rep)])

    rc11, hooks_out = run(["hook", "status"])
    rc12, snap = run(["snapshot"], stdin='{"trigger": "manual"}')
    write("R9-hooks.md", "R9 hooks make the thread automatic",
          [tests("tests.test_hooks"),
           ("python -m lifecycle hook status   # exit %d" % rc11, hooks_out),
           ("printf '{\"trigger\":\"manual\"}' | python -m lifecycle snapshot   # exit %d"
            % rc12, snap)])

    rc14, res2 = run(["resume"])
    rc15, st2 = run(["status"])
    write("R10-plan.md", "R10 a plan makes progress visible",
          [tests("tests.test_plan"),
           ("python -m lifecycle resume   # includes plan progress   # exit %d" % rc14,
            res2[:800]),
           ("python -m lifecycle status   # exit %d" % rc15, st2[:800])])

    rc16, _ = run(["statusline"],
                  stdin='{"context_window": {"used_percentage": 74, "context_window_size": 200000}}')
    rc17, res3 = run(["resume", "--hook"], stdin='{"source": "compact", "context_tokens": 42000}')
    write("R11-context.md", "R11 context usage is recorded when the harness exposes it",
          [tests("tests.test_statusline"),
           ("printf '{\"context_window\":{\"used_percentage\":74}}' | "
            "python -m lifecycle statusline   # exit %d" % rc16,
            "recorded; status now prints: %s" %
            [l for l in run(["status"])[1].splitlines() if "context:" in l][:1]),
           ("printf '{\"source\":\"compact\",\"context_tokens\":42000}' | "
            "python -m lifecycle resume --hook   # exit %d" % rc17,
            (res3 or "").splitlines()[0] if res3 else "")])

    rc13, _ = run(["check"])
    print("final check exit:", rc13)


if __name__ == "__main__":
    main()
