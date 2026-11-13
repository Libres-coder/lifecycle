# R7 guide prints the playbook for the blocking stage

```
$ python -m lifecycle guide   # exit 0
# Stage 5 - Release

Make it usable by someone who was not in the room.

## Answer these

1. **What changed for the user?** Not for the codebase - for the person who has
   to decide whether to upgrade.
2. **How do they upgrade, and how do they roll back?** A release without a
   rollback path is a bet.
3. **What is known broken?** Name it; a known issue costs less trust than a
   surprise.
4. **What does the tag point at?** A version that matches the changelog, on a
   commit that was tested.

## Write

- `CHANGELOG.md` entry for the version - user-facing bullets, not a commit list;
- a git tag matching the version;
- release notes that say what changed, what broke and how to go back.

## Shallow looks like

A changelog that lists commits, a tag that does not match the version, or a
release with no mention of what is known broken.

## Exit

`lifecycle check --stage 5` passes, and a user
```

```
$ python -m lifecycle guide game   # exit 0
# Game pack - long-arc design

An open-world game's design is not an architecture document. It is a world that
has to stay consistent while hundreds of scenes are written out of order.

This pack adds checks to stages 0 and 2. It applies when `docs/game/` exists.

## Answer these

1. **What are the three pillars?** The experiences the game sells, each with how
   the player feels it. Every later decision is tested against these.
2. **Who wants what?** Characters and factions with goals that conflict. A
   faction with no goal is scenery.
3. **What facts are true in this world?** The lore a que
```

measured
