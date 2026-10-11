# remove-future-annotations — Implementation Plan

Remove `from __future__ import annotations` from every Python file in the repository, keep every
annotation resolvable under eager evaluation, and add a prohibition rule to the Python skill so the
import is not reintroduced.

- Requirements source: `.claude/tasks/remove-future-annotations/specs/remove-future-annotations.md`.
- Gate report (human decision document): `.claude/tasks/remove-future-annotations/plan/architecture-gate.md`.
- Nature of the change: mechanical refactor, **no behavior change**. No new modules, no new
  dependencies, no API, schema or configuration change.

---

## 1. Inventory (verified at planning time)

`grep -rn "from __future__ import annotations" --include="*.py" .` returns **27** files (the spec
text says "26" but its own list enumerates 27 — the grep is authoritative and is the DoD check).
No file uses `from __future__ import` for anything other than `annotations`. No file uses
`TYPE_CHECKING`. No `.md`/config file outside `.claude/tasks/constitution/` mentions the import.

| # | File | Import line | Shape around it | Extra fix needed |
|---|---|---|---|---|
| 1 | `gunicorn.conf.py` | 3 | docstring, blank, **import**, blank, imports | no |
| 2 | `src/app.py` | 10 | docstring, blank, **import**, blank, imports | no |
| 3 | `src/core/domain/enum.py` | 1 | **import**, blank, imports | **yes — line 17** |
| 4 | `src/core/domain/exceptions/custom_exception.py` | 1 | **import**, blank, imports | no |
| 5 | `src/core/infrastructure/api/exception_handlers.py` | 1 | **import**, blank, imports | no |
| 6 | `src/core/infrastructure/api/request_id_middleware.py` | 1 | **import**, blank, imports | no |
| 7 | `src/core/infrastructure/api/security/requires_permissions.py` | 17 | docstring, blank, **import**, blank, imports | no |
| 8 | `src/core/infrastructure/bootstrap.py` | 10 | docstring, blank, **import**, blank, imports | no |
| 9 | `src/core/infrastructure/config/settings.py` | 1 | **import**, blank, imports | **yes — lines 43, 52** |
| 10 | `src/core/infrastructure/database/sql/base.py` | 1 | **import**, blank, imports | no |
| 11 | `src/core/infrastructure/database/sql/engine.py` | 1 | **import**, blank, imports | no |
| 12 | `src/core/infrastructure/database/sql/metadata.py` | 9 | docstring, blank, **import**, blank, imports | no |
| 13 | `src/core/infrastructure/database/sql/repositories/i_database_repository_sql.py` | 1 | **import**, blank, imports | no |
| 14 | `src/core/infrastructure/database/sql/session_manager.py` | 12 | docstring, blank, **import**, blank, imports | no |
| 15 | `src/core/infrastructure/logging/logging_config.py` | 1 | **import**, blank, imports | no |
| 16 | `src/core/infrastructure/logging/request_context.py` | 1 | **import**, blank, imports | no |
| 17 | `src/health/application/check_health/i_check_health_use_case.py` | 1 | **import**, blank, imports | no |
| 18 | `src/health/application/check_health/serializers/health_output.py` | 1 | **import**, blank, imports | **yes — lines 17, 33** |
| 19 | `src/health/domain/bo/dependency_check.py` | 1 | **import**, blank, imports | no |
| 20 | `src/health/domain/bo/health_report.py` | 1 | **import**, blank, imports | no |
| 21 | `src/health/domain/enums/health_status_enum.py` | 1 | **import**, blank, imports | no |
| 22 | `src/health/domain/repositories/i_health_query_service.py` | 1 | **import**, blank, imports | no |
| 23 | `src/health/infrastructure/api/v1/health_router.py` | 1 | **import**, blank, imports | no |
| 24 | `src/health/infrastructure/database/health_query_service_sql.py` | 1 | **import**, blank, imports | no |
| 25 | `docs/custom_implementations/custom_exception.py` | 10 | docstring/comments, **import** | no (see §3.3) |
| 26 | `docs/custom_implementations/requires_permissions.py` | 11 | docstring/comments, **import** | no |
| 27 | `docs/custom_implementations/with_transaction.py` | 12 | docstring/comments, **import** | no |

