# constitution — Implementation Plan

Bootstrap of `example-api`: a greenfield modular-monolith FastAPI service whose skeleton is fully
specified by `docs/constitution.md`. This plan tells the Tester and the Developer what to build,
file by file, and — for every file — **which source decided its content**.

- Requirements source: `docs/constitution.md` (there is no mission spec for this task).
- Repository state at planning time: no `src/`, `tests/`, `alembic/`, `Dockerfile`, or
  `pyproject.toml` exists. Only `CLAUDE.md`, `.gitignore`, `.claude/` and `docs/` are present.
  Everything below is an ADD.

---

## 1. Source-priority rule

Every file's content is decided by the first source, in this order, that has something to say
about it:

| # | Source | Authority |
|---|---|---|
| 1 | `docs/constitution.md` (`## Stack`, `## Conventions`, anything it explicitly requires) | Binding. Overrides everything below. |
| 2 | `docs/best_practices.md` | Binding pattern shapes. Apply the matching numbered pattern's "Example code after". |
| 3 | `docs/custom_implementations/` | Reuse `CustomException`, `@requires_permissions`, `@with_transaction` — do not reinvent. |
| 4 | `.claude/skills/*/SKILL.md` (architecture, naming, dependency-injection, testing, python) | Fills every gap the three above leave. Marked "EXAMPLE — adapt per project", so it yields to 1–3. |

Each file section below names its deciding source explicitly as `Decided by: <n> — <where>`.

### 1.1 Conflict register (resolved here once, do not re-litigate per file)

| # | Conflict | Resolution | Rationale |
|---|---|---|---|
| CF1 | Use-case action method: naming skill forbids `execute()` and mandates `get_pokemon()`; `best_practices.md` Patterns 3/4/9 all use `execute()` | **`execute()`** | Source 2 outranks source 4; `best_practices.md` is PR-Agent-enforced, the naming skill is self-labelled "EXAMPLE". Flagged as Q1 for the human. |
| CF2 | Repository naming: naming skill says `I{Entity}QueryRepository` / `SqlAlchemy{Entity}QueryRepository`; `best_practices.md` Pattern 12 says `I{Entity}QueryService` / `{Entity}QueryServiceSQL` | **Pattern 12 names** | Source 2 outranks source 4. |
| CF3 | Repository/model path: constitution's tree has `infrastructure/database/models/`; `best_practices.md` imports `infrastructure.database.sql.models` | **No `sql/` level under `src/<module>/`** (constitution wins); **keep `sql/` under `src/core/`**, whose tree the constitution does not expand, so `best_practices.md`'s literal import `src.core.infrastructure.database.sql.session_manager` stays valid | Source 1 wins where it speaks; source 2 fills the rest. |
| CF4 | Pattern 6 imports `from custom_exceptions import CustomException` (a bare top-level module) | Place it at `src/core/domain/exceptions/custom_exception.py` | `docs/custom_implementations/README.md` calls these "starting points … wire to the project's real stack"; a bare top-level module contradicts the constitution's `src/`-rooted tree. Pattern 6's import line is shorthand. |
| CF5 | Pattern 5 says *every* router endpoint needs `@requires_permissions`; the constitution requires `GET /health` to be unauthenticated | **Health is the single documented exception** | Source 1 is explicit and names the reason (orchestrator liveness probing). Recorded in the health router as a comment and in `docs/`. |
| CF6 | The `## Structure` tree omits files the constitution's prose requires (`uv.lock`, `.env`) and standard tooling files (`.env.example`, `.dockerignore`, CI config) | Tree is **illustrative, not exhaustive**; add them | `## Stack` names `uv.lock`; `## Conventions` names `.env`. |

---

## 2. Target tree (resolved)

```text
src/
  core/
    domain/
      enum.py                                  # CustomEnum
      exceptions/custom_exception.py           # CustomException, CustomNotFoundException
    application/                               # (empty at bootstrap)
    infrastructure/
      api/
        exception_handlers.py                  # custom_exception_handler
        security/requires_permissions.py       # @requires_permissions
      config/settings.py                       # Settings (pydantic-settings)
      database/sql/
        base.py                                # declarative Base, BaseModelPgSQL
        engine.py                              # engine + sessionmaker factory
        session_manager.py                     # session_manager(), @with_transaction, configure_session_factory()
        metadata.py                            # imports every module's models (alembic autogenerate target)
        repositories/i_database_repository_sql.py   # IDatabaseRepositorySQL (self.db)
      logging/logging_config.py
      bootstrap.py                             # DI discovery + session factory wiring
  health/
    domain/
      bo/health_report.py, bo/dependency_check.py
      enums/health_status_enum.py
      repositories/i_health_query_service.py
    application/check_health/
      i_check_health_use_case.py, check_health_use_case.py
      serializers/health_output.py
    infrastructure/
      api/v1/health_router.py
      database/health_query_service_sql.py
  <module>/ …                                  # template, see §4
  app.py
tests/
  conftest.py
  core/ , health/ , <module>/                  # mirror of src
  stress/
alembic/
  env.py
  versions/
alembic.ini
templates/
translations/
infra/
docs/            (exists)
scripts/
Dockerfile
Dockerfile-prod
docker-compose.yml
entrypoint.sh
gunicorn.conf.py
pyproject.toml
uv.lock          (generated)
.env.example     (committed; .env is gitignored)
.dockerignore
README.md
```

