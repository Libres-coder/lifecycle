"""lifecycle contract: what each stage must produce before the next one starts.

A stage is a list of checks. A check answers one question about the repository
as it is right now - it does not run anything and it does not write anything.
Three kinds of check:

    required   the stage cannot pass without it
    advisory   reported, never blocks
    skipped    the tool it needs is not installed (reported as "needs X")

The contract is deliberately small and the stages are the generic product ones;
a project that wants different gates edits `STAGES` or ignores the tool. The
point is that "done" is computed from artifacts, not declared in a meeting.
"""
import json
import os
import re
import shutil
import subprocess
import sys

IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist",
               "build", "target", ".next", ".cache", ".corpus", ".lifecycle",
               ".projtruth", ".claude", ".idea", "graphify-out"}
SOURCE_EXT = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".rb",
              ".cs", ".cpp", ".c", ".h", ".kt", ".swift", ".php", ".lua", ".gd"}
TEST_RE = re.compile(r"(^|/)(tests?|spec|__tests__)/|(^|/)test_[^/]+\.py$|"
                     r"[._-](test|spec)\.[a-z]+$", re.IGNORECASE)
VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"', re.MULTILINE)


def ok(name, detail, required=True):
    return {"name": name, "ok": True, "detail": detail, "required": required}


def fail(name, detail, fix, required=True):
    return {"name": name, "ok": False, "detail": detail, "fix": fix,
            "required": required}


def skip(name, why, fix):
    return {"name": name, "ok": False, "skipped": True, "detail": why, "fix": fix,
            "required": False}


# -- helpers ---------------------------------------------------------------

def read(repo, *candidates):
    for rel in candidates:
        p = os.path.join(repo, rel)
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8-sig", errors="replace") as f:
                    return rel, f.read()
            except OSError:
                continue
    return None, None


def headings(text):
    return [m.group(1).strip().lower()
            for m in re.finditer(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)]


def walk_files(repo):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            yield os.path.relpath(os.path.join(root, f), repo).replace("\\", "/")


