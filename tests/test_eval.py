from __future__ import annotations

import json

import pytest
from collections import Counter
from dataclasses import replace
from pathlib import Path

from mini_swe_harness.cli import main
from mini_swe_harness.eval_report import build_summary
from mini_swe_harness.runner import (
    RunResult,
    arm_flags,
    failed_result,
    load_episode_result,
    write_episode_result,
)
from mini_swe_harness.tasks import load_all_tasks


def test_load_all_tasks_ignores_nested_yaml() -> None:
    tasks = load_all_tasks()
    assert len(tasks) == 15
    assert all(not tid.startswith("lift-") and not tid.startswith("policy-") for tid in (t.id for t in tasks))


def test_load_tasks_dir_skill_lift_when_present() -> None:
    from mini_swe_harness.paths import repo_root

    lift_dir = repo_root() / "evals" / "tasks" / "skill_lift"
    if not lift_dir.is_dir() or not list(lift_dir.glob("*.yaml")):
        return  # skipped until Task 5; keep this assertion in Task 5 instead
    tasks = load_all_tasks(tasks_dir=lift_dir)
    assert len(tasks) == 6


def test_skill_lift_catalog_six() -> None:
    from mini_swe_harness.paths import repo_root

    tasks = load_all_tasks(tasks_dir=repo_root() / "evals" / "tasks" / "skill_lift")
    assert len(tasks) == 6
    assert {t.expected_skill for t in tasks} == {"parse-money", "parse-records", "schedule-window"}
    assert load_all_tasks()  # still 15
    assert len(load_all_tasks()) == 15


def test_mcp_policy_catalog_two() -> None:
    from mini_swe_harness.paths import repo_root

    tasks = load_all_tasks(tasks_dir=repo_root() / "evals" / "tasks" / "mcp_policy")
    assert len(tasks) == 2
    assert {t.id for t in tasks} == {"policy-list-01", "policy-deny-01"}
    assert {t.category for t in tasks} == {"mcp_policy"}
    assert all(t.policy is not None and t.policy.name == "policy.mcp_policy.yaml" for t in tasks)
    assert all(t.policy.is_file() for t in tasks)  # type: ignore[union-attr]
    assert len(load_all_tasks()) == 15
    assert all(t.policy is None for t in load_all_tasks())


def test_expected_skill_and_tasks_dir(tmp_path: Path) -> None:
    src = tmp_path / "fix" / "src"
    vis = tmp_path / "fix" / "tests"
    hid = tmp_path / "grad"
    src.mkdir(parents=True)
    vis.mkdir(parents=True)
    hid.mkdir(parents=True)
    (src / "x.py").write_text("x = 1\n", encoding="utf-8")
    tasks_dir = tmp_path / "tasks"
    nested = tasks_dir / "skill_lift"
    nested.mkdir(parents=True)
    (tasks_dir / "top.yaml").write_text(
        "id: top-01\ncategory: bash\nprompt: hi\n"
        "fixture: fix\nvisible_tests: fix/tests\nhidden_tests: grad\n",
        encoding="utf-8",
    )
    (nested / "lift.yaml").write_text(
        "id: lift-demo-01\ncategory: skill_lift\nexpected_skill: parse-money\n"
        "prompt: hi\nfixture: fix\nvisible_tests: fix/tests\nhidden_tests: grad\n",
        encoding="utf-8",
    )
    from mini_swe_harness.tasks import load_all_tasks

    root = tmp_path
    top = load_all_tasks(root=root, tasks_dir=tasks_dir)
    assert [t.id for t in top] == ["top-01"]
    assert top[0].expected_skill is None
    nested_tasks = load_all_tasks(root=root, tasks_dir=nested)
    assert nested_tasks[0].id == "lift-demo-01"
    assert nested_tasks[0].category == "skill_lift"
    assert nested_tasks[0].expected_skill == "parse-money"


def test_task_catalog_balanced() -> None:
    tasks = load_all_tasks()
    assert len(tasks) == 15
    counts = Counter(task.category for task in tasks)
    assert counts == {"skill": 3, "mcp": 3, "skill_mcp": 3, "bash": 3, "mcp_opt": 3}
    for task in tasks:
        assert task.src.is_dir()
        assert task.visible_tests.is_dir()
        assert task.hidden_tests.is_dir()
        assert task.prompt
        if task.category == "mcp_opt":
            assert task.ticket_id
            assert (task.src / "README.md").is_file()


def test_arm_flags() -> None:
    assert arm_flags("baseline") == (False, False)
    assert arm_flags("skill_only") == (True, False)
    assert arm_flags("mcp_only") == (False, True)
    assert arm_flags("full") == (True, True)


