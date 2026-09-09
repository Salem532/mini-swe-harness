# mini-swe-harness 移交说明

给后续 agent / 协作者：这是仓库现状、架构、已完成工作、正式评测数字和坑。不要把本项目写成 SWE-bench。不要改 mini-swe-agent 上游循环。

- 仓库根目录：`/home/liwanrong/code/bilina-dev`（不要把代码嵌进 `mini-swe-harness/` 子目录）
- 包名：`mini-swe-harness`（`src/mini_swe_harness/`），版本 `0.1.0`
- 作者：李婉榕
- 本文对应日期：2026-09-08
- 正式结果文件：`evals/results/summary.json`（**15 题 × 4 臂 × 3 seeds = 180 runs** 已齐，含 `by_category`；12 题切片仍用于 MCP 归因）
- 类别拆解与 skill_only 分析：`docs/eval-breakdown.md`

---

## 项目是什么 / 不是什么

**是：** 挂在 [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) v2 外面的 **sidecar harness**。上游仍是「一个 bash 工具」的 `DefaultAgent`。本仓库补上：

1. Agent Skills 渐进披露（prompt 里只有 name + description，模型自己 `cat SKILL.md`）
2. MCP 走 bash CLI（`mcp-call`）→ episode 级 **策略网关**（Streamable HTTP），不是模型 native tool
3. **15** 道自己出的合成 Python/pytest 题（3 skill / 3 mcp / 3 skill_mcp / 3 bash / 3 **mcp_opt**），四臂消融 + hidden judge。`summary.json` 是 180 runs；讲 MCP 增益时要同时报 12 题切片（`mcp_opt` 四臂满分会稀释合计）

**不是：** SWE-bench。SWE-bench 是真实 GitHub issue、真实仓库、官方题集。这里是可控小任务，用来归因 Skills / MCP，数字不能和别人的 SWE-bench 分数比，简历/报告里必须写清。

设计里明确不做：fork mini-swe-agent、把 MCP 注入 `litellm.completion(tools=...)`、跑 SWE-bench 全量、抄内部 intern/Lumina 技能、把 CLI 侧 allowlist 当安全边界。

---

## 亮点（给后续 agent 优先保留的叙事）

这些是项目真正站得住的点，比「full 91%」更重要：

1. **Sidecar，不 fork。** 调用 `DefaultAgent` + `DockerEnvironment` + `LitellmModel`。改循环会和上游 100 行 agent 分叉。
2. **四臂消融，可归因。** `baseline` / `skill_only` / `mcp_only` / `full`。12 题合计里 Skills 几乎没拉动（+5.6 pp），真正拉开的是 MCP；**按类别看** Skills 在 `skill` 类是 +33 pp，被 mcp 题平均掉了。`mcp_opt` 四臂 9/9，证明规格在 README 里时不需要 MCP（见 `docs/eval-breakdown.md`）。
3. **网关才是安全边界。** agent 有任意 bash，`mcp-call` 里写 allowlist 可被绕过。ticket 文件只 bind 到网关容器。评测策略 `config/policy.eval.yaml` 只放行 `ticket.get_ticket`。
4. **Hidden judge。** 可见测试故意很弱（例如函数存在）；对错看 `evals/graders/`，不挂进 agent 容器。
5. **MCP 是「受控能力扩展」不是「同一题换个 API」。** 若干题的规格只在 `evals/tickets/TICKET-*.md` 里，baseline / skill_only 读不到。设计如此，报告时必须标明，否则 89%/92% 会被理解成模型变聪明了两倍。`mcp_opt` 题把同一份规格同时放进 workspace `README.md` 和 ticket，MCP 不是刚需。
6. **评测可恢复。** 每条 episode 立刻写 `raw/{task}.{arm}.{seed}.result.json` 和 `raw/episodes.jsonl`；已有结果默认 skip；`--force` 才重跑。中途杀进程不应再丢 judge。
7. **墙钟绑定 LLM HTTP。** `WallBoundModel` 把每次 LiteLLM `timeout` 设成剩余墙钟，超时映射为 `TimeExceeded`，避免卡住的 vLLM 请求拖过 `timeout_s`。

---

## 架构

```
host runner  --LiteLLM-->  vLLM :8000（本机已有，模型 id qwen3.8-27b）
     |
     | DockerEnvironment：每条 episode 起一个 agent 容器，结束后删
     v
agent 容器（非 root、cap-drop ALL、read-only rootfs、只写 /workspace）
     |  bash：改代码、pytest 可见测试、cat SKILL.md、mcp-call
     v
gateway 容器（同网段 alias=gateway，无外网）
     |  策略过滤 + 审计 jsonl
     +-- stdio --> ticket MCP（TICKET_ROOT=/tickets，文件不进 agent 盘）
```

关键约束：

