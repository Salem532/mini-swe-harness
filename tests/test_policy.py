from __future__ import annotations

from pathlib import Path

from mini_swe_harness.policy import join_gateway_tool, load_policy, split_gateway_tool


def test_policy_allow_and_deny(tmp_path: Path) -> None:
    path = tmp_path / "policy.yaml"
    path.write_text(
        "allow_mcp_servers: [ticket]\nallow_mcp_tools:\n  ticket: [get_ticket]\n",
        encoding="utf-8",
    )
    policy = load_policy(path)
    assert policy.tool_allowed("ticket", "get_ticket")
    assert not policy.tool_allowed("ticket", "list_tickets")
    assert not policy.tool_allowed("workspace_fs", "read_file")
    assert "not allowlisted" in (policy.deny_reason("ticket", "list_tickets") or "")


def test_policy_eval_still_denies_list_tickets() -> None:
    from mini_swe_harness.paths import repo_root

    policy = load_policy(repo_root() / "config" / "policy.eval.yaml")
    assert policy.tool_allowed("ticket", "get_ticket")
    assert not policy.tool_allowed("ticket", "list_tickets")
    assert not policy.tool_allowed("workspace_fs", "read_file")


def test_policy_mcp_policy_allows_list_denies_fs() -> None:
    from mini_swe_harness.paths import repo_root

    policy = load_policy(repo_root() / "config" / "policy.mcp_policy.yaml")
    assert policy.tool_allowed("ticket", "get_ticket")
    assert policy.tool_allowed("ticket", "list_tickets")
    assert not policy.tool_allowed("workspace_fs", "read_file")
    assert "not allowlisted" in (policy.deny_reason("workspace_fs", "read_file") or "")


def test_gateway_tool_names() -> None:
    assert join_gateway_tool("ticket", "get_ticket") == "ticket__get_ticket"
    assert split_gateway_tool("ticket__get_ticket") == ("ticket", "get_ticket")
