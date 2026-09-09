from __future__ import annotations

import os
from pathlib import Path

from mcp.server import MCPServer


def workspace_root() -> Path:
    return Path(os.environ.get("WORKSPACE_ROOT", "/workspace")).resolve()


def _safe(path: str) -> Path:
    root = workspace_root()
    target = (root / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise PermissionError(f"path {path!r} is outside WORKSPACE_ROOT") from exc
    return target


def create_server() -> MCPServer:
    mcp = MCPServer("workspace_fs", instructions="Read-only view of the mounted workspace.")

    @mcp.tool()
    def list_directory(path: str = ".") -> list[str]:
        """List a directory under the workspace root."""
        target = _safe(path)
        if not target.is_dir():
            raise FileNotFoundError(f"not a directory: {path}")
        return sorted(child.name + ("/" if child.is_dir() else "") for child in target.iterdir())

    @mcp.tool()
    def read_file(path: str) -> str:
        """Read a UTF-8 text file under the workspace root."""
        target = _safe(path)
        if not target.is_file():
            raise FileNotFoundError(f"not a file: {path}")
        return target.read_text(encoding="utf-8")

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
