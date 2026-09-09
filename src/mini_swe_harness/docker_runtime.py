from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


class DockerError(RuntimeError):
    pass


def host_docker_user() -> str:
    """Match the host uid/gid so bind-mounted copies remain writable."""
    return f"{os.getuid()}:{os.getgid()}"


def docker_available() -> bool:
    return shutil.which("docker") is not None


def run_docker(args: list[str], *, timeout: int = 120, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["docker", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and result.returncode != 0:
        raise DockerError(f"{' '.join(cmd)} failed:\n{result.stdout}\n{result.stderr}")
    return result


def create_internal_network(name: str) -> str:
    try:
        run_docker(["network", "create", "--internal", name])
    except DockerError as exc:
        text = str(exc).lower()
        if "subnetted" in text or "address pools" in text:
            run_docker(["network", "prune", "-f"], check=False)
            run_docker(["network", "create", "--internal", name])
        else:
            raise
    return name


def remove_network(name: str) -> None:
    run_docker(["network", "rm", name], check=False)


def start_gateway_container(
    *,
    image: str,
    name: str,
    network: str,
    workspace: Path,
    tickets: Path,
    mcp_config: Path,
    policy: Path,
    audit_dir: Path,
) -> str:
    audit_dir.mkdir(parents=True, exist_ok=True)
    args = [
        "run",
        "-d",
        "--name",
        name,
        "--network",
        network,
        "--network-alias",
        "gateway",
        "--user",
        host_docker_user(),
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=256m",
        "-v",
        f"{workspace}:/workspace:ro",
        "-v",
        f"{tickets}:/tickets:ro",
        "-v",
        f"{mcp_config}:/config/mcp.yaml:ro",
        "-v",
        f"{policy}:/config/policy.yaml:ro",
        "-v",
        f"{audit_dir}:/audit:rw",
        "-e",
        "TICKET_ROOT=/tickets",
        "-e",
        "WORKSPACE_ROOT=/workspace",
        "-e",
        "MINI_SWE_HARNESS_ROOT=/opt/harness",
        image,
        "python",
        "-m",
        "mini_swe_harness.gateway",
        "--mcp-config",
        "/config/mcp.yaml",
        "--policy",
        "/config/policy.yaml",
        "--audit",
        "/audit/mcp-audit.jsonl",
        "--host",
        "0.0.0.0",
        "--port",
        "8765",
    ]
    result = run_docker(args, timeout=180)
    wait_for_gateway(name)
    return result.stdout.strip()


def wait_for_gateway(name: str, timeout_s: float = 30.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        result = run_docker(["logs", name], check=False)
        text = (result.stdout or "") + (result.stderr or "")
        if "Uvicorn running" in text or "Application startup complete" in text:
            return
        time.sleep(0.3)


def stop_container(container_id: str | None) -> None:
    if not container_id:
        return
    run_docker(["rm", "-f", container_id], check=False)


def agent_run_args(
    *,
    network: str,
    workspace: Path,
    visible_tests: Path,
    skills: Path | None,
    enable_mcp: bool,
    memory: str = "4g",
    cpus: str = "2",
) -> list[str]:
    args = [
        "--rm",
        "--network",
        network,
        "--user",
        host_docker_user(),
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges:true",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=512m",
        "--memory",
        memory,
        "--cpus",
        cpus,
        "--pids-limit",
        "256",
        "-v",
        f"{workspace}:/workspace:rw",
        "-v",
        f"{visible_tests}:/workspace/tests:ro",
        "-e",
        "HOME=/tmp",
        "-e",
        "XDG_CACHE_HOME=/tmp",
        "-e",
        "PYTHONPATH=/workspace/src",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
    ]
    if skills is not None:
        args.extend(["-v", f"{skills}:/workspace/.agents/skills:ro"])
    if enable_mcp:
        args.extend(["-e", "MCP_GATEWAY_URL=http://gateway:8765/mcp"])
    else:
        # Still attach to the episode network so teardown is uniform, but give a dead URL.
        args.extend(["-e", "MCP_GATEWAY_URL="])
    return args


def run_judge(
    *,
    image: str,
    src: Path,
    visible_tests: Path,
    hidden_tests: Path,
    timeout_s: int = 60,
) -> dict[str, Any]:
    args = [
        "run",
        "--rm",
        "--network",
        "none",
        "--user",
        host_docker_user(),
        "--cap-drop",
        "ALL",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,exec,nosuid,size=256m",
        "-v",
        f"{src}:/workspace/src:ro",
        "-v",
        f"{visible_tests}:/workspace/tests/visible:ro",
        "-v",
        f"{hidden_tests}:/workspace/tests/hidden:ro",
        "-e",
        "PYTHONPATH=/workspace/src",
        "-e",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1",
        "-e",
        "HOME=/tmp",
        image,
        "python",
        "-m",
        "pytest",
        "/workspace/tests/hidden",
        "-q",
        "--tb=short",
    ]
    result = run_docker(args, timeout=timeout_s, check=False)
    return {
        "returncode": result.returncode,
        "output": (result.stdout or "") + (result.stderr or ""),
        "passed": result.returncode == 0,
    }


def load_audit(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        events.append(json.loads(line))
    return events
