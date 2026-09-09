from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from mini_swe_harness.paths import skills_dir

logger = logging.getLogger(__name__)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME = 64
MAX_DESCRIPTION = 1024


class SkillValidationError(ValueError):
    """Raised when a SKILL.md fails Agent Skills frontmatter checks."""


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: Path
    body: str
    extra: dict = field(default_factory=dict)

    @property
    def skill_md(self) -> Path:
        return self.path / "SKILL.md"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        raise SkillValidationError("SKILL.md must start with YAML frontmatter delimited by ---")
    rest = text[3:]
    end = rest.find("\n---")
    if end < 0:
        raise SkillValidationError("SKILL.md frontmatter is not closed with ---")
    raw = rest[:end]
    body = rest[end + 4 :].lstrip("\n")
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise SkillValidationError("SKILL.md frontmatter must be a mapping")
    return data, body


def validate_frontmatter(data: dict, directory_name: str) -> tuple[str, str]:
    name = data.get("name")
    description = data.get("description")
    if not isinstance(name, str) or not name.strip():
        raise SkillValidationError("missing required field: name")
    if not isinstance(description, str) or not description.strip():
        raise SkillValidationError("missing required field: description")
    name = name.strip()
    description = description.strip()
    if len(name) > MAX_NAME:
        raise SkillValidationError(f"name exceeds {MAX_NAME} characters")
    if not NAME_RE.fullmatch(name):
        raise SkillValidationError(
            "name must be lowercase alphanumeric with single hyphens, no leading/trailing hyphen"
        )
    if name != directory_name:
        raise SkillValidationError(f"name {name!r} does not match directory {directory_name!r}")
    if len(description) > MAX_DESCRIPTION:
        raise SkillValidationError(f"description exceeds {MAX_DESCRIPTION} characters")
    return name, description


def load_skill(skill_path: Path) -> Skill:
    skill_md = skill_path / "SKILL.md"
    if not skill_md.is_file():
        raise SkillValidationError("SKILL.md is missing")
    data, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    name, description = validate_frontmatter(data, skill_path.name)
    extra = {k: v for k, v in data.items() if k not in {"name", "description"}}
    return Skill(name=name, description=description, path=skill_path, body=body, extra=extra)


def scan_skills(root: Path | None = None) -> tuple[list[Skill], list[tuple[Path, str]]]:
    """Scan `.agents/skills/*/SKILL.md`. Invalid skills are skipped with a reason."""
    base = Path(root) if root is not None else skills_dir()
    skills: list[Skill] = []
    skipped: list[tuple[Path, str]] = []
    if not base.is_dir():
        logger.warning("skills directory does not exist: %s", base)
        return skills, skipped
    for child in sorted(p for p in base.iterdir() if p.is_dir()):
        try:
            skills.append(load_skill(child))
        except SkillValidationError as exc:
            logger.warning("skipping invalid skill %s: %s", child, exc)
            skipped.append((child, str(exc)))
    return skills, skipped


def render_catalog(skills: list[Skill], *, container_skills_root: str = "/workspace/.agents/skills") -> str:
    """Markdown catalog with name, description, and path only — never the SKILL.md body."""
    if not skills:
        return "No skills are available in this run."
    lines = [
        "Available skills (name + description only). Load a skill by reading its SKILL.md;",
        "load scripts/references/assets only if the skill body tells you to.",
        "",
    ]
    for skill in skills:
        skill_file = f"{container_skills_root.rstrip('/')}/{skill.name}/SKILL.md"
        lines.append(f"- `{skill.name}`: {skill.description}")
        lines.append(f"  Load with: `cat {skill_file}`")
    return "\n".join(lines)
