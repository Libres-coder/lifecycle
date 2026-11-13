"""lifecycle packs: extra checks for a kind of product.

A pack adds checks to existing stages; it never adds a stage. The game pack is
the first one, because an open-world game's "design" is not an architecture
document - it is a world bible and a quest graph, and those have their own ways
of being wrong: a quest that requires a quest that does not exist, a reveal of a
fact nobody ever established, a prerequisite loop that makes a quest
unreachable.

Packs are opt-in by presence: create docs/game/ and the game pack applies.
"""
import glob
import os
import re

from .contract import fail, ok, read


def warn(name, detail, fix):
    return {"name": name, "ok": False, "detail": detail, "fix": fix, "required": False}


def frontmatter(text):
    """Tiny YAML subset: `key: value`, `key: [a, b]`, `key:` then `- item` lines."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    data, key = {}, None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            k, v = m.group(1).lower(), m.group(2).strip()
            if v.startswith("["):
                data[k] = [x.strip().strip("'\"") for x in v.strip("[]").split(",") if x.strip()]
                key = None
            elif v:
                data[k] = v.strip("'\"")
                key = None
            else:
                data[k] = []
                key = k
        elif key and line.strip().startswith("- "):
            data[key].append(line.strip()[2:].strip().strip("'\""))
    return data


def _as_list(value):
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


# -- detection -------------------------------------------------------------

def detect(repo):
    """A pack applies when its directory exists. No config file to forget."""
    if os.path.isdir(os.path.join(repo, "docs", "game")):
        return "game"
    return None


# -- game: discovery -------------------------------------------------------

def game_discovery(repo):
    rel, text = read(repo, "docs/game/pillars.md")
    if not text:
        return [fail("game:pillars", "no game pillars document",
                     "write docs/game/pillars.md: the three experiences the game "
                     "sells, one line each, and how the player feels them")]
    bullets = [l for l in text.splitlines() if re.match(r"^\s*[-*]\s+\S", l)]
    if len(bullets) < 3:
        return [warn("game:pillars",
                     "fewer than three pillars",
                     "a pillar is a promise the whole design can be tested against; "
                     "three is the minimum that forces a choice")]
    return [ok("game:pillars", "%d pillar(s)" % len(bullets))]


# -- game: design ----------------------------------------------------------

def _bible(repo):
    rel, text = read(repo, "docs/game/world-bible.md", "docs/game/bible.md")
    if not text:
        return None, None
    fm = frontmatter(text)
    ids = {}
    for key in ("characters", "factions", "locations", "facts"):
        ids[key] = set(_as_list(fm.get(key)))
    return rel, ids


def _quests(repo):
    out = []
    for path in sorted(glob.glob(os.path.join(repo, "docs", "game", "quests", "*.md"))):
        rel = os.path.relpath(path, repo).replace("\\", "/")
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        fm = frontmatter(text)
        out.append({"path": rel, "id": str(fm.get("id") or os.path.splitext(
            os.path.basename(path))[0]),
            "requires": _as_list(fm.get("requires")),
            "reveals": _as_list(fm.get("reveals")),
            "characters": _as_list(fm.get("characters")),
            "factions": _as_list(fm.get("factions"))})
    return out


def _cycle(quests):
    graph = dict((q["id"], [r for r in q["requires"] if any(o["id"] == r for o in quests)])
                 for q in quests)
    state = {}

    def visit(node, stack):
        if state.get(node) == "done":
            return None
        if state.get(node) == "open":
            return stack[stack.index(node):] + [node]
        state[node] = "open"
        for nxt in graph.get(node, []):
            found = visit(nxt, stack + [node])
            if found:
                return found
        state[node] = "done"
        return None

    for node in graph:
        found = visit(node, [])
        if found:
            return found
    return None


def game_design(repo):
    rel, ids = _bible(repo)
    if not ids:
        return [fail("game:bible", "no world bible",
                     "write docs/game/world-bible.md with frontmatter lists for "
                     "characters, factions, locations and facts")]
    out = [ok("game:bible", rel)]
    for key in ("characters", "locations"):
        if not ids[key]:
            out.append(fail("game:bible:%s" % key, "no %s declared" % key,
                            "list %s in the world bible frontmatter so quests can "
                            "reference them" % key))

    quests = _quests(repo)
    if not quests:
        out.append(warn("game:quests", "no quest files yet",
                        "docs/game/quests/<id>.md with id/requires/reveals "
                        "frontmatter, even for one quest"))
        return out

    seen = {}
    for q in quests:
        if q["id"] in seen:
            out.append(fail("game:quest-id", "duplicate quest id %s" % q["id"],
                            "rename one of %s and %s" % (seen[q["id"]], q["path"])))
        seen[q["id"]] = q["path"]

    known = set(seen)
    missing_req, missing_reveal, missing_char = [], [], []
    for q in quests:
        for r in q["requires"]:
            if r not in known:
                missing_req.append("%s -> %s" % (q["id"], r))
        for f in q["reveals"]:
            if f not in ids["facts"]:
                missing_reveal.append("%s -> %s" % (q["id"], f))
        for c in q["characters"]:
            if c not in ids["characters"]:
                missing_char.append("%s -> %s" % (q["id"], c))
        for f in q["factions"]:
            if f not in ids["factions"]:
                missing_char.append("%s -> %s" % (q["id"], f))

    out.append(fail("game:requires", "quest(s) require a quest that does not exist: %s"
                    % ", ".join(missing_req[:5]),
                    "fix the id or add the missing quest file")
               if missing_req else ok("game:requires", "%d quest(s) linked" % len(quests)))
    out.append(fail("game:reveals", "quest(s) reveal a fact not in the bible: %s"
                    % ", ".join(missing_reveal[:5]),
                    "declare the fact under `facts:` in the world bible, or fix the id")
               if missing_reveal else ok("game:reveals", "every reveal is established"))
    out.append(fail("game:actors", "quest(s) reference unknown characters/factions: %s"
                    % ", ".join(missing_char[:5]),
                    "declare them in the world bible frontmatter")
               if missing_char else ok("game:actors", "every actor is declared"))

    cyc = _cycle(quests)
    if cyc:
        out.append(fail("game:cycle", "prerequisite loop: %s" % " -> ".join(cyc),
                        "break the loop; a quest that requires itself can never start"))
    else:
        out.append(ok("game:cycle", "no prerequisite loop"))
    return out


PACKS = {
    "game": {"discovery": [game_discovery], "design": [game_design],
             "title": "Open-world game",
             "playbook": "game.md"},
}
