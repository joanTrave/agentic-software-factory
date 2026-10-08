---
description: Run the architect agent against a task's mission spec to produce the implementation plan and the human-readable architecture gate report.
---

Dispatch the `architect` agent (`.claude/agents/delivery/architect.md`) for the task id supplied
below.

The input to the architect is the path `.claude/tasks/<task-id>/specs/<task-id>.md` — pass that
path, not its content pasted inline. If that file does not exist, stop and tell the human to run
`/refine-task` first; do not fabricate a mission spec.

The architect must produce both of its deliverables for this task:

1. The implementation plan (and test plan) at `.claude/tasks/<task-id>/plan/plan.md` — format and
   purpose unchanged from the existing convention.
2. The architecture gate report at `.claude/tasks/<task-id>/plan/architecture-gate.md`, following
   the deterministic 17-section template in `.claude/skills/artifacts/SKILL.md`.

If no task id is supplied below, ask the human for it before dispatching.

Once both artifacts are written, report their paths to the human and stop. Do not proceed to the
Tester automatically — per `CLAUDE.md`, this is an approval gate: the human reads
`architecture-gate.md` and decides whether to continue, and the pipeline advances only when they
say so.

$ARGUMENTS
