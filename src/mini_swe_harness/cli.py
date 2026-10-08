from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from mini_swe_harness import DEFAULT_SEEDS, EVAL_ARMS, __version__
from mini_swe_harness.eval_report import build_summary, write_failures, write_summary
from mini_swe_harness.paths import evals_dir, repo_root
from mini_swe_harness.runner import (
    EpisodeRunner,
    failed_result,
    file_sha256,
    load_all_results,
    load_episode_result,
    write_episode_result,
)
from mini_swe_harness.tasks import load_all_tasks, load_task


def _load_env() -> None:
    env_path = repo_root() / ".env"
    if env_path.is_file():
        load_dotenv(env_path)


def cmd_eval(args: argparse.Namespace) -> int:
    _load_env()
    root = repo_root()
    tasks = load_all_tasks(root, tasks_dir=Path(args.tasks_dir) if args.tasks_dir else None)
    if args.task:
        tasks = [task for task in tasks if task.id in set(args.task)]
        if not tasks:
            raise SystemExit("no matching tasks")
    arms = list(EVAL_ARMS) if args.arm == "all" else [args.arm]
    seeds = tuple(int(s) for s in args.seeds.split(","))
    runner = EpisodeRunner(image=args.image, root=root)
    out_dir = Path(args.output)
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    planned = [(seed, task, arm) for seed in seeds for task in tasks for arm in arms]
    rows = []
    for seed, task, arm in planned:
        print(f"==> {task.id} arm={arm} seed={seed}", flush=True)
        existing = None if args.force else load_episode_result(raw_dir, task.id, arm, seed)
        if existing is not None:
            print(f"skip existing {task.id}/{arm}/{seed} success={existing.success}", flush=True)
            rows.append(existing)
        else:
            try:
                rows.append(runner.run_task(task, arm=arm, seed=seed, output_dir=raw_dir))
            except Exception as exc:
                print(f"episode error {task.id}/{arm}/{seed}: {type(exc).__name__}: {exc}", flush=True)
                row = failed_result(task.id, arm, seed, exc)
                write_episode_result(raw_dir, row)
                rows.append(row)
        last = rows[-1]
        (out_dir / "eval-progress.json").write_text(
            json.dumps(
                {
                    "planned": len(planned),
                    "done": len(rows),
                    "success": sum(1 for row in rows if row.success),
                    "last": {
                        "task_id": last.task_id,
                        "arm": last.arm,
                        "seed": last.seed,
                        "success": last.success,
                        "exit_status": last.exit_status,
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    summary = _emit_summary(
        root,
        out_dir,
        image=args.image,
        tasks_dir=Path(args.tasks_dir) if args.tasks_dir else None,
    )
    print(json.dumps(summary.get("arms"), indent=2))
    return 0


def _taskset_hash(root: Path) -> str:
    hashed = []
    for folder in (root / "evals" / "tasks", root / "evals" / "fixtures", root / "evals" / "graders", root / ".agents" / "skills"):
        hashed.extend([path for path in folder.rglob("*") if path.is_file()])
    return file_sha256(hashed)


def _emit_summary(
    root: Path,
    out_dir: Path,
    *,
    image: str,
    tasks_dir: Path | None = None,
) -> dict:
    raw_dir = out_dir / "raw"
    rows = load_all_results(raw_dir)
    tasks = load_all_tasks(root, tasks_dir=tasks_dir)
    categories = {task.id: task.category for task in tasks}
    expected_skills = {t.id: t.expected_skill for t in tasks if t.expected_skill}
    summary = build_summary(
        rows,
        model=os.environ.get("LITELLM_MODEL", "unknown"),
        task_categories=categories,
        task_expected_skills=expected_skills or None,
        extra={
            "harness_version": __version__,
            "image": image,
            "seeds": sorted({row.seed for row in rows}),
            "taskset_sha256": _taskset_hash(root),
        },
    )
    write_summary(summary, out_dir / "summary.json")
    write_failures(rows, out_dir / "failures.md")
    return summary


def cmd_run(args: argparse.Namespace) -> int:
    _load_env()
    task = load_task(Path(args.task))
    runner = EpisodeRunner(image=args.image)
    result = runner.run_task(task, arm=args.arm, seed=args.seed, output_dir=Path(args.output) / "raw")
    print(json.dumps({"success": result.success, "exit_status": result.exit_status, "mcp": result.mcp}, indent=2))
    return 0 if result.success else 1


def cmd_summarize(args: argparse.Namespace) -> int:
    _load_env()
    summary = _emit_summary(
        repo_root(),
        Path(args.output),
        image=args.image,
        tasks_dir=Path(args.tasks_dir) if args.tasks_dir else None,
    )
    print(json.dumps({"n_runs": summary.get("n_runs"), "arms": summary.get("arms"), "by_category": summary.get("by_category")}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mini-swe-harness")
    sub = parser.add_subparsers(dest="cmd", required=True)

    eval_p = sub.add_parser("eval", help="Run the four-arm synthetic eval")
    eval_p.add_argument("--arm", default="all", choices=["all", *EVAL_ARMS])
    eval_p.add_argument("--seeds", default=",".join(str(s) for s in DEFAULT_SEEDS))
    eval_p.add_argument("--task", action="append", default=[])
    eval_p.add_argument("--image", default=os.environ.get("MINI_SWE_HARNESS_IMAGE", "mini-swe-harness:local"))
    eval_p.add_argument("--output", default=str(evals_dir() / "results"))
    eval_p.add_argument(
        "--force",
        action="store_true",
        help="Re-run episodes even if raw/*.result.json already exists",
    )
    eval_p.add_argument("--tasks-dir", default=None)
    eval_p.set_defaults(func=cmd_eval)

    run_p = sub.add_parser("run", help="Run a single task yaml")
    run_p.add_argument("--task", required=True)
    run_p.add_argument("--arm", default="full", choices=list(EVAL_ARMS))
    run_p.add_argument("--seed", type=int, default=1)
    run_p.add_argument("--image", default=os.environ.get("MINI_SWE_HARNESS_IMAGE", "mini-swe-harness:local"))
    run_p.add_argument("--output", default=str(evals_dir() / "results"))
    run_p.set_defaults(func=cmd_run)

    sum_p = sub.add_parser("summarize", help="Rebuild summary.json from raw/*.result.json")
    sum_p.add_argument("--image", default=os.environ.get("MINI_SWE_HARNESS_IMAGE", "mini-swe-harness:local"))
    sum_p.add_argument("--output", default=str(evals_dir() / "results"))
    sum_p.add_argument("--tasks-dir", default=None)
    sum_p.set_defaults(func=cmd_summarize)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
