from __future__ import annotations

from pathlib import Path

import yaml

from mini_swe_harness.skills import Skill, render_catalog

SKILLS_SECTION = """
## Available Skills

{catalog}

Do not paste every skill into context. Open a SKILL.md only when its description matches this task.
After loading a skill, follow it; read files under scripts/, references/, or assets/ only when that skill says to.
"""

MCP_SECTION = """
## MCP tools

External tools are available only through the `mcp-call` CLI, which talks to an episode policy gateway.
Unauthorized tools are denied with a readable error; do not try to start MCP servers or bypass the CLI.

Commands:

    mcp-call list-servers
    mcp-call list-tools <server>
    mcp-call call <server> <tool> --args '<json>'

Discover tool schemas at runtime with `list-tools`. Do not assume a full catalog is in this prompt.
If the user names a TICKET-* id, fetch that ticket rather than guessing hidden business rules.
"""

POLICY_SECTION = """
## Tool policy

MCP servers and tools are allowlisted on the gateway. A denied call is not a crash: read the error and change strategy.
Ordinary bash (pytest, sed, git) still goes through the shell. Do not use sudo.
"""


def load_mini_yaml() -> dict:
    try:
        import minisweagent

        path = Path(minisweagent.__file__).resolve().parent / "config" / "mini.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {
            "agent": {
                "system_template": "You are a helpful assistant that can interact with a computer.\n",
                "instance_template": "Please solve this issue: {{task}}\n",
            }
        }


def build_agent_templates(
    *,
    skills: list[Skill] | None,
    enable_mcp: bool,
    container_skills_root: str = "/workspace/.agents/skills",
) -> dict[str, str]:
    """Return system/instance templates. Startup prompt never includes SKILL.md bodies."""
    base = load_mini_yaml()
    agent = base.get("agent") or {}
    system = agent.get("system_template") or "You are a helpful assistant that can interact with a computer.\n"
    instance = agent.get("instance_template") or "Please solve this issue: {{task}}\n"
    extras: list[str] = []
    if skills:
        extras.append(
            SKILLS_SECTION.format(catalog=render_catalog(skills, container_skills_root=container_skills_root))
        )
    if enable_mcp:
        extras.append(MCP_SECTION)
        extras.append(POLICY_SECTION)
    extra_text = "\n".join(extras)
    if extra_text:
        instance = instance.rstrip() + "\n" + extra_text + "\n"
    return {"system_template": system, "instance_template": instance}


def assert_no_skill_bodies(prompt: str, skills: list[Skill]) -> None:
    for skill in skills:
        token = skill.body.strip()
        if len(token) >= 40 and token in prompt:
            raise AssertionError(f"skill body for {skill.name} leaked into the startup prompt")
