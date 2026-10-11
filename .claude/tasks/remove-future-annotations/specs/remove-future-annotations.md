# remove-future-annotations

# Problem
Most Python modules in the project start with `from __future__ import annotations`. A repository-wide
search (`from __future__ import`) finds it in 26 files:

- Root: `gunicorn.conf.py`.
- Application code under `src/`: `src/app.py`, `src/core/domain/enum.py`,
  `src/core/domain/exceptions/custom_exception.py`, `src/core/infrastructure/bootstrap.py`,
  `src/core/infrastructure/config/settings.py`, `src/core/infrastructure/logging/logging_config.py`,
  `src/core/infrastructure/logging/request_context.py`, `src/core/infrastructure/api/request_id_middleware.py`,
  `src/core/infrastructure/api/exception_handlers.py`, `src/core/infrastructure/api/security/requires_permissions.py`,
  `src/core/infrastructure/database/sql/base.py`, `.../engine.py`, `.../metadata.py`, `.../session_manager.py`,
  `.../repositories/i_database_repository_sql.py`, `src/health/domain/repositories/i_health_query_service.py`,
  `src/health/domain/bo/health_report.py`, `src/health/domain/bo/dependency_check.py`,
  `src/health/domain/enums/health_status_enum.py`, `src/health/application/check_health/i_check_health_use_case.py`,
  `src/health/application/check_health/serializers/health_output.py`,
  `src/health/infrastructure/api/v1/health_router.py`,
  `src/health/infrastructure/database/health_query_service_sql.py`.
- Reference implementations: `docs/custom_implementations/with_transaction.py`,
  `docs/custom_implementations/requires_permissions.py`, `docs/custom_implementations/custom_exception.py`.

The import is unwanted: it changes annotations into lazily evaluated strings, which conflicts with code
that inspects annotations at runtime (a prior review,
`.claude/tasks/constitution/reviews/review.md` finding W3, recorded that `check_health_use_case.py` had to
omit it for `@autowired` to work, undocumented). The project's Python skill,
`.claude/skills/python/SKILL.md` (sections Baseline, Imports, Code quality), says nothing about it, so
nothing stops it being reintroduced.

# Solution
1. Remove every `from __future__ import annotations` line from the project's Python files listed above,
   including the blank line that only separated it from the following imports, so that no
   `from __future__ import annotations` remains in any `.py` file in the repository.
2. Code must keep working without the import (annotations are evaluated eagerly; forward references and
   circular type references must be handled by other means than the future import).
3. Add a rule to the `# Python Skill` in `.claude/skills/python/SKILL.md` (Imports or Code quality
   section) stating that `from __future__ import annotations` must not be used.

# Variables
- `PLAN_DIR: .claude/tasks/remove-future-annotations/plan/`
- `FORBIDDEN_IMPORT: from __future__ import annotations`
- `PYTHON_SKILL: .claude/skills/python/SKILL.md`

# Assumptions
- ASSUMPTION: The three files under `docs/custom_implementations/` are in scope as "project Python code" — basis: `docs/custom_implementations/*.py` contain the import and are the reference copies of wired code — if wrong: they would keep the import and diverge from the new skill rule.
- ASSUMPTION: Historical task artifacts under `.claude/tasks/constitution/` that merely mention the import in prose are not edited — basis: `.claude/tasks/constitution/reviews/review.md` is a past review record, not code — if wrong: those review files would also need rewording.
- ASSUMPTION: "proper python skill" means `.claude/skills/python/SKILL.md` — basis: `.claude/skills/python/SKILL.md` — if wrong: the rule would need to be placed in another skill.
- ASSUMPTION: Removing the import must not change application behavior; any annotation that fails to resolve without it is fixed minimally (e.g. quoting a forward reference) rather than reintroducing the import — basis: none, needs confirmation — if wrong: the Developer may need guidance on forward references.

# Workflow
See CLAUDE.md for the workflow definition.

# Definition Of Done
## Workflow Complete
- [ ] The Architect plan and architecture gate report exist under `.claude/tasks/remove-future-annotations/plan/` and were approved.
- [ ] The Reviewer approved the implementation and the user approved the commit.

## Import removal
- [ ] `grep -r "from __future__ import annotations" --include="*.py" .` returns no matches.

## Python skill
- [ ] `.claude/skills/python/SKILL.md` contains an explicit rule that `from __future__ import annotations` must not be used.

# Functional Requirements
- [ ] None of the 26 files listed in `# Problem` contains `from __future__ import annotations`.
- [ ] No other `.py` file in the repository contains `from __future__ import annotations`.
- [ ] The application still starts and the health check endpoint behaves as before.
- [ ] The Python skill rule is worded as a prohibition and is located in `.claude/skills/python/SKILL.md`.

# Technical Requirements
- [ ] Must follow `docs/best_practices.md`.
- [ ] Must follow the existing conventions defined in `CLAUDE.md`.
- [ ] Import ordering in edited files stays Ruff/isort-compliant (`.claude/skills/python/SKILL.md`, Imports).
- [ ] No unrelated changes are made to the edited files.

# Verification
- [ ] Relevant automated tests pass (see proper skill).
- [ ] Static analysis/linting passes (ruff).
- [ ] A repository-wide search for `from __future__ import annotations` in `*.py` files returns zero results.
- [ ] Importing every module under `src/` succeeds without `NameError` or annotation-resolution errors.

# How You're Graded
- Completeness: every occurrence of the import is removed, none left behind.
- The rule in the Python skill is clear, placed correctly and does not alter unrelated guidance.
- No behavioral regressions; tests and ruff pass.
- Changes limited to what the task requires.
