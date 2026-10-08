# Artifacts Skill

## Purpose

Define the concrete, persisted contracts that structure traceable communication between the
delivery agents: where task artifacts live, what the Architect's human-facing gate report must
contain, what the Reviewer's two reports must contain, and the marker convention both reports
share. This replaces an earlier, never-implemented generic artifact envelope — nothing in this
repository emitted or consumed a generic `artifact_id`/`parent_artifact_id` JSON object, so this
skill now documents the artifacts that actually exist instead.

## Task identifier

One `<task-id>` threads the whole pipeline: the Jira key when there is one (`BOF-3006`), otherwise
a kebab-case slug (`better-workflow`). It is simultaneously the mission-spec filename stem
(`.claude/tasks/<task-id>/specs/<task-id>.md`) and the task-artifact directory name (`.claude/tasks/<task-id>/`).

## Task-artifact layout

```text
.claude/tasks/<task-id>/
  specs/
    <task-id>.md             # Refiner: canonical mission spec (see mission-spec skill).
  plan/
    plan.md                 # Architect: implementation plan + test plan. Format/purpose UNCHANGED.
    architecture-gate.md    # Architect: human approval-gate report (see template below).
    [review-fixes.md]       # optional, only when a post-review remediation plan is needed.
  reviews/
    review.json             # Reviewer: machine-readable, authoritative (see schema below).
    review.md               # Reviewer: human-readable, rendered FROM review.json.
  [notes/]                  # only for an artifact with a cited downstream consumer.
```

Nothing else is persisted: no agent reasoning, no per-step conversation logs, no restated copies of
the mission spec, no summary of `plan.md`. The gate report is a *decision* document, not a summary.

## Marker convention

Used inside the architecture gate report (mandatory in its sections 4/11/12/13) and anywhere else
an agent asserts something that a human or a validator needs to be able to point at individually:

- `FACT: <statement> — path:line` — mandatory wherever the report asserts something about existing
  code; must carry a `path:line` reference. Anything about existing code *without* a path reference
  must be written as `ASSUMPTION:` instead — this is what prevents a gate report from stating
  unverified claims as if they were verified ones.
- `ASSUMPTION A<n>: <statement> — basis: <repo path or "none, needs confirmation"> — if wrong: <impact>`
- `DECISION D<n>: <what was decided>` with `Options:`, `Chosen:` (+ one-sentence rationale) and
  `Consequence:` sub-lines.
- `RISK R<n>: <risk>` with `Likelihood`/`Impact` each in `{low, medium, high}` and a `Mitigation`.
- `OPEN QUESTION Q<n>: <question> — blocking: yes/no — default if unanswered: <what the Architect
  will assume>`.

IDs (`D1`, `R1`, `A1`, `Q1`, `C1`, `W1`, `R1` for recommendations) are stable within a single report
and are the handles a human uses to approve or reject individual points.

## Architecture gate report (Architect)

**Path:** `.claude/tasks/<task-id>/plan/architecture-gate.md`
**Budget:** ≤ 150 lines / ~1200 words — anything longer belongs in `plan.md`, not here.
**Determinism rule:** all 17 `##` sections below, in this exact order, in every report. A section
with nothing to say is written as `None.` — never omitted, so a human and a parser both see a
constant shape.

```markdown
# <task-id> — Architecture Gate

| | |
|---|---|
| **Task** | <task-id> — <one-line title> |
| **Mission spec** | `.claude/tasks/<task-id>/specs/<task-id>.md` |
| **Implementation plan** | `.claude/tasks/<task-id>/plan/plan.md` |
| **Branch** | <branch> |
| **Date** | <YYYY-MM-DD> |

## 1. Objective
<= 3 sentences.

## 2. Scope
**In scope:** …
**Out of scope:** …

## 3. Requirements coverage
| Req | Source | Addressed by | Status |
|---|---|---|---|
Status ∈ {covered, partially-covered, deferred, not-covered}. Every requirement in the mission
spec appears exactly once. Any row that is not `covered` must have a matching OPEN QUESTION or RISK.

## 4. Architecture decisions
DECISION D1: <what was decided>
  Options: <a> / <b>
  Chosen: <a> — <rationale in one sentence>
  Consequence: <what this commits us to>

## 5. Affected components
| Path | Change | Why |
|---|---|---|
Change ∈ {ADD, MODIFY, DELETE}.

## 6. Expected code changes
<N files: a added, m modified, d deleted>. One line per file. No code snippets.

## 7. Data model / database changes
Migration required: yes/no. <tables/columns, or `None.`>

## 8. API changes
| Endpoint | Change | Breaking |
|---|---|---|

## 9. External dependencies
Added / removed / unchanged.

## 10. Test strategy
Levels used and why, plus the count of new/changed test files. The detailed test plan stays in
`plan.md` — this is the summary a reviewer needs to judge adequacy, not a copy.

## 11. Risks
| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
RISK R1 … Likelihood/Impact ∈ {low, medium, high}.

## 12. Assumptions
ASSUMPTION A1: <statement> — basis: <path or "none"> — if wrong: <impact>

## 13. Open questions
OPEN QUESTION Q1: <question> — blocking: yes/no — default if unanswered: <what the Architect will assume>

## 14. Breaking changes
Yes/No. <detail, or `None.`>

## 15. Complexity and impact
Size: S/M/L · Files touched: N · Blast radius: <modules> · Rollback: <how>

## 16. Decisions required from the human
Numbered list referencing D#/Q#/R# above. `None.` if the Architect needs nothing.

## 17. Recommendation
**PROCEED** | **PROCEED WITH CONDITIONS** | **DO NOT PROCEED**
<= 3 sentences of justification. If "WITH CONDITIONS", the conditions are the §16 list.
```

