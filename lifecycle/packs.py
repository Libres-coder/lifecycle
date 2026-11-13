"""lifecycle packs: extra checks for a kind of work.

A pack adds checks to existing stages; it never adds a stage. It also brings a
playbook (what deep work in that domain looks like) and a scaffold (`lifecycle
pack init`) that creates the empty structure the checks read - never content.

The games and stories here are the first two, because a game's "design" is not
an architecture document and a novel's is not a quest graph. Both are narrative
structure that has to stay consistent while scenes are written out of order.
Their ways of being wrong are specific: a quest that requires a quest that does
not exist, a reveal of a fact nobody established, a prerequisite loop, a plot
thread nobody resolves, a reveal to a character who already knows.

Packs are opt-in by presence: `docs/game/` or `docs/story/`, or `--pack`.
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
        if line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            k, v = m.group(1).lower(), _strip_comment(m.group(2).strip())
            if v.startswith("["):
                data[k] = _split_items(v.strip("[]"))
                key = None
            elif v:
                data[k] = _clean_quotes(v)
                key = None
            else:
                data[k] = []
                key = k
        elif key and line.strip().startswith("- "):
            item = _strip_comment(line.strip()[2:].strip())
            data[key].append(_clean_quotes(item))
    return data


def _strip_comment(value):
    """Drop a trailing `  # note` only when the `#` is outside quotes."""
    quote = None
    for i, ch in enumerate(value):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
        elif ch == "#" and (i == 0 or value[i - 1].isspace()):
            return value[:i].strip()
    return value.strip()


def _clean_quotes(value):
    """Strip one pair of quotes only when they wrap the whole value.

    `"aria": "war-started"` has quotes around each side; stripping the outer
    two would leave `aria": "war-started`.
    """
    value = value.strip()
    if len(value) >= 2 and value[0] in "'\"":
        end = value.find(value[0], 1)
        if end == len(value) - 1:
            return value[1:-1]
    return value


def _split_items(raw):
    """Split an inline list on commas that are not inside quotes."""
    items, buf, quote = [], [], None
    for ch in raw:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            quote = ch
            buf.append(ch)
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    items.append("".join(buf))
    return [_clean_quotes(x) for x in items if x.strip()]


def _as_list(value):
    if isinstance(value, list):
        return [_clean_quotes(str(v)) for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [_clean_quotes(value)]
    return []


def _as_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _pairs(value):
    """`- aria: war-started` lines become {aria: [war-started, ...]}."""
    out = {}
    for item in _as_list(value):
        who, sep, fact = item.partition(":")
        if sep:
            who = _clean_quotes(who)
            fact = _clean_quotes(fact)
        if sep and who and fact:
            out.setdefault(who, []).append(fact)
    return out


def _frontmatter_files(repo, sub, pattern="**/*.md"):
    """(rel_path, name, frontmatter, text) for files that are not templates."""
    out = []
    root = os.path.join(repo, *sub.split("/"))
    # glob treats [ ] * ? in a directory name as syntax; a repo called
    # "Game [WIP]" must still be scanned.
    for path in sorted(glob.glob(os.path.join(glob.escape(root), pattern),
                                 recursive=True)):
        if os.path.basename(path) == "_template.md":
            continue                       # the scaffold: a template, not data
        try:
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        rel = os.path.relpath(path, repo).replace("\\", "/")
        out.append((rel, os.path.splitext(os.path.basename(path))[0],
                    frontmatter(text), text))
    return out


# -- detection -------------------------------------------------------------

def _has_data_file(path):
    """A directory opts a pack in only when it holds a real file, not a template."""
    if not os.path.isdir(path):
        return False
    for _root, _dirs, files in os.walk(path):
        for name in files:
            if name.endswith(".md") and name != "_template.md":
                return True
    return False


def detect(repo):
    """A pack applies when its artifacts exist, not when an empty directory does.

    `mkdir docs/game` should not turn two stages red. The first match wins; a
    project that is both uses `--pack` to say which one the stage checks follow.
    """
    game = os.path.join(repo, "docs", "game")
    if os.path.isdir(game) and (
            os.path.isfile(os.path.join(game, "pillars.md"))
            or os.path.isfile(os.path.join(game, "world-bible.md"))
            or _has_data_file(os.path.join(game, "quests"))):
        return "game"
    story = os.path.join(repo, "docs", "story")
    if os.path.isdir(story) and (
            os.path.isfile(os.path.join(story, "outline.md"))
            or os.path.isfile(os.path.join(story, "characters.md"))
            or _has_data_file(os.path.join(story, "chapters"))):
        return "story"
    return None


# -- shared narrative checks ----------------------------------------------

def _ids(fm, keys=("characters", "factions", "locations", "facts")):
    return dict((key, set(_as_list(fm.get(key)))) for key in keys)


def _start_knowledge(fm):
    """facts a character knows before the story starts: `- aria: war-started`."""
    knows = {}
    for who, facts in _pairs(fm.get("knows")).items():
        knows.setdefault(who, set()).update(facts)
    return knows


def _knowledge_checks(prefix, ids, knows, items):
    """Knowledge accumulates in story order: a reveal updates the character's
    state, so a second reveal of the same fact is caught, not just a reveal
    against the starting set. `knows:` is validated too - a typo there used to
    disable the warning silently."""
    unknown_actor, unknown_fact, redundant, bad_state = [], [], [], []
    for who, facts in knows.items():
        if who not in ids["characters"]:
            bad_state.append("%s (unknown character)" % who)
        for fact in facts:
            if fact not in ids["facts"]:
                bad_state.append("%s: %s (unknown fact)" % (who, fact))
    state = dict((who, set(facts)) for who, facts in knows.items())
    for item in _ordered(items):
        for who, facts in (item.get("reveals_to") or {}).items():
            if who not in ids["characters"]:
                unknown_actor.append("%s -> %s" % (item["id"], who))
            for fact in facts:
                if fact not in ids["facts"]:
                    unknown_fact.append("%s -> %s" % (item["id"], fact))
                elif fact in state.get(who, set()):
                    redundant.append("%s -> %s already knows %s"
                                     % (item["id"], who, fact))
                else:
                    state.setdefault(who, set()).add(fact)
    out = []
    if bad_state:
        out.append(fail("%s:knows-state" % prefix,
                        "`knows:` names something undeclared: %s"
                        % ", ".join(bad_state[:5]),
                        "a starting state that points at an undeclared character "
                        "or fact silently disables the reveal checks"))
    if unknown_actor:
        out.append(fail("%s:knows-actor" % prefix,
                        "reveal to undeclared character(s): %s"
                        % ", ".join(unknown_actor[:5]),
                        "declare them under `characters:`"))
    if unknown_fact:
        out.append(fail("%s:knows-fact" % prefix,
                        "reveal of a fact the bible never establishes: %s"
                        % ", ".join(unknown_fact[:5]),
                        "declare the fact under `facts:`, or fix the id"))
    if redundant:
        out.append(warn("%s:knows-redundant" % prefix,
                        "a reveal tells a character what they already know: %s"
                        % ", ".join(redundant[:5]),
                        "cut the reveal, or move the fact from `knows:` if the "
                        "character learns it here for the first time"))
    if out:
        return out
    return [ok("%s:knows" % prefix, "knowledge state is consistent")]


def _ordered(items):
    """Story order: act (default 1), then order (unordered last), then id."""
    def key(item):
        act = item.get("act")
        order = item.get("order")
        return (act if act is not None else 1,
                order if order is not None else 10 ** 9,
                item["id"])
    return sorted(items, key=key)


# -- craft: the checkable shadow of the standard ---------------------------
#
# Structure checks say "the graph is consistent". These say "the work is
# concrete": every scene declares a want, an obstacle and a turn, every quest
# declares a stake, and neither is a synopsis of itself. They are advisory -
# craft is not a gate - but a chapter that cannot state these is a summary
# wearing a scene's clothes, and the warning names it.

MIN_CHAPTER_WORDS = 200
MIN_QUEST_WORDS = 40


def _body(text):
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end >= 0:
            text = text[end + 4:]
    return text


def _word_count(text):
    """Words for alphabetic text, characters for CJK - both are units of writing.

    Kana and Hangul count too: a 300-character Japanese chapter is not 0 words.
    """
    return len(re.findall(
        r"[A-Za-z0-9']+|[぀-ヿ㐀-䶿一-鿿가-힯]",
        _body(text)))


def game_craft(repo):
    no_stakes, short = [], []
    for rel, name, fm, text in _frontmatter_files(repo, GAME_DIR, "quests/**/*.md"):
        qid = str(fm.get("id") or name)
        if not str(fm.get("stakes") or "").strip():
            no_stakes.append(qid)
        words = _word_count(text)
        if words < MIN_QUEST_WORDS:
            short.append("%s (%d words)" % (qid, words))
    out = []
    if no_stakes:
        out.append(warn("game:craft-stakes",
                        "quest(s) with no stake: %s" % ", ".join(no_stakes[:5]),
                        "add `stakes:` - what the player loses if they fail or "
                        "refuse. 'The city is in danger' is a premise; 'the fisher "
                        "who hid you loses the boat' is a stake"))
    if short:
        out.append(warn("game:craft-thin",
                        "quest(s) too short to be a quest: %s" % ", ".join(short[:5]),
                        "say what the player does, what it costs and what changes; "
                        "fetch-verbs without a decision are structure, not content"))
    if out:
        return out
    return [ok("game:craft", "every quest declares a stake")]


def story_craft(repo):
    out = []
    rel, text = read(repo, "docs/story/characters.md")
    fm = frontmatter(text or "")
    chars = _as_list(fm.get("characters"))
    if chars:
        wants = set(_pairs(fm.get("want")))
        obstacles = set(_pairs(fm.get("obstacle")))
        flaws = set(_pairs(fm.get("flaw")))
        thin = [c for c in chars
                if c not in wants or c not in obstacles or c not in flaws]
        if thin:
            out.append(warn("story:craft-character",
                            "character(s) with no declared want/obstacle/flaw: %s"
                            % ", ".join(thin[:5]),
                            "add want/obstacle/flaw lines to characters.md - a "
                            "character is a want meeting an obstacle, and the flaw "
                            "is why the obstacle wins for a while"))
    vague, short = [], []
    for _rel, name, cfm, text in _frontmatter_files(repo, STORY_DIR,
                                                    "chapters/**/*.md"):
        cid = str(cfm.get("id") or name)
        if not (cfm.get("want") and cfm.get("obstacle") and cfm.get("turn")):
            vague.append(cid)
        words = _word_count(text)
        if words < MIN_CHAPTER_WORDS:
            short.append("%s (%d words)" % (cid, words))
    if vague:
        out.append(warn("story:craft-scene",
                        "chapter(s) that never say what the POV wants, what "
                        "blocks them, or what changes: %s" % ", ".join(vague[:5]),
                        "add `want:`, `obstacle:` and `turn:` to the frontmatter - "
                        "a chapter without them is a summary wearing a scene's "
                        "clothes"))
    if short:
        out.append(warn("story:craft-thin",
                        "chapter(s) too short to be a scene: %s" % ", ".join(short[:5]),
                        "write the moment instead of noting it; if it is not a "
                        "scene, merge it into the one that carries it"))
    if out:
        return out
    return [ok("story:craft", "every chapter declares a want, an obstacle and a turn")]


# -- game ------------------------------------------------------------------

GAME_DIR = "docs/game"


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


def _bible(repo):
    rel, text = read(repo, "docs/game/world-bible.md", "docs/game/bible.md")
    if not text:
        return None, None, {}
    fm = frontmatter(text)
    return rel, _ids(fm), _start_knowledge(fm)


def _quests(repo):
    out = []
    for rel, name, fm, _text in _frontmatter_files(repo, GAME_DIR, "quests/**/*.md"):
        out.append({"path": rel, "id": str(fm.get("id") or name),
                    "requires": _as_list(fm.get("requires")),
                    "reveals": _as_list(fm.get("reveals")),
                    "characters": _as_list(fm.get("characters")),
                    "factions": _as_list(fm.get("factions")),
                    "act": _as_int(fm.get("act")),
                    "order": _as_int(fm.get("order")),
                    "reveals_to": _pairs(fm.get("reveals_to"))})
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


def _timeline(quests):
    """A quest may not require one that comes later in the act/order timeline."""
    dated = [q for q in quests if q["order"] is not None]
    if not dated:
        return [warn("game:timeline", "no quest carries act/order",
                     "give each quest `act:` and `order:` numbers so the graph can "
                     "be checked against the timeline the player experiences")]
    missing = [q["id"] for q in quests if q["order"] is None]
    missing_act = [q["id"] for q in dated if q["act"] is None]
    by_id = dict((q["id"], q) for q in quests)
    inverted = []
    for q in dated:
        for required in q["requires"]:
            other = by_id.get(required)
            if not other or other["order"] is None:
                continue
            q_key = (q["act"] if q["act"] is not None else 1, q["order"])
            o_key = (other["act"] if other["act"] is not None else 1, other["order"])
            if o_key > q_key:
                inverted.append("%s (act %d, order %d) requires %s (act %d, order %d)"
                                % (q["id"], q_key[0], q_key[1],
                                   other["id"], o_key[0], o_key[1]))
    out = []
    if inverted:
        out.append(fail("game:timeline-order",
                        "quest(s) require a later quest: %s"
                        % "; ".join(inverted[:3]),
                        "swap the order numbers, or cut the requirement - the "
                        "player cannot finish a quest before the one it needs"))
    if missing_act:
        out.append(warn("game:timeline-act",
                        "quest(s) without an act: %s" % ", ".join(missing_act[:5]),
                        "add `act:` - without it a cross-act inversion cannot be "
                        "told from a correct one, and the check has to assume "
                        "act 1"))
    if missing:
        out.append(warn("game:timeline-missing",
                        "quest(s) without an order: %s" % ", ".join(missing[:5]),
                        "add `order:` (and `act:`) so the timeline check covers them"))
    if not out:
        out.append(ok("game:timeline", "%d quest(s) ordered" % len(dated)))
    return out


def game_design(repo):
    rel, ids, knows = _bible(repo)
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

    out.append(fail("game:requires", "quest(s) require a quest that does not exist: %s%s"
                    % (", ".join(missing_req[:5]),
                       (" (+%d more)" % (len(missing_req) - 5)) if len(missing_req) > 5 else ""),
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

    out.extend(_timeline(quests))
    out.extend(_knowledge_checks("game", ids, knows, quests))
    return out


# -- story -----------------------------------------------------------------

STORY_DIR = "docs/story"


def _story_chapters(repo):
    out = []
    for rel, name, fm, _text in _frontmatter_files(repo, STORY_DIR, "chapters/**/*.md"):
        out.append({"path": rel, "id": str(fm.get("id") or name),
                    "order": _as_int(fm.get("order")),
                    "pov": str(fm.get("pov") or "").strip(),
                    "reveals": _as_list(fm.get("reveals")),
                    "reveals_to": _pairs(fm.get("reveals_to")),
                    "threads": _as_list(fm.get("threads")),
                    "resolves": _as_list(fm.get("resolves"))})
    return out


def story_discovery(repo):
    rel, text = read(repo, "docs/story/outline.md")
    if not text:
        return [fail("story:outline", "no story outline",
                     "write docs/story/outline.md with the premise, the acts and "
                     "the plot threads the reader is promised")]
    fm = frontmatter(text)
    acts = _as_list(fm.get("acts"))
    if not acts:
        acts = [l for l in text.splitlines()
                if re.match(r"^#{2,3}\s+(act|第\s*[一二三四五六七八九十\d]+\s*幕|chapter)",
                            l.strip(), re.IGNORECASE)]
    if len(acts) < 2:
        return [warn("story:acts", "fewer than two acts",
                     "a long story turns; two acts is the minimum that makes the "
                     "turn visible (frontmatter `acts: [setup, turn]`)")]
    threads = _as_list(fm.get("threads"))
    if not threads:
        return [warn("story:threads", "no plot threads declared",
                     "list the promises the story makes under `threads:` so the "
                     "chapters can be checked against them")]
    return [ok("story:outline", "%d act(s), %d thread(s)" % (len(acts), len(threads)))]


def story_design(repo):
    rel, text = read(repo, "docs/story/characters.md")
    if not text:
        return [fail("story:characters", "no characters document",
                     "write docs/story/characters.md with frontmatter lists for "
                     "characters and facts, and `knows:` for what each starts out "
                     "knowing")]
    fm = frontmatter(text)
    ids = _ids(fm)
    knows = _start_knowledge(fm)
    out = [ok("story:characters", rel)]
    if not ids["characters"]:
        out.append(fail("story:characters:list", "no characters declared",
                        "list them under `characters:`"))

    outline_fm = frontmatter(read(repo, "docs/story/outline.md")[1] or "")
    threads = set(_as_list(outline_fm.get("threads")))

    chapters = _story_chapters(repo)
    if not chapters:
        out.append(warn("story:chapters", "no chapter files yet",
                        "docs/story/chapters/<id>.md with id/order/pov frontmatter"))
        return out

    seen, orders = {}, {}
    for c in chapters:
        if c["id"] in seen:
            out.append(fail("story:chapter-id", "duplicate chapter id %s" % c["id"],
                            "rename one of %s and %s" % (seen[c["id"]], c["path"])))
        seen[c["id"]] = c["path"]
        if c["order"] is None:
            out.append(fail("story:order", "chapter %s has no `order:`" % c["id"],
                            "number the chapters; the order is what a reader "
                            "experiences and what continuity is checked against"))
        elif c["order"] in orders:
            out.append(fail("story:order-dup", "two chapters share order %d: %s and %s"
                            % (c["order"], orders[c["order"]], c["id"]),
                            "give each chapter a unique order number"))
        else:
            orders[c["order"]] = c["id"]

    bad_pov = ["%s -> %s" % (c["id"], c["pov"]) for c in chapters
               if c["pov"] and c["pov"] not in ids["characters"]]
    if bad_pov:
        out.append(fail("story:pov", "chapter POV is not a declared character: %s"
                        % ", ".join(bad_pov[:5]),
                        "declare them under `characters:` or fix the name"))

    unknown_fact = ["%s -> %s" % (c["id"], f) for c in chapters
                    for f in c["reveals"] if f not in ids["facts"]]
    if unknown_fact:
        out.append(fail("story:reveals", "chapter reveals a fact not established: %s"
                        % ", ".join(unknown_fact[:5]),
                        "declare the fact under `facts:`, or fix the id"))
    else:
        out.append(ok("story:reveals", "every reveal is established"))

    unknown_thread = ["%s -> %s" % (c["id"], t) for c in chapters
                      for t in c["threads"] + c["resolves"] if t not in threads]
    if unknown_thread:
        out.append(fail("story:threads-unknown",
                        "chapter uses a plot thread the outline never declares: %s"
                        % ", ".join(unknown_thread[:5]),
                        "declare it under `threads:` in docs/story/outline.md"))

    resolved = set(t for c in chapters for t in c["resolves"])
    open_threads = sorted(threads - resolved)
    if open_threads:
        out.append(warn("story:threads-open",
                        "plot thread(s) nobody resolves: %s" % ", ".join(open_threads),
                        "resolve each in a chapter's `resolves:` or drop the thread - "
                        "an abandoned promise is what readers call a plot hole"))
    else:
        out.append(ok("story:threads", "every thread is resolved"))

    ordered = sorted(chapters, key=lambda c: (c["order"] if c["order"] is not None
                                              else 10 ** 9, c["id"]))
    last_advance, first_resolve = {}, {}
    for c in ordered:
        if c["order"] is None:
            continue
        for t in c["threads"]:
            last_advance[t] = c["order"]
        for t in c["resolves"]:
            if t in threads:
                first_resolve.setdefault(t, c["order"])
    backwards = ["%s resolved at order %s, advanced at order %s"
                 % (t, r, last_advance[t])
                 for t, r in first_resolve.items()
                 if t in last_advance and last_advance[t] > r]
    if backwards:
        out.append(warn("story:threads-order",
                        "thread(s) resolved before their last appearance: %s"
                        % "; ".join(backwards[:5]),
                        "move the resolution after the last chapter that advances "
                        "the thread, or drop the late mention"))

    out.extend(_knowledge_checks("story", ids, knows, chapters))
    return out


# -- scaffold --------------------------------------------------------------

PILLARS = """# Pillars

