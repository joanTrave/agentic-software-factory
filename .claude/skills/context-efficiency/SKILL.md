# Context Efficiency Skill

## Purpose

Keep the context passed to every agent execution proportional to the actual complexity of its
current task, not to the accumulated history of the workflow.

## Core rule

Never pass more context to an agent than is strictly necessary to complete its current task.

Before every agent execution, determine: the agent's exact task; what information is strictly
required to perform it; which artifacts, files and previous execution results are relevant; and
what can be omitted because it is already represented by an artifact, repository state, or a
deterministic execution result. Only provide the minimum sufficient context.

## Stopping condition (when to stop reading)

Stop investigating once you can state:

1. The directly affected bounded context(s).
2. The interface(s) you must add or change.
3. The key decision(s) and risk(s).

If you cannot state these, read one more targeted thing, then re-check. If still unable, stop
anyway and note the gap as an open risk rather than continuing to read speculatively. Full
understanding of the surrounding system is not the bar — sufficiency to act is.

## Do not carry forward what isn't needed

Do not automatically propagate the complete conversation or workflow history, all previous agent
outputs or artifacts, the entire repository, all test output/logs, all agent instructions, or
unrelated/no-longer-relevant files — an agent must never receive the full context merely because
it is available. This holds across iterative loops too: in sequences such as
`Developer → Tester → Developer → Tester → Reviewer`, each new execution starts from a fresh,
minimal context built for that step (still-relevant requirements, current implementation state,
the latest failure information, and the files relevant to fixing it) rather than accumulating
every prior round's conversation.

## Prefer references over duplication

- When information already exists as a first-class artifact (a mission spec in `.claude/tasks/<task-id>/specs/`, an
  architecture plan, a repository file), reference it by path and let the agent read it — do not
  paste its content into the prompt.
- When information can be obtained deterministically from the repository, filesystem, CLI, or a
  tool, do not reproduce it in the prompt unless the agent needs it immediately and re-deriving it
  would be wasteful.
- When a previous agent produced a large output, pass a concise structured result or a reference to
  the artifact it produced, not the complete output.
- Concretely: an architect's implementation plan MUST be written to a file
  (`.claude/tasks/<task-id>/plan/plan.md`) rather than only returned as response text. Downstream
  agents (developer/tester/reviewer) are then told to read that file, not handed the plan pasted
  into their prompt. This is the flagship case of "reference over duplication" in this project's
  workflow.

Do not delete or mutate historical information merely to shrink a prompt, either — keep the full
execution history in storage (artifacts, git history, docs) for observability and debugging; pass
only the minimal relevant subset forward to the next execution.

## Architectural constraint

Context construction is a coordination concern, not agent business logic. Scoping which context a
stage needs is the responsibility of whoever dispatches that agent (a human, the top-level
session, or a deterministic workflow definition) — not a judgment call the agent makes about
itself mid-run. Do not hardcode agent-specific context rules (`if agent == "developer":
include(...)`) unless the workflow/stage definition explicitly models that requirement as data.

## Validation

For every agent execution it should be possible to answer: why was each piece of context included;
what was deliberately excluded; which artifacts were provided; how large was the resulting
context. The goal is not merely fewer tokens — it's that token consumption tracks the actual
complexity of the current task, not the accumulated history of the workflow.
