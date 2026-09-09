# External SWE-bench Lite subset (P1)

Sampled **25** SWE-bench Lite `test` instance IDs (`sample_seed=20260908`) are in `instance_ids.json`.

**Result:** baseline **18/25 resolved (72%)** by official `swebench.harness.run_evaluation` (swebench 5.0.2, dataset `SWE-bench/SWE-bench_Lite`). Agent wall 4.32 h; official eval 0.25 h. One empty patch (`django__django-13265`, context window). Infra failures: 0.

This is a **25-id sample**, not SWE-bench Lite full. Do not average with the synthetic 93.3%. `full` arm was not run.

Harness: upstream `mini-extra swebench` (mini-swe-agent 2.4.6) for patches, then official resolve. Not this repo’s ticket MCP gateway.

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

Official report: `evals/external/runs/lite25-baseline/openai__qwen3.8-27b.lite25-baseline.json`. Summary: `evals/external/summary.json`.
