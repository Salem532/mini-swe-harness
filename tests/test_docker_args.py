from __future__ import annotations

from mini_swe_harness.docker_runtime import agent_run_args, host_docker_user
from mini_swe_harness.paths import repo_root


def test_agent_run_args_isolation(tmp_path) -> None:
    args = agent_run_args(
        network="harness-test",
        workspace=tmp_path / "ws",
        visible_tests=tmp_path / "tests",
        skills=repo_root() / ".agents" / "skills",
        enable_mcp=True,
    )
    joined = " ".join(args)
    assert "--cap-drop ALL" in joined
    assert "--internal" not in joined  # network is created separately
    assert "no-new-privileges" in joined
    assert "MCP_GATEWAY_URL=http://gateway:8765/mcp" in joined
    assert str(tmp_path / "tests") + ":/workspace/tests:ro" in joined
    assert f"--user {host_docker_user()}" in joined
