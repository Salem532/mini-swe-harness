# mini-swe-harness 第二阶段交接（给另一台 server）

发给在 `/home/liwanrong/code/bilina-dev` 上继续干活的 agent。  
日期：2026-09-08  
作者侧约束：中文沟通；**不要 git commit / push**（除非用户当面要求）；不要改 `/etc/docker`；不要改用户简历 tex。

跑完后把本文 **第 8 节清单** 发回给用户（用户会转给简历这边的 agent）。

---

## 0. 你是谁、仓库在哪

- 仓库：**`/home/liwanrong/code/bilina-dev`**（代码就在根目录，不要嵌进 `mini-swe-harness/` 子目录）
- 包名：`mini-swe-harness`，`src/mini_swe_harness/`
- 上一阶段说明（已完成工作、180 runs、踩过的坑）：仓库里应已有或用户会附上 `HANDOFF.md`（2026-09-08）。**先读它，再动手。**
- 上游循环：[mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) v2 的 `DefaultAgent` + `DockerEnvironment` + `LitellmModel`。本仓是 **sidecar**。

模型（不要换，除非 vLLM 挂了）：

- `LITELLM_MODEL=openai/qwen3.8-27b`
- `OPENAI_API_BASE=http://127.0.0.1:8000/v1`
- 本机 vLLM 不由本仓库启动

---

## 1. 这一阶段的目的（和简历的关系）

简历已经写入自建 15 题四臂消融（57.8% → 93.3%、skill 类 6/9 → 9/9、MCP 刚需题无网关为 0）。**这些数字不要作废、不要重跑刷分。**

用户担心项目「看起来 low」。结论已经定了：

- **不要**换成 SWE-agent（卖点是 sidecar + bash-only + Skill 渐进加载 + MCP 网关，换底座等于推倒）
- **不要**把本项目宣传成 SWE-bench
- 真正缺的是：README 写得像评测仓，以及（有算力再做）一份 **不是自己出的题** 的外部子集

同类参照：AgentAblate、skill-eval-harness、Caliper。不是 OpenHands / SWE-bench 榜。

---

## 2. 禁止事项（违反就停）

1. **禁止** fork / 修改 mini-swe-agent 上游循环。  
2. **禁止** 换成 SWE-agent 当默认 runner。  
3. **禁止** 把 MCP 接到 `litellm.completion(tools=...)`。  
4. **禁止** `--force` 重跑已有 15 题 × 四臂 × 3 seed（`evals/results/raw/` 里 180 条）。`summarize` 可以，重跑不可以。  
5. **禁止** 为了让 MCP 更好看去改那 15 道题的规格/ticket/judge。  
6. **禁止** 跑 SWE-bench Verified / Lite **全量**，禁止四臂 × 3 seed 打在外部题上。  
7. **禁止** 把外部子集分数和 93.3% 写进同一句话，或声称「SWE-bench 93%」。  
8. **禁止** 默认 `git commit` / 建 GitHub / 改 resume。  
9. 改 `src/` 后若动了网关路径：**必须** `docker build` 重建 `mini-swe-harness:local`（editable install 进不了网关容器）。

---

## 3. 已完成、直接当事实用

来自上一阶段 `HANDOFF.md`，不要再验证一遍 180 runs：

| 项 | 值 |
|---|---|
| 模型 | Qwen 3.8 27B（vLLM GPTQ） |
| 自建题 | 15 题（3 skill / 3 mcp / 3 skill_mcp / 3 bash / 3 mcp_opt） |
| 规模 | 15 × 4 臂 × 3 seed = **180** |
| baseline | 26/45 = **57.8%** |
| skill_only | 28/45 = **62.2%**（+4.4 pp） |
| mcp_only | 41/45 = **91.1%**（+33.3 pp） |
| full | 42/45 = **93.3%**（+35.6 pp） |
| skill 类 | Skills：6/9 → 9/9 |
| mcp 刚需 | 无网关 = 0（规格只在 ticket） |
| mcp_opt | 四臂 9/9（规格同时在 README） |

解读（写任何文档都要带）：MCP 大涨是 **受控能力扩展**（读到私有 ticket），不是通编翻倍。

工程上已有：策略网关、hidden judge、逐条落盘、`WallBoundModel`、stdio MCP 修复。运维：`sg docker`；网络池满则 `docker network prune -f`。

---

## 4. 本阶段任务（按优先级，做完 P0 就可以停）

### P0 — 必须：把 README / 设计说明写成评测仓（不需要 GPU）

把仓库门面改成「回答 Skill/MCP 有没有因果提升」，不要写成「一个很强的编码 Agent」。

README 至少包含：

1. 一句话：sidecar harness on mini-swe-agent；bash-only；不 fork。  
2. 四臂表（上表数字）+ 按类一句话（bash/mcp_opt 满分；skill 类 Skills 有效；mcp 类无网关为 0）。  
3. **明确：不是 SWE-bench**；15 题是自建可控任务，用来归因。  
4. 架构：agent 容器 / 网关容器 / ticket 不进 agent 盘 / hidden judge。  
5. 渐进加载：prompt 只有 name+description，模型 `cat SKILL.md`。  
6. MCP：`mcp-call` → 网关，不是 native tools；CLI allowlist 不是安全边界。  
7. 怎么跑单测、怎么 `eval`（并写清：已有 result 会 skip，不要 `--force` 那 180 条）。  
8. 指向 `docs/eval-breakdown.md`、`docs/design.md`。

可把 `docs/design.md` 补一节「为什么不换 SWE-agent / 为什么不上 SWE-bench 全量」。

验收：陌生人只看 README 不会以为这是 SWE-bench 93% 的 Agent。

