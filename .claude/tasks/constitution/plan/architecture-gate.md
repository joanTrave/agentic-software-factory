# constitution — Architecture Gate

| | |
|---|---|
| **Task** | constitution — bootstrap the `example-api` modular-monolith skeleton |
| **Mission spec** | `docs/constitution.md` (no spec file exists for this task) |
| **Implementation plan** | `.claude/tasks/constitution/plan/plan.md` |
| **Branch** | example |
| **Date** | 2026-10-08 |

## 1. Objective
Turn `docs/constitution.md` into a buildable skeleton — layer tree, health module, Alembic, containerized
test path, every root file `## Structure` lists — so a developer can clone, `docker compose up`, and add a
bounded context without inventing conventions.

## 2. Scope
**In scope:** every `## Structure` line; `src/core/` primitives wired from `docs/custom_implementations/`;
`src/health/` end to end; the env-var contract; Docker/compose; test harness.
**Out of scope:** business bounded contexts (`src/<module>/` is a template, not built); `infra/` contents;
real auth credentials; the CI pipeline file.

## 3. Requirements coverage
| Req | Source (`docs/constitution.md`) | Addressed by (`plan.md`) | Status |
|---|---|---|---|
| CR-1 Stack: 3.11–3.13, FastAPI, SQLAlchemy 1.4 + Alembic, uv, pytest, ruff, Docker | :9-15 | §8, §7 | covered |
| CR-2 Every `## Structure` file line exists | :19-63 | §8, §9 | covered |
| CR-3 Strict dependency direction; no framework imports in `domain` | :67-69 | §4, DoD 6 | covered |
| CR-4 One module = one bounded context; no cross-module `infrastructure` import | :70-71 | §4 | covered |
| CR-5 `tests/<module>/` mirrors `src/`; real test DB, not mocks | :72-74 | §9, §11.2 | covered |
| CR-6 One Alembic migration per logical schema change | :75-76 | §8 | covered |
| CR-7 Domain exceptions extend a shared base | :77-79 | §3 (D4) | covered |
| CR-8 Pydantic serializers built `from_bo` | :80-81 | §4 | covered |
| CR-9 Ruff clean; pinned version authoritative | :82-84 | §11.4 | partially-covered (Q4) |
| CR-10 Custom primitives not reinvented per module | :85-88 | §3, DoD 7 | covered |
| CR-11 Unauthenticated `GET /health` as its own module; 200/503 | :89-95 | §5 | covered |
| CR-12 `docker compose up` runnable; `api`/`test`/`db` services | :96-107 | §7.3 (D5) | covered |
| CR-13 Multi-stage non-root `Dockerfile`; `Dockerfile-prod` without dev groups | :108-111 | §7.1-7.2 | covered |

## 4. Architecture decisions
DECISION D1: Use-case action method is `execute()`.
  Options: `execute()` (`docs/best_practices.md:87,104,134`) / `get_pokemon()`-style (`.claude/skills/naming/SKILL.md:36-48`)
  Chosen: `execute()` — the priority order ranks `best_practices.md` above the skills, and FACT: the naming skill labels itself "EXAMPLE — adapt per project's stack" — `.claude/skills/naming/SKILL.md:1`.
  Consequence: the naming skill must be rewritten to match, or two conventions stay in conflict for every module.

DECISION D2: Keep a `sql/` path level under `src/core/` but not under `src/<module>/`.
  Options: constitution tree everywhere / `best_practices.md` import paths everywhere / split
  Chosen: split — FACT: the module tree has no `sql/` level — `docs/constitution.md:32`, while FACT: Pattern 3 imports `src.core.infrastructure.database.sql.session_manager` — `docs/best_practices.md:95`; the constitution never expands `src/core/`.
  Consequence: both documents stay literally true; the asymmetry must be noted in `README.md` or it reads as an accident.

DECISION D3: The health check probes the database through the application's own session factory.
  Options: `IDatabaseRepositorySQL.self.db` + `SELECT 1` / a separate short-lived engine
  Chosen: the shared factory — it exercises the real pool, credentials and `pool_pre_ping`, so the probe cannot report healthy while the app's own pool is exhausted.
  Consequence: it shares that pool, so it gets a 2s deadline and no `@with_transaction` — a dead connection would make the rollback itself raise.

