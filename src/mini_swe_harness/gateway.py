from __future__ import annotations

import argparse
import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mini_swe_harness.mcp_bridge import ListedTool, call_tool, format_exception, list_tools
from mini_swe_harness.mcp_config import McpServerSpec, load_mcp_config, spec_by_name
from mini_swe_harness.policy import Policy, join_gateway_tool, load_policy, split_gateway_tool

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    ts: str
    server: str
    tool: str
    status: str
    duration_ms: float
    error: str = ""

    def to_json(self) -> str:
        return json.dumps(self.__dict__, ensure_ascii=False)


class AuditLog:
    def __init__(self, path: Path | None = None):
        self.path = path
        self.events: list[AuditEvent] = []
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event: AuditEvent) -> None:
        self.events.append(event)
        if self.path:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(event.to_json() + "\n")


def _make_tool(name: str, description: str, input_schema: dict[str, Any]):
    from mcp.types import Tool

    try:
        return Tool(name=name, description=description, input_schema=input_schema)
    except TypeError:
        return Tool(name=name, description=description, inputSchema=input_schema)


class PolicyGateway:
    """MCP proxy that filters upstream tools and audits every call."""

    def __init__(self, policy: Policy, specs: list[McpServerSpec], audit: AuditLog | None = None):
        self.policy = policy
        self.specs = specs
        self.audit = audit or AuditLog()

    def allowed_specs(self) -> list[McpServerSpec]:
        return [spec for spec in self.specs if self.policy.server_allowed(spec.name)]

    async def filtered_tools(self) -> list[ListedTool]:
        out: list[ListedTool] = []
        for spec in self.allowed_specs():
            try:
                upstream = await list_tools(spec, timeout_s=self.policy.tool_timeout_s)
            except Exception as exc:
                logger.warning("gateway could not list tools for %s: %s", spec.name, exc)
                continue
            for tool in upstream:
                if self.policy.tool_allowed(spec.name, tool.name):
                    out.append(
                        ListedTool(
                            name=join_gateway_tool(spec.name, tool.name),
                            description=f"[{spec.name}] {tool.description}",
                            input_schema=tool.input_schema,
                        )
                    )
        return out

    async def invoke(self, gateway_name: str, arguments: dict[str, Any] | None) -> tuple[bool, str, str]:
        started = datetime.now(timezone.utc)
        status = "error"
        error = ""
        try:
            server, tool = split_gateway_tool(gateway_name)
        except ValueError as exc:
            error = str(exc)
            return False, error, "error"
        denied = self.policy.deny_reason(server, tool)
        if denied:
            status = "denied"
            error = denied
            return False, denied, status
        try:
            spec = spec_by_name(self.specs, server)
        except KeyError:
            status = "denied"
            error = f"Policy denied: unknown MCP server {server!r}"
            return False, error, status
        try:
            ok, text = await call_tool(
                spec,
                tool,
                arguments,
                timeout_s=self.policy.tool_timeout_s,
                max_output_chars=self.policy.max_output_chars,
            )
            status = "ok" if ok else "error"
            if not ok:
                error = text
            return ok, text, status
        except Exception as exc:
            status = "error"
            error = format_exception(exc)
            return False, error, status
        finally:
            duration_ms = (datetime.now(timezone.utc) - started).total_seconds() * 1000
            try:
                server_name, tool_name = split_gateway_tool(gateway_name)
            except ValueError:
                server_name, tool_name = "?", gateway_name
            self.audit.record(
                AuditEvent(
                    ts=started.isoformat(),
                    server=server_name,
                    tool=tool_name,
                    status=status,
                    duration_ms=round(duration_ms, 2),
                    error=error,
                )
            )


def build_mcp_server(gateway: PolicyGateway):
    from mcp.server import Server, ServerRequestContext
    from mcp.types import (
        CallToolRequestParams,
        CallToolResult,
        ListToolsResult,
        PaginatedRequestParams,
        TextContent,
    )

    async def on_list_tools(
        ctx: ServerRequestContext, params: PaginatedRequestParams | None
    ) -> ListToolsResult:
        tools = [
            _make_tool(item.name, item.description, item.input_schema)
            for item in await gateway.filtered_tools()
        ]
        return ListToolsResult(tools=tools)

    async def on_call_tool(ctx: ServerRequestContext, params: CallToolRequestParams) -> CallToolResult:
        ok, text, status = await gateway.invoke(params.name, params.arguments or {})
        is_error = status != "ok" or not ok
        return CallToolResult(content=[TextContent(type="text", text=text)], is_error=is_error)

    return Server("mini-swe-harness-gateway", on_list_tools=on_list_tools, on_call_tool=on_call_tool)


def serve_http(server, host: str, port: int) -> None:
    import uvicorn

    try:
        app = server.streamable_http_app(host=host, stateless_http=True)
    except TypeError:
        app = server.streamable_http_app(host=host)
    uvicorn.run(app, host=host, port=port, log_level="info")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Episode-scoped MCP policy gateway")
    parser.add_argument("--mcp-config", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--audit", type=Path, default=Path("/audit/mcp-audit.jsonl"))
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    policy = load_policy(args.policy)
    specs = load_mcp_config(args.mcp_config)
    gateway = PolicyGateway(policy, specs, AuditLog(args.audit))
    server = build_mcp_server(gateway)
    serve_http(server, args.host, args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
