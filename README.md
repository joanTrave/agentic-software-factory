# 🏭 Agentic Software Factory

> You write the idea. A tiny crew of AI agents writes the rest.
> You just say "approved" twice and look important. 😎

## 👀 Show me, don't tell me

Check out the **[`example`](https://github.com/joanTrave/agentic-software-factory/tree/example)**
branch. It's a full repository built by this factory, following the house rules in
[`docs/`](docs/): a FastAPI service with a health check that actually talks to the database,
plus Alembic, Docker and tests. The receipts (plan, architecture gate, review) live in
`.claude/tasks/constitution/`.

## 🧑‍🔧 Meet the crew

| Agent | Job description |
|---|---|
| 🔍 **Refiner** | Turns your vague ticket into a crisp mission spec |
| 📐 **Architect** | Draws the blueprints so nobody builds a kitchen in the garage |
| 🧪 **Tester** | Writes the tests first. Nobody else gets to touch them |
| 🛠️ **Developer** | Writes code until the Tester stops complaining |
| 🧐 **Reviewer** | Judges everything. Says no a lot |

## 🎮 Commands

| Command | What happens |
|---|---|
| `/initiate-repository <name>` | Reads `docs/constitution.md` and builds a real, runnable repo (Docker, DB and health check included) once you approve the plan |
| `/refine-task <jira-key\|text\|url>` | Writes the mission spec to `.claude/tasks/<id>/specs/` |
| `/architect-plan <id>` | Writes `plan.md` + `architecture-gate.md` → **🚦 you approve** |
| `/implement <id>` | Tester → Developer ⇄ Reviewer (3 rounds max) → **🚦 you approve** |
| `/ship <id>` | Branch, Conventional Commit, push, draft PR to `development` |

## 🚀 Your first day

```text
1. Describe your project in docs/constitution.md
2. /initiate-repository my-shiny-service   ← once per repo

3. /refine-task BOF-1234                   ← for every task
4. /architect-plan BOF-1234                → read architecture-gate.md, approve
5. /implement BOF-1234                     → read review.md, approve
6. /ship BOF-1234                          → go get a coffee ☕
```

## 🗺️ Where things live

- `docs/`: the house rules (constitution, best practices, reusable building blocks)
- `.claude/agents/`: the crew
- `.claude/commands/`: the buttons
- `.claude/skills/`: the rulebook every agent follows
- `CLAUDE.md`: the workflow, start to finish

## 🔧 Make it yours

Swap the skills marked **EXAMPLE** (`python`, `dependency-injection`, `naming`) for your stack.
Then add your reviewers in `.claude/skills/git/SKILL.md`.