Line numbers are pre-change; the Developer must re-confirm with the grep before editing.

---

## 2. Step 1 — remove the import line (all 27 files)

Rule, applied identically to every file:

- Delete the `from __future__ import annotations` line **and exactly one** adjacent blank line —
  the one that separated it from the next import block.
- Files where the import is on line 1: the file must then start directly with the first remaining
  import (no leading blank line).
- Files where a module docstring precedes the import: the result must be
  `"""docstring"""` + **one** blank line + first import. Never leave two consecutive blank lines,
  never glue the docstring to the import.
- Touch nothing else in the file — no reordering, no reformatting, no added comments.

Ruff/isort: the future import is its own isort section; deleting it leaves the stdlib →
third-party → local order intact, so `ruff check` (rule `I`) must stay clean without any reordering.

---

## 3. Step 2 — fix annotations that no longer resolve

Without the future import, annotations on `def` signatures, class bodies and module-level
annotated assignments are evaluated eagerly. A name that is **not yet bound** at evaluation time
raises `NameError` at import. Static analysis of all 27 files found exactly one category of hazard:
**a method annotation that refers to its own enclosing class** (the class name is bound only
after the class body finishes). There are **5 sites in 3 files**:

| File:line | Current annotation | Required annotation |
|---|---|---|
| `src/core/domain/enum.py:17` (`CustomEnum._missing_`, classmethod) | `-> CustomEnum \| None` | `-> "CustomEnum \| None"` |
| `src/core/infrastructure/config/settings.py:43` (`Settings._derive_test_database_url`, `@model_validator`) | `-> Settings` | `-> "Settings"` |
| `src/core/infrastructure/config/settings.py:52` (`Settings._require_cognito_settings_in_deployed_environments`) | `-> Settings` | `-> "Settings"` |
| `src/health/application/check_health/serializers/health_output.py:17` (`DependencyCheckOutput.from_bo`, staticmethod) | `-> DependencyCheckOutput` | `-> "DependencyCheckOutput"` |
| `src/health/application/check_health/serializers/health_output.py:33` (`HealthOutput.from_bo`, staticmethod) | `-> HealthOutput` | `-> "HealthOutput"` |

Constraints (load-bearing):

- **Quote the whole annotation**, not just the class name. `"CustomEnum" | None` is a runtime
  `TypeError` (`str | NoneType`); `Optional["CustomEnum"]` would violate Ruff `UP007`. The only
  correct form is `"CustomEnum | None"`.
- Use **double quotes** (Ruff `Q` rule and `ruff format`).
- Do not switch to `typing.Self`, do not convert staticmethods to classmethods, do not restructure
  the classes — see gate report D2. Quoting is the minimal, behavior-neutral fix (spec assumption A4).

### 3.1 Sites verified as safe (do not touch)

- `health_output.py:28` `checks: list[DependencyCheckOutput]` — `DependencyCheckOutput` is
  defined earlier in the file (line 10), so it resolves eagerly.
- Module-level annotated globals `_session_factory: sessionmaker | None`,
  `_current_session: ContextVar[Session | None]`, `_request_id: ContextVar[str | None]` —
  `sessionmaker` is a class in SQLAlchemy 1.4 (supports `|`), `ContextVar` is subscriptable at
  runtime on 3.11.
- `Callable[...]`/`Awaitable[...]` from `collections.abc` — subscriptable at runtime on 3.11.
- Every other annotated name is imported at runtime (no `TYPE_CHECKING` blocks exist; Ruff `F821`
  would already have flagged undefined names), so no new imports and no circular-import risk are
  introduced.

### 3.2 Frameworks that read annotations at runtime

FastAPI (endpoint signatures in `health_router.py`), Pydantic (model fields, validators) and
summer `@autowired` already resolve real objects; removing the future import moves them from
"string resolved via module globals" to "real object", which is the supported path. No behavior
change is expected. `check_health_use_case.py` already has no future import and is not touched.

### 3.3 `docs/custom_implementations/`

Excluded from Ruff (`pyproject.toml` `extend-exclude`) and from the Docker image (`.dockerignore`).
Static check: the only class self-reference candidate, `custom_exception.py:57`
(`exc: CustomException`), is in a module-level function defined after the class — resolves
eagerly. No annotation fix needed. Apply Step 1 only.

