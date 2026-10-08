---
description: Transform a technical task (Jira key, raw text, or URL) into the canonical mission spec at .claude/tasks/<task-id>/specs/<task-id>.md, via the refiner agent.
---

Dispatch the `refiner` agent (`.claude/agents/delivery/refiner.md`) with the task supplied below as
its input. The refiner agent determines the task identifier, resolves any technical context it
needs from the repository, and writes `.claude/tasks/<task-id>/specs/<task-id>.md` following
`.claude/skills/mission-spec/SKILL.md` exactly.

If no task is supplied below, ask the human for it before dispatching — a Jira key, pasted task
text, or a URL are all acceptable.

Once the mission spec is written, report its path to the human and stop. Do not proceed to the
Architect automatically — the next step in the pipeline (see `CLAUDE.md`) starts only when the
human decides to continue.

$ARGUMENTS
