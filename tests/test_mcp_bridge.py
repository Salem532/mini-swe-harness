from __future__ import annotations

import sys

from mini_swe_harness.mcp_bridge import call_tool, list_tools
from mini_swe_harness.mcp_config import McpServerSpec
from mini_swe_harness.servers.ticket import create_server


async def test_inmemory_ticket_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("TICKET_ROOT", str(tmp_path))
    (tmp_path / "TICKET-9.md").write_text("body-9\n", encoding="utf-8")
    spec = McpServerSpec(name="ticket", transport="memory", memory_server=create_server())
    tools = await list_tools(spec)
    names = {tool.name for tool in tools}
    assert "get_ticket" in names
    ok, text = await call_tool(spec, "get_ticket", {"ticket_id": "TICKET-9"})
    assert ok
    assert "body-9" in text


async def test_stdio_ticket_roundtrip(tmp_path) -> None:
    (tmp_path / "TICKET-9.md").write_text("body-9\n", encoding="utf-8")
    spec = McpServerSpec(
        name="ticket",
        transport="stdio",
        command=[sys.executable, "-m", "mini_swe_harness.servers.ticket"],
        env={"TICKET_ROOT": str(tmp_path)},
    )
    tools = await list_tools(spec)
    assert "get_ticket" in {tool.name for tool in tools}
    ok, text = await call_tool(spec, "get_ticket", {"ticket_id": "TICKET-9"})
    assert ok
    assert "body-9" in text
    assert "asynchronous context manager" not in text
