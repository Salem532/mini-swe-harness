from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class McpServerSpec:
    name: str
    transport: str
    command: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    url: str | None = None
    memory_server: Any = None

    @property
    def is_stdio(self) -> bool:
        return self.transport == "stdio"

    @property
    def is_http(self) -> bool:
        return self.transport in {"http", "streamable-http", "streamable_http"}

    @property
    def is_memory(self) -> bool:
        return self.transport == "memory" or self.memory_server is not None


def load_mcp_config(path: Path) -> list[McpServerSpec]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    servers: list[McpServerSpec] = []
    for raw in data.get("servers") or []:
        servers.append(
            McpServerSpec(
                name=str(raw["name"]),
                transport=str(raw.get("transport", "stdio")),
                command=[str(c) for c in (raw.get("command") or [])],
                env={str(k): str(v) for k, v in (raw.get("env") or {}).items()},
                cwd=raw.get("cwd"),
                url=raw.get("url"),
            )
        )
    return servers


def spec_by_name(specs: list[McpServerSpec], name: str) -> McpServerSpec:
    for spec in specs:
        if spec.name == name:
            return spec
    raise KeyError(f"unknown MCP server {name!r}")
