# mini-swe-harness

A **sidecar eval harness** on [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) v2. One native tool: **bash**. This repo does **not** fork the agent loop.

It answers one question: **do Agent Skills and MCP cause a measurable lift**, not “is this a strong coding agent?”

This is **not SWE-bench**. The 15 tasks are synthetic, auto-gradable Python/pytest items designed so a Skill or a private ticket can matter. Do not compare the 93.3% figure to anyone’s SWE-bench score.

## Results (Qwen 3.8 27B, local vLLM)

Primary metric: **hidden-judge pass rate**. 15 tasks × 4 arms × 3 seeds = **180** episodes. MCP’s jump is a **controlled capability extension** (the agent can read a private ticket), not a 2× coding upgrade.

| Arm | Skills | MCP gateway | Pass | Rate | vs baseline |
|---|---|---|---|---|---|
| baseline | off | off | 26/45 | 57.8% | — |
| skill_only | on | off | 28/45 | 62.2% | +4.4 pp |
| mcp_only | off | on | 41/45 | 91.1% | +33.3 pp |
| full | on | on | 42/45 | 93.3% | +35.6 pp |

Process (same 180 episodes; timeouts = `TimeExceeded` ∪ `Timeout`, independent of the hidden judge):

| Arm | Pass | avg steps | avg tokens | timeouts |
|---|---|---|---|---|
| baseline | 26/45 | 20.6 | 84k | 17 |
| skill_only | 28/45 | 22.8 | 108k | 19 |
| mcp_only | 41/45 | 14.5 | 53k | 4 |
| full | 42/45 | 14.2 | 55k | 8 |

skill_only is more expensive; gateway arms are shorter and time out less. Do not treat this table as a second pass ranking.

By category (n=9 each): **bash** and **mcp_opt** are 9/9 on every arm; **skill** is where Skills help (6/9 → 9/9); **mcp-required** is 0 without the gateway (spec lives only in the ticket). The 12-task slice without `mcp_opt` is the right cut for “MCP required” attribution (47.2% → 88.9% mcp_only). Breakdown: [`docs/eval-breakdown.md`](docs/eval-breakdown.md).

`mcp_opt` is a **control**: the same spec is in workspace `README.md` *and* the ticket. All four arms score 9/9; baseline never needs MCP. That is why MCP-required tasks are allowed to hide the spec.

## Skill Lift slice (6 tasks)

Separate catalog (`evals/tasks/skill_lift/`). Happy path is in the workspace;
edge rules live only in three Skills (`parse-money`, `parse-records`,
`schedule-window`). Primary comparison: **skill_only vs baseline** (paired Lift),
plus Trigger / Compliance. 6 tasks × 4 arms × 3 seeds = **72** episodes. **Do not
average with 93.3%.**

| Arm | Skills | MCP gateway | Pass | Rate | vs baseline |
|---|---|---|---|---|---|
| baseline | off | off | 7/18 | 38.9% | — |
| skill_only | on | off | 16/18 | 88.9% | +50.0 pp |
| mcp_only | off | on | 7/18 | 38.9% | +0.0 pp |
| full | on | on | 17/18 | 94.4% | +55.6 pp |

Trigger (expected `SKILL.md` in the trajectory): skill_only 18/18, baseline 0/18.
Compliance (pass AND trigger): skill_only 88.9%, full 94.4%. mcp_only matches
baseline — these tasks have no ticket. Details: `evals/results/skill_lift/summary.json`.

## MCP policy slice (2 tasks)

Separate catalog (`evals/tasks/mcp_policy/`) and policy file
(`config/policy.mcp_policy.yaml`: `get_ticket` + `list_tickets`; `workspace_fs`
denied). Frozen 180 still uses `policy.eval.yaml`. **policy-list-01** splits the
spec across two tickets (must list, then read both). **policy-deny-01** baits
`workspace_fs.read_file`; the agent must recover via tickets. 2 × 4 × 3 = 24
episodes. **Do not average with 93.3%.**

