from __future__ import annotations

from pathlib import Path

from mini_swe_harness.mcp_config import load_mcp_config


def test_load_mcp_config(tmp_path: Path) -> None:
    path = tmp_path / "mcp.yaml"
    path.write_text(
        """
servers:
  - name: ticket
    transport: stdio
    command: ["python", "-m", "mini_swe_harness.servers.ticket"]
  - name: remote
    transport: http
    url: http://example:9000/mcp
""",
        encoding="utf-8",
    )
    specs = load_mcp_config(path)
    assert specs[0].is_stdio and specs[0].name == "ticket"
    assert specs[1].is_http and specs[1].url.endswith("/mcp")