- TODO: the first experience the game sells, and how the player feels it
- TODO: the second
- TODO: the third
"""

BIBLE = """---
characters: []
factions: []
locations: []
facts: []
knows: []
  # - aria: war-started      # facts a character knows before the story starts
---

# World bible

One paragraph: what is true in this world before any quest happens.
Every fact a quest reveals must be listed under `facts:`.
"""

QUEST_TEMPLATE = """---
id: q-example
act: 1
order: 10
requires: []
reveals: []
characters: []
factions: []
reveals_to: []
  # - aria: war-started
stakes: TODO - what the player loses if they fail or refuse
---

What the player does, what it costs, what changes. Copy this file to
`<id>.md`; files starting with `_` are templates and are not checked.
"""

OUTLINE = """---
acts: [setup, turn]
threads: []
  # - the-heir            # a promise the story makes and must resolve
---

# Outline

Premise: who wants what, and what stands in the way.

## Act 1 - setup

## Act 2 - turn
"""

CHARACTERS = """---
characters: []
facts: []
knows: []
  # - aria: war-started
want:
  # - aria: to reclaim the harbor her father lost
obstacle:
  # - aria: the guild holds the deed and the law is on its side
flaw:
  # - aria: trusts the wrong people when she is afraid
---

# Characters

One line each: what they want, what stands in the way, what is wrong with them.
"""

CHAPTER_TEMPLATE = """---
id: ch-01
order: 10
pov: aria
want: TODO - what the POV wants in this scene, in this moment
obstacle: TODO - what stands in the way, concretely
turn: TODO - what changes by the end, even if only for the POV
reveals: []
threads: []
resolves: []
reveals_to: []
---

