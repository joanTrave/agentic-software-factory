# Agent Usage Metrics

`agent-usage.jsonl` is an append-only log of subagent token consumption, kept as durable state
(not conversation history) so cost/context data survives session resets.

## Convention

Whoever dispatches an agent (a human or the top-level session) appends exactly one line per
completed dispatch, as soon as its result/usage is known — never batched, never reconstructed
after the fact from memory. One JSON object per line:

```json
{"timestamp": "2026-09-11T10:00:00Z", "role": "developer", "task": "US-007: add X", "model": "haiku", "effort": "low", "subagent_tokens": 34945, "tool_uses": 12, "duration_ms": 45000}
```

Fields:
- `timestamp` — ISO 8601, UTC, when the dispatch completed.
- `role` — the `subagent_type` used (`architect`, `developer`, `tester`, `reviewer`, etc.).
- `task` — a short description of what was dispatched (matches the `description` passed to the
  Agent tool).
- `model` / `effort` — the agent's declared frontmatter values at dispatch time (so a later change
  to an agent's tier doesn't retroactively mislabel historical rows).
- `subagent_tokens`, `tool_uses`, `duration_ms` — taken verbatim from the dispatch's own
  `<usage>` block; do not estimate or round.

Append with a single line, e.g.:

```bash
echo '{"timestamp":"...","role":"developer","task":"...","model":"haiku","effort":"low","subagent_tokens":N,"tool_uses":N,"duration_ms":N}' >> .claude/metrics/agent-usage.jsonl
```

## Reporting

`python3 .claude/metrics/report.py` prints a summary grouped by role (count, total tokens, average
tokens, total tool uses) plus the full per-dispatch table, largest first.

## Scope note

This captures dispatches made directly by whoever is driving the workflow. A dispatched agent that
itself spawns further agents would need its own append inside that agent's own execution — not
something this file's convention can enforce from outside.

## Historical prune (2026-10-08)

The 22 historical `discovery-*` rows (all dated 2026-09-11/2026-09-12, from the Discovery
subsystem's evaluation window) were removed in a single one-time filter as part of removing the
Discovery subsystem itself (decision H1/H5, `better-workflow`). This is the append-only
convention's one documented exception — do not treat the resulting row-count discontinuity as data
loss. At prune time the file held 143 rows (121 non-Discovery + 22 Discovery); the plan's original
evidence (F7) captured it earlier at 141 rows (119 + 22) — the file is live and grew by 2
non-Discovery dispatches between plan authorship and execution, which is expected of an append-only
log and does not affect the prune itself. After the prune: 121 rows, zero `discovery-*` entries.

## Automated anomaly check

A `SubagentStop` hook (`.claude/settings.json`) runs `check_token_anomaly.py` after every agent
dispatch. It appends a best-effort row itself (approximating `subagent_tokens` from the dispatch's
last assistant turn, since the harness's own `<usage>` tally isn't available until the
task-notification reaches the dispatcher — a manual append per the convention above is still more
accurate and should be preferred when you have the real numbers), then compares that row against
the role's history: flags a "token hole" when a dispatch is ≥2σ above its role's mean (3+ prior
samples) or ≥3x the mean (fewer samples). A flagged dispatch surfaces as a `systemMessage` in the
session.
