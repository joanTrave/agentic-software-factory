# example-api

A modular-monolith FastAPI service: one deployable exposing several bounded-context modules under
`src/`, each structured `domain/` -> `application/` -> `infrastructure/`. See
[`docs/constitution.md`](docs/constitution.md) for the full stack/structure contract,
[`docs/best_practices.md`](docs/best_practices.md) for the coding patterns PR-Agent enforces, and
[`docs/custom_implementations/README.md`](docs/custom_implementations/README.md) for the reference
primitives wired into `src/core/`.

## The rule in three lines

- `domain/` has no framework imports; `application/` orchestrates use cases against domain
  interfaces; `infrastructure/` implements those interfaces and is the only layer allowed to
  import frameworks/drivers.
- One module = one bounded context. A module never imports another module's `infrastructure/`
  directly — cross-module calls go through the other module's application-layer use case.
- Every module mirrors its `src/<module>/` tree under `tests/<module>/`.

## Getting started

```sh
cp .env.example .env
docker compose up          # starts api + db
docker compose run --rm test   # the one command that runs the full suite, against a real db
```

`docker compose up` does **not** also run the test suite (it sits behind the `test` profile) —
`docker compose run --rm test` is the sanctioned command, locally and in CI.

## Adding a new bounded context

Copy the `src/health/` layout (it is itself a full module, just one with no persistence) as a
starting template:

```text
src/<module>/
  domain/{bo,enums,exceptions,repositories}/
  application/{use_case_name}/{i_<use_case>.py, <use_case>.py, serializers/}
  infrastructure/
    api/v1/{action}_{entity}_router.py
    database/models/{entity}_model.py
    database/repositories/{entity}_query_service_sql.py
    database/fixtures/   # idempotent seed data, if any
tests/<module>/          # mirrors the tree above
```

Then:

1. Add the module's `infrastructure/database/models/` import to
   `src/core/infrastructure/database/sql/metadata.py` so Alembic autogenerate sees its tables.
2. Register the module's `v1` router in `src/app.py`'s explicit include list.
3. Generate the migration: `alembic revision --autogenerate -m "add <module> tables"`, review the
   generated file, then `alembic upgrade head`.

Follow `docs/best_practices.md`'s numbered patterns and `.claude/skills/naming/SKILL.md` for
naming — in particular, this project resolves the one conflict between them (use-case action
method naming) in favor of `best_practices.md`'s `execute()` (see
`.claude/tasks/constitution/plan/plan.md` §1.1, CF1).

## Running checks locally

```sh
uv sync --all-groups
uv run ruff check . --exclude alembic/env.py
uv run ruff format --check .
```

The pinned ruff version in `pyproject.toml`'s `[dependency-groups]` is authoritative over whatever
is installed locally or in CI's own tool cache.

## Database migrations

One Alembic migration per logical schema change, generated and reviewed, never hand-edited after
being applied anywhere:

```sh
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
```

## Health check

`GET /api/example-api/v1/health` is unauthenticated by design (it is what the container
orchestrator polls for liveness/readiness, so it must never depend on auth or another service) and
verifies the database connection through the application's own session factory. `200` when
healthy, `503` with a structured body when not.
