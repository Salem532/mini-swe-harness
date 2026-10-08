# External SWE-bench Lite subset (P1)

Sampled **25** SWE-bench Lite `test` instance IDs (`sample_seed=20260908`) are in `instance_ids.json`.

**Result:** official `swebench.harness.run_evaluation` (swebench 5.0.2, dataset `SWE-bench/SWE-bench_Lite`): baseline **18/25 resolved (72%)**; skill_only **20/25 (80%)**. Paired: +2 (`django__django-13265`, `scikit-learn__scikit-learn-10508`), 0 regressions. Baseline empty patch `django__django-13265` (context window) resolved under skill_only. Infra failures: 0.

This is a **25-id sample**, not SWE-bench Lite full. Do not average with the synthetic catalog. **skill_only** uses a SWE-bench skill subset (`pytest-debug` + `repo-qa` only; no ticket MCP, no Skill Lift skills).

Harness: upstream `mini-extra swebench` (mini-swe-agent) for patches, then official resolve. Not this repo’s ticket MCP gateway.

```bash
# agent
FILTER=$(python3 -c "import json,re; ids=json.load(open('evals/external/instance_ids.json'))['instance_ids']; print('^(' + '|'.join(re.escape(i) for i in ids) + ')$')")

sg docker -c "uv run mini-extra swebench \
  --model openai/qwen3.8-27b \
  --subset lite --split test \
  --filter '$FILTER' \
  --workers 1 \
  -c swebench.yaml \
  -c evals/external/local-model.yaml \
  -c agent.cost_limit=999999 \
  --output evals/external/runs/lite25-baseline"

# official resolve
IDS=$(python3 -c "import json; print(' '.join(json.load(open('evals/external/instance_ids.json'))['instance_ids']))")
sg docker -c "uv run python -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test \
  -i $IDS \
  -p evals/external/runs/lite25-baseline/preds.json \
  --max_workers 1 -id lite25-baseline \
  --report_dir evals/external/runs/lite25-baseline \
  -t 1800"
```

```bash
# skill_only agent (resume: omit --redo-existing)
FILTER=$(python3 -c "import json,re; ids=json.load(open('evals/external/instance_ids.json'))['instance_ids']; print('^(' + '|'.join(re.escape(i) for i in ids) + ')$')")
IDS=$(python3 -c "import json; print(' '.join(json.load(open('evals/external/instance_ids.json'))['instance_ids']))")
.venv/bin/python evals/external/render_skill_only_config.py
sg docker -c "uv run mini-extra swebench \
  --model openai/qwen3.8-27b \
  --subset lite --split test \
  --filter '$FILTER' \
  --workers 1 \
  -c swebench.yaml \
  -c evals/external/local-model.yaml \
  -c evals/external/skill-only.generated.yaml \
  -c agent.cost_limit=999999 \
  --output evals/external/runs/lite25-skill-only"

# official resolve (preds from skill_only, never baseline preds)
sg docker -c "uv run python -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test \
  -i $IDS \
  -p evals/external/runs/lite25-skill-only/preds.json \
  --max_workers 1 -id lite25-skill-only \
  --report_dir evals/external/runs/lite25-skill-only \
  -t 1800"
```

Official report: `evals/external/runs/lite25-baseline/openai__qwen3.8-27b.lite25-baseline.json`. Summary: `evals/external/summary.json`.
