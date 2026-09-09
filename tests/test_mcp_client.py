from __future__ import annotations

from mini_swe_harness.mcp_bridge import format_exception
from mini_swe_harness.mcp_client import build_parser
from mini_swe_harness.policy import join_gateway_tool


def test_format_exception_flattens_group() -> None:
    grouped = ExceptionGroup("unhandled errors in a TaskGroup", [TypeError("no async context manager")])
    text = format_exception(grouped)
    assert "TypeError: no async context manager" in text


def test_cli_parser() -> None:
    parser = build_parser()
    ns = parser.parse_args(["list-tools", "ticket"])
    assert ns.command == "list-tools"
    assert ns.server == "ticket"
    ns = parser.parse_args(["call", "ticket", "get_ticket", "--args", "{}"])
    assert ns.tool == "get_ticket"
    assert join_gateway_tool("ticket", "get_ticket") == "ticket__get_ticket"