def run_json(repo, tool, args):
    """Run a sibling tool and parse its JSON. None if it cannot be run.

    Two ways, because these tools are often checkouts rather than installed
    packages: an executable on PATH, or -m <module> with the scanned repo on
    PYTHONPATH (which is how a self-hosted repo finds its own tool).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = repo + (os.pathsep + env["PYTHONPATH"]
                                if env.get("PYTHONPATH") else "")
    candidates = []
    exe = shutil.which(tool)
    if exe:
        candidates.append([exe])
    candidates.append([sys.executable, "-m", tool])
    for base in candidates:
        try:
            proc = subprocess.run(base + ["--repo", repo] + args, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, timeout=120, cwd=repo,
                                  env=env)
        except (OSError, subprocess.SubprocessError):
            continue
        if proc.returncode not in (0, 1):
            continue
        try:
            return json.loads(proc.stdout.decode("utf-8", "replace"))
        except ValueError:
            continue
    return None


def git(repo, *args):
    try:
        proc = subprocess.run(["git", "-C", repo] + list(args), stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.decode("utf-8", "replace").strip()


def project_version(repo):
    rel, text = read(repo, "pyproject.toml")
    if text:
        m = VERSION_RE.search(text)
        if m:
            return m.group(1)
    rel, text = read(repo, "package.json")
    if text:
        try:
            return str(json.loads(text).get("version") or "")
        except ValueError:
            pass
    rel, text = read(repo, "VERSION")
    if text:
        return text.strip()
    return ""


# -- stage 0: discovery ----------------------------------------------------

def check_vision(repo):
    rel, text = read(repo, "docs/product/vision.md", "docs/vision.md", "VISION.md")
    if not text:
        return [fail("vision", "no product vision document",
                     "write docs/product/vision.md with Problem, Audience and Non-goals")]
    have = headings(text)
    out = [ok("vision", rel)]
    for needed, label in (("problem", "Problem"), ("audience", "Audience"),
                          ("non-goal", "Non-goals")):
        if any(h.startswith(needed) for h in have):
            out.append(ok("vision:%s" % needed, "%s section present" % label))
        else:
            out.append(fail("vision:%s" % needed, "%s section missing" % label,
                            "add a '## %s' section to %s" % (label, rel)))
    return out


# -- stage 1: spec ---------------------------------------------------------

def check_spec(repo):
    path = os.path.join(repo, ".projtruth", "requirements.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return [fail("requirements", "no requirement registry",
                     "projtruth init && projtruth import-spec spec.md "
                     "(or write .projtruth/requirements.json)")]
    reqs = data.get("requirements") or []
    if not isinstance(reqs, list) or not reqs:
        return [fail("requirements", "registry has no requirements",
                     "add at least one requirement with acceptance criteria")]
    no_criteria = [r.get("id") for r in reqs if not r.get("criteria")]
    out = [ok("requirements", "%d requirement(s)" % len(reqs))]
    if no_criteria:
        out.append(fail("criteria", "%d requirement(s) without acceptance criteria: %s"
                        % (len(no_criteria), ", ".join(no_criteria[:5])),
                        "add criteria - an unverifiable requirement is a wish"))
    else:
        out.append(ok("criteria", "every requirement has criteria"))
    return out


# -- stage 2: design -------------------------------------------------------

def check_design(repo):
    rel, _ = read(repo, "docs/design/architecture.md", "docs/architecture.md",
                  "ARCHITECTURE.md", "docs/design/README.md")
    out = []
    if rel:
        out.append(ok("architecture", rel))
    else:
        out.append(fail("architecture", "no architecture document",
                        "write docs/design/architecture.md: components, data flow, "
                        "and the trade-off you chose"))
    decisions = os.path.join(repo, ".projtruth", "decisions.jsonl")
    count = 0
    if os.path.isfile(decisions):
        with open(decisions, encoding="utf-8", errors="replace") as f:
            count = len([line for line in f if line.strip()])
    if count:
        out.append(ok("decisions", "%d recorded decision(s)" % count))
    else:
        out.append(fail("decisions", "no recorded decision",
                        "projtruth decide \"<choice>\" --why \"<reason>\" for each "
                        "non-obvious choice"))
    return out


# -- stage 3: build --------------------------------------------------------

def check_build(repo):
    sources, tests = 0, 0
    for rel in walk_files(repo):
        ext = os.path.splitext(rel)[1].lower()
        if TEST_RE.search(rel):
            tests += 1
        elif ext in SOURCE_EXT:
            sources += 1
    out = []
    if sources:
        out.append(ok("source", "%d source file(s)" % sources))
    else:
        out.append(fail("source", "no source files found",
                        "build the thing, or point lifecycle at the right --repo"))
    if tests:
        out.append(ok("tests", "%d test file(s)" % tests))
    else:
        out.append(fail("tests", "no test files found",
                        "add tests before claiming the build stage is done"))
    return out


# -- stage 4: verify -------------------------------------------------------

def check_verify(repo):
    data = run_json(repo, "projtruth", ["report", "--json"])
    if data is None:
        return [skip("projtruth", "projtruth is not installed",
                     "pip install git+https://github.com/Libres-coder/projtruth")]
    out = []
    bad = [r for r in data if r.get("status") != "verified"]
    if bad:
        out.append(fail("evidence", "%d requirement(s) not verified: %s"
                        % (len(bad), ", ".join(r.get("id", "?") for r in bad[:6])),
                        "re-run each requirement's verification and write evidence, "
                        "then `projtruth report`"))
    else:
        out.append(ok("evidence", "%d requirement(s) verified" % len(data)))
    corpus = run_json(repo, "corpus", ["report", "--json"])
    if corpus is None:
        out.append(skip("docs", "corpus is not installed",
                        "pip install git+https://github.com/Libres-coder/corpus"))
    else:
        incorrect = (corpus.get("metrics", {}).get("severity", {}) or {}).get("incorrect", 0)
        if incorrect:
            out.append(fail("docs", "%d document finding(s) mislead a reader" % incorrect,
                            "`corpus report` and fix the incorrect findings"))
        else:
            out.append(ok("docs", "no incorrect document findings"))
    return out


# -- stage 5: release ------------------------------------------------------

def check_release(repo):
    version = project_version(repo)
    rel, changelog = read(repo, "CHANGELOG.md", "CHANGELOG", "docs/CHANGELOG.md")
    out = []
    if not changelog:
        out.append(fail("changelog", "no CHANGELOG",
                        "write CHANGELOG.md - what changed, for whom"))
    elif version and version not in changelog:
        out.append(fail("changelog", "CHANGELOG has no entry for %s" % version,
                        "add a '## [%s]' section to %s" % (version, rel)))
    else:
        out.append(ok("changelog", rel))
    tags = git(repo, "tag", "--sort=-v:refname")
    if tags is None:
        out.append(skip("tag", "not a git repository", "git init and tag the release"))
    elif not tags:
        out.append(fail("tag", "no release tag",
                        "git tag -a v%s -m \"release\"" % (version or "0.1.0")))
    else:
        newest = tags.splitlines()[0]
        if version and version not in newest:
            out.append(fail("tag", "newest tag %s does not match version %s"
                            % (newest, version),
                            "bump the version or tag %s" % version))
        else:
            out.append(ok("tag", newest))
    return out


STAGES = [
    {"id": 0, "key": "discovery", "title": "Discovery",
     "question": "Why does this exist, and what will it not do?",
     "checks": [check_vision]},
    {"id": 1, "key": "spec", "title": "Spec",
     "question": "What exactly is promised, in a way a stranger can check?",
     "checks": [check_spec]},
    {"id": 2, "key": "design", "title": "Design",
     "question": "How is it built, and why this way?",
     "checks": [check_design]},
    {"id": 3, "key": "build", "title": "Build",
     "question": "Does the code and its tests exist?",
     "checks": [check_build]},
    {"id": 4, "key": "verify", "title": "Verify",
     "question": "Is every promise backed by evidence that still holds?",
     "checks": [check_verify]},
    {"id": 5, "key": "release", "title": "Release",
     "question": "Is there a version, a changelog and a tag?",
     "checks": [check_release]},
]


def evaluate(repo):
    """Run every stage's checks. Returns [stage dict + results + state]."""
    out = []
    for stage in STAGES:
        results = []
        for check in stage["checks"]:
            results.extend(check(repo))
        blocking = [r for r in results if r["required"] and not r["ok"]]
        flagged = [r for r in results if not r["required"] and not r["ok"]]
        state = "failed" if blocking else ("flagged" if flagged else "passed")
        out.append({"id": stage["id"], "key": stage["key"], "title": stage["title"],
                    "question": stage["question"], "results": results,
                    "state": state})
    return out
