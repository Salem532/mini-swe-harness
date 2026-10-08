from __future__ import annotations

import re
from collections import Counter
from typing import Any

SKILL_MD_RE = re.compile(r"\.agents/skills/([a-z0-9-]+)/SKILL\.md")
SKILL_RESOURCE_RE = re.compile(
    r"\.agents/skills/([a-z0-9-]+)/(scripts|references|assets)/[A-Za-z0-9._/-]+"
)
MCP_CALL_RE = re.compile(r"\bmcp-call\b")


def iter_commands(trajectory: dict[str, Any]) -> list[str]:
    commands: list[str] = []
    for message in trajectory.get("messages") or []:
        extra = message.get("extra") or {}
        for action in extra.get("actions") or []:
            if isinstance(action, dict) and action.get("command"):
                commands.append(str(action["command"]))
            elif isinstance(action, str):
                commands.append(action)
    return commands


def extract_usage(trajectory: dict[str, Any]) -> dict[str, int]:
    prompt_tokens = 0
    completion_tokens = 0
    for message in trajectory.get("messages") or []:
        extra = message.get("extra") or {}
        response = extra.get("response") or {}
        usage = response.get("usage") or extra.get("usage") or {}
        if isinstance(usage, dict):
            prompt_tokens += int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
            completion_tokens += int(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "api_calls": int(((trajectory.get("info") or {}).get("model_stats") or {}).get("api_calls") or 0),
        "bash_actions": len(iter_commands(trajectory)),
    }


def skill_activation(trajectory: dict[str, Any]) -> dict[str, Any]:
    loaded: list[str] = []
    resources: list[str] = []
    for command in iter_commands(trajectory):
        loaded.extend(SKILL_MD_RE.findall(command))
        resources.extend(match.group(0) for match in SKILL_RESOURCE_RE.finditer(command))
    unique_skills = sorted(set(loaded))
    return {
        "activated_skills": unique_skills,
        "skill_activation_count": len(unique_skills),
        "resource_reads": resources,
        "activated": bool(unique_skills),
    }


def skill_triggered(skill: dict[str, Any], expected_skill: str | None) -> bool:
    if not expected_skill:
        return False
    activated = skill.get("activated_skills") or []
    return expected_skill in activated


def mcp_cli_mentions(trajectory: dict[str, Any]) -> int:
    return sum(1 for command in iter_commands(trajectory) if MCP_CALL_RE.search(command))


def summarize_audit(events: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(event.get("status") or "unknown") for event in events)
    return {
        "ok": int(counts.get("ok", 0)),
        "denied": int(counts.get("denied", 0)),
        "error": int(counts.get("error", 0)),
        "total": sum(counts.values()),
    }