DECISION D4: `CustomException` lives at `src/core/domain/exceptions/`, its FastAPI handler at `src/core/infrastructure/api/`.
  Options: a bare top-level `custom_exceptions` module as Pattern 6 imports it / split under `src/core/`
  Chosen: split — FACT: the reference file guards its FastAPI import precisely because domain code must not depend on a web framework — `docs/custom_implementations/custom_exception.py:63-66`; a split makes that structural rather than a `try/except`.
  Consequence: Pattern 6's `from custom_exceptions import …` is shorthand and should be corrected in `docs/best_practices.md`.

DECISION D5: The compose `test` service sits behind `profiles: ["test"]` and targets a separate `*_test` database.
  Options: no profile (runs on `up`) / profile plus `docker compose run --rm test`
  Chosen: profile — FACT: `docker compose up` must be runnable as-is — `docs/constitution.md:96`; firing the suite on every `up` makes that unusable.
  Consequence: `docker compose run --rm test` is the sanctioned command, in `README.md` and in CI.

DECISION D6: The health router returns an explicit `JSONResponse(503, …)` instead of raising.
  Options: raise a `CustomException` and let the shared handler map it / return the response directly
  Chosen: return — FACT: the shared handler emits only 404 or 400 — `docs/custom_implementations/custom_exception.py:58`, so raising cannot produce the mandated 503.
  Consequence: the 503 body still carries `detail` + `reason`, staying shape-compatible with every other error response.

## 5. Affected components
| Path | Change | Why |
|---|---|---|
| `src/core/**` | ADD | Shared primitives every module imports (CR-10) |
| `src/health/**` | ADD | The health bounded context (CR-11) |
| `src/app.py` | ADD | App factory, DI bootstrap, router mounting |
| `tests/**` | ADD | Harness, mirror skeleton, health suite (CR-5) |
| `alembic/**`, `alembic.ini` | ADD | Migration tooling (CR-6) |
| `Dockerfile`, `Dockerfile-prod`, `docker-compose.yml`, `.dockerignore` | ADD | Containerization (CR-12, CR-13) |
| `entrypoint.sh`, `gunicorn.conf.py` | ADD | Migrate-then-serve container command |
| `pyproject.toml`, `uv.lock`, `.env.example` | ADD | Dependencies, tool config, env contract |
| `templates/`, `translations/`, `infra/`, `scripts/`, `README.md` | ADD | Remaining `## Structure` lines |
| `docs/custom_implementations/README.md` | MODIFY | Record where each primitive was wired into `src/core/` |

## 6. Expected code changes
~45 files: 44 added, 1 modified, 0 deleted — 12 in `src/core/`, 10 in `src/health/`, `src/app.py`, 11 tests,
2 Alembic files, 4 Docker/compose files, `entrypoint.sh`, `gunicorn.conf.py`, `pyproject.toml`,
`.env.example`, `README.md`, 3 placeholder READMEs, `scripts/init_test_db.sh`.

## 7. Data model / database changes
Migration required: yes — one initial revision creating **no tables**. Health owns no persistence and no
business module is in scope; it establishes `alembic_version` and a parent for the next migration.

## 8. API changes
| Endpoint | Change | Breaking |
|---|---|---|
| `GET /api/example-api/v1/health` | ADD — 200 healthy / 503 unhealthy, unauthenticated | No (new service) |

## 9. External dependencies
Added: fastapi, uvicorn[standard], gunicorn, sqlalchemy 1.4.x, alembic, psycopg2-binary, pydantic,
pydantic-settings, pyjwt, the `summer.inversion_of_control` DI framework (`docs/best_practices.md:128`);
dev/test: pytest, pytest-cov, polyfactory, requests-mock, moto, diff-cover, ruff. Images: `python:3.12-slim`,
`postgres:16-alpine`, a pinned `ghcr.io/astral-sh/uv`. Removed: none.

## 10. Test strategy
Unit for the exception/enum/report logic and `CheckHealthUseCase` against a fake repository — no database,
proving the use case depends on the interface. Integration against the real `db` container for
`@with_transaction` commit/rollback/nesting, the health SQL repository, and a migration up/down round-trip
(CR-5 forbids mocking the persistence boundary). API tests for the health contract, including an
unauthenticated-access regression and a credential-leak assertion. 11 new files; cases in `plan.md` §11.

