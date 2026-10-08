from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from mini_swe_harness.paths import repo_root


def _pytest(src: Path, tests: Path) -> int:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(tests), "-q", "--tb=no"],
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )
    return result.returncode


def test_hidden_graders_fail_on_unfixed_fixtures() -> None:
    root = repo_root()
    for grader in sorted((root / "evals" / "graders").iterdir()):
        if not grader.is_dir():
            continue
        src = root / "evals" / "fixtures" / grader.name / "src"
        assert src.is_dir(), grader
        assert _pytest(src, grader) != 0, f"hidden tests unexpectedly passed for {grader.name}"


def test_skill_visible_tests_can_pass_without_edge_cases() -> None:
    root = repo_root()
    encoding = root / "evals" / "fixtures" / "skill_encoding_01"
    empty = root / "evals" / "fixtures" / "skill_empty_01"
    assert _pytest(encoding / "src", encoding / "tests") == 0
    assert _pytest(empty / "src", empty / "tests") == 0


LIFT = [
    "lift_money_halfup_01",
    "lift_money_sum_01",
    "lift_records_hash_01",
    "lift_records_delim_01",
    "lift_hours_sunday_01",
    "lift_hours_range_01",
]


def test_lift_visible_pass_hidden_fail() -> None:
    root = repo_root()
    for name in LIFT:
        src = root / "evals" / "fixtures" / name / "src"
        vis = root / "evals" / "fixtures" / name / "tests"
        hid = root / "evals" / "graders" / name
        assert src.is_dir(), name
        assert _pytest(src, vis) == 0, f"visible should pass for {name}"
        assert _pytest(src, hid) != 0, f"hidden should fail for {name}"


POLICY = ["policy_list_01", "policy_deny_01"]


def test_policy_visible_pass_hidden_fail() -> None:
    root = repo_root()
    for name in POLICY:
        src = root / "evals" / "fixtures" / name / "src"
        vis = root / "evals" / "fixtures" / name / "tests"
        hid = root / "evals" / "graders" / name
        assert src.is_dir(), name
        assert _pytest(src, vis) == 0, f"visible should pass for {name}"
        assert _pytest(src, hid) != 0, f"hidden should fail for {name}"

