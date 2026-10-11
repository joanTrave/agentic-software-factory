# remove-future-annotations — Architecture Gate

| | |
|---|---|
| **Task** | remove-future-annotations — Remove `from __future__ import annotations` and forbid it in the Python skill |
| **Mission spec** | `.claude/tasks/remove-future-annotations/specs/remove-future-annotations.md` |
| **Implementation plan** | `.claude/tasks/remove-future-annotations/plan/plan.md` |
| **Branch** | example |
| **Date** | 2026-10-11 |

## 1. Objective
Delete every `from __future__ import annotations` from the repository's `.py` files and keep all annotations resolving under eager evaluation, with no behavior change. Add a prohibition rule to `.claude/skills/python/SKILL.md` so the import is not reintroduced.

## 2. Scope
**In scope:** the 27 `.py` files found by the grep (root, `src/`, `docs/custom_implementations/`); minimal quoting of 5 self-referencing annotations; one rule in the Python skill's `## Imports`.
**Out of scope:** any new or changed test file (human decision); historical `.claude/tasks/constitution/` artifacts; `.claude/skills/dependency-injection/SKILL.md`; Ruff/`pyproject.toml` config; the unrelated uncommitted edits to `entrypoint.sh` and `scripts/init_test_db.sh`.

## 3. Requirements coverage
| Req | Source | Addressed by | Status |
|---|---|---|---|
| Plan + gate exist and are approved | spec DoD / Workflow | this report, plan.md | covered |
| Reviewer + user approval of commit | spec DoD / Workflow | CLAUDE.md pipeline, plan §7 | covered |
| Grep returns no matches | spec DoD / Import removal | plan §2, §6 step 1 | covered |
| Skill contains explicit rule | spec DoD / Python skill | plan §4, D3 | covered |
| None of the listed files has the import | spec FR | plan §1–2 (27 files, see A5) | covered |
| No other `.py` file has the import | spec FR | plan §1, §6 step 1 | covered |
| App starts, health check unchanged | spec FR | plan §3, existing tests, plan §6 | covered |
| Rule is a prohibition, in python skill | spec FR | plan §4 | covered |
| Follow `docs/best_practices.md` | spec TR | no pattern touched | covered |
| Follow `CLAUDE.md` conventions | spec TR | pipeline unchanged | covered |
| Ruff/isort-compliant import order | spec TR | plan §2, §6 step 2 | covered |
| No unrelated changes | spec TR | plan §2, §7, R2 | covered |
| Tests pass | spec Verification | existing suite, plan §5–6 | covered |
| Ruff passes | spec Verification | plan §6 step 2 | covered |
| Repo-wide grep is empty | spec Verification | plan §6 step 1 | covered |
| Every `src/` module imports | spec Verification | existing suite via app/bootstrap/Alembic imports; optional one-off command (plan §6) | covered |

## 4. Architecture decisions
FACT: 27 files contain the import; no `TYPE_CHECKING` blocks exist — `grep -rn "from __future__ import annotations" --include="*.py" .` (e.g. `src/core/domain/enum.py:1`)
FACT: 5 annotations refer to their own enclosing class, which fails eagerly — `src/core/domain/enum.py:17`, `src/core/infrastructure/config/settings.py:43`, `src/core/infrastructure/config/settings.py:52`, `src/health/application/check_health/serializers/health_output.py:17`, `src/health/application/check_health/serializers/health_output.py:33`
FACT: existing tests exercise all 5 sites — `tests/core/domain/test_enum.py`, `tests/core/infrastructure/config/test_settings.py:32`, `tests/health/infrastructure/api/v1/test_health_router.py:50`

DECISION D1: Remove the import from all 27 files, including `docs/custom_implementations/`.
  Options: all 27 / only `src/` + `gunicorn.conf.py`
  Chosen: all 27 — the human confirmed A1.
  Consequence: reference copies change (Step 1 only, no annotation fixes needed there).

DECISION D2: Fix self-references by quoting the whole annotation (`-> "CustomEnum | None"`, `-> "Settings"`).
  Options: quote whole annotation / `typing.Self` / restructure classes
  Chosen: quote — it is minimal and behavior-neutral (A4), and it works on staticmethods, where `Self` is invalid.
  Consequence: 5 string annotations remain. None is inspected by `@autowired`. `"X" | None` is forbidden (runtime `TypeError`).

DECISION D3: Place the rule in `## Imports` of `.claude/skills/python/SKILL.md`.
  Options: `## Imports` / `## Code quality`
  Chosen: `## Imports` — the rule is about an import statement, and the human confirmed the file (A3).
  Consequence: `## Code quality` and other skills are untouched.

DECISION D4: Add no tests; verify with the existing suite, Ruff check/format and a working-tree grep.
  Options: existing verification only / + pytest guard and import smoke test / + Ruff `TID251`
  Chosen: existing verification only — the human's decision; the existing tests already exercise the 5 fixed sites.
  Consequence: nothing mechanically prevents reintroduction beyond the skill rule and review; the Tester step writes nothing.

## 5. Affected components
| Path | Change | Why |
|---|---|---|
| `src/**/*.py` (23 files) | MODIFY | remove import; quote 5 self-references in 3 of them |
| `gunicorn.conf.py` | MODIFY | remove import |
| `docs/custom_implementations/*.py` (3 files) | MODIFY | remove import (D1) |
| `.claude/skills/python/SKILL.md` | MODIFY | prohibition rule (D3) |

