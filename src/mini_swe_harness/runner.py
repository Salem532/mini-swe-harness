from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import time
import traceback
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mini_swe_harness import EVAL_ARMS
from mini_swe_harness.docker_runtime import (
    agent_run_args,
    create_internal_network,
    docker_available,
    load_audit,
    remove_network,
    run_judge,
    start_gateway_container,
    stop_container,
)
from mini_swe_harness.metrics import extract_usage, mcp_cli_mentions, skill_activation, summarize_audit
from mini_swe_harness.paths import config_dir, repo_root, skills_dir
from mini_swe_harness.prompt import build_agent_templates
from mini_swe_harness.skills import scan_skills
from mini_swe_harness.tasks import TaskSpec

DEFAULT_IMAGE = os.environ.get("MINI_SWE_HARNESS_IMAGE", "mini-swe-harness:local")


def arm_flags(arm: str) -> tuple[bool, bool]:
    if arm not in EVAL_ARMS:
        raise ValueError(f"unknown arm {arm}")
    enable_skills = arm in {"skill_only", "full"}
    enable_mcp = arm in {"mcp_only", "full"}
    return enable_skills, enable_mcp


def copy_src(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def _model_config(seed: int) -> dict[str, Any]:
    model_name = os.environ.get("LITELLM_MODEL") or os.environ.get("MSWEA_MODEL_NAME") or "openai/qwen"
    kwargs: dict[str, Any] = {
        "drop_params": True,
        "temperature": float(os.environ.get("LITELLM_TEMPERATURE", "0.2")),
        "seed": seed,
    }
    if os.environ.get("OPENAI_API_BASE"):
        kwargs["api_base"] = os.environ["OPENAI_API_BASE"]
    if os.environ.get("OPENAI_API_KEY"):
        kwargs["api_key"] = os.environ["OPENAI_API_KEY"]
    kwargs["timeout"] = float(os.environ.get("LITELLM_TIMEOUT", "90"))
    kwargs["num_retries"] = int(os.environ.get("LITELLM_NUM_RETRIES", "0"))
    return {
        "model_name": model_name,
        "cost_tracking": os.environ.get("MSWEA_COST_TRACKING", "ignore_errors"),
        "model_kwargs": kwargs,
    }


class WallBoundModel:
    """Cap each LLM HTTP call to remaining episode wall-clock so a hung vLLM request cannot outlive timeout_s."""

    def __init__(self, inner: Any, *, wall_s: int, started_at: float):
        self._inner = inner
        self._wall_s = wall_s
        self._started_at = started_at

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def _remaining(self) -> float:
        return self._wall_s - (time.time() - self._started_at)

    def query(self, messages: Any, **kwargs: Any) -> Any:
        from minisweagent.exceptions import TimeExceeded

        remaining = self._remaining()
        if remaining <= 1:
            raise TimeExceeded(
                {
                    "role": "exit",
                    "content": "TimeExceeded",
                    "extra": {"exit_status": "TimeExceeded", "submission": ""},
                }
            )
        timeout = min(float(os.environ.get("LITELLM_TIMEOUT", "90")), remaining)
        cfg = getattr(self._inner, "config", None)
        previous: dict[str, Any] | None = None
        if cfg is not None and hasattr(cfg, "model_kwargs"):
            previous = dict(cfg.model_kwargs)
            cfg.model_kwargs["timeout"] = timeout
            cfg.model_kwargs["num_retries"] = int(os.environ.get("LITELLM_NUM_RETRIES", "0"))
        try:
            return self._inner.query(messages, **kwargs)
        except Exception as exc:
            name = type(exc).__name__
            timed_out = name in {"Timeout", "APITimeoutError", "TimeoutError"} or "timed out" in str(exc).lower()
            if timed_out or self._remaining() <= 1:
                raise TimeExceeded(
                    {
                        "role": "exit",
                        "content": "TimeExceeded",
                        "extra": {"exit_status": "TimeExceeded", "submission": ""},
                    }
                ) from exc
            raise
        finally:
            if previous is not None and cfg is not None:
                cfg.model_kwargs.clear()
                cfg.model_kwargs.update(previous)


@dataclass
class RunResult:
    task_id: str
    arm: str
    seed: int
    success: bool
    exit_status: str
    judge: dict[str, Any]
    usage: dict[str, Any]
    skill: dict[str, Any]
    mcp: dict[str, Any]
    trajectory_path: Path | None
    model_name: str
    extra: dict[str, Any]


def episode_result_path(output_dir: Path, task_id: str, arm: str, seed: int) -> Path:
    return output_dir / f"{task_id}.{arm}.{seed}.result.json"


def result_to_dict(row: RunResult) -> dict[str, Any]:
    return {
        "task_id": row.task_id,
        "arm": row.arm,
        "seed": row.seed,
        "success": row.success,
        "exit_status": row.exit_status,
        "judge": row.judge,
        "usage": row.usage,
        "skill": row.skill,
        "mcp": row.mcp,
        "trajectory_path": str(row.trajectory_path) if row.trajectory_path else None,
        "model_name": row.model_name,
        "extra": row.extra,
    }


def result_from_dict(data: dict[str, Any]) -> RunResult:
    path = data.get("trajectory_path")
    return RunResult(
        task_id=str(data["task_id"]),
        arm=str(data["arm"]),
        seed=int(data["seed"]),
        success=bool(data.get("success")),
        exit_status=str(data.get("exit_status") or ""),
        judge=dict(data.get("judge") or {}),
        usage=dict(data.get("usage") or {}),
        skill=dict(data.get("skill") or {}),
        mcp=dict(data.get("mcp") or {}),
        trajectory_path=Path(path) if path else None,
        model_name=str(data.get("model_name") or ""),
        extra=dict(data.get("extra") or {}),
    )


def write_episode_result(output_dir: Path, row: RunResult) -> Path:
    """Persist one episode immediately: result.json + append-only jsonl."""
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = result_to_dict(row)
    path = episode_result_path(output_dir, row.task_id, row.arm, row.seed)
    path.write_text(json.dumps(payload, default=str, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    ledger = output_dir / "episodes.jsonl"
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, default=str, ensure_ascii=False) + "\n")
    return path


def load_episode_result(output_dir: Path, task_id: str, arm: str, seed: int) -> RunResult | None:
    path = episode_result_path(output_dir, task_id, arm, seed)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or "success" not in data or "task_id" not in data:
        return None
    return result_from_dict(data)


def load_all_results(output_dir: Path) -> list[RunResult]:
    rows: list[RunResult] = []
    if not output_dir.is_dir():
        return rows
    for path in sorted(output_dir.glob("*.result.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or "success" not in data or "task_id" not in data:
            continue
        rows.append(result_from_dict(data))
    return rows


def failed_result(task_id: str, arm: str, seed: int, exc: BaseException, *, trajectory_path: Path | None = None) -> RunResult:
    return RunResult(
        task_id=task_id,
        arm=arm,
        seed=seed,
        success=False,
        exit_status=type(exc).__name__,
        judge={"passed": False, "output": traceback.format_exc()[-2000:]},
        usage={},
        skill={},
        mcp={},
        trajectory_path=trajectory_path,
        model_name=str(os.environ.get("LITELLM_MODEL") or ""),
        extra={"error": str(exc)},
    )


class EpisodeRunner:
    def __init__(self, *, image: str = DEFAULT_IMAGE, root: Path | None = None):
        self.image = image
        self.root = root or repo_root()

    def run_task(
        self,
        task: TaskSpec,
        *,
        arm: str,
        seed: int,
        output_dir: Path,
    ) -> RunResult:
        if not docker_available():
            raise RuntimeError("docker is required to run agent episodes")
        enable_skills, enable_mcp = arm_flags(arm)
        episode_id = f"{task.id}-{arm}-{seed}-{uuid.uuid4().hex[:8]}"
        work = Path(tempfile.mkdtemp(prefix=f"harness-{episode_id}-"))
        workspace = work / "ws"
        workspace_src = workspace / "src"
        audit_dir = work / "audit"
        network = f"harness-{uuid.uuid4().hex[:10]}"
        gateway_name = f"gw-{uuid.uuid4().hex[:10]}"
        env = None
        output_dir.mkdir(parents=True, exist_ok=True)
        traj_path = output_dir / f"{task.id}.{arm}.{seed}.traj.json"
        try:
            copy_src(task.src, workspace_src)
            create_internal_network(network)
            if enable_mcp:
                start_gateway_container(
                    image=self.image,
                    name=gateway_name,
                    network=network,
                    workspace=workspace,
                    tickets=self.root / "evals" / "tickets",
                    mcp_config=config_dir(self.root) / "mcp.yaml",
                    policy=config_dir(self.root) / "policy.eval.yaml",
                    audit_dir=audit_dir,
                )
            skills, _skipped = scan_skills(skills_dir(self.root)) if enable_skills else ([], [])
            templates = build_agent_templates(skills=skills if enable_skills else None, enable_mcp=enable_mcp)
            run_args = agent_run_args(
                network=network,
                workspace=workspace,
                visible_tests=task.visible_tests,
                skills=skills_dir(self.root) if enable_skills else None,
                enable_mcp=enable_mcp,
            )
            env, agent = self._build_agent(
                templates=templates,
                run_args=run_args,
                step_limit=task.max_steps,
                wall_time=task.timeout_s,
                seed=seed,
                output_path=traj_path,
            )
            info = agent.run(task.prompt)
            trajectory = agent.serialize() if hasattr(agent, "serialize") else json.loads(traj_path.read_text())
            judge = run_judge(
                image=self.image,
                src=workspace_src,
                visible_tests=task.visible_tests,
                hidden_tests=task.hidden_tests,
                timeout_s=min(task.timeout_s, 90),
            )
            audit_events = load_audit(audit_dir / "mcp-audit.jsonl")
            usage = extract_usage(trajectory)
            skill = skill_activation(trajectory)
            mcp = {**summarize_audit(audit_events), "cli_mentions": mcp_cli_mentions(trajectory)}
            row = RunResult(
                task_id=task.id,
                arm=arm,
                seed=seed,
                success=bool(judge.get("passed")),
                exit_status=str((info or {}).get("exit_status") or ""),
                judge=judge,
                usage=usage,
                skill=skill,
                mcp=mcp,
                trajectory_path=traj_path if traj_path.is_file() else None,
                model_name=str(_model_config(seed)["model_name"]),
                extra={"episode_id": episode_id, "mini_info": info},
            )
            write_episode_result(output_dir, row)
            return row
        finally:
            if env is not None and hasattr(env, "cleanup"):
                try:
                    env.cleanup()
                except Exception:
                    pass
            stop_container(gateway_name)
            remove_network(network)
            # keep workspace only if MINI_SWE_HARNESS_KEEP_WORKSPACE=1
            if os.environ.get("MINI_SWE_HARNESS_KEEP_WORKSPACE") != "1":
                shutil.rmtree(work, ignore_errors=True)

    def _build_agent(self, *, templates: dict[str, str], run_args: list[str], step_limit: int, wall_time: int, seed: int, output_path: Path):
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.environments.docker import DockerEnvironment
        from minisweagent.models import get_model

        model_cfg = _model_config(seed)
        model = get_model(input_model_name=model_cfg["model_name"], config=model_cfg)
        env = DockerEnvironment(
            image=self.image,
            cwd="/workspace",
            timeout=60,
            run_args=run_args,
            env={
                "PAGER": "cat",
                "MANPAGER": "cat",
                "PYTHONPATH": "/workspace/src",
                "HOME": "/tmp",
            },
        )
        agent = DefaultAgent(
            model,
            env,
            system_template=templates["system_template"],
            instance_template=templates["instance_template"],
            step_limit=step_limit,
            wall_time_limit_seconds=wall_time,
            cost_limit=0,
            output_path=output_path,
        )
        agent.model = WallBoundModel(model, wall_s=wall_time, started_at=agent._start_time)
        return env, agent


def file_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: str(p)):
        digest.update(str(path).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()
