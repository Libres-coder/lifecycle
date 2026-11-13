"""lifecycle depth: advisory checks for shallow work, not missing work.

Presence is cheap to fake: a vision document with three headings and no thought,
a requirement whose only criterion is "works", a decision recorded without a
reason. These checks never block a stage - taste is not a gate - but they show
up in the report as WARN with the sentence that says what a shallow version
looks like.

Everything here is text-based and therefore arguable. That is what "advisory"
means: the record of a judgement, not the judgement itself.
"""
import glob
import json
import os
import re

from .contract import _load_registry, normalize_heading, project_version, read

TIER_LINE_RE = re.compile(r"^[ \t]*(measured|inferred|guessed)[ \t]*\.?[ \t]*$",
                          re.IGNORECASE | re.MULTILINE)


def warn(name, detail, fix):
    return {"name": name, "ok": False, "detail": detail, "fix": fix, "required": False}


def _section(text, *names):
    """Body of the first '## name' section, or '' - headings normalised."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        m = re.match(r"^#{1,3}\s+(.+)$", line)
        if m and any(normalize_heading(m.group(1)).startswith(n) for n in names):
            start = i + 1
            continue
        if start is not None and re.match(r"^#{1,3}\s+", line):
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else ""


def _bullets(text):
    return [l for l in text.splitlines() if re.match(r"^\s*[-*]\s+\S", l)]


# -- stage 0 ---------------------------------------------------------------

def vision_depth(repo):
    rel, text = read(repo, "docs/product/vision.md", "docs/vision.md", "VISION.md")
    if not text or not text.strip():
        return []
    out = []
    words = len(text.split())
    if words < 100:
        out.append(warn("vision:depth",
                        "the vision is %d words - a stranger cannot act on it" % words,
                        "write the problem as a specific situation, not a category"))
    non_goals = _bullets(_section(text, "non-goal", "non goal", "not doing"))
    if len(non_goals) < 2:
        out.append(warn("vision:non-goals",
                        "fewer than two non-goals",
                        "name what this product explicitly will not do - the scope "
                        "you refuse is the design"))
    metric = _section(text, "success", "metric", "how we know")
    if not metric.strip():
        out.append(warn("vision:metric",
                        "no success metric",
                        "add a '## Success metric' section: one number, and where it "
                        "comes from"))
    rel2, body = read(repo, "docs/product/research.md",
                      "docs/product/research/index.md")
    if not body:
        out.append(warn("vision:research",
                        "no research log",
                        "write docs/product/research.md: who you talked to or what you "
                        "read about how this problem is solved today, with links"))
    elif not re.search(r"https?://", body):
        out.append(warn("vision:research",
                        "the research log has no sources",
                        "every claim about users or alternatives needs a link or a "
                        "recorded observation"))
    return out


# -- stage 1 ---------------------------------------------------------------

def spec_depth(repo):
    data, err = _load_registry(repo)
    if err or data is None:
        return []
    thin = []
    for req in data.get("requirements", []):
        for c in req.get("criteria", []):
            if len(str(c.get("text") or "").strip()) < 15:
                thin.append(str(c.get("id") or req.get("id")))
    if thin:
        return [warn("spec:criteria",
                     "%d criterion(s) too vague to test: %s"
                     % (len(thin), ", ".join(thin[:5])),
                     "a criterion names an action and an observable result "
                     "('POST returns 201 and a GET lists it'), not 'works'")]
    return []


# -- stage 2 ---------------------------------------------------------------

def design_depth(repo):
    out = []
    path = os.path.join(repo, ".projtruth", "decisions.jsonl")
    if os.path.isfile(path):
        empty = 0
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if isinstance(row, dict) and not str(row.get("why") or "").strip():
                    empty += 1
        if empty:
            out.append(warn("design:why",
                            "%d decision(s) recorded without a reason" % empty,
                            "the why is the part that stops the next session from "
                            "re-litigating it"))
    rel, text = read(repo, "docs/design/architecture.md", "docs/architecture.md",
                     "ARCHITECTURE.md")
    if text and text.strip():
        if not re.search(r"trade[- ]?off|alternative|rejected|considered|instead of",
                         text, re.IGNORECASE):
            out.append(warn("design:alternatives",
                            "the architecture does not mention a trade-off or an "
                            "alternative",
                            "record what you did not choose and why - a design with no "
                            "rejected option is a description"))
        if not re.search(r"fail|error|timeout|outage|retry|degrade|offline",
                         text, re.IGNORECASE):
            out.append(warn("design:failure",
                            "the architecture does not discuss failure",
                            "add what happens when a dependency is down, the input is "
                            "bad, or the data is large"))
    return out


# -- stage 4 ---------------------------------------------------------------

def _tier_of(path):
    """A standalone tier line decides; otherwise the file declares no tier.

    Counting 'any tier word anywhere' made a test name or a quoted log decide
    the answer, which is how guessed evidence got through before.
    """
    try:
        with open(path, encoding="utf-8-sig", errors="replace") as f:
            body = f.read()
    except OSError:
        return "unreadable"
    m = TIER_LINE_RE.search(body)
    return m.group(1).lower() if m else "none"


def verify_depth(repo):
    files = glob.glob(os.path.join(repo, ".projtruth", "evidence", "**", "*"),
                      recursive=True)
    files += glob.glob(os.path.join(repo, ".claude", "skills", "verify-*",
                                    "evidence", "**", "*"), recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return []
    tiers = {"measured": 0, "inferred": 0, "guessed": 0, "none": 0}
    for f in files:
        key = _tier_of(f)
        tiers[key] = tiers.get(key, 0) + 1
    out = []
    if tiers["guessed"]:
        out.append(warn("verify:tiers",
                        "%d evidence file(s) are marked guessed" % tiers["guessed"],
                        "run the check; guessed evidence is a note to yourself"))
    if tiers["none"]:
        out.append(warn("verify:tiers",
                        "%d evidence file(s) declare no tier" % tiers["none"],
                        "end each evidence file with a line that is just "
                        "measured / inferred / guessed"))
    if not tiers["measured"] and files:
        out.append(warn("verify:measured",
                        "no evidence file is marked measured",
                        "at least one requirement needs a real run with real output"))
    return out


# -- stage 5 ---------------------------------------------------------------

def release_depth(repo):
    rel, text = read(repo, "CHANGELOG.md", "CHANGELOG", "docs/CHANGELOG.md")
    if not text:
        return []
    version = str(project_version(repo) or "").strip().lstrip("vV")
    if not version:
        return []
    heading = re.search(r"^#{1,3}\s*(\[[^\]]*\]|v?%s\b.*)$" % re.escape(version),
                        text, re.MULTILINE)
    if not heading:
        return []
    body = text[heading.end():]
    nxt = re.search(r"^#{1,3}\s+", body, re.MULTILINE)
    body = body[:nxt.start()] if nxt else body
    if not _bullets(body):
        return [warn("release:notes",
                     "the changelog entry for %s has no bullet" % version,
                     "say what changed for the user, not that a version exists")]
    return []


DEPTH = {
    "discovery": [vision_depth],
    "spec": [spec_depth],
    "design": [design_depth],
    "verify": [verify_depth],
    "release": [release_depth],
}