## 6. Expected code changes
28 files: 0 added, 28 modified, 0 deleted.
- `gunicorn.conf.py`, `src/app.py`, `src/core/infrastructure/bootstrap.py` — remove import.
- `src/core/domain/enum.py` — remove import; quote return annotation of `_missing_`.
- `src/core/domain/exceptions/custom_exception.py` — remove import.
- `src/core/infrastructure/api/exception_handlers.py`, `.../api/request_id_middleware.py`, `.../api/security/requires_permissions.py` — remove import.
- `src/core/infrastructure/config/settings.py` — remove import; quote 2 validator return annotations.
- `src/core/infrastructure/database/sql/base.py`, `engine.py`, `metadata.py`, `session_manager.py`, `repositories/i_database_repository_sql.py` — remove import.
- `src/core/infrastructure/logging/logging_config.py`, `request_context.py` — remove import.
- `src/health/application/check_health/i_check_health_use_case.py` — remove import.
- `src/health/application/check_health/serializers/health_output.py` — remove import; quote 2 `from_bo` return annotations.
- `src/health/domain/bo/dependency_check.py`, `bo/health_report.py`, `enums/health_status_enum.py`, `repositories/i_health_query_service.py` — remove import.
- `src/health/infrastructure/api/v1/health_router.py`, `database/health_query_service_sql.py` — remove import.
- `docs/custom_implementations/custom_exception.py`, `requires_permissions.py`, `with_transaction.py` — remove import.
- `.claude/skills/python/SKILL.md` — add the prohibition under `## Imports`.

## 7. Data model / database changes
Migration required: no. None.

## 8. API changes
| Endpoint | Change | Breaking |
|---|---|---|
| `GET /health` | none (behavior must be identical) | no |

## 9. External dependencies
Unchanged.

## 10. Test strategy
No new or changed test files (human decision, D4). The existing unit and API tests already exercise all 5 fixed sites: `test_enum.py`, `test_settings.py` and `test_health_router.py`. An eager-evaluation error surfaces at import, during collection through `tests/conftest.py`. These tests must pass unchanged. On top of that come Ruff check/format and a grep for `from __future__ import` over `src/`, `gunicorn.conf.py` and `docs/`. Diff coverage is about 100%: the only changed `src` lines are the 5 `def` lines, which run at import.

## 11. Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | An eager-evaluation failure missed by static analysis (no runnable Python was available at planning time) | low | medium | it would raise at import, so the existing suite would fail at collection (conftest imports `src.app` and runs `bootstrap()`); optional one-off import command in plan §6 |
| R2 | Unrelated dirty files (`entrypoint.sh`, `scripts/init_test_db.sh`) are swept into the commit | medium | medium | stage explicit paths only (plan §7); Reviewer checks the diff file list |
| R3 | Blank-line handling glues a docstring to its import or leaves a double blank (`docs/` is not linted) | low | low | `ruff format --check` for linted files; Reviewer reads the `docs/` diff |
| R4 | `docs/custom_implementations/` has no lint or test coverage (`.dockerignore:20`, Ruff `extend-exclude`) | high | low | working-tree grep (plan §6 step 1) + Reviewer diff read; static analysis found no annotation hazard there |
| R5 | Pinned Ruff `0.16.10` flags the quoted annotations (UP037) | low | low | run ruff; on a misfire escalate, never reintroduce the import or add `noqa` silently |
| R6 | The import is reintroduced later; only the skill rule and review prevent it | medium | low | accepted by the human (D4) |

## 12. Assumptions
ASSUMPTION A1: `docs/custom_implementations/*.py` are in scope — basis: `docs/custom_implementations/custom_exception.py:10` — if wrong: n/a. **Confirmed by the human.**
ASSUMPTION A2: `.claude/tasks/constitution/` artifacts are not edited — basis: `.claude/tasks/constitution/reviews/review.md:42` is a historical record — if wrong: reword W3 in `review.md`/`review.json`. **Plan default; not blocking.**
ASSUMPTION A3: the target skill is `.claude/skills/python/SKILL.md` — basis: `.claude/skills/python/SKILL.md:23` — if wrong: n/a. **Confirmed by the human.**
ASSUMPTION A4: no behavior change; unresolvable annotations are fixed by quoting, never by reintroducing the import — basis: none, needs confirmation — if wrong: the Developer needs a different forward-reference policy (D2). **Plan default; not blocking.**
ASSUMPTION A5: the spec's "26 files" is a miscount; its list and the grep both give 27 — basis: spec lines 7–21 — if wrong: none, because the grep-based DoD governs.

## 13. Open questions
OPEN QUESTION Q1: Object to the defaults A2 (constitution artifacts untouched) or A4 (quote the 5 self-references, no behavior change)? — blocking: no — default if unanswered: proceed as stated.
OPEN QUESTION Q2: Prefer `typing.Self` over quoting for the 3 non-static sites (`enum.py:17`, `settings.py:43`, `settings.py:52`)? — blocking: no — default if unanswered: quote all 5 (D2).
OPEN QUESTION Q3: Also add a Ruff `TID251` banned-api entry to `pyproject.toml`? — blocking: no — default if unanswered: no.

## 14. Breaking changes
No. None.

## 15. Complexity and impact
Size: S · Files touched: 28 · Blast radius: `src/core`, `src/health`, `gunicorn.conf.py`, `docs/custom_implementations`, python skill · Rollback: `git revert` of the single commit.

## 16. Decisions required from the human
None. A1, A3 and D4 have been decided. A2, A4, Q2 and Q3 proceed on their stated defaults unless the human objects.

## 17. Recommendation
**PROCEED**
The change is a small, mechanical refactor. Its only eager-evaluation hazards are 5 identified self-references with a behavior-neutral fix, and the existing tests already exercise all of them. All blocking points are resolved; the remaining items are non-blocking defaults.
