# 第二阶段回交接（给简历 agent / 用户转发）

日期：2026-09-09  
仓库：`/home/liwanrong/code/bilina-dev`  
约束仍有效：**不要 git commit / push**（除非用户当面要求）；不要改简历 tex；不要 `--force` 重跑 180；不要把外部分数和 93.3% 写进同一句。

本文对应 `HANDOFF-phase2.md` **第 8 节**。P0 + P1 已完成，P2 未做。

---

## 1. README（P0）

路径：仓库根 `README.md`。

门面已改成评测仓，不是「很强的编码 Agent」：sidecar on mini-swe-agent；bash-only；不 fork；四臂表 + 按类一句话；明确不是 SWE-bench；架构 / 渐进加载 / MCP 经网关；pytest 与 `eval`（禁止 `--force` 那 180）；指向 `docs/eval-breakdown.md`、`docs/design.md`。

回交接时补了一句：外部 25 题子集在 `evals/external/summary.json`，**不得**和 93.3% 平均。删掉了过时的「本机因磁盘没跑外部题」。

---

## 2. P1 外部子集（已跑完）

### 数字（官方 resolve，唯一可报的外部分）

| 项 | 值 |
|---|---|
| 基准 | SWE-bench Lite `test` |
| n | **25**（固定抽样 `sample_seed=20260908`） |
| 臂 | **baseline only**（Skills 关、本仓 ticket MCP 关） |
| seed | 1 |
| 模型 | `openai/qwen3.8-27b`（本机 vLLM） |
| 官方 resolved | **18 / 25 = 72%** |
| Agent 退出 | 24 Submitted + 1 `ContextWindowExceededError` |
| 空 patch | `django__django-13265`（计入分母） |
| 基础设施失败 | 0 |
| Agent 墙钟 | 4.32 h |
| 官方 harness 墙钟 | 0.25 h |

未修好（6）：`django__django-12700`、`psf__requests-2148`、`pydata__xarray-4493`、`scikit-learn__scikit-learn-10508`、`sympy__sympy-13146`、`sympy__sympy-15308`。

**抽样构成：** 11 django（9 过 / 1 不过 / 1 空）+ 10 sympy（8 过 / 2 不过）+ sphinx 过 + requests/xarray/sklearn 全挂。n=25，点估计不稳，**不是 Lite 全量**。

文件：

- `evals/external/summary.json`
- `evals/external/instance_ids.json`
- 官方报告：`evals/external/runs/lite25-baseline/openai__qwen3.8-27b.lite25-baseline.json`
- preds：`evals/external/runs/lite25-baseline/preds.json`
- 命令说明：`evals/external/README.md`

### 评测命令

Agent（mini-swe-agent 2.4.6 `mini-extra swebench`，不是本仓网关）：

```bash
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
```

官方 resolve（swebench 5.0.2；数据集必须用带 `image` 字段的 `SWE-bench/SWE-bench_Lite`）：

```bash
IDS=$(python3 -c "import json; print(' '.join(json.load(open('evals/external/instance_ids.json'))['instance_ids']))")
sg docker -c "uv run python -m swebench.harness.run_evaluation \
  -d SWE-bench/SWE-bench_Lite -s test \
  -i $IDS \
  -p evals/external/runs/lite25-baseline/preds.json \
  --max_workers 1 -id lite25-baseline \
  --report_dir evals/external/runs/lite25-baseline \
  -t 1800"
```

运维备忘（简历不必写）：Docker Hub 超时，镜像从 `ghcr.io/epoch-research/swe-bench.eval.x86_64.<id>` pull 后 tag 成 mini-swe-agent 期望的 `docker.io/swebench/sweb.eval.x86_64.*`。data-root 由管理员改为 `/data8/docker`。vLLM 需 `OPENAI_API_KEY`（只在 gitignore 的 `.env`）。

---

## 3. P1 未跳过

`evals/external/SKIPPED.md` 现改为「已完成，以 summary.json 为准」，不要再当跳过理由。

---

## 4. P2

未做。无新 task id。简历不依赖 P2。

---

## 5. 设计改动

`docs/design.md` 已有「为什么不换 SWE-agent / 为什么不上全量 SWE-bench」。回交接时改掉「本机 P1 因磁盘跳过」那句，改为已跑 25 题 baseline、分数在 `evals/external/`。

未 fork mini-swe-agent，未换成 SWE-agent，未把 MCP 接到 `litellm.completion(tools=...)`，未动 15 题规格，未 `--force` 180。

`evals/external/local-model.yaml` 只给 LiteLLM `num_retries=0`、`timeout=180`，避免 vLLM 挂掉时重试数小时。

---

## 6. 仍未做 / git

- **未 git commit**（`git init` 过，工作区大量 staged + `evals/external/`、`HANDOFF-phase2.md`、`logs/` 未提交）。用户未要求 commit。
- 未跑外部题 `full` 臂，未跑 3 seed，未跑 Lite/Verified 全量。
- 未改简历 tex、未建 GitHub。
- 自建 180 未重跑。数字仍是：baseline 57.8% / skill_only 62.2% / mcp_only 91.1% / full 93.3%。

---

## 7. 一句人话（给简历）

外部 25 题子集官方 resolve 是 **18/25（72%）**，说明循环在别人的题上能跑完、能出分，比「个位数」预期好；但这是 Lite 的小样本（偏 django/sympy），**不要写成 SWE-bench Lite 72%**，也不要和自建 93.3% 放同一句。没跑 Skills 臂，**看不出 Skills 在 SWE-bench 上掉不掉点**。

建议半句（可改）：「另在 SWE-bench Lite 25 题固定子集上，baseline（官方 harness）resolve 18/25。」