| 点 | 实现 |
|---|---|
| Agent 工具 | mini-swe-agent v2 **只有 bash**；MCP 不进模型 tools |
| 网关工具名 | 线上 `{server}__{tool}`，例如 `ticket__get_ticket`；CLI 写成 `mcp-call call ticket get_ticket --args '...'` |
| Docker `--user` | `host_docker_user()` = `os.getuid():os.getgid()`。用 `sg docker` 跑时 gid 会变成 docker 组。不要写死 `1000:1000`，否则 bind mount 会 Permission denied / TimeExceeded |
| 网络 | `--internal` 的 `harness-*`；地址池耗尽时 `docker network prune`（runner 里已对 subnet 耗尽做一次 retry） |
| 镜像 | `mini-swe-harness:local`（`docker/Dockerfile`）。**网关跑在镜像里的已安装包**，改 `src/` 后必须重建镜像，host 上的 editable install 不会进网关 |
| 模型 | `.env`：`LITELLM_MODEL=openai/qwen3.8-27b`，`OPENAI_API_BASE=http://127.0.0.1:8000/v1`，`MSWEA_COST_TRACKING=ignore_errors`。vLLM 不是本仓库启动的 |
| 墙钟 | 默认 `LITELLM_TIMEOUT=90`、`LITELLM_NUM_RETRIES=0`；每次 `query` 再取 `min(该值, 剩余墙钟)` |

四臂开关（`arm_flags`）：

| arm | Skills | MCP 网关 |
|---|---|---|
| baseline | 否 | 否 |
| skill_only | 是 | 否 |
| mcp_only | 否 | 是 |
| full | 是 | 是 |

---

## 目录

| 路径 | 内容 |
|---|---|
| `src/mini_swe_harness/` | CLI、runner、gateway、mcp_bridge、policy、metrics、eval_report |
| `config/mcp.yaml` | 上游：`ticket`（stdio）+ `workspace_fs`（stdio，评测策略里不开） |
| `config/policy.eval.yaml` | 评测：只允许 `ticket.get_ticket` |
| `.agents/skills/` | `pytest-debug`、`repo-qa`、`mcp-ticket-context` |
| `evals/tasks/` | 15 个 yaml（3 skill / 3 mcp / 3 skill_mcp / 3 bash / 3 mcp_opt） |
| `evals/fixtures/` | 可见源码 + 可见测试。`mcp_opt` 的规格在 fixture `src/README.md` |
| `evals/graders/` | 隐藏测试 |
| `evals/tickets/` | MCP 私有工单正文（mcp_opt 与 README 同文） |
| `evals/results/summary.json` | 正式报告（180，含 `by_category`） |
| `evals/results/raw/` | `*.traj.json` + `*.result.json`（gitignored） |
| `docker/Dockerfile` | agent / gateway / judge 共用镜像 |
| `docs/design.md` | 设计锁定项 |
| `docs/eval-breakdown.md` | 按类拆解 + skill_only 轨迹分析 |
| `tests/` | 单元测试（不需要 GPU） |

15 个已评测 task id：`bash-clamp-01`、`bash-fizz-01`、`bash-slug-01`、`mcp-discount-01`、`mcp-hours-01`、`mcp-tax-01`、`skill-empty-01`、`skill-encoding-01`、`skill-pytest-01`、`skillmcp-invoice-01`、`skillmcp-records-01`、`skillmcp-window-01`、`mcpopt-round-01`（TICKET-7001）、`mcpopt-title-01`（TICKET-7002）、`mcpopt-initials-01`（TICKET-7003）。

---

## 已经做成的工程

- Python 包 + `uv` 可编辑安装；CLI：`mini-swe-harness eval|run|summarize`、`mcp-call`
- Skills 扫描与 frontmatter 校验；无效 skill 跳过
- 策略网关 + 审计；`mcp-call` 只打网关
- Docker episode：内部网、资源限制、judge 另起容器跑 hidden pytest
- 正式评测循环：12 × 4 × 3 = 144，加上 mcp_opt 36 条后磁盘上是 **180**；`summarize` 从全部 `*.result.json` 重建 summary（含 `by_category`）
- **逐条落盘：** `write_episode_result`；`eval` 默认 skip 已有 `result.json`；`--force` 重跑；summary 从磁盘汇总（只跑一个 arm 不会把另外三臂从 summary 里抹掉）
- 单条 episode 异常会记失败 stub 并继续，不中断整场
- LiteLLM：默认 timeout 90s / retries 0；`WallBoundModel` 按剩余墙钟截断单次 HTTP
- 题库：`mcp_opt` 三题（规格在 README **和** ticket）

单元测试：`uv run pytest -q`。

---

## 评测过程中修过的坑（后续不要再踩）

### 1. MCP stdio 接到错误的 Client 类型（导致正式数字里一度 `ok=0, error=17`）

`mcp.Client` 只接受：内存 Server、HTTP URL、或 Transport。评测网关用 **stdio 子进程** 拉 ticket 时，曾把 `StdioServerParameters` 直接塞进 `Client(...)`，报错：

`StdioServerParameters object does not support the asynchronous context manager protocol`

修复：`mcp_bridge._client_target` 对 stdio 使用 `stdio_client(params)`。单元测试：`tests/test_mcp_bridge.py::test_stdio_ticket_roundtrip`、`tests/test_gateway.py::test_gateway_stdio_get_ticket`。

