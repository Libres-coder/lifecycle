"""lifecycle contract: what each stage must produce before the next one starts.

A stage is a list of checks. A check answers one question about the repository
as it is right now - it does not run the product and it does not write anything.
Three kinds of result:

    required   the stage cannot pass without it
    advisory   reported, never blocks
    skipped    the tool or the artifact it needs is absent (reported as WARN)

The contract is deliberately small and the stages are the generic product ones;
a project that wants different gates forks the contract.
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
              ".cs", ".cpp", ".cc", ".c", ".h", ".hpp", ".kt", ".kts", ".swift",
              ".php", ".lua", ".gd", ".dart", ".ex", ".exs", ".clj", ".scala",
              ".m", ".mm", ".fs", ".vb", ".jl", ".r", ".pl", ".sh"}
# A test file is named like a test or lives in a test directory. "spec" as a
# directory is excluded on purpose - docs/spec/openapi.yaml is documentation.
TEST_RE = re.compile(r"(^|/)(tests?|__tests__)/|(^|/)test_[^/]+\.py$|"
                     r"(^|/)[^/]+_test\.(go|rs|rb|exs)$|"
                     r"[._-](test|spec)\.[a-z]+$", re.IGNORECASE)
INLINE_TEST_RE = re.compile(r"#\[cfg\(test\)\]|#\[test\]|mod tests\s*\{|"
                            r"\bfunc Test[A-Z]\w*\(|\bdescribe\(|\bit\(")
VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"', re.MULTILINE)
HEADING_NUM_RE = re.compile(r"^[\d.)\s]+")
HEADING_ARTICLE_RE = re.compile(r"^(the|our|your|a|an)\s+", re.IGNORECASE)


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


def normalize_heading(text):
    """'2. The Problem' -> 'problem'. Numbering and articles are noise."""
    t = HEADING_NUM_RE.sub("", text.strip().lower())
    t = HEADING_ARTICLE_RE.sub("", t)
    return t.strip()


def headings(text):
    return [normalize_heading(m.group(1))
            for m in re.finditer(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)]


def walk_files(repo):
    for root, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            yield os.path.relpath(os.path.join(root, f), repo).replace("\\", "/")


def _installed(tool):
    try:
        import importlib.util
        return importlib.util.find_spec(tool) is not None
    except (ImportError, ValueError):
        return False


def run_json(repo, tool, args):
    """Run an installed sibling tool and parse its JSON. None if unavailable.

    Only tools on PATH (or installed as a module) run. The scanned repository is
    deliberately NOT put on PYTHONPATH: a repository under review must not be
    able to execute code because someone asked for its status.
    """
    exe = shutil.which(tool)
    if exe:
        cmd = [exe]
    elif _installed(tool):
        cmd = [sys.executable, "-m", tool]
    else:
        return None
    try:
        proc = subprocess.run(cmd + ["--repo", repo] + args, stdout=subprocess.PIPE,
                              stderr=subprocess.DEVNULL, timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode not in (0, 1):
        return None
    try:
        return json.loads(proc.stdout.decode("utf-8", "replace"))
    except ValueError:
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
    f, text = read(repo, "pyproject.toml")
    if text:
        m = VERSION_RE.search(text)
        if m:
            return m.group(1).strip()
    f, text = read(repo, "Cargo.toml")
    if text:
        section = re.search(r"^\[package\](.*?)(^\[|\Z)", text,
                            re.MULTILINE | re.DOTALL)
        m = VERSION_RE.search(section.group(1)) if section else None
        if m:
            return m.group(1).strip()
    f, text = read(repo, "package.json")
    if text:
        try:
            return str(json.loads(text).get("version") or "")
        except ValueError:
            pass
    f, text = read(repo, "VERSION")
    if text:
        return text.strip()
    return ""


def _norm_version(v):
    return str(v or "").strip().lstrip("vV")


# -- stage 0: discovery ----------------------------------------------------

def check_vision(repo):
    rel, text = read(repo, "docs/product/vision.md", "docs/vision.md", "VISION.md")
    if not text or not text.strip():
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

def _load_registry(repo):
    """(data, error). Shape errors are reported, never raised."""
    path = os.path.join(repo, ".projtruth", "requirements.json")
    try:
        with open(path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except FileNotFoundError:
        return None, "missing"
    except (OSError, ValueError):
        return None, "unreadable"
    if not isinstance(data, dict):
        return None, "malformed"
    reqs = data.get("requirements", [])
    if not isinstance(reqs, list):
        return None, "malformed"
    for r in reqs:
        if not isinstance(r, dict):
            return None, "malformed"
        if not isinstance(r.get("criteria", []), list):
            return None, "malformed"
    return data, None


def check_spec(repo):
    data, err = _load_registry(repo)
    if err == "missing":
        return [fail("requirements", "no requirement registry",
                     "projtruth init && projtruth import-spec spec.md "
                     "(or write .projtruth/requirements.json)")]
    if err:
        return [fail("requirements", "the requirement registry is not readable JSON",
                     "fix .projtruth/requirements.json - an object with a "
                     "'requirements' list")]
    reqs = data.get("requirements") or []
    if not reqs:
        return [fail("requirements", "registry has no requirements",
                     "add at least one requirement with acceptance criteria")]
    no_criteria = [str(r.get("id") or "?") for r in reqs if not r.get("criteria")]
    out = [ok("requirements", "%d requirement(s)" % len(reqs))]
    if no_criteria:
        out.append(fail("criteria", "%d requirement(s) without acceptance criteria: %s"
                        % (len(no_criteria), ", ".join(no_criteria[:5])),
                        "add criteria - an unverifiable requirement is a wish"))
    else:
        out.append(ok("criteria", "every requirement has criteria"))
    return out


# -- stage 2: design -------------------------------------------------------

def _decision_count(repo):
    path = os.path.join(repo, ".projtruth", "decisions.jsonl")
    count = 0
    if not os.path.isfile(path):
        return 0
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                count += 1
    return count


def check_design(repo):
    rel, text = read(repo, "docs/design/architecture.md", "docs/architecture.md",
                     "ARCHITECTURE.md", "docs/design/README.md")
    out = []
    if text and text.strip():
        out.append(ok("architecture", rel))
    elif text is not None:
        out.append(fail("architecture", "the architecture document is empty",
                        "write docs/design/architecture.md: components, data flow, "
                        "and the trade-off you chose"))
    else:
        out.append(fail("architecture", "no architecture document",
                        "write docs/design/architecture.md: components, data flow, "
                        "and the trade-off you chose"))
    count = _decision_count(repo)
    if count:
        out.append(ok("decisions", "%d recorded decision(s)" % count))
    else:
        out.append(fail("decisions", "no recorded decision",
                        "projtruth decide \"<choice>\" --why \"<reason>\" for each "
                        "non-obvious choice"))
    return out


# -- stage 3: build --------------------------------------------------------

def _inline_tests(repo, sources):
    """Rust, Java and friends often keep tests in the source file."""
    for rel in sources[:300]:
        try:
            with open(os.path.join(repo, rel), encoding="utf-8-sig",
                      errors="replace") as f:
                head = f.read(40000)
        except OSError:
            continue
        if INLINE_TEST_RE.search(head):
            return rel
    return None


def check_build(repo):
    sources, tests = [], []
    for rel in walk_files(repo):
        ext = os.path.splitext(rel)[1].lower()
        if TEST_RE.search(rel):
            tests.append(rel)
        elif ext in SOURCE_EXT:
            sources.append(rel)
    out = []
    if sources:
        out.append(ok("source", "%d source file(s)" % len(sources)))
    else:
        out.append(fail("source", "no source files found",
                        "build the thing, or point lifecycle at the right --repo"))
    if tests:
        out.append(ok("tests", "%d test file(s)" % len(tests)))
    elif sources:
        inline = _inline_tests(repo, sources)
        if inline:
            out.append(ok("tests", "tests inline in %s" % inline))
        else:
            out.append(fail("tests", "no test files found",
                            "add tests before claiming the build stage is done"))
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
    if not isinstance(data, list) or not data:
        # No registry is stage 1's problem; claiming "verified" here would be a
        # false pass on a repository that has promised nothing.
        return [skip("evidence", "no requirements registered - nothing to verify",
                     "stage 1 comes first: add requirements with criteria")]
    out = []
    bad = [r for r in data if isinstance(r, dict) and r.get("status") != "verified"]
    if bad:
        out.append(fail("evidence", "%d requirement(s) not verified: %s"
                        % (len(bad), ", ".join(str(r.get("id", "?")) for r in bad[:6])),
                        "re-run each requirement's verification and write evidence, "
                        "then `projtruth report`"))
    else:
        out.append(ok("evidence", "%d requirement(s) verified" % len(data)))
    corpus = run_json(repo, "corpus", ["report", "--json"])
    if corpus is None:
        out.append(skip("docs", "corpus is not installed",
                        "pip install git+https://github.com/Libres-coder/corpus"))
    else:
        severity = ((corpus or {}).get("metrics") or {}).get("severity") or {}
        incorrect = severity.get("incorrect", 0)
        if incorrect:
            out.append(fail("docs", "%d document finding(s) mislead a reader" % incorrect,
                            "`corpus report` and fix the incorrect findings"))
        else:
            out.append(ok("docs", "no incorrect document findings"))
    return out


# -- stage 5: release ------------------------------------------------------

def check_release(repo):
    version = _norm_version(project_version(repo))
    rel, changelog = read(repo, "CHANGELOG.md", "CHANGELOG", "docs/CHANGELOG.md")
    out = []
    if not changelog:
        out.append(fail("changelog", "no CHANGELOG",
                        "write CHANGELOG.md - what changed, for whom"))
    elif not version:
        out.append(skip("changelog", "no version file to match against",
                        "set a version in pyproject.toml, Cargo.toml, package.json "
                        "or VERSION"))
    elif not re.search(r"\[\s*v?%s\s*\]|^#+\s*v?%s\s*$" % (re.escape(version),
                                                           re.escape(version)),
                       changelog, re.MULTILINE):
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
        if version and _norm_version(newest) != version:
            out.append(fail("tag", "newest tag %s does not match version %s"
                            % (newest, version),
                            "bump the version or tag v%s" % version))
        else:
            out.append(ok("tag", newest))
    return out


def check_sustain(repo):
    """Stage 6 lives in thread.py; imported here to keep the cycle one-way."""
    from . import thread
    return thread.check_sustain(repo)


def check_review(repo):
    """A review note is the only quality signal that is checkable at all."""
    from . import thread
    return thread.check_review(repo)


def check_plan(repo):
    from . import thread
    return thread.check_plan(repo)


def check_thread_structure(repo):
    from . import thread
    return thread.check_thread_structure(repo)


def check_cadence(repo):
    from . import thread
    return thread.check_cadence(repo)


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
    {"id": 6, "key": "sustain", "title": "Sustain",
     "question": "Does the work survive a context reset, and is it summarised?",
     "checks": [check_sustain, check_thread_structure, check_plan,
                check_review, check_cadence]},
]


def evaluate(repo, pack="auto"):
    """Run every stage's checks: structural, then depth, then the active pack.

    Returns [stage dict + results + state]. Depth checks are advisory; pack
    checks may be blocking, because a quest that requires a quest that does not
    exist is wrong, not merely shallow.
    """
    from . import depth as depthmod
    from . import packs as packsmod

    active = packsmod.detect(repo) if pack == "auto" else pack
    if active in ("none", "", None):
        active = None
    elif active not in packsmod.PACKS:
        raise ValueError("unknown pack: %s" % active)
    pack_def = packsmod.PACKS.get(active or "", {})
    out = []
    for stage in STAGES:
        results = []
        for check in stage["checks"]:
            results.extend(check(repo))
        for check in depthmod.DEPTH.get(stage["key"], []):
            results.extend(check(repo))
        if active:
            for check in pack_def.get(stage["key"], []):
                results.extend(check(repo))
        blocking = [r for r in results if r["required"] and not r["ok"]]
        flagged = [r for r in results if not r["required"] and not r["ok"]]
        state = "failed" if blocking else ("flagged" if flagged else "passed")
        out.append({"id": stage["id"], "key": stage["key"], "title": stage["title"],
                    "question": stage["question"], "results": results,
                    "state": state, "pack": active})
    return out
