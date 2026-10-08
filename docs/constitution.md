# api-service

A modular-monolith API: one FastAPI service exposing several bounded-context modules
(orders, products, clients, billing, notifications, ...), each internally structured as
domain/application/infrastructure per `.claude/skills/architecture/SKILL.md`.

## Stack

- Language: Python >=3.11,<3.14
- Framework: FastAPI (ASGI, served via gunicorn/uvicorn workers), SQLAlchemy 1.4 + Alembic migrations
- Package manager: uv (`pyproject.toml` + `uv.lock`)
- Testing: pytest + pytest-cov + polyfactory (test data factories) + requests-mock/moto for external
  services
- Lint/format: ruff (lint + format), enforced in CI
- Containerization: Docker (dev image + prod image), docker-compose for local dependencies

## Structure

​```text
src/
src/core/
src/<module>/
src/<module>/domain/
src/<module>/domain/bo/
src/<module>/domain/enums/
src/<module>/domain/exceptions/
src/<module>/domain/repositories/
src/<module>/application/
src/<module>/infrastructure/
src/<module>/infrastructure/api/
src/<module>/infrastructure/database/
src/<module>/infrastructure/database/models/
src/<module>/infrastructure/database/repositories/
src/<module>/infrastructure/database/fixtures/
src/health/
src/health/domain/
src/health/application/
src/health/infrastructure/
src/health/infrastructure/api/
src/health/infrastructure/database/
src/app.py
tests/
tests/<module>/
tests/conftest.py
tests/stress/
alembic/
alembic/versions/
alembic/env.py
alembic.ini
templates/
translations/
infra/
docs/
docs/custom_implementations/
scripts/
Dockerfile
Dockerfile-prod
docker-compose.yml
entrypoint.sh
gunicorn.conf.py
pyproject.toml
README.md
​```

## Conventions

- Dependency direction is strict: `domain` has no framework imports; `application` orchestrates
  use cases against domain interfaces; `infrastructure` implements those interfaces (DB models,
  repositories, API routers) and is the only layer allowed to import frameworks/drivers.
- One module = one bounded context. A module never imports another module's `infrastructure` layer
  directly — cross-module calls go through application-layer use cases.
- Every module mirrors its `src/<module>/` tree under `tests/<module>/` (unit tests close to domain
  logic, integration tests against a real test database via containerized fixtures, not mocks, for
  anything crossing the persistence boundary).
- Database schema changes are Alembic migrations under `alembic/versions/`, one migration per
  logical schema change, generated and reviewed — never hand-edited after being applied anywhere.
- Custom domain exceptions extend a shared base exception type (see `docs/best_practices.md`
  Pattern 6) rather than raising bare `Exception`/framework exceptions from domain or application
  code.
- Serializers are Pydantic models built `from_bo` (business object) rather than coupling API schemas
  directly to SQLAlchemy models (see `docs/best_practices.md` Pattern 9).
- `ruff check` and `ruff format --check` must pass with zero violations before a change is
  considered done; the pinned ruff version in `pyproject.toml`/CI is authoritative over whatever
  version is installed locally.
- The project's custom cross-cutting primitives (`CustomException`, `@requires_permissions`,
  `@with_transaction`) are not reinvented per module — reference implementations live in
  `docs/custom_implementations/` (see `docs/custom_implementations/README.md`), wired to the
  project's real session factory/auth stack once at startup.
- The service exposes an unauthenticated `GET /health` endpoint, structured as its own module
  (`src/health/`) like any other bounded context rather than a one-off route bolted onto `app.py`.
  It verifies the service's critical dependencies (at minimum the database connection) and
  returns `200` when healthy, `503` with a structured error body when not — this is what the
  container orchestrator / load balancer polls for liveness and readiness, so it must never
  itself depend on authentication, another service being up, or any state the service can't
  verify on its own.
- `docker-compose.yml` must be runnable as-is (`docker compose up`) and define at least three
  services:
  - `api` — the application, built from `Dockerfile`, reading its configuration from `.env`,
    waiting on `db`'s healthcheck before starting (`depends_on: db: condition: service_healthy`),
    migrating the schema and then starting the app server as its container command (mirroring
    `entrypoint.sh`).
  - `test` — the same image as `api`, overriding the entrypoint to run the test suite against `db`
    instead of starting the server; this is the one command a developer or CI runs to execute the
    full test suite in a clean, reproducible environment, not a convenience alias for a locally
    configured interpreter.
  - `db` — the project's database engine (Postgres by default) with a healthcheck, seed credentials
    matching `.env`'s database variables, and a named volume so data survives a container restart.
  `Dockerfile` is multi-stage: a builder stage that installs dependencies via the project's package
  manager, and a final stage that copies only the built artifacts (not build tooling) and runs as a
  non-root user. `Dockerfile-prod` is the same shape tuned for production (no dev/test dependency
  groups, no bind-mounted source).