---

## 4. Step 3 — Python skill rule

Edit `.claude/skills/python/SKILL.md`, section `## Imports` only (an import rule belongs with the
import rules; `## Code quality` stays untouched). Append, after the existing
"Use Ruff/isort-compatible ordering." line, a prohibition with this content:

- `from __future__ import annotations` must not be used in any Python file.
- Why (one sentence): annotations must be evaluated eagerly because runtime-inspecting code — the
  DI container's `@autowired`, FastAPI, Pydantic — resolves them.
- How to handle a forward or self reference instead (one sentence): quote that single annotation,
  quoting the whole expression (e.g. `-> "MyClass | None"`).

Keep it to a short bullet list or 2–3 lines. Do not change any other line of the skill.
`.claude/skills/dependency-injection/SKILL.md` is **not** edited (out of the spec's scope).

---

## 5. Test plan (Tester)

**No new test files.** Per the human's decision at the architecture gate, this task adds no
tests: no guard test, no import-every-module test. The Tester writes nothing for this task and
only confirms that the existing suite is the regression evidence.

The existing suite already exercises the behavior of every fixed annotation site (verified at
planning time):

| Fixed site | Existing test that exercises it |
|---|---|
| `CustomEnum._missing_` (`enum.py:17`) | `tests/core/domain/test_enum.py` |
| `Settings` validators (`settings.py:43`, `:52`) | `tests/core/infrastructure/config/test_settings.py` (test DB URL derivation, Cognito checks) |
| `DependencyCheckOutput.from_bo` / `HealthOutput.from_bo` (`health_output.py:17`, `:33`) | `tests/health/infrastructure/api/v1/test_health_router.py` (end-to-end `/health` body: `status`, `checks[]`) |

An eager-evaluation failure in any of these modules is raised **at import time**, so it would
fail test collection through `tests/conftest.py` (imports `src.app` and runs `bootstrap()`) before
any assertion runs. These tests must pass **unchanged** — they are the "no behavior change" evidence.

Diff coverage: changed lines under `src/` are only the 5 annotation lines; they execute at import,
so diff coverage is 100%. Removed lines are not measured.

---

## 6. Verification (Developer, then Reviewer)

```bash
# 1. Zero occurrences of the future import (scoped paths, then repository-wide DoD check)
grep -rn "from __future__ import" --include="*.py" src gunicorn.conf.py docs   # expect: no output
grep -rn "from __future__ import annotations" --include="*.py" .               # expect: no output

# 2. Lint and format
uv run ruff check . --exclude alembic/env.py                                   # expect: exit 0
uv run ruff format --check .                                                   # expect: exit 0

# 3. Existing test suite (also runs `alembic upgrade head`, which imports metadata.py)
docker compose run --rm test                                                   # expect: all pass
```

Plus: the application starts (`docker compose up api`) and `GET /health` returns the same
status/body shape as before.

Spec Verification item "importing every module under `src/` succeeds" is satisfied by step 3
(the app factory, `bootstrap()` DI discovery and the Alembic run import every `src` module). If
the Reviewer wants direct evidence, a one-off command — **not** a committed test — is acceptable:
`docker compose run --rm test python -c "import importlib, pkgutil, src; [importlib.import_module(m.name) for m in pkgutil.walk_packages(src.__path__, 'src.')]"`.

`docs/custom_implementations/*.py` are not linted (Ruff `extend-exclude`) and not in the test
image (`.dockerignore`); their verification is the grep in step 1 plus the Reviewer reading their
diff for correct blank-line handling. Static analysis (§3.3) found no annotation hazard there.

---

## 7. Commit hygiene

The working tree already contains **unrelated** uncommitted changes (`entrypoint.sh`,
`scripts/init_test_db.sh`). They must **not** be staged in this task's commit. Stage only: the 27
`.py` files, `.claude/skills/python/SKILL.md`, and this task's
`.claude/tasks/remove-future-annotations/` artifacts. No file under `tests/` is added or changed.
Historical files under `.claude/tasks/constitution/` are not edited.

Suggested message: `refactor: remove from __future__ import annotations and forbid it in the python skill`.