The implementation plan (`plan.md`) is unchanged in format and purpose by this skill — it remains
the Architect's existing implementation-plan-plus-test-plan deliverable, consumed by Tester and
Developer. The gate report is an additional, separate deliverable for the human.

## Reviewer machine-readable report (`review.json`)

**Path:** `.claude/tasks/<task-id>/reviews/review.json`
**Schema version:** `1.0`. Additive changes bump the minor version; any field removal or enum
narrowing bumps the major version.

**Scoring scale:** integer `0`–`10`, identical for every dimension and for the overall score.

| Band | Meaning |
|---|---|
| 9–10 | Meets the standard with no findings above cosmetic. |
| 7–8 | Acceptable; minor findings that do not block. |
| 5–6 | Weak; at least one major finding to address. |
| 3–4 | Poor; substantial rework needed in this dimension. |
| 0–2 | Unacceptable, or a critical issue in this dimension. |
| `null` | Not applicable to this change. Requires `status: "not_applicable"` and a `summary` giving the reason. Excluded from `overall_score`. |

**`overall_score` is computed deterministically as the *minimum* of all non-null dimension
scores.** No weights, no averaging — the same inputs always produce the same number, and a single
bad dimension cannot be averaged away.

**`status` enum (5 values)** — evaluated top to bottom; the first match wins:

| # | `status` | Condition |
|---|---|---|
| 1 | `blocked` | The review could not be completed with evidence — tests could not be run, or diff coverage could not be measured (`coverage.measured == false`), or the diff could not be obtained. **Never** report `approved` in this case. |
| 2 | `rejected` | ≥1 entry in `critical_issues`, OR any in-scope requirement with `status == "not_verified"`, OR `tests_executed.failed > 0`, OR measured `coverage.diff_coverage_percent < 90`. |
| 3 | `changes_requested` | No critical issues, but ≥1 warning with `severity == "major"`, OR any dimension score < 6, OR any requirement with `status == "partially_verified"`. |
| 4 | `approved_with_warnings` | At least one `minor` warning (and none above minor); every dimension ≥ 6; every requirement `verified` or `not_applicable`. |
| 5 | `approved` | Zero warnings; every dimension ≥ 8; every requirement `verified` or `not_applicable`. |

If no rule matches (e.g. an unanticipated combination), the implementation falls back to
`changes_requested` — never silently default to `approved`.

**Schema:**

