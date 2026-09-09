from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from mini_swe_harness.runner import RunResult


def _mean(values: list[float]) -> float:
    return round(statistics.fmean(values), 4) if values else 0.0


def _wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n) / denom
    return round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4)


def _arm_stats(rows: list[RunResult]) -> dict[str, Any]:
    n = len(rows)
    successes = sum(1 for row in rows if row.success)
    rate = successes / n if n else 0.0
    lo, hi = _wilson_interval(successes, n)
    successful = [row for row in rows if row.success]
    def avg(getter, subset: list[RunResult]) -> float:
        values = [float(getter(row)) for row in subset]
        return _mean(values)

    skill_on = sum(1 for row in rows if row.skill.get("activated"))
    return {
        "n": n,
        "success": successes,
        "success_rate": round(rate, 4),
        "success_rate_ci95": [lo, hi],
        "avg_steps_all": avg(lambda r: r.usage.get("bash_actions") or 0, rows),
        "avg_steps_success": avg(lambda r: r.usage.get("bash_actions") or 0, successful),
        "avg_tokens_all": avg(lambda r: r.usage.get("total_tokens") or 0, rows),
        "avg_tokens_success": avg(lambda r: r.usage.get("total_tokens") or 0, successful),
        "avg_api_calls_all": avg(lambda r: r.usage.get("api_calls") or 0, rows),
        "skill_activation_rate": round(skill_on / n, 4) if n else 0.0,
        "mcp_calls": {
            "ok": sum(row.mcp.get("ok", 0) for row in rows),
            "denied": sum(row.mcp.get("denied", 0) for row in rows),
            "error": sum(row.mcp.get("error", 0) for row in rows),
        },
    }


def paired_gain(baseline: list[RunResult], other: list[RunResult]) -> dict[str, Any]:
    base = {(row.task_id, row.seed): row.success for row in baseline}
    deltas = []
    for row in other:
        key = (row.task_id, row.seed)
        if key in base:
            deltas.append(int(row.success) - int(base[key]))
    if not deltas:
        return {"n_pairs": 0, "pass_rate_delta": 0.0}
    return {"n_pairs": len(deltas), "pass_rate_delta": _mean(deltas)}


def _by_category(rows: list[RunResult], task_categories: dict[str, str]) -> dict[str, Any]:
    grouped: dict[str, dict[str, list[RunResult]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[task_categories.get(row.task_id, "unknown")][row.arm].append(row)
    out: dict[str, Any] = {}
    for category, arms in sorted(grouped.items()):
        stats = {arm: _arm_stats(items) for arm, items in sorted(arms.items())}
        baseline = arms.get("baseline", [])
        stats["paired_gains"] = {
            f"{arm}_vs_baseline": paired_gain(baseline, items)
            for arm, items in sorted(arms.items())
            if arm != "baseline"
        }
        out[category] = stats
    return out


def build_summary(
    rows: list[RunResult],
    *,
    model: str,
    extra: dict[str, Any] | None = None,
    task_categories: dict[str, str] | None = None,
) -> dict[str, Any]:
    by_arm: dict[str, list[RunResult]] = defaultdict(list)
    for row in rows:
        by_arm[row.arm].append(row)
    arms = {arm: _arm_stats(items) for arm, items in sorted(by_arm.items())}
    baseline = by_arm.get("baseline", [])
    summary = {
        "model": model,
        "n_tasks": len({row.task_id for row in rows}),
        "n_repeats": len({row.seed for row in rows}),
        "n_runs": len(rows),
        "primary_metric": "hidden_judge_pass_rate",
        "arms": arms,
        "paired_gains": {
            f"{arm}_vs_baseline": paired_gain(baseline, items)
            for arm, items in sorted(by_arm.items())
            if arm != "baseline"
        },
        "skill_activation_rate": arms.get("full", {}).get("skill_activation_rate")
        or arms.get("skill_only", {}).get("skill_activation_rate"),
        "mcp_calls": arms.get("full", {}).get("mcp_calls") or arms.get("mcp_only", {}).get("mcp_calls"),
    }
    if task_categories:
        summary["by_category"] = _by_category(rows, task_categories)
    if extra:
        summary.update(extra)
    return summary


def write_summary(summary: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_failures(rows: list[RunResult], path: Path, *, limit: int = 4) -> None:
    failed = [row for row in rows if not row.success]
    lines = ["# Failure cases", ""]
    if not failed:
        lines.append("No failures in this run.")
    for row in failed[:limit]:
        lines.append(f"## {row.task_id} / {row.arm} / seed={row.seed}")
        lines.append(f"- exit_status: `{row.exit_status}`")
        lines.append(f"- skills loaded: {row.skill.get('activated_skills')}")
        lines.append(f"- mcp: {row.mcp}")
        output = (row.judge.get("output") or "")[-800:]
        lines.append("```")
        lines.append(output)
        lines.append("```")
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
