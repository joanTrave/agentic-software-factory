# Agentic Software Factory

A Claude Code setup that turns a short project description into a working repository, then delivers
every task through a team of specialised agents. The agents do the heavy lifting; you keep the final
say at two approval gates.

## See it in action

The [`example`](https://github.com/joanTrave/agentic-software-factory/tree/example) branch holds a
repository built with this factory, following the conventions in [`docs/`](docs/). It's a FastAPI
service with:

- a health check endpoint that really talks to the database
- Alembic migrations
- Docker and docker-compose with `api`, `test` and `db` services
- a test suite

The artifacts that produced it (the plan, the architecture gate and the review) are in
`.claude/tasks/constitution/`, so you can follow how it was built step by step.

## The team

| Agent | Responsibility |
|---|---|
| **Refiner** | Turns a ticket, a pasted description or a URL into a precise mission spec. |
| **Architect** | Designs the solution: module boundaries, dependencies, persistence, API. Writes the plan and the decision document you approve. |
| **Tester** | Writes the tests from the approved plan before any code exists. Only the Tester can change them. |
| **Developer** | Implements the plan until the Tester's tests pass, then commits once you approve. |
| **Reviewer** | Independently checks correctness, architecture, maintainability, security and test quality, and returns a verdict. |

## Commands

Run these inside Claude Code from the repository root.

### `/initiate-repository <repository-name>`

Builds a new project from `docs/constitution.md`. The Architect plans the structure and you approve
it. After that, every file is written with real content, never as an empty placeholder. Each file's
content comes from the first of these sources that settles it:

1. `docs/constitution.md`
2. `docs/best_practices.md`
3. `docs/custom_implementations/`
4. the skills in `.claude/skills/`

The result includes a database-connected health check, a `.env`, and a runnable Docker setup.
`<repository-name>` becomes the project name and the API path segment (`/api/<repository-name>/v1/...`).

### `/refine-task <jira-key | text | url>`

Writes the mission spec to `.claude/tasks/<task-id>/specs/<task-id>.md`. `<task-id>` is the Jira key
when there is one, otherwise a kebab-case slug.

### `/architect-plan <task-id>`

Produces two files in `.claude/tasks/<task-id>/plan/`:

- `plan.md`: the implementation and test plan the other agents follow.
- `architecture-gate.md`: the decision document you read and approve. This is **approval gate 1**.

### `/implement <task-id>`

1. The Tester writes the tests.
2. The Developer and the Reviewer loop for up to three rounds. The verdict is written to
   `.claude/tasks/<task-id>/reviews/review.json` and `review.md`.
   - `approved` or `approved_with_warnings` ends the loop.
   - `changes_requested` sends the Developer back for another round.
   - `rejected` or `blocked` stops the loop and hands the problem to you.
3. It stops for your approval before anything is committed. This is **approval gate 2**.

### `/ship <task-id>`

Commits approved work on a `feature/<task-id>-<slug>` (or `hotfix/...`) branch, using Conventional
Commits with a `Refs: <task-id>` footer. It then pushes the branch and opens a draft PR against
`development` with the standing reviewers.

## Your first project

```text
1. Describe your project in docs/constitution.md
2. /initiate-repository my-service      once per repository

3. /refine-task BOF-1234                for every task
4. /architect-plan BOF-1234             read architecture-gate.md and approve
5. /implement BOF-1234                  read review.md and approve
6. /ship BOF-1234
```

## Where things live

| Path | Contents |
|---|---|
| `docs/constitution.md` | The project definition: stack, structure, conventions. Written by a human. |
| `docs/best_practices.md` | Numbered code patterns: domain isolation, transactions, dependency injection, permissions, repositories, tests, naming. |
| `docs/custom_implementations/` | Reusable building blocks (`CustomException`, `@requires_permissions`, `@with_transaction`). Wire them in; don't reimplement them. |
| `.claude/agents/delivery/` | The agent definitions. |
| `.claude/commands/` | The commands above. |
| `.claude/skills/` | The rules every agent follows: architecture, naming, testing, git, artifacts, mission spec. |
| `.claude/metrics/` | A log of agent token usage, with reporting scripts. |
| `CLAUDE.md` | The full workflow Claude Code follows in this repository. |

## Adapting it to your stack

- Skills marked **EXAMPLE** (`python`, `dependency-injection`, `naming`) are meant to be swapped for
  your own stack.
- Add your standing reviewers in `.claude/skills/git/SKILL.md`.
- Adjust the PR tooling section of that skill if you aren't on Bitbucket.
