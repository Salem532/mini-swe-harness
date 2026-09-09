from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from mini_swe_harness.mcp_bridge import format_exception, result_text
from mini_swe_harness.policy import GATEWAY_TOOL_SEP, join_gateway_tool

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_DENIED = 2


def _gateway_url() -> str:
    return os.environ.get("MCP_GATEWAY_URL", "http://127.0.0.1:8765/mcp")


def _parse_server_tool(name: str) -> tuple[str | None, str]:
    if GATEWAY_TOOL_SEP in name:
        server, tool = name.split(GATEWAY_TOOL_SEP, 1)
        return server, tool
    return None, name


async def _with_client(fn):
    from mcp import Client

    async with Client(_gateway_url()) as client:
        return await fn(client)


def _print(text: str, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    stream.write(text.rstrip() + "\n")


async def cmd_list_servers() -> int:
    async def _run(client) -> int:
        listed = await client.list_tools()
        servers = sorted({_parse_server_tool(tool.name)[0] or "gateway" for tool in listed.tools})
        if not servers:
            _print("No MCP servers are currently exposed by the policy gateway.")
            return EXIT_OK
        for name in servers:
            _print(name)
        return EXIT_OK

    return await _with_client(_run)


async def cmd_list_tools(server: str | None) -> int:
    async def _run(client) -> int:
        listed = await client.list_tools()
        rows = []
        for tool in listed.tools:
            prefix, name = _parse_server_tool(tool.name)
            if server and prefix != server and name != server:
                continue
            schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None) or {}
            rows.append(
                {
                    "server": prefix,
                    "tool": name if prefix else tool.name,
                    "gateway_name": tool.name,
                    "description": getattr(tool, "description", "") or "",
                    "input_schema": schema,
                }
            )
        if server and not rows:
            _print(f"No tools visible for server {server!r} (unknown, empty, or not allowlisted).", error=True)
            return EXIT_ERROR
        _print(json.dumps(rows, indent=2, ensure_ascii=False))
        return EXIT_OK

    return await _with_client(_run)


async def cmd_call(server: str, tool: str, args_json: str) -> int:
    try:
        arguments: dict[str, Any] = json.loads(args_json) if args_json else {}
        if not isinstance(arguments, dict):
            raise ValueError("args must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exc:
        _print(f"Invalid --args JSON: {exc}", error=True)
        return EXIT_ERROR

    gateway_name = join_gateway_tool(server, tool)

    async def _run(client) -> int:
        result = await client.call_tool(gateway_name, arguments)
        text = result_text(result)
        is_error = bool(getattr(result, "is_error", False))
        _print(text, error=is_error)
        lowered = text.lower()
        if is_error and "policy denied" in lowered:
            return EXIT_DENIED
        return EXIT_ERROR if is_error else EXIT_OK

    return await _with_client(_run)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mcp-call",
        description="Bash CLI for the episode MCP policy gateway (not a direct upstream client).",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list-servers", help="List allowlisted servers currently exposed by the gateway")
    list_tools = sub.add_parser("list-tools", help="List tools, optionally for one server")
    list_tools.add_argument("server", nargs="?", default=None)
    call = sub.add_parser("call", help="Call an upstream tool through the gateway")
    call.add_argument("server")
    call.add_argument("tool")
    call.add_argument("--args", default="{}", help="JSON object of tool arguments")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "list-servers":
            return asyncio.run(cmd_list_servers())
        if args.command == "list-tools":
            return asyncio.run(cmd_list_tools(args.server))
        if args.command == "call":
            return asyncio.run(cmd_call(args.server, args.tool, args.args))
    except KeyboardInterrupt:
        return EXIT_ERROR
    except Exception as exc:
        _print(format_exception(exc), error=True)
        return EXIT_ERROR
    return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