What happens in this chapter, from the POV's eyes. A scene, not a summary:
place, bodies, what is said and what is not.
"""

TEMPLATES = {
    "game": {"docs/game/pillars.md": PILLARS,
             "docs/game/world-bible.md": BIBLE,
             "docs/game/quests/_template.md": QUEST_TEMPLATE},
    "story": {"docs/story/outline.md": OUTLINE,
              "docs/story/characters.md": CHARACTERS,
              "docs/story/chapters/_template.md": CHAPTER_TEMPLATE},
}


def scaffold(repo, name):
    """Write the empty structure a pack checks. Never overwrites, never fills."""
    files = TEMPLATES.get(name)
    if files is None:
        return None, "unknown pack %r (have: %s)" % (name, ", ".join(sorted(PACKS)))
    created, kept = [], []
    for rel in files:
        path = os.path.join(repo, *rel.split("/"))
        parent = os.path.dirname(path)
        while parent and os.path.abspath(parent) != os.path.abspath(repo):
            if os.path.exists(parent) and not os.path.isdir(parent):
                return None, ("%s exists and is not a directory; move it first "
                              "(nothing was changed unless listed above)"
                              % os.path.relpath(parent, repo))
            parent = os.path.dirname(parent)
    for rel, text in files.items():
        path = os.path.join(repo, *rel.split("/"))
        if os.path.exists(path):
            if os.path.isfile(path):
                kept.append(rel)
                continue
            return None, ("%s exists and is not a regular file; move it first "
                          "(nothing was changed unless listed above)" % rel)
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        except OSError as exc:
            return None, ("could not write %s: %s (files written before it were "
                          "kept: %s)" % (rel, exc, ", ".join(created) or "none"))
        created.append(rel)
    return {"created": created, "kept": kept}, None


PACKS = {
    "game": {"discovery": [game_discovery], "design": [game_design, game_craft],
             "title": "Open-world game",
             "stages": (0, 2), "playbook": "game.md"},
    "story": {"discovery": [story_discovery], "design": [story_design, story_craft],
              "title": "Long-form story",
              "stages": (0, 2), "playbook": "story.md"},
}