---

## 3. `src/core/` — shared foundation

`src/core/` is not a bounded context; it holds the cross-cutting primitives every module imports.
It must contain **no business rules**. Nothing in `core` may import from a module.

| File | What it implements | Decided by |
|---|---|---|
| `domain/exceptions/custom_exception.py` | `CustomException` (sets `self.message` + `self.reason`) and `CustomNotFoundException`. Copied verbatim from `docs/custom_implementations/custom_exception.py` **minus** its `try: from fastapi …` block — domain must not import a framework. | 3 — `docs/custom_implementations/custom_exception.py:13-44`; Pattern 1 forces the FastAPI split |
| `infrastructure/api/exception_handlers.py` | `custom_exception_handler(request, exc)` → `JSONResponse({"detail", "reason"})`, 404 when `reason` ends `NotFound`, else 400. Registered once in `app.py`. | 3 — `custom_exception.py:57-62` |
| `domain/enum.py` | `CustomEnum` — `str`-valued enum base giving consistent serialization/validation; `_missing_` for case-tolerant parsing, `__str__` returning the value, and a `values()` classmethod. | 2 — Pattern 7 (import path `src.core.domain.enum`) |
| `infrastructure/api/security/requires_permissions.py` | `@requires_permissions([...])` — 403 with `{"detail": "Required permissions: a, b"}` when the caller holds none. Reference implementation **with its unverified-JWT read replaced** by a call into the project's token verification (signature/issuer/audience/expiry) before the claim read. | 3 — `requires_permissions.py:52-80`; README's "replace … before relying on it" |
| `infrastructure/database/sql/session_manager.py` | `configure_session_factory()`, `session_manager()`, `@with_transaction`. Verbatim from the reference implementation — import path must stay exactly `src.core.infrastructure.database.sql.session_manager`. | 3 — `with_transaction.py`; 2 — Pattern 3 import line |
| `infrastructure/database/sql/base.py` | Declarative `Base` plus `BaseModelPgSQL` mixin: `id` UUID PK (`uuid4` default), `created_at`/`updated_at` timestamptz. | 2 — Pattern 2 (`class PokemonModelSQL(BaseModelPgSQL, Base)`) |
| `infrastructure/database/sql/repositories/i_database_repository_sql.py` | `IDatabaseRepositorySQL` — exposes `self.db` as a property resolving the active session via `session_manager()`, so repositories never open their own. | 2 — Pattern 8 ("inherit from both the interface and `IDatabaseRepositorySQL`. Use `self.db`") |
| `infrastructure/database/sql/engine.py` | Builds `create_engine(settings.database_url, pool_pre_ping=True, pool_size=…, future=False)` + `sessionmaker`. SQLAlchemy **1.4** API (`Query`-style, per Pattern 8's `self.db.query(...)`), not 2.0 style. | 1 — `## Stack` "SQLAlchemy 1.4" |
| `infrastructure/database/sql/metadata.py` | Imports every module's `models` package so `Base.metadata` is complete for Alembic autogenerate. Single place to register a new module's tables. | 1 — `## Conventions` (migrations are generated, so autogenerate must see all models) |
| `infrastructure/config/settings.py` | `Settings(BaseSettings)` — see §6. Single source for every env var; nothing else calls `os.getenv`. | 4 — python skill "Keep configuration outside source code" |
| `infrastructure/logging/logging_config.py` | JSON structured logging to stdout, level from `LOG_LEVEL`, request-id propagation. | 4 — architecture skill (observability is not decided by 1–3) |
| `infrastructure/bootstrap.py` | `bootstrap()`: load `Settings` → configure logging → `discover_services(get_executable_parent_path(src.__file__))` → build engine/sessionmaker → `configure_session_factory(...)`. Idempotent; called by `app.py` and by `tests/conftest.py`. | 4 — DI skill "Application bootstrap"; 3 — `configure_session_factory` |

---

## 4. `src/<module>/` — the bounded-context template

One module = one bounded context (orders, products, clients, billing, notifications). A module
never imports another module's `infrastructure/`; cross-module calls go through the other
module's application-layer use case interface. Dependency direction: `domain ← application ←
infrastructure`.

| Path | Contains | Decided by |
|---|---|---|
| `domain/bo/` | Business Objects — Pydantic models, PascalCase, **no** imports from `application/` or `infrastructure/`. | 2 — Patterns 1, 12 |
| `domain/enums/` | `{Name}Enum(CustomEnum)`. | 2 — Pattern 7 |
| `domain/exceptions/` | `{Name}Exception(CustomException)` / `(CustomNotFoundException)`, each setting `message` + `reason`. Never a bare `Exception`. | 1 — `## Conventions`; 2 — Pattern 6 |
| `domain/repositories/` | ABCs: `i_{entity}_query_service.py` → `I{Entity}QueryService`, `i_{entity}_command_repository.py` → `I{Entity}CommandRepository`. Command side only when a write use case exists. | 2 — Pattern 12 (CF2); 4 — naming skill for the file-name casing and the "only when needed" rule |
| `application/{use_case_name}/` | `i_{use_case_name}.py` (ABC), `{use_case_name}.py` (`@service()` + `@autowired` ctor, injected **by interface**), `serializers/` (Pydantic in/out DTOs with `from_bo()`). Action method `execute()`. Writes carry `@with_transaction`. | 2 — Patterns 3, 4, 9; 4 — naming skill for the directory layout |
| `infrastructure/api/v1/` | `{action}_{entity}_router.py` — `APIRouter`, `response_model=` a serializer, `@requires_permissions([...])`, `Request` parameter present (the decorator needs it). Never returns a BO. | 2 — Patterns 5, 9; 3 — `requires_permissions.py:22-26` |
| `infrastructure/database/models/` | `{entity}_model.py` → `{Entity}ModelSQL(BaseModelPgSQL, Base)`, `__tablename__` plural snake_case, with `from_bo()` staticmethod and `to_bo()` method. | 2 — Patterns 2, 12 |
| `infrastructure/database/repositories/` | `{entity}_query_service_sql.py` → `@service() class {Entity}QueryServiceSQL(I{Entity}QueryService, IDatabaseRepositorySQL)` using `self.db`. | 2 — Pattern 8; 1 — path has no `sql/` level (CF3) |
| `infrastructure/database/fixtures/` | Idempotent seed/reference data loaders (catalogues, lookup tables) invoked from `scripts/`. Not test data — test factories live under `tests/`. | 4 — nothing in 1–3 decides this |

---

## 5. Health module — design (deliverable **(a)**)

### 5.1 Why it is a module

`## Conventions` requires `src/health/` to be "structured as its own module … like any other
bounded context rather than a one-off route bolted onto `app.py`". It therefore gets the full
domain/application/infrastructure split, even though it owns no tables.

### 5.2 Route and mounting

- Router prefix: `/api/example-api/v1` (the project-wide API prefix, from Pattern 11's
  `ENDPOINT = "/api/example-api/v1/pokemons"`), path `/health`.
- **Effective URL: `GET /api/example-api/v1/health`.**
- Included in `app.py` **first**, before any auth-bearing router.
- **No** `@requires_permissions`, no auth dependency, no middleware that can reject it (CF5). The
  endpoint must never depend on authentication, another service, or anything the service cannot
  verify alone.
- Not rate-limited, excluded from access-log sampling to avoid drowning the log in probe noise.

### 5.3 How the database is verified

`HealthQueryServiceSQL(IHealthQueryService, IDatabaseRepositorySQL)` runs the cheapest possible
round-trip that proves a real connection was acquired and a statement executed:

```
self.db.execute(text("SELECT 1")).scalar()
```

Deliberate properties:

- Uses the **same** engine/sessionmaker the application serves requests with (via
  `IDatabaseRepositorySQL.self.db` → `session_manager()`), so the probe exercises the real
  connection path — including `pool_pre_ping`, credentials and network — rather than opening a
  second, differently-configured connection that could succeed while the app's pool is exhausted.
- **No** `@with_transaction`. The check is read-only, and on failure the decorator's
  `session.rollback()` would itself raise against a dead connection and mask the original error.
- Wrapped in a per-check deadline (`HEALTHCHECK_DB_TIMEOUT_SECONDS`, default `2`) applied as a
  statement timeout on the connection, so a hung database produces a fast `503` instead of a
  request that outlives the orchestrator's own probe timeout.
- Catches `SQLAlchemyError` (and `RuntimeError` from an unconfigured session factory) and returns a
  failed `DependencyCheck` — it never lets an exception escape to the generic 500 handler, because
  a 500 and a 503 mean different things to a load balancer.
- Measures elapsed milliseconds and returns it, so a *degrading* database is visible before it is
  a *down* database.

### 5.4 Files

| File | Implements | Decided by |
|---|---|---|
| `domain/enums/health_status_enum.py` | `HealthStatusEnum(CustomEnum)`: `HEALTHY` / `UNHEALTHY`; `DependencyStatusEnum`: `UP` / `DOWN`. | 2 — Pattern 7 |
| `domain/bo/dependency_check.py` | `DependencyCheck` BO: `name`, `status`, `latency_ms`, `error` (sanitized, optional). | 2 — Pattern 1 |
| `domain/bo/health_report.py` | `HealthReport` BO: `checks: list[DependencyCheck]` + computed `status` = `UNHEALTHY` if any check is `DOWN`. This aggregation rule is the module's only domain logic and is unit-testable with no database. | 4 — architecture skill |
| `domain/repositories/i_health_query_service.py` | `IHealthQueryService(ABC)` with `check_database_connection() -> DependencyCheck`. | 2 — Pattern 8; 4 — DI skill |
| `application/check_health/i_check_health_use_case.py` | `ICheckHealthUseCase(ABC)` → `execute() -> HealthReport`. | 2 — Pattern 4; CF1 |
| `application/check_health/check_health_use_case.py` | `@service() class CheckHealthUseCase(ICheckHealthUseCase)`, `@autowired __init__(self, health_query_service: IHealthQueryService)`. Collects every dependency check, builds the `HealthReport`. Adding a future dependency (cache, queue) means adding a check here, not touching the router. | 2 — Patterns 3, 4 |
| `application/check_health/serializers/health_output.py` | `HealthOutput` / `DependencyCheckOutput` Pydantic models with `from_bo()`. | 2 — Pattern 9 |
| `infrastructure/database/health_query_service_sql.py` | `@service() class HealthQueryServiceSQL(IHealthQueryService, IDatabaseRepositorySQL)` — §5.3. Lives directly under `infrastructure/database/` (the constitution's `src/health/` tree has no `repositories/` level). | 1 — `## Structure` lines 40; 2 — Pattern 8 |
| `infrastructure/api/v1/health_router.py` | The endpoint — §5.5. | 1 — `## Conventions`; 2 — Pattern 9 |

### 5.5 Responses

Healthy — **200**:

```json
{
  "status": "healthy",
  "checks": [{"name": "database", "status": "up", "latency_ms": 3}]
}
```

Unhealthy — **503**:

```json
{
  "status": "unhealthy",
  "detail": "One or more critical dependencies are unavailable.",
  "reason": "healthCheckFailed",
  "checks": [{"name": "database", "status": "down", "latency_ms": 2012, "error": "OperationalError"}]
}
```

Implementation notes:

- The router **returns** a `JSONResponse(status_code=200|503, content=HealthOutput.from_bo(report).model_dump())`
  rather than raising a `CustomException`. The shared handler
  (`custom_exception_handler`) can only emit 400 or 404, so it cannot express 503; raising would
  produce the wrong status code for a load balancer. The 503 body keeps `detail` + `reason` so it
  is still shape-compatible with every other error body in the API.
- `response_model=HealthOutput` is declared on the route for OpenAPI, with
  `responses={503: {"model": HealthOutput}}`.
- `error` carries the **exception class name only**, never `str(exc)` — a SQLAlchemy
  `OperationalError` message embeds the DSN, including the password, and this endpoint is
  unauthenticated. The full exception is logged at `ERROR` with a request id.

### 5.6 Liveness vs readiness

A single endpoint serves both probes. Docker/compose and the orchestrator point their liveness
**and** readiness checks at `GET /api/example-api/v1/health`. The constitution does not ask for
split probes; if one is needed later, add `/health/live` (process-only, always 200) next to the
existing dependency-checking route. Recorded as Q2.

---

## 6. Environment variables (deliverable **(b)**)

All read exactly once, in `src/core/infrastructure/config/settings.py`, via
`pydantic-settings.BaseSettings` (`env_file=".env"`, `extra="ignore"`). No other module calls
`os.getenv`. Validation failure at startup is fatal and loud — the service must not boot
half-configured.

### 6.1 Minimum to run

**`DATABASE_URL` is the only variable with no default.** With it set, the service starts.

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | **yes** | — | SQLAlchemy DSN, e.g. `postgresql+psycopg2://example:example@db:5432/example_api`. Consumed by `engine.py` and `alembic/env.py`. |

### 6.2 Database container credentials (consumed by the `db` service, same `.env`)

Required by `## Conventions`: "seed credentials matching `.env`'s database variables".

| Variable | Default (dev) | Purpose |
|---|---|---|
| `POSTGRES_USER` | `example` | Postgres image bootstrap user; must match `DATABASE_URL`. |
| `POSTGRES_PASSWORD` | `example` | Dev-only value in `.env.example`; never a real secret in git. |
| `POSTGRES_DB` | `example_api` | Bootstrap database; must match `DATABASE_URL`. |

### 6.3 Everything else (defaulted — the service runs without them)

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `local` | `local` / `test` / `staging` / `production`. Gates `/docs` exposure and log format. |
| `LOG_LEVEL` | `INFO` | Root log level. |
| `PORT` | `8000` | Bind port for gunicorn. |
| `TEST_DATABASE_URL` | derived: `DATABASE_URL` with `_test` appended to the database name | Target of the compose `test` service, so running tests never truncates dev data. |
| `DB_POOL_SIZE` | `5` | Engine pool size. |
| `DB_MAX_OVERFLOW` | `10` | Engine overflow. |
| `DB_POOL_PRE_PING` | `true` | Discard dead connections before use — also what makes the health probe meaningful. |
| `HEALTHCHECK_DB_TIMEOUT_SECONDS` | `2` | §5.3 deadline. |
| `GUNICORN_WORKERS` | `(2 × CPU) + 1`, capped at `8` | Worker count. |
| `GUNICORN_TIMEOUT` | `60` | Worker timeout (seconds). |
| `COGNITO_REGION`, `COGNITO_USER_POOL_ID`, `COGNITO_CLIENT_ID` | unset | JWKS/issuer/audience for real token verification. Unset is tolerated in `local`/`test` (the mock fixture signs tokens); **required** when `APP_ENV` is `staging`/`production` — enforced by a `Settings` validator, so a deployment can't silently run with authentication disabled. |

`.env.example` is committed with every variable and dev-safe values. `.env` is gitignored.

---

## 7. Docker setup (deliverable **(c)**)

### 7.1 `Dockerfile` (dev/CI image) — multi-stage

Decided by 1 — `## Conventions` ("builder stage that installs dependencies via the project's
package manager, and a final stage that copies only the built artifacts (not build tooling) and
runs as a non-root user") and `## Stack` (uv, Python >=3.11,<3.14).

**Stage 1 `builder`** — `python:3.12-slim`:
1. Copy the pinned `uv` binary in from `ghcr.io/astral-sh/uv:<pinned>` (no `pip install uv`, no
   network package resolution at build time beyond the lockfile).
2. Install only the build-time OS packages `psycopg2` needs (`build-essential`, `libpq-dev`).
3. `COPY pyproject.toml uv.lock ./`
4. `uv sync --frozen --no-install-project` — **all** groups including dev/test. This layer is
   cached on the lockfile alone, so a source edit does not re-resolve dependencies.
5. Result: a self-contained `/app/.venv`.

**Stage 2 (final)** — `python:3.12-slim`:
1. Install only the **runtime** OS package `libpq5`. No compiler, no `uv`, no `build-essential`.
2. `COPY --from=builder /app/.venv /app/.venv`; `ENV PATH="/app/.venv/bin:$PATH"`,
   `PYTHONUNBUFFERED=1`, `PYTHONDONTWRITEBYTECODE=1`.
3. `COPY` the source: `src/`, `alembic/`, `alembic.ini`, `entrypoint.sh`, `gunicorn.conf.py`,
   `pyproject.toml`, `templates/`, `translations/`, `tests/` (the `test` compose service runs from
   this same image).
4. `RUN adduser --system --group appuser && chown -R appuser:appuser /app`; `USER appuser`.
5. `EXPOSE 8000`; `ENTRYPOINT ["/app/entrypoint.sh"]`.

`.dockerignore` excludes `.git`, `.venv`, `.idea`, `__pycache__`, `.pytest_cache`, `coverage.xml`,
`.env` — the build must never bake a real `.env` into a layer.

### 7.2 `Dockerfile-prod`

Same two-stage shape, tuned for production (1 — `## Conventions`):

- Builder runs `uv sync --frozen --no-dev --no-group test` — no pytest, polyfactory, moto, ruff,
  diff-cover in the image.
- Final stage does **not** copy `tests/`, and the compose dev bind-mount does not apply to it.
- `APP_ENV=production` baked as a default; `/docs` and `/openapi.json` disabled by `app.py` when
  `APP_ENV == production`.
- Non-root `appuser`, read-only-friendly layout (no writes outside `/tmp`).
- `HEALTHCHECK CMD` curling `http://localhost:${PORT}/api/example-api/v1/health`.

### 7.3 `docker-compose.yml`

Must be runnable as-is with `docker compose up` (1 — `## Conventions`), and define `api`, `test`,
`db`.

**`db`** — `postgres:16-alpine`
- `env_file: [.env]` → consumes `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (§6.2).
- `healthcheck: pg_isready -U $POSTGRES_USER -d $POSTGRES_DB`, `interval: 5s`, `timeout: 3s`,
  `retries: 10`, `start_period: 5s`.
- Named volume `example-api-db-data:/var/lib/postgresql/data` — data survives a restart.
- Mounts `scripts/init_test_db.sh` into `/docker-entrypoint-initdb.d/` so the `*_test` database
  exists on first boot.
- Port `5432` published for local tooling.

**`api`** — the application
- `build: {context: ., dockerfile: Dockerfile}`.
- `env_file: [.env]`.
- `depends_on: {db: {condition: service_healthy}}` — literally as the constitution requires.
- `ports: ["${PORT:-8000}:8000"]`.
- Dev bind-mounts `./src` and `./tests` for reload-free iteration.
- Container command is `./entrypoint.sh`: migrate, then start the app server — mirroring
  `entrypoint.sh` rather than duplicating its steps inline.
- Its own `healthcheck` hits `GET /api/example-api/v1/health`.

**`test`** — the same image, entrypoint overridden
- `build:` identical to `api` (same Dockerfile, so the image is shared, not rebuilt differently).
- `entrypoint: [""]`, `command: ["sh", "-lc", "alembic upgrade head && pytest --cov=src --cov-report=term-missing --cov-report=xml"]`.
- `environment: {DATABASE_URL: "${TEST_DATABASE_URL}"}` — runs against `db` but a **separate
  database**, so the suite's truncation never destroys dev data.
- `depends_on: {db: {condition: service_healthy}}`.
- `profiles: ["test"]`, so a bare `docker compose up` starts `api` + `db` only and does not also
  fire the suite. The single command a developer or CI runs is
  **`docker compose run --rm test`** — a real containerized run against `db`, not an alias for a
  locally configured interpreter.

### 7.4 `entrypoint.sh`

```sh
#!/bin/sh
set -eu
alembic upgrade head
exec gunicorn "src.app:app" --config gunicorn.conf.py
```

`exec` so gunicorn becomes PID 1 and receives `SIGTERM` directly (clean shutdown, no 10-second
kill delay). Executable bit committed (`git update-index --chmod=+x`). Decided by 1 —
`## Conventions` ("migrating the schema and then starting the app server").

### 7.5 `gunicorn.conf.py`

| Setting | Value | Why |
|---|---|---|
| `bind` | `0.0.0.0:${PORT}` | |
| `worker_class` | `uvicorn.workers.UvicornWorker` | 1 — `## Stack` "served via gunicorn/uvicorn workers" |
| `workers` | `GUNICORN_WORKERS` | §6.3 |
| `timeout` / `graceful_timeout` / `keepalive` | `GUNICORN_TIMEOUT` / `30` / `5` | |
| `preload_app` | `False` | Each worker must build its **own** engine and session factory. Preloading forks a parent that already opened TCP sockets, and forked children sharing pooled connections corrupt them. |
| `accesslog` / `errorlog` | `-` (stdout/stderr) | Container-native logging |
| `access_log_format` | includes request id and duration | |

---

## 8. Root file plans — the remaining `## Structure` file lines

### `src/app.py`
**Decided by:** 1 — `## Stack` (FastAPI), `## Conventions` (health is a module, not a route here);
3 — exception-handler registration; 4 — DI skill bootstrap ordering.

Exposes `create_app() -> FastAPI` plus a module-level `app = create_app()` (the `src.app:app`
gunicorn target). Responsibilities, in this exact order:

1. `bootstrap()` (§3) — settings, logging, DI service discovery, engine, `configure_session_factory`.
   DI discovery must complete **before** any `@autowired` constructor runs.
2. `FastAPI(title="example-api", version=…, docs_url=None if APP_ENV == "production" else "/docs")`.
3. `app.add_exception_handler(CustomException, custom_exception_handler)`.
4. Include routers: health first, then each module's `v1` router, all under prefix
   `/api/example-api/v1`. The include list is an **explicit import list**, not filesystem
   autodiscovery — "prefer explicit dependencies over service locators and hidden globals"
   (architecture skill), and an explicit list makes an accidentally unmounted router a review-visible
   diff.

Contains **no** business logic, no route definitions, no SQL.

### `tests/conftest.py`
**Decided by:** 2 — Patterns 10 and 11 (the fixtures they assume); 1 — `## Conventions`
(integration tests hit a real test database, not mocks); 4 — testing skill.

Fixtures:
- `_bootstrap` (session, autouse): runs `bootstrap()` against `TEST_DATABASE_URL`, then
  `alembic upgrade head` — the suite exercises the **migrations**, not `create_all`, so a broken
  migration fails the build.
- `api_client` → `TestClient(create_app())`.
- `clean_database` (function, autouse): `TRUNCATE … RESTART IDENTITY CASCADE` across all tables
  after each test. Chosen over a rollback-per-test wrapper because `@with_transaction` commits
  inside the use case under test — a wrapping transaction would be committed away by the code
  being tested.
- `mock_cognito_auth` with `generate_token(custom_claims={"custom:action": '["x:y"]'})` — exactly
  the call shape Pattern 11 uses, issuing a JWT whose `custom:action` claim `@requires_permissions`
  reads.
- Shared domain fixtures as modules land (e.g. Pattern 11's `collaborator_with_spain_site`
  equivalent).

No module-level docstring (testing skill).

### `alembic.ini`
**Decided by:** 1 — `## Stack` (Alembic) / `## Conventions` (one migration per logical change).

`script_location = alembic`; `prepend_sys_path = .`;
`file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s` so
`alembic/versions/` sorts chronologically and a reviewer can read intent from the filename.
**`sqlalchemy.url` is left empty** — the DSN comes from `Settings` inside `env.py`, so a database
password is never committed and `alembic.ini` is environment-independent.

### `alembic/env.py`
**Decided by:** 1 — `## Conventions`; 4 — testing skill (`ruff check . --exclude alembic/env.py`,
so this file is exempt from lint by convention).

- Reads the DSN from `Settings` (never from `alembic.ini`).
- `target_metadata = Base.metadata` after importing `src.core.infrastructure.database.sql.metadata`,
  so autogenerate sees every module's `*ModelSQL`.
- `compare_type=True`, `compare_server_default=True` — otherwise autogenerate silently misses
  column type changes.
- Implements both `run_migrations_offline()` and `run_migrations_online()`.
- `version_table_schema` left default; migrations run inside a transaction per migration.

`alembic/versions/` starts with exactly one migration creating the modules' initial tables. The
health module contributes **no** tables.

### `pyproject.toml`
**Decided by:** 1 — `## Stack` (every tool choice below is named there); 4 — python skill (ruff
config shape).

- `[project]`: `name = "example-api"`, `requires-python = ">=3.11,<3.14"`.
- Runtime deps: `fastapi`, `uvicorn[standard]`, `gunicorn`, `sqlalchemy>=1.4,<2.0`, `alembic`,
  `psycopg2-binary`, `pydantic`, `pydantic-settings`, `pyjwt`, and the DI framework
  (`python-summer-boot` — the `summer.inversion_of_control` package Pattern 4 imports).
- `[dependency-groups] dev` / `test`: `pytest`, `pytest-cov`, `polyfactory`, `requests-mock`,
  `moto`, `diff-cover`, `ruff` **pinned to an exact version** (`## Conventions`: the pin here is
  authoritative over whatever is installed locally; CI must install this same pin).
- `[tool.ruff]`: `line-length = 120`, `target-version = "py311"`;
  `[tool.ruff.lint] extend-select = ["Q", "RUF100", "C90", "UP", "I", "T"]`, `max-complexity = 10`.
  Per-file ignores for `tests/` where justified.
- `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "--strict-markers --ignore=tests/stress"`.
- `[tool.coverage.run]`: `source = ["src"]`, omit `alembic/*`.
- `uv.lock` is committed (`## Stack`) and is what the Docker builder stage installs from.

### `README.md`
**Decided by:** 4 — nothing in 1–3 specifies it.

Short and operational: what the service is, the layer/dependency rule in three lines, the exact
bootstrap sequence (`cp .env.example .env` → `docker compose up` → `docker compose run --rm test`),
how to add a new module (the §4 template), how to generate a migration, how to run ruff with the
pinned version, and links to `docs/constitution.md`, `docs/best_practices.md`,
`docs/custom_implementations/README.md`. It must not restate the constitution — it points at it.

---

## 9. Remaining `## Structure` directories

| Directory | Contents | Decided by |
|---|---|---|
| `tests/<module>/` | Mirrors `src/<module>/`: `domain/`, `application/`, `infrastructure/api/v1/`, `infrastructure/database/`, plus `infrastructure/database/factories/` holding `{Entity}BOFactory(ModelFactory[...])` with `build_and_save_to_db()`. | 1 — `## Conventions`; 2 — Pattern 10 |
| `tests/stress/` | Load profiles (one scenario file per critical endpoint) run on demand against a deployed environment. Excluded from the default pytest run via `--ignore=tests/stress`, so a slow load test never blocks CI. | 4 — nothing in 1–3 decides it |
| `templates/` | Jinja2 templates for generated artifacts (emails, PDFs). Rendering helper in `src/core/infrastructure/templates/`; no module reads the directory directly. | 4 |
| `translations/` | Locale message catalogues (`<locale>/LC_MESSAGES/*.po|.mo`). Only user-facing strings — notably `CustomException.message` — are translatable; `reason` codes are **never** translated, as clients switch on them. | 4 (constrained by 3 — `custom_exception.py:21-24`) |
| `infra/` | Deployment-as-code (IaC modules, pipeline definitions). Nothing in the constitution specifies a target platform — created with a placeholder `README.md` stating the platform is undecided. Tracked as Q3. | 4 |
| `scripts/` | Operational entry points: `init_test_db.sh` (creates the `*_test` database, mounted into the `db` container's initdb hook), plus fixture-loading and migration-helper scripts. Each named `{command_name}_cli.py` / `{command}.sh` — never `main.py`/`cli.py`. | 4 — naming skill |
| `docs/`, `docs/custom_implementations/` | Already exist. Unchanged by this task except for a short note in `docs/custom_implementations/README.md` recording where each primitive was wired into `src/core/`. | 1 |

---

## 10. Work packages (implementation order)

Each package is independently reviewable and leaves the repo in a working state.

1. **WP1 — Project skeleton.** `pyproject.toml`, `uv.lock`, `.env.example`, `.dockerignore`,
   `.gitignore` additions, `README.md`, empty package tree with `__init__.py`.
2. **WP2 — Core foundation.** `src/core/**` (§3). Blocks everything else.
3. **WP3 — Persistence + migrations.** `alembic.ini`, `alembic/env.py`, initial empty migration.
4. **WP4 — Health module.** `src/health/**` (§5).
5. **WP5 — App assembly.** `src/app.py`, `entrypoint.sh`, `gunicorn.conf.py`.
6. **WP6 — Containerization.** `Dockerfile`, `Dockerfile-prod`, `docker-compose.yml`,
   `scripts/init_test_db.sh`.
7. **WP7 — Test harness.** `tests/conftest.py`, the `tests/` mirror skeleton, `tests/stress/`
   placeholder.
8. **WP8 — Placeholders.** `templates/`, `translations/`, `infra/` with their READMEs.

Dependencies: WP2 → (WP3, WP4); (WP4, WP3) → WP5 → WP6; WP2 → WP7.

---

## 11. Test plan

Levels, per the testing skill and `## Conventions` ("unit tests close to domain logic, integration
tests against a real test database … not mocks, for anything crossing the persistence boundary").

### 11.1 Unit — no database, no FastAPI

| File | Cases |
|---|---|
| `tests/core/domain/test_custom_exception.py` | `CustomException` sets `message`/`reason` and `str()` returns `message`; `CustomNotFoundException("Pokemon", "7")` produces `"Pokemon with ID 7 not found."` / `"pokemonNotFound"`; a multi-word entity name lower-cases only its first character. |
| `tests/core/domain/test_enum.py` | `CustomEnum` serializes to its value; unknown value raises; `values()` lists members. |
| `tests/core/infrastructure/api/test_exception_handlers.py` | `reason` ending `NotFound` → 404; any other reason → 400; body is `{"detail", "reason"}`. |
| `tests/health/domain/test_health_report.py` | All checks `UP` → `HEALTHY`; any check `DOWN` → `UNHEALTHY`; empty check list → `HEALTHY` (documents the boundary deliberately). |
| `tests/health/application/test_check_health_use_case.py` | Use case returns a report built from an injected fake `IHealthQueryService` — proves the use case depends on the **interface**, with no database. |

### 11.2 Integration — real test database

| File | Cases |
|---|---|
| `tests/core/infrastructure/database/test_session_manager.py` | `@with_transaction` commits on success; rolls back and **re-raises the original exception** on failure; a nested `session_manager()` reuses the outer session rather than opening a second; calling `session_manager()` before `configure_session_factory()` raises `RuntimeError`. |
| `tests/health/infrastructure/database/test_health_query_service_sql.py` | Against a live `db`: returns `UP` with a non-negative `latency_ms`; with the session factory pointed at an unreachable DSN, returns `DOWN` and **does not raise**; the returned `error` contains no credentials (assert the password string is absent). |
| `tests/core/test_migrations.py` | `alembic upgrade head` then `downgrade base` round-trips cleanly on an empty database. |

### 11.3 API — HTTP contract (Pattern 11 conventions)

`tests/health/infrastructure/api/v1/test_health_router.py`, with module-level
`ENDPOINT = "/api/example-api/v1/health"` (testing skill: never inline the path).

| Test | Asserts |
|---|---|
| `test_health_returns_200_when_database_is_reachable` | 200; `status == "healthy"`; `checks[0] == {"name": "database", "status": "up", ...}`. |
| `test_health_returns_503_when_database_is_unreachable` | With the DB dependency forced to fail: **503**, `status == "unhealthy"`, `reason == "healthCheckFailed"`, `checks[0]["status"] == "down"`. |
| `test_health_requires_no_authentication` | No `Authorization` header → **200**, not 401/403. This is the regression test for CF5. |
| `test_health_does_not_leak_connection_details` | On failure, the serialized body contains neither the password nor the host from `DATABASE_URL`. |
| `test_health_response_matches_openapi_schema` | The 503 body validates against the declared `responses[503]` model. |

**No `test_*_forbidden_wrong_permission` test here** — Pattern 11 mandates one per endpoint, but
this endpoint is deliberately unauthenticated; `test_health_requires_no_authentication` is its
inverse and must be present instead. This is the one documented exemption from Pattern 11.

### 11.4 Gates (all must pass before the change is done)

- `docker compose run --rm test` is green (1 — `## Conventions`: this is *the* command).
- `ruff check . --exclude alembic/env.py` → **0** violations, using the version pinned in
  `pyproject.toml`.
- `ruff format --check .` → clean.
- Diff coverage ≥ **90%** via `diff-cover coverage.xml --compare-branch=main --fail-under=90`.
- `docker compose up` brings `api` to a healthy state from a clean checkout with only
  `cp .env.example .env` done first.

---

## 12. Definition of done

1. Every file line in `## Structure` exists, with the content described above.
2. `docker compose up` works on a clean machine; `api` reaches healthy; `GET /api/example-api/v1/health`
   returns 200 with `status: "healthy"`.
3. Stopping `db` turns that same endpoint into a 503 with a structured body and no credential leak.
4. `docker compose run --rm test` runs the full suite against `db` and passes.
5. Ruff check and format are clean; diff coverage ≥ 90%.
6. No file under `src/*/domain/` imports `fastapi`, `sqlalchemy`, or any `infrastructure` module
   (verified by a lint rule or an explicit import-direction test).
7. `CustomException`, `@requires_permissions` and `@with_transaction` exist exactly once each, in
   `src/core/`, wired to the real session factory and the real token verification.