def _row(task_id: str, arm: str, seed: int, success: bool) -> RunResult:
    return RunResult(
        task_id=task_id,
        arm=arm,
        seed=seed,
        success=success,
        exit_status="Submitted",
        judge={"passed": success, "output": ""},
        usage={"bash_actions": 5, "total_tokens": 100, "api_calls": 4},
        skill={"activated": arm in {"skill_only", "full"}, "activated_skills": []},
        mcp={"ok": 1 if arm in {"mcp_only", "full"} else 0, "denied": 0, "error": 0},
        trajectory_path=None,
        model_name="openai/qwen",
        extra={},
    )


def test_arm_stats_counts_timeouts_even_on_success() -> None:
    from mini_swe_harness.eval_report import PROCESS_TIMEOUT_EXITS, build_summary

    assert PROCESS_TIMEOUT_EXITS == frozenset({"TimeExceeded", "Timeout"})
    rows = [
        replace(_row("a", "baseline", 1, True), exit_status="TimeExceeded"),
        replace(_row("a", "baseline", 2, False), exit_status="Timeout"),
        replace(_row("a", "baseline", 3, False), exit_status="Submitted"),
        replace(_row("a", "baseline", 4, False), exit_status="TimeoutError"),
    ]
    summary = build_summary(rows, model="x")
    stats = summary["arms"]["baseline"]
    assert stats["timeouts"] == 2
    assert stats["timeout_rate"] == 0.5
    assert stats["success"] == 1
    assert stats["avg_steps_all"] == 5.0


def test_summary_primary_metric() -> None:
    rows = [
        _row("a", "baseline", 1, False),
        _row("a", "full", 1, True),
        _row("b", "baseline", 1, True),
        _row("b", "full", 1, True),
    ]
    summary = build_summary(rows, model="openai/qwen")
    assert summary["primary_metric"] == "hidden_judge_pass_rate"
    assert summary["arms"]["baseline"]["success_rate"] == 0.5
    assert summary["arms"]["full"]["success_rate"] == 1.0
    assert summary["paired_gains"]["full_vs_baseline"]["pass_rate_delta"] == 0.5


def test_skill_lift_block() -> None:
    rows = [
        _row("lift-a", "baseline", 1, False),
        _row("lift-a", "skill_only", 1, True),
        _row("lift-a", "mcp_only", 1, False),
        _row("lift-a", "full", 1, True),
    ]
    rows[0].skill["activated_skills"] = []
    rows[1].skill["activated_skills"] = ["parse-money"]
    rows[1].skill["activated"] = True
    rows[2].skill["activated_skills"] = []
    rows[3].skill["activated_skills"] = ["parse-money"]
    summary = build_summary(
        rows,
        model="x",
        task_expected_skills={"lift-a": "parse-money"},
    )
    sl = summary["skill_lift"]
    assert sl["n_pairs"] == 1
    assert sl["pass_lift_skill_only_vs_baseline"] == 1.0
    assert sl["trigger_rate_by_arm"]["skill_only"] == 1.0
    assert sl["trigger_rate_by_arm"]["baseline"] == 0.0
    assert sl["compliance_rate_by_arm"]["skill_only"] == 1.0


def test_summary_by_category() -> None:
    rows = [
        _row("bash-fizz-01", "baseline", 1, False),
        _row("bash-fizz-01", "full", 1, True),
        _row("mcp-tax-01", "baseline", 1, False),
        _row("mcp-tax-01", "full", 1, True),
    ]
    summary = build_summary(
        rows,
        model="openai/qwen",
        task_categories={"bash-fizz-01": "bash", "mcp-tax-01": "mcp"},
    )
    assert summary["by_category"]["bash"]["baseline"]["success_rate"] == 0.0
    assert summary["by_category"]["mcp"]["full"]["success_rate"] == 1.0
    assert summary["by_category"]["mcp"]["paired_gains"]["full_vs_baseline"]["pass_rate_delta"] == 1.0


def test_write_and_load_episode_result(tmp_path: Path) -> None:
    row = _row("bash-fizz-01", "baseline", 1, True)
    path = write_episode_result(tmp_path, row)
    assert path == tmp_path / "bash-fizz-01.baseline.1.result.json"
    loaded = load_episode_result(tmp_path, "bash-fizz-01", "baseline", 1)
    assert loaded is not None
    assert loaded.success is True
    assert loaded.task_id == "bash-fizz-01"
    assert loaded.arm == "baseline"
    assert loaded.seed == 1
    ledger = tmp_path / "episodes.jsonl"
    assert ledger.is_file()
    assert "bash-fizz-01" in ledger.read_text(encoding="utf-8")


def test_corrupt_result_is_treated_as_missing(tmp_path: Path) -> None:
    (tmp_path / "bash-fizz-01.baseline.1.result.json").write_text("{", encoding="utf-8")
    assert load_episode_result(tmp_path, "bash-fizz-01", "baseline", 1) is None
    assert load_episode_result(tmp_path, "missing", "baseline", 1) is None


