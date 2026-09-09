# Eval results

`summary.json` is the resume-facing report. Current file is the **180-run / 15-task** formal eval, including `by_category`. Rebuild from `raw/*.result.json` with:

```bash
uv run mini-swe-harness summarize
```

`raw/` holds per-episode trajectories and `*.result.json` (gitignored).

See `docs/eval-breakdown.md` for the category split, the 12-task vs 15-task totals, and skill_only analysis.
