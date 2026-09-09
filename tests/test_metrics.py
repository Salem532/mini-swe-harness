from __future__ import annotations

from mini_swe_harness.metrics import extract_usage, skill_activation, summarize_audit


def test_extract_usage_and_skill_cat() -> None:
    trajectory = {
        "info": {"model_stats": {"api_calls": 3}},
        "messages": [
            {
                "role": "assistant",
                "extra": {
                    "actions": [
                        {"command": "cat /workspace/.agents/skills/pytest-debug/SKILL.md"},
                        {
                            "command": "cat /workspace/.agents/skills/pytest-debug/references/traceback-reading.md"
                        },
                        {"command": "mcp-call list-tools ticket"},
                    ],
                    "response": {"usage": {"prompt_tokens": 100, "completion_tokens": 20}},
                },
            }
        ],
    }
    usage = extract_usage(trajectory)
    assert usage["prompt_tokens"] == 100
    assert usage["completion_tokens"] == 20
    assert usage["bash_actions"] == 3
    skill = skill_activation(trajectory)
    assert skill["activated"] is True
    assert "pytest-debug" in skill["activated_skills"]
    assert skill["resource_reads"]


def test_audit_counts() -> None:
    summary = summarize_audit(
        [
            {"status": "ok"},
            {"status": "ok"},
            {"status": "denied"},
            {"status": "error"},
        ]
    )
    assert summary == {"ok": 2, "denied": 1, "error": 1, "total": 4}
