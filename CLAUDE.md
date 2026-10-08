# Jira Ticket Workflow

When starting work on a new task, follow this pipeline. Each agent is invoked with only the minimum context it needs for its step (the ticket details/requirements and the specific prior artifact it must act on) — not the full conversation history.

0. **Refiner** (`/refine-task` command → `refiner` agent): transform a technical task (a Jira key, raw text, or a URL) into the canonical mission spec at `.claude/tasks/<task-id>/specs/<task-id>.md`.
1. **Architect** (`/architect-plan <task-id>` command → `architect` agent): from `.claude/tasks/<task-id>/specs/<task-id>.md`, produce the implementation plan at `.claude/tasks/<task-id>/plan/plan.md` **and** the architecture gate report at `.claude/tasks/<task-id>/plan/architecture-gate.md`.
2. **Approval gate**: stop and wait for the user to approve the architecture before proceeding. Read `architecture-gate.md` to approve — it is the deterministic decision document; `plan.md` is what the downstream agents read, not what the human reviews line by line.
3. Once approved, `/implement <task-id>` runs the following in order:
   - **Tester** (`tester` agent): write tests derived from the approved plan. These tests are Tester-owned once written.
   - **Developer** (`developer` agent): implement the feature per the approved plan and run the tests written by the tester until they pass. The Developer must not modify or delete Tester-owned tests to make an implementation pass (see `.claude/agents/delivery/developer.md`).
   - **Reviewer** (`reviewer` agent): review the implementation (diff) for correctness, architecture, maintainability, security, and test quality; produce `.claude/tasks/<task-id>/reviews/review.json` (authoritative) and `.claude/tasks/<task-id>/reviews/review.md` (rendered from it); return an explicit approve/reject recommendation.
4. **Approval gate**: once the reviewer approves, stop and wait for the user to approve before committing.
5. Once the user approves, the **Developer** commits the change (Conventional Commits).

Do not skip either approval gate, and do not let the developer commit before the second approval is given.

## Artifact locations

| Artifact | Path | Produced by |
|---|---|---|
| Mission spec | `.claude/tasks/<task-id>/specs/<task-id>.md` | Refiner |
| Implementation plan | `.claude/tasks/<task-id>/plan/plan.md` | Architect |
| Architecture gate report | `.claude/tasks/<task-id>/plan/architecture-gate.md` | Architect |
| Review (machine-readable) | `.claude/tasks/<task-id>/reviews/review.json` | Reviewer |
| Review (human-readable) | `.claude/tasks/<task-id>/reviews/review.md` | Reviewer |

`<task-id>` is the Jira key when there is one (`BOF-3006`), otherwise a kebab-case slug. See
`.claude/skills/artifacts/SKILL.md` for the full layout and the report templates/schemas, and
`.claude/skills/mission-spec/SKILL.md` for the mission-spec template.
