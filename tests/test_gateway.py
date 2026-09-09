from __future__ import annotations

import sys

from mini_swe_harness.gateway import PolicyGateway
from mini_swe_harness.mcp_config import McpServerSpec
from mini_swe_harness.policy import Policy, join_gateway_tool
from mini_swe_harness.servers.ticket import create_server


def _gateway(tmp_path, monkeypatch) -> PolicyGateway:
    monkeypatch.setenv("TICKET_ROOT", str(tmp_path))
    (tmp_path / "TICKET-7.md").write_text("secret-spec\n", encoding="utf-8")
    spec = McpServerSpec(name="ticket", transport="memory", memory_server=create_server())
    policy = Policy(
        allow_mcp_servers={"ticket"},
        allow_mcp_tools={"ticket": {"get_ticket"}},
    )
    return PolicyGateway(policy, [spec])


async def test_gateway_allows_and_denies(tmp_path, monkeypatch) -> None:
    gateway = _gateway(tmp_path, monkeypatch)
    tools = await gateway.filtered_tools()
    names = {tool.name for tool in tools}
    assert join_gateway_tool("ticket", "get_ticket") in names
    assert join_gateway_tool("ticket", "list_tickets") not in names

    ok, text, status = await gateway.invoke("ticket__get_ticket", {"ticket_id": "TICKET-7"})
    assert ok and status == "ok" and "secret-spec" in text

    ok, text, status = await gateway.invoke("ticket__list_tickets", {})
    assert not ok and status == "denied" and "Policy denied" in text

    ok, text, status = await gateway.invoke("workspace_fs__read_file", {"path": "x"})
    assert not ok and status == "denied"


async def test_gateway_stdio_get_ticket(tmp_path) -> None:
    (tmp_path / "TICKET-7.md").write_text("secret-spec\n", encoding="utf-8")
    spec = McpServerSpec(
        name="ticket",
        transport="stdio",
        command=[sys.executable, "-m", "mini_swe_harness.servers.ticket"],
        env={"TICKET_ROOT": str(tmp_path)},
    )
    policy = Policy(
        allow_mcp_servers={"ticket"},
        allow_mcp_tools={"ticket": {"get_ticket"}},
    )
    gateway = PolicyGateway(policy, [spec])
    ok, text, status = await gateway.invoke("ticket__get_ticket", {"ticket_id": "TICKET-7"})
    assert ok and status == "ok" and "secret-spec" in text
    assert gateway.audit.events[-1].status == "ok"
