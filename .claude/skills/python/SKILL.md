# Python Skill (EXAMPLE — swap per project)

> Adjust the baseline and Ruff config below to the actual project. Keep the shape of this skill
> (baseline, imports, code quality rules, lint config) — replace the specific tool choices.

## Purpose

Define the Python implementation conventions for the project.

## Baseline (example)

- Python 3.11+
- Ruff
- Pydantic where typed domain/DTO models are appropriate
- Pytest
- A test-factory library (e.g. Polyfactory) where it improves test readability
- Whatever DI framework the project has chosen, if any — see `.claude/skills/dependency-injection/SKILL.md`

## Naming

Follow `.claude/skills/naming/SKILL.md`.

## Imports

Use this order:

1. Standard library
2. Third-party packages
3. Local application packages

Use Ruff/isort-compatible ordering.

Do not use `from __future__ import annotations` in any Python file.

- Why: annotations must be evaluated eagerly, because runtime-inspecting code (the DI container's
  `@autowired`, FastAPI, Pydantic) resolves them.
- For a forward or self reference, quote that single annotation, quoting the whole expression
  (e.g. `-> "MyClass | None"`).

## Code quality

- Use type hints consistently.
- Prefer focused classes and functions.
- Avoid circular imports.
- Avoid mutable global state.
- Keep configuration outside source code.
- Do not hardcode credentials or environment-specific values.
- Prefer explicit dependencies.
- Keep domain code independent from infrastructure concerns.

## Ruff (example baseline — tune per project)

```toml
[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
extend-select = ["Q", "RUF100", "C90", "UP", "I", "T"]
mccabe = { max-complexity = 10 }
```

Tests may use targeted per-file ignores where justified.
