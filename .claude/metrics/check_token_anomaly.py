#!/usr/bin/env python3
"""SubagentStop hook: log this dispatch's token usage and flag a "token hole"
(an outlier dispatch for its role) by comparing against that role's history in
agent-usage.jsonl. Reads the hook's stdin JSON, writes a systemMessage back on
stdout when an anomaly is found.

Convention/file format matches .claude/metrics/README.md. This automates what
that README describes as a manual append, using the best signal available at
SubagentStop time (the last assistant turn's usage block) rather than the
harness's own <usage> tally, which is only surfaced later, in the dispatcher's
task-notification.
"""
import json
import statistics
import sys
from pathlib import Path

METRICS_DIR = Path(__file__).resolve().parent
LOG_PATH = METRICS_DIR / "agent-usage.jsonl"

# Z-score threshold for flagging an outlier dispatch, once a role has enough history.
Z_THRESHOLD = 2.0
MIN_SAMPLES_FOR_ZSCORE = 3
# Below MIN_SAMPLES_FOR_ZSCORE, fall back to a simple multiple-of-mean check.
FALLBACK_MULTIPLE = 3.0


def load_hook_input() -> dict:
    return json.load(sys.stdin)


def last_turn_usage(transcript_path: str) -> tuple[int, str] | None:
    """Best-effort (tokens, model) for the dispatch, from the last assistant message:
    its usage block (input + cache_creation + cache_read + output tokens), which
    reflects that request's full context rather than an incremental delta, and its
    `model` field — the hook's stdin input has no model/effort of its own beyond the
    agent's declared effort, so model must come from the transcript."""
    path = Path(transcript_path)
    if not path.exists():
        return None
    usage = None
    model = "unknown"
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            msg = entry.get("message")
            if isinstance(msg, dict) and isinstance(msg.get("usage"), dict):
                usage = msg["usage"]
                model = msg.get("model", model)
    if usage is None:
        return None
    tokens = (
        usage.get("input_tokens", 0)
        + usage.get("cache_creation_input_tokens", 0)
        + usage.get("cache_read_input_tokens", 0)
        + usage.get("output_tokens", 0)
    )
    return tokens, model


def effort_level(raw_effort) -> str:
    """The hook's stdin `effort` field is `{"level": "..."}`, not the flat string
    the README's row example documents — normalize it here rather than logging the
    nested object verbatim."""
    if isinstance(raw_effort, dict):
        return raw_effort.get("level", "unknown")
    return raw_effort or "unknown"


def load_rows() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    rows = []
    with LOG_PATH.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def append_row(row: dict) -> None:
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(row) + "\n")


def detect_hole(role: str, tokens: int, history: list[dict]) -> str | None:
    prior = [r["subagent_tokens"] for r in history if r.get("role") == role]
    if not prior:
        return None
    mean = statistics.mean(prior)
    if len(prior) >= MIN_SAMPLES_FOR_ZSCORE:
        stdev = statistics.pstdev(prior) or 1.0
        z = (tokens - mean) / stdev
        if z >= Z_THRESHOLD:
            return (
                f"Token hole detected: '{role}' dispatch used {tokens:,} tokens, "
                f"{z:.1f}σ above its {len(prior)}-dispatch average of {mean:,.0f}."
            )
    elif tokens >= mean * FALLBACK_MULTIPLE:
        return (
            f"Token hole detected: '{role}' dispatch used {tokens:,} tokens, "
            f"{tokens / mean:.1f}x its average of {mean:,.0f} over only {len(prior)} prior dispatch(es)."
        )
    return None


def main() -> None:
    hook_input = load_hook_input()
    role = hook_input.get("agent_type", "unknown")
    agent_id = hook_input.get("agent_id", "unknown")
    transcript_path = hook_input.get("agent_transcript_path", "")

    result = last_turn_usage(transcript_path)
    if result is None:
        # Nothing usable to log/analyze; stay silent rather than corrupt the log.
        return
    tokens, model = result

    history = load_rows()
    message = detect_hole(role, tokens, history)

    append_row(
        {
            "timestamp": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "role": role,
            "task": f"agent:{agent_id}",
            "model": model,
            "effort": effort_level(hook_input.get("effort")),
            "subagent_tokens": tokens,
            "tool_uses": None,
            "duration_ms": None,
        }
    )

    if message:
        print(json.dumps({"systemMessage": message}))


if __name__ == "__main__":
    main()
