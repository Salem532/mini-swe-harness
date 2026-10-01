# Design notes

Condensed from the 2026-08-18 handoff and the 2026-08-21 grilling session.

## Locked direction

Approach B: sidecar harness. Call mini-swe-agent v2 via its Python API (`DefaultAgent` + `DockerEnvironment` + `LitellmModel`). Do not edit the upstream loop.

Bash action format: keep v2 default **single bash tool-call**. MCP is not a native tool.

Repo root: this directory. Skills live at `.agents/skills/` (Agent Skills discovery path).

## Isolation

Each episode:

1. Internal Docker network (no egress).
2. Agent container: non-root uid 1000, `cap-drop ALL`, `no-new-privileges`, read-only rootfs, tmpfs `/tmp`, resource limits. Writable mount is `/workspace` (copy of fixture `src/`). Visible tests are a **separate read-only** mount at `/workspace/tests`.
3. Gateway container: same hardening. Ticket files mounted only here. Exposes Streamable HTTP MCP. Starts upstream stdio servers with a **short-lived session per list/call**.
4. Judge container: started after the agent exits. Hidden tests only. `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

## MCP

`config/mcp.yaml` lists `ticket` and `workspace_fs` (Python stdio servers in this repo). HTTP/Streamable HTTP specs are also valid (`transport: http`, `url:`).

Eval uses `config/policy.eval.yaml`: only `ticket.get_ticket`. That is a **controlled capability extension** — the spec is not in the workspace. Baseline/Skill-only arms cannot read ticket files. This is labeled as such; it is not “the same task with a nicer API”.

Gateway tool names: `{server}__{tool}`. `mcp-call` maps CLI `(server, tool)` onto that.

Denied calls: tool result `is_error` + CLI exit 2, so the model can recover. Audit JSONL is the source of MCP metrics.

## Skills

Frontmatter follows [agentskills.io](https://agentskills.io): `name` matches the directory, lowercase hyphenated, description ≤1024 and must say **what** and **when**. Invalid skills are skipped.

Startup catalog is name + description + `cat` path. Bodies and `references/` stay off the system/instance templates (enforced by unit tests).

v1 skills: `pytest-debug` (script + traceback note), `repo-qa` (verification matrix), `mcp-ticket-context` (tool contract).

## Eval

15 synthetic Python/pytest tasks, 3 per category (`skill`, `mcp`, `skill_mcp`, `bash`, `mcp_opt`). `mcp_opt` puts the same spec in workspace `README.md` **and** the ticket; MCP is optional. Formal numbers are 180 runs; keep the 12-task slice when attributing MCP-required gains. Arms: baseline / skill_only / mcp_only / full. Seeds 1,2,3. Timeout 180s, 30 steps. Per-category rates: `docs/eval-breakdown.md`.

Wall-clock: `WallBoundModel` sets each LiteLLM HTTP `timeout` to remaining episode time so a hung request cannot outlive `timeout_s`.

Main metric: hidden judge pass rate, with Wilson CI and paired deltas vs baseline on `(task, seed)` pairs.

Local model: LiteLLM → `OPENAI_API_BASE` (vLLM). `MSWEA_COST_TRACKING=ignore_errors` because local ids are not in the LiteLLM registry. Token counts come from trajectory `response.usage` when present.

## Why not swap in SWE-agent

The claim is **sidecar**: same 100-line bash loop, Skills loaded by `cat`, MCP only through `mcp-call` + gateway. SWE-agent is a different product (ACI, extra tools, its own eval story). Using it as the default runner would make the four-arm numbers incomparable and throw away the “we did not fork mini-swe-agent” line. Referenced peers are ablation harnesses (AgentAblate, skill-eval-harness, Caliper), not OpenHands.

## Why not full SWE-bench

- Real GitHub issues do not use this repo’s ticket MCP. A 35 pp MCP lift on synthetic tasks **cannot** be restated as a SWE-bench score.
- Verified/Lite full × even one arm is days of GPU and is a leaderboard run, which this project is not.
- If an external subset is run, it is a **smoke that the loop finishes on someone else’s instances**, reported in `evals/external/`, never in the same sentence as 93.3%. This host ran a 25-id Lite baseline (`evals/external/summary.json`).

## Explicit non-goals

SWE-bench full, native MCP tool injection, old SSE, MCP prompts/resources, multimedia, a complete bash allowlist, copying private third-party skills, `--force` reruns of the published 180 synthetic episodes.
