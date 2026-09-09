from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

GATEWAY_TOOL_SEP = "__"


@dataclass(frozen=True)
class Policy:
    allow_mcp_servers: set[str]
    allow_mcp_tools: dict[str, set[str]]
    tool_timeout_s: float = 30.0
    max_output_chars: int = 8000

    def server_allowed(self, server: str) -> bool:
        return server in self.allow_mcp_servers

    def tool_allowed(self, server: str, tool: str) -> bool:
        if not self.server_allowed(server):
            return False
        allowed = self.allow_mcp_tools.get(server)
        if allowed is None:
            return False
        if "*" in allowed:
            return True
        return tool in allowed

    def deny_reason(self, server: str, tool: str) -> str | None:
        if not self.server_allowed(server):
            return f"Policy denied: MCP server {server!r} is not allowlisted"
        if not self.tool_allowed(server, tool):
            return f"Policy denied: tool {server}/{tool} is not allowlisted"
        return None


def load_policy(path: Path) -> Policy:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    servers = {str(s) for s in data.get("allow_mcp_servers", [])}
    tools_raw = data.get("allow_mcp_tools") or {}
    tools = {str(server): {str(t) for t in names} for server, names in tools_raw.items()}
    return Policy(
        allow_mcp_servers=servers,
        allow_mcp_tools=tools,
        tool_timeout_s=float(data.get("tool_timeout_s", 30)),
        max_output_chars=int(data.get("max_output_chars", 8000)),
    )


def split_gateway_tool(name: str) -> tuple[str, str]:
    server, sep, tool = name.partition(GATEWAY_TOOL_SEP)
    if not sep or not server or not tool:
        raise ValueError(
            f"gateway tool name {name!r} must be '{{server}}{GATEWAY_TOOL_SEP}{{tool}}'"
        )
    return server, tool


def join_gateway_tool(server: str, tool: str) -> str:
    return f"{server}{GATEWAY_TOOL_SEP}{tool}"
