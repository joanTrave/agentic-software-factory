# Testing Skill

## Purpose

Define reliable and maintainable verification practices.

## Rules

- Every new behavior should have tests.
- Prefer unit tests for domain logic.
- Use integration tests at persistence/external boundaries.
- Use API tests for HTTP contracts.
- Test failure paths, not only happy paths.
- Keep tests deterministic.
- Do not depend on real external services in unit tests.
- Use factories for complex test data where they improve readability.
- Do not add a module-level docstring/comment block at the top of a test file. A well-named test
  file and well-named test functions are already self-explanatory; a top-of-file docstring
  restating "tests for X" or listing which fields/behaviors are covered just repeats what the
  file path and function names already say, and goes stale the moment a test is added or removed.
  The same applies to per-test docstrings that only restate the test's name. Keep a comment only
  when it explains something a reader couldn't infer from the code — a subtle invariant, a
  non-obvious edge case being deliberately tested, or a real constraint (e.g. why a specific date
  or magic value was chosen).

## API test conventions

In router/API test files, never hardcode the endpoint path or permission string inline in each
test function. Declare them as module-level constants instead:

- A single endpoint/permission used by every test in the file: `ENDPOINT = "..."` and
  `PERMISSION = "..."`.
- Multiple distinct endpoints/permissions in the same file (e.g. the endpoint under test plus a
  related one like an audit-log lookup): suffix each with a short descriptive name, e.g.
  `ENDPOINT_AUDIT_ENTITIES` / `PERMISSION_AUDIT_ENTITIES` alongside the unsuffixed `ENDPOINT` /
  `PERMISSION` for the primary one, or two suffixed pairs if there is no single "primary" endpoint.

See `tests/collaborators_liquidations/infrastructure/api/v1/test_collaborator_liquidation_history_router.py`
(single pair) and
`tests/collaborators_liquidations/infrastructure/api/v1/test_delete_collaborator_liquidation_router.py`
(primary pair plus a suffixed pair) for the existing pattern to match.

## Test organization

Mirror the source structure where practical:

```text
tests/
  <module>/
    domain/
    application/
    infrastructure/
```

## Coverage (adapt commands per project)

Run coverage with the project's actual test runner and package name, e.g.
`.venv/bin/pytest --cov=<package_name> --cov-report=term-missing` — always through the project's
own virtualenv/toolchain, never a bare `pytest`/global install, since a stale system copy can give
misleading results. The reviewer should factor this report into every approval decision, not just
whether tests pass.

**Watch for measurement artifacts before treating a low number as a real gap.** Some DI/service-
discovery frameworks re-compile `@service()`-style modules at test-session startup via a manual
`exec_module` call, which can make `coverage.py` report those specific files as 0%/near-0% even
when a normal test fully exercises them through the standard import path. If a project has this
kind of framework, maintain a short, explicit list here of the affected files/classes (verified
causally — e.g. by re-running the same test with `--noconftest` and confirming the number changes)
so the reviewer knows to check for a real test file (`grep -rl ClassName tests/`) before flagging
one of them as under-tested. Do not carry this project's artifact list into a project that doesn't
have the same framework quirk — re-derive it per project, or delete this paragraph if it doesn't
apply.

## Diff coverage gate (reviewer, mandatory)

New/changed code must have at least 90% diff coverage — coverage scoped to the lines the change
actually touches, not the file's or project's overall percentage. Measure it with `diff-cover`
against the branch's base:

```bash
.venv/bin/pytest --cov=<package_name> --cov-report=xml -q
.venv/bin/diff-cover coverage.xml --compare-branch=main --fail-under=90
```

`diff-cover` exits non-zero when diff coverage is below the threshold — the reviewer treats that as
a rejection unless every line it flags falls inside a documented known-measurement-artifact file
(see above). When `diff-cover` flags a line inside one of those listed files, check for a real test
covering that class before rejecting on the tool's number alone; when it flags a line in any other
file, treat it as a real gap and require a test before approval. `coverage.xml` is a generated file
(should be gitignored) — regenerate it fresh for each review, do not reuse a stale one.

## Lint and format compliance

Whoever writes or edits a test file is responsible for that file's ruff compliance — this is not
solely a developer-agent responsibility. Before reporting test-writing work as done, run the exact
ruff check used in CI: `ruff check . --exclude alembic/env.py` (config in `pyproject.toml` under
`[tool.ruff]`/`[tool.ruff.lint]`; pinned version in `bitbucket-pipelines.yml`, currently
`ruff@0.2.0` — match it, since a newer local ruff can silently diverge from what CI enforces). Also
run `ruff format --check .` and apply `ruff format` for anything unformatted. Fix every violation
in the files you touched.

## Completion checklist

- Happy path covered.
- Important edge cases covered.
- Error behavior covered.
- Relevant integration boundary covered.
- Test suite executed and result reported.
- Coverage report reviewed; any genuine (non-artifact) gap identified and justified or flagged.
- Ruff check and format check clean on every test file added or modified.
