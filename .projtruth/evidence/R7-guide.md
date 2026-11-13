# R7 guide prints the playbook for the blocking stage

```
$ python -m lifecycle guide design   # exit 0
# Stage 2 - Design

Choose a shape and record why, so the next session does not re-litigate a
settled question.

## Answer these

1. **What are the components, and how does data move between them?** Boxes are
   cheap; the arrows are the design.
2. **What did you reject?** Two alternatives, and the specific reason each lost.
   A design with no rejected option is a description of the first idea.
3. **What happens when a dependency fails?** Down database, slow network, bad
   data, 100x volume. The answer is a paragraph, not a shrug.
4. **What are the invariants?** What must always be true of the data, and where
   is it enforced?
5. **Which decision is expensive to reverse?** Storage model, 
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
2. **Who wants what?** Characters and factions with goals that conf
```

measured