## 11. Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | The unauthenticated 503 leaks the DSN password — SQLAlchemy `OperationalError` messages embed it | medium | high | `error` carries the exception class name only; a test asserts neither password nor host appears |
| R2 | The probe shares the app pool, so a saturated pool hangs it and the orchestrator kills a recoverable container | medium | medium | 2s statement deadline, `pool_pre_ping`, fast 503 instead of a hang |
| R3 | DI `exec_module` discovery under-reports coverage of `@service()` classes, tripping the 90% gate — FACT: the testing skill documents this artifact — `.claude/skills/testing/SKILL.md:63-72` | medium | medium | Verify causally with `--noconftest` at bootstrap and record the affected files in the testing skill before the first review |
| R4 | SQLAlchemy 1.4 is pinned while the ecosystem moved to 2.0, so new deps may not resolve | low | medium | `<2.0` pin plus a committed lockfile; CR-1 makes 1.4 binding, not a default |
| R5 | A truthy `preload_app` would fork workers sharing pooled sockets and corrupt connections | low | high | `preload_app = False` set explicitly, with the reason in a comment |

## 12. Assumptions
ASSUMPTION A1: `summer.inversion_of_control` is the installable `python-summer-boot` package — basis: `docs/best_practices.md:128`, `.claude/skills/dependency-injection/SKILL.md:5` — if wrong: the package name in `pyproject.toml` changes, no layer or import path does.
ASSUMPTION A2: Postgres on Python 3.12 — basis: `docs/constitution.md:106,9` — if wrong: the driver, `db` image and base image tags change; nothing structural.
ASSUMPTION A3: The `## Structure` tree is illustrative, not exhaustive — basis: it omits `uv.lock` and `.env`, both required by the constitution's own prose (`docs/constitution.md:11,98`) — if wrong: `.env.example`, `.dockerignore` and `uv.lock` must be dropped, leaving the project unbuildable.
ASSUMPTION A4: `src/<module>/` is a template to document, not a context to implement — basis: the literal placeholder at `docs/constitution.md:22` — if wrong: scope grows by one or more full bounded contexts.

## 13. Open questions
OPEN QUESTION Q1: Accept D1, and should `.claude/skills/naming/SKILL.md` be rewritten to match? — blocking: no — default if unanswered: use `execute()`, leave the skill as is, note the conflict in `README.md`.
OPEN QUESTION Q2: Does the orchestrator need split `/health/live` and `/health/ready` probes? — blocking: no — default if unanswered: one endpoint serving both, as the constitution describes.
OPEN QUESTION Q3: What platform does `infra/` target (Terraform/AWS, CDK, Helm)? — blocking: no — default if unanswered: a placeholder README stating the platform is undecided.
OPEN QUESTION Q4: Which exact ruff version is pinned (CR-9)? — blocking: no — default if unanswered: pin the latest stable ruff at bootstrap and make CI install that pin.
OPEN QUESTION Q5: Is Cognito the real auth provider, or is the reference JWT read a placeholder? — blocking: no — default if unanswered: Cognito JWKS verification, required by a `Settings` validator in `staging`/`production` only.

## 14. Breaking changes
No. Greenfield repository with no existing source, consumers, or database.

## 15. Complexity and impact
Size: L · Files touched: ~45 · Blast radius: the whole repository · Rollback: revert the branch — nothing is deployed and no database exists to migrate back.

## 16. Decisions required from the human
1. Confirm D1 and answer Q1 — this sets the use-case method convention for every future module and is expensive to reverse.
2. Confirm D2 and D4, both of which imply a correction to `docs/best_practices.md` Patterns 3 and 6.
3. Confirm D5 — `docker compose run --rm test` is the sanctioned test command and `up` starts only `api` + `db`.
4. Answer Q4 (ruff pin), the only item leaving CR-9 partially-covered.
5. Confirm A4 — no business bounded context is in scope for this task.

## 17. Recommendation
**PROCEED WITH CONDITIONS**
The architecture follows `docs/constitution.md` directly and every gap is filled by a named lower-priority
source. The conditions are the §16 list: four convention confirmations that are cheap now and costly once the
first business module exists, plus the ruff pin that CR-9 cannot close without.
