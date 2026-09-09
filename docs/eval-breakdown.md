# 评测拆解

数据来自 `evals/results/summary.json` 的 `by_category`，以及 `evals/results/raw/*.result.json`。
模型：`openai/qwen3.8-27b`。主指标：hidden judge。不是 SWE-bench。

`summary.json` 现在是 **15 题 × 4 臂 × 3 seeds = 180**。归因时务必同时看 12 题切片：`mcp_opt` 四臂全满分，会把合计里的 MCP 增益稀释掉。

## 按类别通过率

每格 n=9（3 题 × 3 seeds）。

| 类别 | baseline | skill_only | mcp_only | full | skill_only vs base | mcp_only vs base |
|---|---|---|---|---|---|---|
| bash | 9/9 (100%) | 9/9 (100%) | 9/9 (100%) | 9/9 (100%) | +0 | +0 |
| skill | 6/9 (66.7%) | 9/9 (100%) | 6/9 (66.7%) | 9/9 (100%) | **+33.3 pp** | +0 |
| mcp | 0/9 (0%) | 0/9 (0%) | 8/9 (88.9%) | 9/9 (100%) | +0 | **+88.9 pp** |
| skill_mcp | 2/9 (22.2%) | 1/9 (11.1%) | 9/9 (100%) | 6/9 (66.7%) | **−11.1 pp** | **+77.8 pp** |
| mcp_opt | 9/9 (100%) | 9/9 (100%) | 9/9 (100%) | 9/9 (100%) | +0 | +0 |
| **12 题合计** | **17/36 (47.2%)** | **19/36 (52.8%)** | **32/36 (88.9%)** | **33/36 (91.7%)** | **+5.6 pp** | **+41.7 pp** |
| **15 题合计** | **26/45 (57.8%)** | **28/45 (62.2%)** | **41/45 (91.1%)** | **42/45 (93.3%)** | **+4.4 pp** | **+33.3 pp** |

12 题合计里 skill_only「几乎没动」是加权假象：bash 已经封顶，mcp 题没有网关等于没有规格，真正有 Skills 增益的只有 `skill` 类。

## mcp_opt：MCP 不是刚需

三题规格同时在 workspace `README.md` 和 TICKET-7001/7002/7003。2026-09-08 跑完 36 条，**四臂都是 9/9**。

- baseline / skill_only **零次**成功的 MCP 调用，照样全过 → 读 README 就够，不是「把答案藏进 ticket 再发钥匙」。
- mcp_only 仍调用了 MCP（audit ok=7/9 条量级），full 较少（ok=2）。有网关时模型会可选地去拉 ticket，但不拉也能过。
- 3 条 `TimeExceeded`（都在 `mcpopt-round-01`）judge 仍然通过：实现在超时前已经写对。

所以 `mcp` 类（没钥匙=0）和 `mcp_opt` 类（没钥匙=满分）要分开报。15 题合计把 MCP vs baseline 从 +41.7 pp 降到 +33.3 pp，是因为多了 9 对「大家都会」的题，不是 MCP 变弱了。

## C：skill_only 为什么整体只 +5.6 pp

### 1. Skills 在该用的地方是有效的

`skill` 类 3 题里，增益全部来自 `skill-empty-01`：

| 任务 | baseline | skill_only |
|---|---|---|
| skill-empty-01 | 0/3 | 3/3 |
| skill-encoding-01 | 3/3 | 3/3 |
| skill-pytest-01 | 3/3 | 3/3 |

baseline 在空 JSON / 空白输入上直接 `json.loads` 崩掉。skill_only 读了 `repo-qa`（验证矩阵里写了 empty/whitespace），3 个 seed 全过。encoding / pytest 两题不靠 Skills 也能过，所以 Skills 在 skill 类上是 +3/9，不是「技能系统没用」。

### 2. 总表被 mcp / skill_mcp 拖平

skill_only 36 条里：

- 激活过 SKILL.md：28 条，通过 11/28（39%）
- 没激活：8 条，通过 8/8（都是 bash / 已会做的 skill 题）
- 打开过的 skill：`mcp-ticket-context` 18 次、`repo-qa` 13 次
- `TimeExceeded`：18/36，**全部**落在 mcp（9）和 skill_mcp（9）

mcp + skill_mcp 共 18 条 skill_only 里，有 17 条失败轨迹带 `mcp-call` 命令（没有网关，CLI 报错）。模型按 `mcp-ticket-context` 的流程去 `list-servers` / `list-tools` / `get_ticket`，失败后反复重试，直到 180s 墙钟。skill 告诉它「不要猜隐藏规则」，于是它宁可不实现也不瞎编 — 在 **没有 MCP 网关** 的臂上这是正确行为，judge 仍然失败。

skill_mcp 上 skill_only 甚至比 baseline 更差（1/9 vs 2/9）：Skills 把步数花在打不通的 `mcp-call` 上，baseline 偶尔还能猜中一部分规则。唯一一条 skill_mcp 通过（`skillmcp-window-01` seed=1）也是 `TimeExceeded` 之后 judge 碰巧过了，不是干净提交。

### 3. 和 full / mcp_only 对照

- mcp 类：没有钥匙就是 0；有网关就接近满分。这是任务设计（规格只在 ticket 里），不是模型变聪明两倍。
- skill_mcp 类：`mcp_only` 9/9，`full` 6/9。挂上 Skills 以后有的 episode 更慢、更容易超时。Skills 不是免费的。
- skill_only 平均 token（117k）高于 baseline（90k），失败臂在空转。

### 结论

skill_only 弱，不是「渐进披露坏了」，而是：

1. 12 题里只有 1 题（空输入）真正需要 `repo-qa`；
2. 一半题的规格在 MCP ticket 里，skill_only 读得到 skill、打不开网关，skill 还禁止瞎猜；
3. 总体 +5.6 pp 把 (1) 的 +33 pp 和 (2) 的 0 / 负增益平均掉了。

要让 Skills 消融可看，需要更多「规格在仓库里、edge case 在 skill 里」的题。`mcp_opt` 验证的是另一轴（MCP 可选），四臂封顶，帮不了 Skills 归因。不要用 52.8% vs 47.2%（或 15 题的 62.2% vs 57.8%）单独讲 Skills。
