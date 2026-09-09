from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    """Return the checkout root (skills, config, evals live here)."""
    override = os.environ.get("MINI_SWE_HARNESS_ROOT")
    if override:
        return Path(override).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file() and (parent / ".agents" / "skills").is_dir():
            return parent
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").is_file():
        return cwd
    msg = "Cannot locate mini-swe-harness repo root; set MINI_SWE_HARNESS_ROOT"
    raise FileNotFoundError(msg)


def skills_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / ".agents" / "skills"


def config_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "config"


def evals_dir(root: Path | None = None) -> Path:
    return (root or repo_root()) / "evals"
