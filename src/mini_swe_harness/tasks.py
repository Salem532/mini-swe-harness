from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from mini_swe_harness.paths import evals_dir, repo_root

ALLOWED_CATEGORIES = {"skill", "mcp", "skill_mcp", "bash", "mcp_opt"}


@dataclass(frozen=True)
class TaskSpec:
    id: str
    category: str
    prompt: str
    fixture: Path
    visible_tests: Path
    hidden_tests: Path
    timeout_s: int = 180
    max_steps: int = 30
    ticket_id: str | None = None

    @property
    def src(self) -> Path:
        return self.fixture / "src"


def _as_path(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path)


def load_task(path: Path, *, root: Path | None = None) -> TaskSpec:
    root = root or repo_root()
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    category = str(data["category"])
    if category not in ALLOWED_CATEGORIES:
        raise ValueError(f"{path}: unknown category {category}")
    spec = TaskSpec(
        id=str(data["id"]),
        category=category,
        prompt=str(data["prompt"]).strip(),
        fixture=_as_path(root, data["fixture"]),
        visible_tests=_as_path(root, data.get("visible_tests") or str(Path(data["fixture"]) / "tests")),
        hidden_tests=_as_path(root, data["hidden_tests"]),
        timeout_s=int(data.get("timeout_s", 180)),
        max_steps=int(data.get("max_steps", 30)),
        ticket_id=data.get("ticket_id"),
    )
    if not spec.src.is_dir():
        raise FileNotFoundError(f"{path}: fixture src missing at {spec.src}")
    if not spec.visible_tests.is_dir():
        raise FileNotFoundError(f"{path}: visible tests missing at {spec.visible_tests}")
    if not spec.hidden_tests.is_dir():
        raise FileNotFoundError(f"{path}: hidden tests missing at {spec.hidden_tests}")
    return spec


def load_all_tasks(root: Path | None = None) -> list[TaskSpec]:
    base = evals_dir(root) / "tasks"
    tasks = [load_task(path, root=root) for path in sorted(base.glob("*.yaml"))]
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate task ids")
    return tasks
