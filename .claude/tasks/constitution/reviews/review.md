# constitution — Review Report
**Status:** approved_with_warnings · **Overall score:** 7/10 · **Recommendation:** approve

All four blocking/major items from the previous rejected review are resolved and independently re-verified: the IDatabaseRepositorySQL connection leak is fixed and empirically confirmed clean at the unit-test, docker-compose-test-service, and real-containerized-app levels; tests/core/test_migrations.py's path bug is fixed and the mandatory `docker compose run --rm test` gate is green (61/61); the unsafe run_local_tests.sh script is gone; and the custom @autowired reimplementation is gone in favor of summer's own @autowired as mandated. Diff coverage (98%) and lint are clean. Remaining findings are four minor, non-blocking disclosure/documentation gaps — two architecture/process decisions made correctly but not recorded against the approved plan (HealthQueryServiceSQL's departure from §5.3, and extending the shared docs/custom_implementations/ reference files rather than only this project's wired copy), one undocumented but necessary @autowired/future-annotations constraint, and one test whose correctness depends on implicit file-order execution rather than an explicit contract.

## 1. Verdict
No blocking reasons.

## 2. Quality dimensions

| Dimension | Score | Status | Summary |
|---|---|---|---|
| Architecture | 8 | concern | C1 fixed at the root (`get_read_session()` replaces the broken `with ... return` pattern); CF1–CF6 and domain purity intact. HealthQueryServiceSQL's justified departure from plan §5.3 (own `session_manager()` block instead of `self.db`) is undisclosed in plan.md/architecture-gate.md. |
| Correctness | 9 | ok | Connection leak fixed and empirically re-verified via unit tests, the `docker compose run --rm test` gate, and 30 live calls to the health endpoint on a built Docker image — all 200. Migration test path bug fixed. |
| Maintainability | 7 | concern | run_local_tests.sh and custom `@autowired` are both gone. New gaps: the Developer extended the shared `docs/custom_implementations/` reference files (not just this project's wired copy) without recorded sign-off, and the required omission of `from __future__ import annotations` in `check_health_use_case.py` (for `@autowired` to work) is undocumented anywhere. |
| Testing | 8 | concern | 99% overall / 98% diff coverage, 61/61 passing. Strong, deliberate pool-exhaustion regression tests added (exactly R1 from the prior review). One test (`test_override_service_restores_the_real_service_after_the_test`) relies on implicit file-order execution rather than an explicit contract. |
| Security | 8 | ok | Health-check errors never leak exception text; Cognito JWKS verification enforced in staging/production. New request-id middleware validates inbound headers against a strict regex, uses a ContextVar cleared in `finally`, and is pure-ASGI to prevent cross-request leakage. |
| Performance | 9 | ok | The pool-exhaustion defect that caused a self-inflicted outage is fixed and re-verified at the real containerized-application level (30 consecutive real HTTP calls, all 200). |
| Observability | 8 | ok | Request-id propagation (plan §3 deliverable, missing in the prior review) is now implemented end-to-end: middleware generates/reuses/validates the id, binds it via a ContextVar, and `_JsonFormatter` includes it on every log record during the request. |

## 3. Critical issues
None.

## 4. Warnings

### W1 — HealthQueryServiceSQL's departure from plan §5.3 (own session_manager() block instead of self.db) is undisclosed
**Dimension:** architecture · **Severity:** minor
**Location:** `src/health/infrastructure/database/health_query_service_sql.py:28-33`

plan.md §5.3 specifies the probe runs "via IDatabaseRepositorySQL.self.db -> session_manager()". The implementation instead opens an explicit `with session_manager() as session:` block and never touches `self.db`. This is the technically correct choice, not a shortcut: outside an enclosing transaction, `self.db` (now backed by `get_read_session()`) hands back a brand-new autocommit-mode session on every property access, so two separate `self.db` reads for `SET LOCAL statement_timeout` and `SELECT 1` would not even share a connection, silently defeating the timeout. The deviation is explained in the class's own docstring but is not recorded in plan.md or architecture-gate.md, so a reader comparing the approved design to the code would see an unexplained discrepancy.

*Suggested fix:* Add a one-line note to plan.md §5.3 (or a short addendum) recording that read-only repositories needing more than one statement on the same connection must open an explicit `session_manager()` block rather than relying on `self.db`, and that HealthQueryServiceSQL is the first example of this.

### W2 — Developer extended the shared reference implementation files, not just this project's wired copy
**Dimension:** maintainability · **Severity:** minor
**Location:** `docs/custom_implementations/with_transaction.py:56-74`; `docs/custom_implementations/README.md:10-30`

`docs/custom_implementations/README.md` describes its files as "starting points for a new project, not drop-in production code" — a cross-project reference asset, not this project's own source. The Developer added the new `get_read_session()` function (and a wiring-table section) directly to that shared file and its README, rather than confining the new primitive to the project's wired copy at `src/core/infrastructure/database/sql/session_manager.py` and only linking back to it. The addition is correct and necessary (it is what fixes the previous review's C1), but changing a shared, human-maintained reference asset's permanent shape is a decision with consequences for every future project bootstrapped from it, and nothing in this task's trail (plan.md, architecture-gate.md) records that this was a deliberate, reviewed choice rather than an incidental side effect of fixing C1.

*Suggested fix:* Confirm with the human maintainer of `docs/custom_implementations/` whether `get_read_session()` belongs in the shared reference permanently, or whether the reference file should stay as it was and the addition should live only in `src/core/infrastructure/database/sql/session_manager.py` with a comment noting the extension.

### W3 — Undocumented `from __future__ import annotations` omission required for @autowired
**Dimension:** maintainability · **Severity:** minor
**Location:** `src/health/application/check_health/check_health_use_case.py:1`

Every other source file in `src/` carries `from __future__ import annotations`; this file is the sole exception, because summer's `@autowired` resolves constructor parameter annotations at runtime and cannot do so when they are postponed (string) annotations. This is a correct, necessary constraint, but it is not documented anywhere — no comment in the file, no mention in `.claude/skills/dependency-injection/SKILL.md`, no note in plan.md. The next bounded context's first `@autowired` constructor is likely to be written by copying a sibling file (which has the future import) and will hit a confusing runtime resolution failure with no breadcrumb pointing at the cause.

*Suggested fix:* Add a one-line comment at the top of `check_health_use_case.py` explaining the omission, and add a sentence to `.claude/skills/dependency-injection/SKILL.md`'s `@autowired` example noting that the future-annotations import must be omitted from any module defining an `@autowired` constructor.

### W4 — test_override_service_restores_the_real_service_after_the_test relies on implicit execution order
**Dimension:** testing · **Severity:** minor
**Location:** `tests/health/application/test_check_health_use_case.py:60-64`

This test has no explicit dependency (fixture, marker, or ordering plugin) on running after the two preceding `override_service`-based tests in the same file; it is only a meaningful assertion because pytest's default behavior runs test functions in file-declaration order. Run alone (e.g. `pytest -k test_override_service_restores`) it passes vacuously, since nothing was ever overridden in that run, which means a real regression in the `override_service` fixture's monkeypatch-based restoration would not be caught by a selective/filtered test run. No reordering plugin (pytest-randomly, xdist) is installed, so there is no live failure risk today, but the test's correctness is coupled to an implementation detail of the test runner rather than to an explicit contract.

*Suggested fix:* Either compose the restoration check into the same test function as one of the override tests (assert the real service is back immediately after the overriding test body) or add an explicit `pytest.mark.order` / fixture dependency documenting the intended order, so the test's meaning does not depend on file layout.

## 5. Requirements verification

| Req | Status | Evidence |
|---|---|---|
| CR-1 (Stack) | verified | `pyproject.toml:5,7-16`; Docker build resolves `sqlalchemy==1.4.54` |
| CR-2 (Structure) | verified | `find src tests alembic -type f` — every listed path present |
| CR-3 (Dependency direction / domain purity) | verified | `grep -rn "^import\|^from" src/core/domain src/health/domain` — no framework imports |
| CR-4 (One module = one bounded context) | not_applicable | only the `health` module exists at this stage |
| CR-5 (tests mirror src; integration hits real DB) | verified | `test_check_database_connection_returns_up_with_non_negative_latency` passes against live Postgres |
| CR-6 (One Alembic migration per schema change) | verified | single initial revision; upgrade/downgrade round-trip test passes |
| CR-7 (Custom exceptions extend shared base) | verified | `test_custom_not_found_exception_builds_message_and_reason` passes |
| CR-8 (Serializers are Pydantic `from_bo`) | verified | `health_output.py:16-23,32-40`; exercised by passing router tests |
| CR-9 (ruff check/format clean; pinned version authoritative) | verified | `ruff check` / `ruff format --check` clean; installed 0.16.10 matches the pin exactly |
| CR-10 (Shared primitives not reinvented) | verified | `docs/custom_implementations/README.md:18-30` wiring table matches `src/core/**` |
| CR-11 (Unauthenticated health endpoint, 200/503, reflects real DB health) | verified | router test passes; pool-exhaustion regression test passes; 30x live curl against Docker image all 200 |
| CR-12 (docker-compose runnable with api/test/db) | verified | `docker compose --profile test build test && run --rm test` → 61 passed; `docker compose up -d --build api` → healthy, health endpoint 200 |
| CR-13 (Multi-stage non-root Dockerfile; Dockerfile-prod excludes dev/test groups) | verified | `Dockerfile-prod:16`; `USER appuser` in both Dockerfiles |

## 6. Verification evidence

Tests: 61 passed / 0 failed / 0 errors / 0 skipped, exit 0.
Command: `DATABASE_URL=postgresql+psycopg2://example:example@localhost:5432/example_api_test pytest --cov=src --cov-report=term-missing --cov-report=xml -q -p no:cacheprovider`; confirmed again via `docker compose --profile test run --rm test`.

Diff coverage: 98% vs 90% threshold → pass.
Command: `diff-cover coverage.xml --compare-branch=main --fail-under=90`.

Lint: 0 violations, exit 0.
Command: `ruff check . --exclude alembic/env.py && ruff format --check .`.

Additional live verification: `docker compose up -d --build api` (real containerized app against the real `db` service), then 30 sequential `curl http://localhost:8000/api/example-api/v1/health` calls — all returned `200`.

## 7. Test ownership

Tester-authored tests modified: no (modified file list: none). Note: nothing is committed yet for this task, so a Developer-vs-Tester authorship boundary cannot be established via `git diff` — all test files are untracked in the current working tree. This is an inherent limitation of reviewing before any commit exists, not a finding against the diff itself.

## 8. Recommendations

### R1 — Record the HealthQueryServiceSQL / get_read_session design in plan.md or a short addendum
**Dimension:** maintainability · **Priority:** medium

Both W1 and W2 stem from the same root cause: a real, correct architectural fix (C1) was made without updating the approved plan or getting explicit sign-off on extending the shared reference files. A short `review-fixes.md` or a plan.md patch recording "self.db now resolves via get_read_session(); read-only repos needing a single connection across statements must open their own session_manager() block; get_read_session() was added to the shared reference, confirmed with the maintainer" would close both gaps at once.

### R2 — Note the SQLAlchemy 2.0 migration debt from get_read_session()'s autocommit mode
**Dimension:** maintainability · **Priority:** low

`get_read_session()` relies on `sessionmaker`'s deprecated `autocommit=True` kwarg (confirmed: triggers a `RemovedIn20Warning` on every call outside a transaction). This is correct and intentional for the pinned SQLAlchemy 1.4 stack, but it is a specific, named item of technical debt if the project ever upgrades to SQLAlchemy 2.0 (autocommit mode is fully removed there). Worth a one-line note near the function or in a future ADR so the upgrade isn't a surprise.

---
Machine-readable: `.claude/tasks/constitution/reviews/review.json` (schema 1.0)