```jsonc
{
  "schema_version": "1.0",                 // string, fixed "1.0"
  "artifact_type": "review_report",        // string, fixed
  "task_id": "BOF-3006",                   // string
  "generated_at": "2026-10-08T09:12:00Z",  // string, ISO-8601 UTC
  "reviewed": {
    "base": "origin/development",          // string
    "head": "a1b2c3d",                     // string, commit sha or "working-tree"
    "diff_command": "git diff origin/development...HEAD"   // string, the exact command run
  },
  "plan_ref": ".claude/tasks/BOF-3006/plan/plan.md",   // string|null
  "spec_ref": ".claude/tasks/BOF-3006/specs/BOF-3006.md",                   // string|null

  "status": "approved_with_warnings",      // enum, see table above
  "overall_score": 7,                      // integer 0..10 == min(non-null dimension scores)

  "dimensions": {                          // all 7 keys ALWAYS present
    "architecture":    { "score": 8,    "status": "ok",             "summary": "…", "evidence": ["src/x/y.py:41"] },
    "correctness":     { "score": 7,    "status": "ok",             "summary": "…", "evidence": [] },
    "maintainability": { "score": 8,    "status": "ok",             "summary": "…", "evidence": [] },
    "testing":         { "score": 7,    "status": "ok",             "summary": "…", "evidence": ["tests/…::test_x"] },
    "security":        { "score": 9,    "status": "ok",             "summary": "…", "evidence": [] },
    "performance":     { "score": null, "status": "not_applicable", "summary": "No hot path touched.", "evidence": [] },
    "observability":   { "score": 6,    "status": "concern",        "summary": "…", "evidence": [] }
  },
  // dimension.status enum: "ok" | "concern" | "fail" | "not_applicable" | "not_assessed"
  // "not_assessed" requires score null AND forces overall status "blocked".

  "coverage": {
    "measured": true,                      // boolean — false ⇒ status must be "blocked"
    "tool": "diff-cover",                  // string
    "command": "…",                        // string, exact command run
    "diff_coverage_percent": 94.2,         // number|null
    "threshold_percent": 90,               // number, fixed 90 (reviewer.md hard gate)
    "passed": true,                        // boolean|null
    "exempt_files": ["…"]                  // string[], the testing skill's known-measurement-artifact list
  },

  "tests_executed": {
    "run": true,                           // boolean — false ⇒ status must be "blocked"
    "command": "…",                        // string
    "exit_code": 0,                        // integer|null
    "passed": 128, "failed": 0, "errors": 0, "skipped": 2   // integer|null each
  },

  "lint": {
    "run": true,                           // boolean
    "command": "ruff check . --exclude alembic/env.py",     // string
    "exit_code": 0,                        // integer|null
    "violations": 0                        // integer|null
  },

  "requirements_verification": [           // array, one entry per mission-spec requirement
    {
      "id": "FR-1",                        // string
      "source": ".claude/tasks/BOF-3006/specs/BOF-3006.md#functional-requirements",  // string
      "statement": "…",                    // string, verbatim from the spec
      "status": "verified",                // enum: verified | partially_verified | not_verified | not_applicable
      "evidence": [                        // array; MUST be non-empty when status == "verified"
        { "type": "test", "ref": "tests/…::test_x", "detail": "passes, asserts …" }
      ]                                    // evidence.type enum: test | code | command_output | diff
    }
  ],

  "critical_issues": [                     // array; severity always "critical"
    { "id": "C1", "dimension": "correctness", "severity": "critical",
      "title": "…", "location": "src/…:88", "detail": "…", "suggested_fix": "…" }
  ],
  "warnings": [                            // array; same shape, severity "major" | "minor"
    { "id": "W1", "dimension": "testing", "severity": "major",
      "title": "…", "location": "tests/…:12", "detail": "…", "suggested_fix": "…" }
  ],
  "recommendations": [                     // array; non-blocking improvements
    { "id": "R1", "dimension": "maintainability", "title": "…", "detail": "…", "priority": "low" }
  ],                                       // priority enum: high | medium | low

  "test_ownership": {                      // enforces the Developer/Tester boundary
    "tester_tests_modified": false,        // boolean — true ⇒ at minimum a "major" warning
    "modified_files": []                   // string[]
  },

  "verdict": {
    "recommendation": "approve",           // enum: approve | reject
    "blocking_reasons": [],                // string[]; MUST be non-empty when recommendation == "reject"
    "summary": "…"                         // string, <= 3 sentences
  }
}
```

**Anti-overclaim invariants** (validated mechanically): a requirement may be `verified` only with
non-empty `evidence`; `coverage.measured == false` or `tests_executed.run == false` forces
`status: "blocked"`; `overall_score` must equal `min(non-null dimension scores)`; `status` must
match the derivation table above.

## Reviewer human-readable report (`review.md`)

**Path:** `.claude/tasks/<task-id>/reviews/review.md`

**Generation rule — this is the mechanism that guarantees "both reports represent the same review
result":** the Reviewer **writes `review.json` first**, then renders `review.md` **from that file
only**. Every number, status, score, issue and requirement row in the Markdown is a transcription
of a JSON field. The Reviewer may add prose only inside the `summary`/`detail` strings that already
exist in the JSON. No statement may appear in `review.md` that is not derivable from `review.json`.

Fixed section order:

```markdown
# <task-id> — Review Report
**Status:** <status> · **Overall score:** <overall_score>/10 · **Recommendation:** <verdict.recommendation>
<verdict.summary>

## 1. Verdict
Blocking reasons (if any), as a list.

## 2. Quality dimensions
| Dimension | Score | Status | Summary |
(7 rows, always; `n/a` for null.)

## 3. Critical issues
(one `### C<n> — <title>` block each, or `None.`)

## 4. Warnings
(`### W<n> — <title>` blocks, or `None.`)

## 5. Requirements verification
| Req | Status | Evidence |

## 6. Verification evidence
Tests: <passed/failed/errors/skipped>, exit <code>, command.
Diff coverage: <pct>% vs 90% threshold → pass/fail (or "NOT MEASURED").
Lint: <violations>, exit <code>.

## 7. Test ownership
Tester-authored tests modified: yes/no (+ file list).

## 8. Recommendations
(non-blocking, or `None.`)

---
Machine-readable: `.claude/tasks/<task-id>/reviews/review.json` (schema 1.0)
```

## Requirements

- Validate artifacts structurally before downstream consumption (required sections present and in
  order, schema fields valid).
- Keep `review.json` authoritative; `review.md` is a rendering, never a second source of truth.
- Keep payloads machine-readable when another agent will consume them.
- Do not use these artifacts as a dumping ground for arbitrary logs — agent reasoning and
  conversation history are separate concerns and are not persisted here.
