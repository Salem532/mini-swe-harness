from __future__ import annotations

import json
from collections import Counter
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
