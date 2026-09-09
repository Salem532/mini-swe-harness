from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mini_swe_harness.mcp_config import McpServerSpec

logger = logging.getLogger(__name__)


def format_exception(exc: BaseException) -> str:
    """Flatten ExceptionGroup so agents see the actual transport/tool error."""
    if isinstance(exc, BaseExceptionGroup):
        inner = "\n".join(format_exception(item) for item in exc.exceptions)
        return f"{type(exc).__name__}: {exc}\n{inner}"
    return f"{type(exc).__name__}: {exc}"


def _stdio_params(spec: McpServerSpec):
    try:
        from mcp.client.stdio import StdioServerParameters
    except ImportError:  # pragma: no cover - SDK layout fallback
        from mcp import StdioServerParameters  # type: ignore

    if not spec.command:
        raise ValueError(f"stdio server {spec.name!r} is missing command")
    kwargs: dict[str, Any] = {
        "command": spec.command[0],
        "args": list(spec.command[1:]),
    }
    if spec.env:
        kwargs["env"] = spec.env
    if spec.cwd:
        kwargs["cwd"] = spec.cwd
    return StdioServerParameters(**kwargs)


def _client_target(spec: McpServerSpec) -> Any:
    if spec.is_memory:
        if spec.memory_server is None:
            raise ValueError(f"memory server {spec.name!r} has no memory_server object")
        return spec.memory_server
    if spec.is_http:
        if not spec.url:
            raise ValueError(f"http server {spec.name!r} is missing url")
        return spec.url
    if spec.is_stdio:
        from mcp.client.stdio import stdio_client

        return stdio_client(_stdio_params(spec))
    raise ValueError(f"unsupported MCP transport {spec.transport!r} for {spec.name}")


@asynccontextmanager
async def open_mcp_client(spec: McpServerSpec) -> AsyncIterator[Any]:
    from mcp import Client

    target = _client_target(spec)
    async with Client(target) as client:
        yield client


def _tool_schema(tool: Any) -> dict[str, Any]:
    schema = getattr(tool, "input_schema", None) or getattr(tool, "inputSchema", None)
    return dict(schema) if isinstance(schema, dict) else {"type": "object"}


def _tool_description(tool: Any) -> str:
    return str(getattr(tool, "description", None) or "")


def result_text(result: Any, *, max_chars: int | None = None) -> str:
    if getattr(result, "structured_content", None) is not None:
        text = json.dumps(result.structured_content, ensure_ascii=False)
    else:
        chunks: list[str] = []
        for block in getattr(result, "content", None) or []:
            text_value = getattr(block, "text", None)
            if text_value:
                chunks.append(text_value)
        text = "\n".join(chunks) if chunks else json.dumps(_safe_dump(result), ensure_ascii=False)
    if max_chars is not None and len(text) > max_chars:
        extra = len(text) - max_chars
        text = text[:max_chars] + f"\n...[truncated {extra} chars]"
    return text


def _safe_dump(value: Any) -> Any:
    dump = getattr(value, "model_dump", None)
    if callable(dump):
        try:
            return dump(mode="json")
        except TypeError:
            return dump()
    return repr(value)


@dataclass
class ListedTool:
    name: str
    description: str
    input_schema: dict[str, Any]


async def list_tools(spec: McpServerSpec, *, timeout_s: float = 30.0) -> list[ListedTool]:
    async def _inner() -> list[ListedTool]:
        async with open_mcp_client(spec) as client:
            listed = await client.list_tools()
            tools = []
            for tool in listed.tools:
                tools.append(
                    ListedTool(
                        name=str(tool.name),
                        description=_tool_description(tool),
                        input_schema=_tool_schema(tool),
                    )
                )
            return tools

    try:
        return await asyncio.wait_for(_inner(), timeout=timeout_s)
    except TimeoutError as exc:
        raise TimeoutError(f"list-tools timed out for server {spec.name}") from exc
    except Exception as exc:
        logger.warning("list-tools failed for %s: %s", spec.name, exc)
        raise


async def call_tool(
    spec: McpServerSpec,
    tool: str,
    arguments: dict[str, Any] | None,
    *,
    timeout_s: float = 30.0,
    max_output_chars: int = 8000,
) -> tuple[bool, str]:
    async def _inner() -> tuple[bool, str]:
        async with open_mcp_client(spec) as client:
            result = await client.call_tool(tool, arguments or {})
            ok = not bool(getattr(result, "is_error", False))
            return ok, result_text(result, max_chars=max_output_chars)

    try:
        return await asyncio.wait_for(_inner(), timeout=timeout_s)
    except TimeoutError as exc:
        raise TimeoutError(f"call {spec.name}/{tool} timed out") from exc
