from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from mini_swe_harness.paths import repo_root, skills_dir
from mini_swe_harness.prompt import SKILLS_SECTION
from mini_swe_harness.skills import scan_skills, render_catalog

EXTERNAL_SKILLS = ("pytest-debug", "repo-qa")
CONTAINER_SKILLS_ROOT = "/opt/agent-skills"

TIMEOUT_EXITS = frozenset({"TimeExceeded", "TimeoutError", "TimeoutExpired"})


def load_exit_status_map(run_dir: Path) -> dict[str, str]:
    files = sorted(Path(run_dir).glob("exit_statuses_*.yaml"))
    if not files:
        return {}
    data = yaml.safe_load(files[-1].read_text(encoding="utf-8")) or {}
    mapping: dict[str, str] = {}
    for status, ids in (data.get("instances_by_exit_status") or {}).items():
        for iid in ids or []:
            mapping[str(iid)] = str(status)
    return mapping


def classify_instance(instance_id: str, *, official: dict, agent_exit: str | None) -> dict[str, Any]:
    empty_ids = {str(x) for x in (official.get("empty_patch_ids") or [])}
    infra_ids = {str(x) for x in (official.get("infra_failure_ids") or [])} | {
        str(x) for x in (official.get("error_ids") or [])
    }
    unresolved = {str(x) for x in (official.get("unresolved_ids") or [])}
    resolved = {str(x) for x in (official.get("resolved_ids") or [])}
    exit_name = str(agent_exit or "")
    if instance_id in infra_ids:
        primary = "infra"
    elif exit_name == "ContextWindowExceededError":
        primary = "context_window"
    elif exit_name in TIMEOUT_EXITS:
        primary = "timeout"
    elif instance_id in empty_ids:
        primary = "empty_patch"
    elif instance_id in unresolved:
        primary = "tests_failed"
    elif instance_id in resolved:
        primary = "resolved"
    else:
        raise KeyError(f"unclassified instance {instance_id}")
    return {
        "primary": primary,
        "empty_patch": instance_id in empty_ids,
        "agent_exit": exit_name,
    }


def classify_arm(
    official: dict,
    exit_by_id: dict[str, str],
    instance_ids: list[str],
) -> dict[str, dict[str, Any]]:
    return {
        iid: classify_instance(iid, official=official, agent_exit=exit_by_id.get(iid))
        for iid in instance_ids
    }


def taxonomy_markdown(arm: str, rows: dict[str, dict], instance_ids: list[str]) -> str:
    lines = [
        f"# Failure taxonomy ({arm})",
        "",
        "| instance | primary | empty_patch | agent_exit |",
        "|---|---|---|---|",
    ]
    for iid in instance_ids:
        row = rows[iid]
        if row["primary"] == "resolved":
            continue
        lines.append(
            f"| {iid} | `{row['primary']}` | {str(row['empty_patch']).lower()} | `{row['agent_exit']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def merge_baseline_taxonomy(summary: dict, rows: dict[str, dict]) -> dict:
    out = dict(summary)
    taxonomy = dict(out.get("failure_taxonomy") or {})
    taxonomy["baseline"] = rows
    out["failure_taxonomy"] = taxonomy
    return out


def paired_flips(
    baseline_resolved: set[str],
    other_resolved: set[str],
    instance_ids: list[str],
) -> dict[str, list[str]]:
    base = set(baseline_resolved)
    other = set(other_resolved)
    return {
        "both_resolved": sorted(iid for iid in instance_ids if iid in base and iid in other),
        "skill_fixed": sorted(iid for iid in instance_ids if iid not in base and iid in other),
        "skill_regressed": sorted(iid for iid in instance_ids if iid in base and iid not in other),
        "both_failed": sorted(iid for iid in instance_ids if iid not in base and iid not in other),
    }


def swebench_yaml_path() -> Path:
    import minisweagent

    return Path(minisweagent.__file__).resolve().parent / "config" / "benchmarks" / "swebench.yaml"


def build_skill_only_overlay(root: Path | None = None) -> dict:
    root = root or repo_root()
    data = yaml.safe_load(swebench_yaml_path().read_text(encoding="utf-8")) or {}
    instance = str((data.get("agent") or {}).get("instance_template") or "")
    skills, _skipped = scan_skills(skills_dir(root))
    selected = [s for s in skills if s.name in EXTERNAL_SKILLS]
    names = {s.name for s in selected}
    if names != set(EXTERNAL_SKILLS):
        raise ValueError(f"missing SWE-bench skills: {set(EXTERNAL_SKILLS) - names}")
    catalog = render_catalog(selected, container_skills_root=CONTAINER_SKILLS_ROOT)
    extra = SKILLS_SECTION.format(catalog=catalog)
    host = skills_dir(root)
    run_args: list[str] = ["--rm"]
    for name in EXTERNAL_SKILLS:
        run_args.extend(
            ["-v", f"{(host / name).resolve()}:{CONTAINER_SKILLS_ROOT}/{name}:ro"]
        )
    return {
        "agent": {"instance_template": instance.rstrip() + "\n" + extra + "\n"},
        "environment": {"run_args": run_args},
    }


def write_skill_only_overlay(dest: Path | None = None, *, root: Path | None = None) -> Path:
    root = root or repo_root()
    dest = dest or (root / "evals" / "external" / "skill-only.generated.yaml")
    dest.parent.mkdir(parents=True, exist_ok=True)
    overlay = build_skill_only_overlay(root)
    dest.write_text(yaml.safe_dump(overlay, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return dest