| Arm | Pass | list | deny | vs baseline |
|---|---|---|---|---|
| baseline | 0/6 | 0/3 | 0/3 | — |
| skill_only | 0/6 | 0/3 | 0/3 | +0 |
| mcp_only | 5/6 | 3/3 | 2/3 | +5 |
| full | 5/6 | 3/3 | 2/3 | +5 |

No gateway → 0. Multi-tool list+read is 3/3 with the gateway. Deny-bait still needs the ticket (2/3); audit `denied` stayed 0 (gateway arms used tickets, did not have to hit `workspace_fs`). Details: `evals/results/mcp_policy/summary.json`.

## What it adds (sidecar only)

1. **Skills, progressive disclosure.** The prompt lists `name` + `description`. The model `cat`s `SKILL.md` and `references/` when it wants them. Bodies are not dumped into the system prompt.
2. **MCP as bash.** `mcp-call` talks to an episode **policy gateway** (Streamable HTTP). Tools are never injected into `litellm.completion(tools=...)`. A CLI allowlist is **not** the security boundary — the agent has arbitrary bash.
3. **Four-arm ablation** on the synthetic catalog, plus a hidden pytest judge the agent never sees.

## Architecture

```
host runner  --LiteLLM-->  vLLM :8000
     |
     | DockerEnvironment (mini-swe-agent, unmodified loop)
     v
agent container (non-root, cap-drop ALL, read-only rootfs, only /workspace writable)
     |  bash: edit code, pytest (visible tests), cat SKILL.md, mcp-call
     v
policy gateway container (same internal network, no egress)
     |  allowlist + audit jsonl
     +-- stdio --> ticket MCP
            tickets bind-mounted here only — not on the agent disk
```

After the agent exits, a **judge** container runs hidden tests from `evals/graders/`. Visible tests are intentionally weak (often “the function exists”).

## Layout

- `.agents/skills/` — `pytest-debug`, `repo-qa`, `mcp-ticket-context`
- `src/mini_swe_harness/` — catalog, policy, MCP bridge, gateway, runner, report
- `config/policy.eval.yaml` — frozen-180 allowlist: `ticket.get_ticket` only
- `config/policy.mcp_policy.yaml` — MCP-policy catalog: `get_ticket` + `list_tickets`
- `evals/tasks/` — 15 yaml specs
- `evals/graders/` — hidden tests (never mounted into the agent)
- `evals/tickets/` — private ticket bodies (gateway only)
- `docs/design.md` — locked choices, including why not SWE-agent / full SWE-bench
- `docs/eval-breakdown.md` — per-category rates and why skill_only barely moves the total

## Setup

Python 3.11+, Docker Engine, OpenAI-compatible endpoint (this machine: vLLM on `localhost:8000`).

```bash
uv sync --extra dev --extra host
cp .env.example .env   # LITELLM_MODEL must match GET /v1/models
docker build -f docker/Dockerfile -t mini-swe-harness:local \
  --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.12-slim .
```

If Docker Hub is reachable, omit `--build-arg`. Unit tests need neither GPU nor Docker:

```bash
uv run pytest -q
```

## Eval

Do **not** pass `--force` on the published 180 episodes. Existing `evals/results/raw/*.result.json` are skipped; killing the process must not require a rerun.

```bash
# rebuild summary.json from disk (safe)
uv run mini-swe-harness summarize

# smoke one episode
sg docker -c 'uv run mini-swe-harness run --task evals/tasks/bash-fizz-01.yaml --arm baseline --seed 1'

# full catalog: 15 × 4 × 3; skips rows that already exist
sg docker -c 'uv run mini-swe-harness eval --arm all --seeds 1,2,3'
```

External (non-synthetic) subsets belong under `evals/external/` and **must not** be averaged with the synthetic catalog. A 25-id SWE-bench Lite sample is in `evals/external/summary.json`: baseline **18/25**, skill_only **20/25** (`pytest-debug` + `repo-qa` only; +2, no regressions). Failure labels: `evals/external/failure-taxonomy.md`.

## What this repo will not do

Fork mini-swe-agent, replace it with SWE-agent, inject MCP into model tool-calling, run SWE-bench Verified/Lite **full**, treat CLI allowlists as isolation, or copy private intern skills.
