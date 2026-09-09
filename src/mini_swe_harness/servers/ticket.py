from __future__ import annotations

import os
import re
from pathlib import Path

from mcp.server import MCPServer

TICKET_ID_RE = re.compile(r"^[A-Z]+-[0-9]+$")


def ticket_root() -> Path:
    return Path(os.environ.get("TICKET_ROOT", "/tickets"))


def create_server() -> MCPServer:
    mcp = MCPServer("ticket", instructions="Read external tickets that are not in the agent workspace.")

    @mcp.tool()
    def get_ticket(ticket_id: str) -> str:
        """Return the full text of an external ticket/work-order. Use when the task names a TICKET-* id."""
        if not TICKET_ID_RE.fullmatch(ticket_id):
            raise ValueError("ticket_id must look like TICKET-1234")
        path = ticket_root() / f"{ticket_id}.md"
        if not path.is_file():
            raise FileNotFoundError(f"unknown ticket {ticket_id}")
        return path.read_text(encoding="utf-8")

    @mcp.tool()
    def list_tickets() -> list[str]:
        """List ticket ids available to this episode. Not a substitute for reading a named ticket."""
        root = ticket_root()
        if not root.is_dir():
            return []
        return sorted(path.stem for path in root.glob("*.md"))

    return mcp


def main() -> None:
    create_server().run()


if __name__ == "__main__":
    main()
