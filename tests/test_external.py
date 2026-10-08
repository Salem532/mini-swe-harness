from __future__ import annotations

import json
from pathlib import Path

import yaml

from mini_swe_harness.paths import repo_root


BASELINE_RUN = repo_root() / "evals" / "external" / "runs" / "lite25-baseline"
OFFICIAL = BASELINE_RUN / "openai__qwen3.8-27b.lite25-baseline.json"
IDS = json.loads((repo_root() / "evals" / "external" / "instance_ids.json").read_text(encoding="utf-8"))["instance_ids"]

EXPECTED_MISSES = {
    "django__django-13265": ("context_window", True, "ContextWindowExceededError"),
    "django__django-12700": ("tests_failed", False, "Submitted"),
    "psf__requests-2148": ("tests_failed", False, "Submitted"),
    "pydata__xarray-4493": ("tests_failed", False, "Submitted"),
    "scikit-learn__scikit-learn-10508": ("tests_failed", False, "Submitted"),
    "sympy__sympy-13146": ("tests_failed", False, "Submitted"),
    "sympy__sympy-15308": ("tests_failed", False, "Submitted"),
}


def test_classify_baseline_frozen_report() -> None:
    from mini_swe_harness.external import classify_arm, load_exit_status_map

    official = json.loads(OFFICIAL.read_text(encoding="utf-8"))
    exits = load_exit_status_map(BASELINE_RUN)
    rows = classify_arm(official, exits, IDS)
    assert len(rows) == 25
    for iid, (primary, empty, exit_name) in EXPECTED_MISSES.items():
        assert rows[iid]["primary"] == primary, iid
        assert rows[iid]["empty_patch"] is empty, iid
        assert rows[iid]["agent_exit"] == exit_name, iid
    resolved = [iid for iid, row in rows.items() if row["primary"] == "resolved"]
    assert len(resolved) == 18
    assert official["resolved_instances"] == 18
    assert all(rows[iid]["primary"] == "resolved" for iid in official["resolved_ids"])
    assert sum(1 for row in rows.values() if row["primary"] == "infra") == 0


def test_classify_priority_context_window_beats_empty_patch() -> None:
    from mini_swe_harness.external import classify_instance

    official = {
        "empty_patch_ids": ["x"],
        "unresolved_ids": ["x"],
        "resolved_ids": [],
        "infra_failure_ids": [],
        "error_ids": [],
    }
    row = classify_instance("x", official=official, agent_exit="ContextWindowExceededError")
    assert row["primary"] == "context_window"
    assert row["empty_patch"] is True


def test_paired_flips() -> None:
    from mini_swe_harness.external import paired_flips

    ids = ["a", "b", "c", "d"]
    out = paired_flips({"a", "b"}, {"a", "c"}, ids)
    assert out["both_resolved"] == ["a"]
    assert out["skill_fixed"] == ["c"]
    assert out["skill_regressed"] == ["b"]
    assert out["both_failed"] == ["d"]


def test_merge_baseline_taxonomy_does_not_invent_skill_only() -> None:
    from mini_swe_harness.external import merge_baseline_taxonomy

    summary = {"arms": {"baseline": {"resolved": 18}}, "n_instances": 25}
    merged = merge_baseline_taxonomy(
        summary,
        {
            "django__django-13265": {
                "primary": "context_window",
                "empty_patch": True,
                "agent_exit": "ContextWindowExceededError",
            }
        },
    )
    assert merged["arms"]["baseline"]["resolved"] == 18
    assert "skill_only" not in merged["arms"]
    assert "paired" not in merged
    assert merged["failure_taxonomy"]["baseline"]["django__django-13265"]["primary"] == "context_window"


def test_written_summary_has_baseline_and_skill_only() -> None:
    data = json.loads((repo_root() / "evals" / "external" / "summary.json").read_text(encoding="utf-8"))
    assert data["arms"]["baseline"]["resolved"] == 18
    assert data["arms"]["skill_only"]["resolved"] == 20
    assert data["paired"]["skill_only_vs_baseline"]["resolved_delta"] == 2
    assert data["paired"]["skill_only_vs_baseline"]["skill_fixed"] == [
        "django__django-13265",
        "scikit-learn__scikit-learn-10508",
    ]
    assert data["paired"]["skill_only_vs_baseline"]["skill_regressed"] == []
    assert data["failure_taxonomy"]["baseline"]["django__django-13265"]["primary"] == "context_window"
    assert data["failure_taxonomy"]["skill_only"]["django__django-13265"]["primary"] == "resolved"
    md = (repo_root() / "evals" / "external" / "failure-taxonomy.md").read_text(encoding="utf-8")
    assert "django__django-13265" in md
    assert "context_window" in md


def test_skill_only_overlay_catalog_and_binds() -> None:
    from mini_swe_harness.external import (
        CONTAINER_SKILLS_ROOT,
        EXTERNAL_SKILLS,
        build_skill_only_overlay,
    )
    from mini_swe_harness.paths import repo_root, skills_dir
    from mini_swe_harness.prompt import assert_no_skill_bodies
    from mini_swe_harness.skills import scan_skills

    overlay = build_skill_only_overlay()
    template = overlay["agent"]["instance_template"]
    assert CONTAINER_SKILLS_ROOT in template
    assert "pytest-debug" in template
    assert "repo-qa" in template
    assert "mcp-ticket-context" not in template
    assert "parse-money" not in template
    assert "mcp-call" not in template
    assert "/testbed/.agents" not in template
    skills, _ = scan_skills()
    selected = [s for s in skills if s.name in EXTERNAL_SKILLS]
    assert_no_skill_bodies(template, selected)
    args = overlay["environment"]["run_args"]
    assert "--rm" in args
    host = skills_dir(repo_root())
    joined = " ".join(args)
    assert f"{host / 'pytest-debug'}:{CONTAINER_SKILLS_ROOT}/pytest-debug:ro" in joined
    assert f"{host / 'repo-qa'}:{CONTAINER_SKILLS_ROOT}/repo-qa:ro" in joined
    assert "mcp-ticket-context" not in joined
