# Contributing

Two rules:

- **A check must be checkable.** If a human cannot verify it from the
  repository, it is a checklist item, not a gate.
- **Never make a passing stage harder to reach.** A gate that fails on a
  healthy repository gets deleted by its users.

```bash
python -m unittest discover -s tests -v
python -m lifecycle --repo . status
```

The repository follows its own contract: vision, requirements with criteria,
architecture, decisions, tests, evidence, changelog and a tag. Adding a stage
means adding it to `lifecycle/contract.py` and to `docs/design/architecture.md`.
