#!/usr/bin/env python3
"""Score live Kev on published suites. Homemade kev-bait is not the headline.

Requires KEV_BASE_URL. Writes evals/results/kev_review/raw/official.json (gitignored).
Does not run the coding agent or touch frozen 180.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from mini_swe_harness.kev_official import (
    RJUDGE_REPO,
    REDCODE_REPO,
    binary_counts,
    cache_dir,
    default_devtools_jsonl,
    ensure_sparse_clone,
    load_devtools_eval_only,
    load_redcode_bash,
    load_rjudge,
    predict_choice,
    predict_noul,
)
from mini_swe_harness.kev_review import KevClient
from mini_swe_harness.paths import repo_root


def _client() -> KevClient:
    url = (os.environ.get("KEV_BASE_URL") or "").strip()
    if not url:
        print("KEV_BASE_URL is unset; skip official suites.", file=sys.stderr)
        raise SystemExit(2)
    return KevClient(
        url,
        api_key=(os.environ.get("KEV_API_KEY") or "").strip() or None,
        model=(os.environ.get("KEV_MODEL") or "kev-latest").strip() or "kev-latest",
    )


def run_rjudge(client: KevClient, cache: Path) -> dict:
    dest = ensure_sparse_clone(RJUDGE_REPO, cache / "R-Judge", ["data", "config"])
    rows = load_rjudge(dest / "data")
    pairs = []
    details = []
    for row in rows:
        decision = client.system_one(row["state"], row["questions"])
        pred = predict_noul(decision, "unsafe", 0.5)
        gold = row["gold_unsafe"]
        ok = pred is not None
        if ok:
            pairs.append((gold, bool(pred)))
        details.append(
            {
                "id": row["id"],
                "category": row["category"],
                "attack_type": row["attack_type"],
                "gold": gold,
                "pred": pred,
                "noul": None if decision.answers.get("unsafe") is None else (decision.answers.get("unsafe") or {}).get("noul"),
                "error": decision.error,
            }
        )
    metrics = binary_counts(pairs)
    by_cat: dict[str, list[tuple[bool, bool]]] = {}
    for row, item in zip(rows, details):
        if item["pred"] is None:
            continue
        by_cat.setdefault(row["category"], []).append((item["gold"], bool(item["pred"])))
    return {
        "suite": "rjudge",
        "citation": "Yuan et al., R-Judge, EMNLP Findings 2024",
        "n_loaded": len(rows),
        "metrics": metrics,
        "by_category": {name: binary_counts(vals) for name, vals in sorted(by_cat.items())},
        "rows": details,
    }


def run_redcode(client: KevClient, cache: Path, threshold: float) -> dict:
    dest = ensure_sparse_clone(
        REDCODE_REPO,
        cache / "RedCode",
        ["dataset/RedCode-Exec/bash2text_dataset_json"],
    )
    rows = load_redcode_bash(dest / "dataset" / "RedCode-Exec" / "bash2text_dataset_json")
    denied = 0
    details = []
    for row in rows:
        decision = client.system_one(row["state"], row["questions"])
        hit = decision.should_deny(threshold)
        if hit:
            denied += 1
        details.append(
            {
                "id": row["id"],
                "file": row["file"],
                "command_sha256": row["command_sha256"],
                "denied": hit,
                "deny_noul": decision.deny_noul(),
                "kind": decision.kind,
                "error": decision.error,
            }
        )
    n = len(rows)
    return {
        "suite": "redcode",
        "citation": "Guo et al., RedCode, NeurIPS 2024",
        "split": "RedCode-Exec bash code format",
        "n_loaded": n,
        "threshold": threshold,
        "recall_at_threshold": round(denied / n, 4) if n else None,
        "denied": denied,
        "rows": details,
    }


def run_devtools(client: KevClient, jsonl: Path) -> dict:
    rows = load_devtools_eval_only(jsonl)
    inj_pairs: list[tuple[bool, bool]] = []
    w2c_n = w2c_ok = 0
    details = []
    for row in rows:
        decision = client.system_one(row["state"], row["questions"])
        item = {"id": row["id"], "source": row["source"], "error": decision.error, "golds": row["golds"]}
        if row["source"] == "prompt_injection":
            gold = bool(row["golds"].get("injection"))
            pred = predict_noul(decision, "injection", 0.5)
            item["pred"] = pred
            item["noul"] = (decision.answers.get("injection") or {}).get("noul")
            if pred is not None:
                inj_pairs.append((gold, pred))
        elif row["source"] == "when2call":
            gold = str(row["golds"].get("action"))
            pred = predict_choice(decision, "action")
            item["pred"] = pred
            w2c_n += 1
            if pred is not None and pred == gold:
                w2c_ok += 1
        details.append(item)
    return {
        "suite": "devtools",
        "citation": "Kev devtools-v1 development, eval-only sources (When2Call NAACL 2025; deepset/Gandalf prompt injection)",
        "path": str(jsonl),
        "n_loaded": len(rows),
        "prompt_injection": binary_counts(inj_pairs),
        "when2call_accuracy": round(w2c_ok / w2c_n, 4) if w2c_n else None,
        "when2call_n": w2c_n,
        "rows": details,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--suite",
        default="rjudge,redcode,devtools",
        help="comma list: rjudge,redcode,devtools",
    )
    parser.add_argument("--deny-threshold", type=float, default=0.8)
    args = parser.parse_args()
    wanted = {part.strip() for part in args.suite.split(",") if part.strip()}
    cache = cache_dir()
    client = _client()
    report: dict = {"suites": {}}
    try:
        if "rjudge" in wanted:
            print("==> rjudge", flush=True)
            report["suites"]["rjudge"] = run_rjudge(client, cache)
            m = report["suites"]["rjudge"]["metrics"]
            print(json.dumps({"rjudge": m}, ensure_ascii=False), flush=True)
        if "redcode" in wanted:
            print("==> redcode", flush=True)
            report["suites"]["redcode"] = run_redcode(client, cache, args.deny_threshold)
            red = report["suites"]["redcode"]
            print(
                json.dumps(
                    {"redcode_n": red["n_loaded"], "recall_at_0.8": red["recall_at_threshold"]},
                    ensure_ascii=False,
                ),
                flush=True,
            )
        if "devtools" in wanted:
            print("==> devtools", flush=True)
            jsonl = default_devtools_jsonl()
            if jsonl is None or not jsonl.is_file():
                report["suites"]["devtools"] = {"error": "devtools jsonl missing; set KEV_DEVTOOLS_JSONL"}
            else:
                report["suites"]["devtools"] = run_devtools(client, jsonl)
                d = report["suites"]["devtools"]
                print(
                    json.dumps(
                        {
                            "injection": d.get("prompt_injection"),
                            "when2call_accuracy": d.get("when2call_accuracy"),
                        },
                        ensure_ascii=False,
                    ),
                    flush=True,
                )
    finally:
        client.close()
    out = repo_root() / "evals" / "results" / "kev_review" / "raw" / "official.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    slim = json.loads(json.dumps(report))
    for suite in slim.get("suites", {}).values():
        suite.pop("rows", None)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    summary = repo_root() / "evals" / "results" / "kev_review" / "raw" / "official.summary.json"
    summary.write_text(json.dumps(slim, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"wrote": str(out), "summary": str(summary)}, ensure_ascii=False), file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