**改完必须 `docker build -f docker/Dockerfile -t mini-swe-harness:local`（本机曾用 DaoCloud 的 `python:3.12-slim` 前缀）。** 然后 **只重跑了 `mcp_only` 和 `full`（72 条）**。baseline / skill_only 未重跑（它们本来就没有网关）。

修完后 MCP：`error=0`；`mcp_only` ok=17，`full` ok=15。不是每条 episode 都会调 MCP（纯 bash/skill 题可以不调）。

### 2. Judge 只在内存里，杀进程就丢

第一场 144 跑到一半卡在 `mcp-tax-01` × `full` × seed=2（LiteLLM 等 vLLM 超时重试；当时墙钟 180s 只在每步开始时检查）。杀进程后前 71 条轨迹还在、hidden judge 没落盘。已改为每条立刻写 `result.json`。缺的 71 条后来补跑齐了。现在 `WallBoundModel` 会把进行中的 HTTP timeout 绑到剩余墙钟。

### 3. 其它运维

- 必须 `sg docker`（或等价 docker 组）才能用 socket
- `harness-*` 网络堆满会 `all predefined address pools have been fully subnetted` → `docker network prune -f`
- 历史日志（gitignore）：`evals/results/eval-run-backfill.log`、`evals/results/eval-run-mcp-rerun.log`、`evals/results/eval-run-mcpopt.log`

---

## 正式结果（`evals/results/summary.json`）

- 模型：`openai/qwen3.8-27b`（本机 vLLM GPTQ Qwen3.8-27B）
- 主指标：`hidden_judge_pass_rate`
- `n_runs=180`，每臂 n=45，seeds=1,2,3，`n_tasks=15`
- 镜像：`mini-swe-harness:local`
- 12 题切片（归因 MCP 刚需题）不要和 15 题合计混用

15 题合计：

| Arm | 通过 | 通过率 | 95% Wilson CI | vs baseline（paired） | MCP audit |
|---|---|---|---|---|---|
| baseline | 26/45 | 57.8% | 43.3–71.0% | — | ok=0 error=0 |
| skill_only | 28/45 | 62.2% | 47.6–74.9% | **+4.4 pp** | ok=0 error=0 |
| mcp_only | 41/45 | 91.1% | 79.3–96.5% | **+33.3 pp** | ok=24 error=0 |
| full | 42/45 | 93.3% | 82.1–97.7% | **+35.6 pp** | ok=17 error=0 |

12 题切片（无 mcp_opt）：baseline 17/36 (47.2%)、skill_only 19/36 (52.8%, +5.6 pp)、mcp_only 32/36 (88.9%, +41.7 pp)、full 33/36 (91.7%, +44.4 pp)。

按类别（每格 n=9）见 `docs/eval-breakdown.md`。一句话：bash / mcp_opt 全满分；skill 类 Skills 有效（6/9 → 9/9）；mcp 类没网关就是 0；skill_mcp 上 skill_only 更差、mcp_only 满分。

解读（写报告时必须带上）：

- MCP 大涨主要来自「能读到私有 ticket」，不是通用编码能力翻倍。`mcp_opt` 四臂 9/9，baseline 不调 MCP 也能过。
- skill_only 合计几乎没增益，是因为一半刚需题没有钥匙；在 `skill-empty-01` 上 Skills 是有效的。
- baseline / skill_only 的 12 题是 stdio 修复 **之前**；mcp_only / full 的 12 题是修复 **之后** 重跑。mcp_opt 36 条是 2026-09-08 补跑。
- 不要对外说 SWE-bench；不要只报 93% 不报 baseline 和任务设计。

---

## 常用命令

```bash
uv sync --extra dev --extra host
uv run pytest -q

# 本机 docker.io 不通时：
docker build -f docker/Dockerfile -t mini-swe-harness:local \
  --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.12-slim .

# 需要 docker 组：
sg docker -c 'uv run mini-swe-harness run --task evals/tasks/bash-fizz-01.yaml --arm baseline --seed 1'

# 15 题 180；已有 result.json 会 skip
sg docker -c 'uv run mini-swe-harness eval --arm all --seeds 1,2,3'

# 只重建 summary（不跑 episode）
uv run mini-swe-harness summarize

# 重跑某一臂
sg docker -c 'uv run mini-swe-harness eval --arm full --seeds 1,2,3 --force'
```

墙钟相关默认已在 runner 里：`LITELLM_TIMEOUT=90`、`LITELLM_NUM_RETRIES=0`。仍可用环境变量覆盖。

---

## 尚未做（可选）

- git commit（用户说全部完成后再看；本机还缺 `user.name` / `user.email`）
- GitHub 私有仓库（若需要公开/私有托管）
- **不要**默认去跑 SWE-bench 或改 resume tex，除非用户明确要求

用户约束：对话用中文；不要主动 git commit / push，除非用户明确要求；不要改 `/etc/docker`。
