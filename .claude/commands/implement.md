---
description: Run Tester → Developer → Reviewer (looping Developer↔Reviewer until approved), then the second human approval gate, then Developer commits/pushes/opens the PR.
---

Task id supplied below. This command assumes the first approval gate already passed — the human
has read `.claude/tasks/<task-id>/plan/architecture-gate.md` and approved the architecture. If you
have not seen that approval in this conversation, ask the human to confirm it before dispatching
anything; do not infer approval from the mere existence of the plan files.

Preconditions — stop and tell the human what's missing rather than fabricating it:
- `.claude/tasks/<task-id>/plan/plan.md` must exist (Architect's implementation + test plan).
- `.claude/tasks/<task-id>/plan/architecture-gate.md` must exist.

## 1. Tester

Dispatch the `tester` agent (`.claude/agents/delivery/tester.md`) with the task id and the path to
`plan.md`. The Tester writes tests derived from the approved plan. Once written, these tests are
Tester-owned for the remainder of this task — the Developer must not modify or delete them (see
`.claude/agents/delivery/developer.md`).

## 2. Developer ↔ Reviewer loop

1. Dispatch the `developer` agent (`.claude/agents/delivery/developer.md`) with the task id, the
   plan, and (from the second iteration on) the prior `review.json`/`review.md` findings to
   address. The Developer implements per the plan and runs the Tester's tests until they pass,
   without touching Tester-owned tests.
2. Dispatch the `reviewer` agent (`.claude/agents/delivery/reviewer.md`) with the task id. It
   independently reviews the diff and writes
   `.claude/tasks/<task-id>/reviews/review.json` + `.claude/tasks/<task-id>/reviews/review.md`
   per `.claude/skills/artifacts/SKILL.md`.
3. Read `review.json`'s `status`:
   - `approved` or `approved_with_warnings` → exit the loop, proceed to the human gate below.
   - `changes_requested` → send the findings back to the Developer (step 1) for another pass.
   - `rejected` or `blocked` → stop and report to the human immediately; do not keep looping on a
     rejection that needs a human or architectural decision, and never silently relax the
     Reviewer's gate to force a pass.
4. Cap the loop at 3 Developer↔Reviewer rounds. If still not `approved`/`approved_with_warnings`
   after 3 rounds, stop and report the unresolved findings to the human instead of iterating
   further on your own judgement.

## 3. Second approval gate

Stop here. Report the Reviewer's final `status`, `overall_score`, any `warnings`, and the paths to
`review.json`/`review.md` to the human. Per `CLAUDE.md`, do not let the Developer commit until the
human explicitly approves.

## 4. Commit, push, open PR

Only after explicit human approval, dispatch the `developer` agent to:
- Branch per `.claude/skills/git/SKILL.md` (if not already on a dedicated branch for this task).
- Commit only the files relevant to this change, using Conventional Commits, with no AI-authorship
  trailer — see the git skill's full rules.
- Push the branch.
- Open a pull request targeting `development`, as a draft unless the human explicitly asked for a
  ready PR, with the standing reviewer group from the git skill added.

Report back the branch name, commit hash, and PR URL.

$ARGUMENTS
