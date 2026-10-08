#!/usr/bin/env python3
"""Summarize .claude/metrics/agent-usage.jsonl by agent role.

Usage: python3 .claude/metrics/report.py
"""

import json
from collections import defaultdict
from pathlib import Path

LOG_PATH = Path(__file__).parent / "agent-usage.jsonl"


def main() -> None:
    rows = []
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    if not rows:
        print(f"No entries in {LOG_PATH}.")
        return

    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])  # role -> [count, tokens, tool_uses]
    for row in rows:
        role = row.get("role", "unknown")
        agg[role][0] += 1
        agg[role][1] += int(row.get("subagent_tokens", 0))
        agg[role][2] += int(row.get("tool_uses", 0))

    print(f"{'Role':<20}{'Count':>7}{'Total tokens':>16}{'Avg tokens':>14}{'Total tool_uses':>18}")
    grand_total = 0
    grand_count = 0
    for role, (count, total, tool_uses) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
        avg = total // count if count else 0
        print(f"{role:<20}{count:>7}{total:>16,}{avg:>14,}{tool_uses:>18}")
        grand_total += total
        grand_count += count
    print("-" * 75)
    print(f"{'TOTAL':<20}{grand_count:>7}{grand_total:>16,}")

    print("\nPer-dispatch detail, largest first:\n")
    for row in sorted(rows, key=lambda r: -int(r.get("subagent_tokens", 0))):
        print(
            f"{row.get('role', '?'):<16}{int(row.get('subagent_tokens', 0)):>9,} tok  "
            f"{int(row.get('tool_uses', 0)):>3} tools  {row.get('model', '?'):<8}{row.get('effort', '?'):<8}"
            f"{row.get('task', '')}"
        )


if __name__ == "__main__":
    main()
