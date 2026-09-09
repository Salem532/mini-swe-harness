from __future__ import annotations

from mini_swe_harness.prompt import assert_no_skill_bodies, build_agent_templates
from mini_swe_harness.skills import scan_skills


def test_startup_prompt_has_catalog_not_bodies() -> None:
    skills, skipped = scan_skills()
    assert not skipped
    templates = build_agent_templates(skills=skills, enable_mcp=True)
    prompt = templates["system_template"] + templates["instance_template"]
    assert "pytest-debug" in prompt
    assert "mcp-call list-tools" in prompt
    assert_no_skill_bodies(prompt, skills)
    for skill in skills:
        assert skill.description in prompt


def test_baseline_omits_skills_and_mcp() -> None:
    templates = build_agent_templates(skills=None, enable_mcp=False)
    text = templates["instance_template"]
    assert "mcp-call" not in text
    assert "Available Skills" not in text
