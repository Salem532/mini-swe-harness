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
