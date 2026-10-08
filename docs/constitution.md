# backoffice-api

A modular-monolith backoffice API: one FastAPI service exposing several bounded-context modules
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
