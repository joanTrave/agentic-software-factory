---
description: Commit the current changes, push the branch, and open a PR with the standing reviewer group.
---

Task id supplied below as `$ARGUMENTS`. This command does not run Tester/Developer/Reviewer — it
assumes implementation work is already done and approved (e.g. via `/implement`), and only handles
the final commit/push/PR step. If the implementation has not been reviewed/approved yet, say so and
suggest `/implement <task-id>` instead, rather than shipping unreviewed work.

Delegate the commit/push/PR step below to the `developer` agent rather than performing it directly.
Give the agent the task id (`$ARGUMENTS`), the current branch/diff state, and this file's contents
so it has the full instructions. Report back whatever the agent reports in step 5.

Follow `.claude/skills/git/SKILL.md` exactly for branching, commit message format and PR rules.

## 1. Pre-flight

- Run `git status` and `git diff` to see what's staged/unstaged and what's untracked.
- If the current branch is `main` (or `development`), stop and create a branch first, named
  `feature/<task-id>-<slug>` or `hotfix/<task-id>-<slug>` per the git skill's convention — ask the
  user which prefix fits if it's not obvious from the task id/ticket type.
- Only stage files relevant to this change. If you see unrelated untracked/modified files, leave
  them out and tell the user.
- Never commit secrets/credentials. If a staged file looks suspicious, inspect its contents before
  proceeding.
- Run the relevant formatting/linting/test suites before committing. If anything fails, stop and
  report instead of committing over it.

## 2. Commit

- Write a Conventional Commits message (`type(scope): description`), referencing the task id in the
  body/footer (e.g. `Refs: <task-id>`) when there is one.
- No AI-authorship trailer of any kind (no `Co-Authored-By: Claude`, no `Claude-Session:`, no
  mention of Claude/Anthropic/AI generation).
- Prefer one logical commit; if the staged changes are clearly multiple unrelated logical changes,
  split into multiple commits rather than bundling them.

## 3. Push

- Push the branch with `-u` if it has no upstream yet.

## 4. Open PR

- Target `development`, not `main`.
- Open as a **draft** unless the user explicitly asked for a ready-for-review PR.
- Add the standing reviewer group as listed in `.claude/skills/git/SKILL.md`.
- Title should reference the task id when there is one. Body: concise summary + test plan, no
  AI-authorship mention, following the PR body conventions already used in this repo (see
  `gh pr create` guidance in your system prompt).

## 5. Report

Report back the branch name, commit hash(es), and PR URL.

$ARGUMENTS