### P1 — 有算力再做：外部子集（不是自己出的题）

目的：**证明循环在非自造题上能跑完、能出分**，不是再证明 MCP 涨 35 pp。

SWE-bench 真实 issue **用不到** 本仓的 ticket MCP。因此：

- **只跑 1 臂或最多 2 臂**，**1 个 seed**  
- **25 题即可**（最多 50；禁止 300/500 全量）  
- 优先 **SWE-bench Lite 或 Verified 的固定抽样**，`instance_id` 列表写入 `evals/external/instance_ids.json`（抽样随机种子写死，例如 `seed=20260908`）  
- 推荐臂：  
  - 必跑：`baseline`（Skills 关、MCP 网关关）= 纯 mini-swe-agent bash  
  - 可选：`full`（Skills 开；MCP 开了也几乎帮不上 SWE-bench，允许 Skills 掉点）  
- **禁止** 在外部题上跑 `skill_only` / `mcp_only` / 3 个 seed  

接入方式（选成本最低的，不要为了「接进本仓 yaml」耗一周）：

**优先 A：** 用 **上游 mini-swe-agent 自带的 SWE-bench 评测入口**（或官方 SWE-bench harness + 同一 vLLM 端点），本仓只负责记录命令、instance 列表、原始输出路径和一份 `evals/external/summary.json`。

**其次 B：** Harbor / 官方 docker 评测。同样只抽 25 题。

不要把 SWE-bench 仓库硬塞进 `evals/tickets/` 去配合现有网关。那是造假。

`evals/external/summary.json` 最小字段：

```json
{
  "benchmark": "swe-bench-lite|verified",
  "n_instances": 25,
  "instance_ids": ["..."],
  "sample_seed": 20260908,
  "model": "openai/qwen3.8-27b",
  "arms": {
    "baseline": {"n": 25, "resolved": 0, "resolve_rate": 0.0, "notes": ""},
    "full": {"n": 25, "resolved": 0, "resolve_rate": 0.0, "notes": "optional"}
  },
  "wall_hours": 0,
  "harness": "mini-swe-agent official eval | harbor | other（写清）"
}
```

**分数低也要交。** Qwen 27B 在子集上个位数或十几都正常。禁止丢掉失败 instance 只报成功的。

若官方评测装不上 / 磁盘或时间不够：在 `evals/external/SKIPPED.md` 写原因，**停在 P0**，不要改 15 题凑数。

时间盒：P1 墙钟 **不超过 24 小时**；超时就停，交已跑完的 instance。

### P2 — 可选、低优先级：1–3 道「题面可见、MCP 加速」的新题

不要动旧 15 题。若还有余力，**新增** 任务（新 id），规格在 workspace 里可见，MCP 只提供辅助（例如查额外约束）。baseline 也能做，full 应更稳或更少步。

每题仍要 hidden judge。跑 **四臂 × 3 seed 不必**；新题 `baseline` vs `full` × 2 seed 即可。

没有时间就跳过。简历不依赖 P2。

---

## 5. 建议顺序

```
1. 读 HANDOFF.md + docs/eval-breakdown.md + 现有 README
2. uv run pytest -q          # 确认环境
3. 写/改 README（P0）
4. 若 GPU 空闲且时间够：抽 25 个 instance_id，先跑 1 条 smoke，再跑 baseline 25
5. 有余力再跑 full 25；没有就只交 baseline
6. 写 evals/external/summary.json 或 SKIPPED.md
7. 不要 commit；把第 8 节打包给用户
```

常用命令（15 题那套，**不要加 --force**）：

```bash
uv sync --extra dev --extra host
uv run pytest -q
uv run mini-swe-harness summarize

docker build -f docker/Dockerfile -t mini-swe-harness:local \
  --build-arg BASE_IMAGE=docker.m.daocloud.io/library/python:3.12-slim .

sg docker -c 'uv run mini-swe-harness run --task evals/tasks/bash-fizz-01.yaml --arm baseline --seed 1'
```

外部评测命令以你选的 A/B 为准，写进 `evals/external/README.md`。

---

## 6. 简历侧已经写了什么（你改数字会打架）

项目名：基于 mini-swe-agent 的 Skill / MCP Harness（2026.08–2026.09）

- Sidecar、渐进加载、MCP 经网关  
- Docker 隔离 + 180 次 hidden-judge  
- 57.8% → 93.3%；MCP 刚需无网关为 0；Skills 在 skill 类 6/9 → 9/9  

P1 若跑出外部子集，回来后由简历 agent **另加半句或第四条**，例如「另在 SWE-bench Lite 25 题子集上 baseline 为 x%」。你不要自己改 tex。

---

## 7. 质量标准

P0 完成 = 本阶段成功。  
P1 有完整 25 题 baseline 表 = 加分。  
P1 只跑了 5 题也交，写明 aborted。  
把 15 题改难/改易来抬分 = **失败**。

---

## 8. 交回用户的材料（缺这个等于没做完）

请打包或原文回复：

1. **改过的 README.md**（全文或 diff）  
2. 若做了 P1：`evals/external/summary.json` + `instance_ids.json` + 用的评测命令  
3. 若跳过 P1：`SKIPPED.md` 和原因  
4. 若做了 P2：新 task id、两臂分数  
5. 设计改动（若有）和原因  
6. 仍未做的、以及 git 是否仍未 commit  
7. 一句人话：外部子集分数低不高、Skills 在 SWE-bench 上有没有掉点  

用户会把这些转给简历这边，用来决定要不要在简历上加「外部子集」半句。

---

## 9. 一句话给执行者

**保住 180 runs，写清 README；有空用官方入口抽 25 道别人的题跑一臂；别换 SWE-agent，别重跑自造题。**