def test_eval_skips_existing_result(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    write_episode_result(raw, _row("bash-fizz-01", "baseline", 1, True))
    called: list[tuple[str, str, int]] = []

    def fake_run(self, task, *, arm, seed, output_dir):
        called.append((task.id, arm, seed))
        return _row(task.id, arm, seed, False)

    monkeypatch.setattr("mini_swe_harness.cli.EpisodeRunner.run_task", fake_run)
    rc = main(
        [
            "eval",
            "--task",
            "bash-fizz-01",
            "--arm",
            "baseline",
            "--seeds",
            "1",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0
    assert called == []
    summary = (tmp_path / "summary.json").read_text(encoding="utf-8")
    assert '"success": 1' in summary or '"success":1' in summary


def test_eval_records_exception_without_aborting(tmp_path: Path, monkeypatch) -> None:
    def boom(self, task, *, arm, seed, output_dir):
        raise RuntimeError("simulated crash")

    monkeypatch.setattr("mini_swe_harness.cli.EpisodeRunner.run_task", boom)
    rc = main(
        [
            "eval",
            "--task",
            "bash-fizz-01",
            "--arm",
            "baseline",
            "--seeds",
            "1",
            "--output",
            str(tmp_path),
        ]
    )
    assert rc == 0
    loaded = load_episode_result(tmp_path / "raw", "bash-fizz-01", "baseline", 1)
    assert loaded is not None
    assert loaded.success is False
    assert loaded.exit_status == "RuntimeError"


def test_eval_summary_keeps_other_arms_on_disk(tmp_path: Path, monkeypatch) -> None:
    raw = tmp_path / "raw"
    write_episode_result(raw, _row("bash-fizz-01", "baseline", 1, True))
    write_episode_result(raw, _row("bash-fizz-01", "full", 1, False))

    def fake_run(self, task, *, arm, seed, output_dir):
        row = _row(task.id, arm, seed, True)
        write_episode_result(output_dir, row)
        return row

    monkeypatch.setattr("mini_swe_harness.cli.EpisodeRunner.run_task", fake_run)
    rc = main(
        [
            "eval",
            "--task",
            "bash-fizz-01",
            "--arm",
            "mcp_only",
            "--seeds",
            "1",
            "--output",
            str(tmp_path),
            "--force",
        ]
    )
    assert rc == 0
    summary = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["n_runs"] == 3
    assert summary["arms"]["baseline"]["n"] == 1
    assert summary["arms"]["full"]["n"] == 1
    assert summary["arms"]["mcp_only"]["n"] == 1


def test_failed_result_shape() -> None:
    row = failed_result("bash-fizz-01", "full", 2, RuntimeError("x"))
    assert row.success is False
    assert row.exit_status == "RuntimeError"
    assert row.judge.get("passed") is False


EXPECTED_ARM_TIMEOUTS = {
    "baseline": 17,
    "skill_only": 19,
    "mcp_only": 4,
    "full": 8,
}

EXPECTED_CATEGORY_TIMEOUTS = {
    "bash": {"baseline": 0, "skill_only": 0, "mcp_only": 0, "full": 0},
    "skill": {"baseline": 2, "skill_only": 0, "mcp_only": 2, "full": 0},
    "mcp": {"baseline": 7, "skill_only": 9, "mcp_only": 1, "full": 1},
    "skill_mcp": {"baseline": 7, "skill_only": 9, "mcp_only": 1, "full": 6},
    "mcp_opt": {"baseline": 1, "skill_only": 1, "mcp_only": 0, "full": 1},
}


def test_frozen_180_timeout_matrix() -> None:
    from mini_swe_harness.paths import repo_root
    from mini_swe_harness.runner import load_all_results

    raw = repo_root() / "evals" / "results" / "raw"
    rows = load_all_results(raw)
    if len(rows) != 180:
        pytest.skip("frozen 180 raw results not present")
    tasks = load_all_tasks()
    categories = {t.id: t.category for t in tasks}
    summary = build_summary(rows, model="x", task_categories=categories)
    for arm, n in EXPECTED_ARM_TIMEOUTS.items():
        assert summary["arms"][arm]["timeouts"] == n, arm
        assert summary["arms"][arm]["n"] == 45
    for cat, arms in EXPECTED_CATEGORY_TIMEOUTS.items():
        for arm, n in arms.items():
            assert summary["by_category"][cat][arm]["timeouts"] == n, (cat, arm)
            assert summary["by_category"][cat][arm]["n"] == 9
    assert summary["arms"]["baseline"]["success"] == 26
    assert summary["arms"]["skill_only"]["success"] == 28
    assert summary["arms"]["mcp_only"]["success"] == 41
    assert summary["arms"]["full"]["success"] == 42
