# mini-swe-harness 交接文档

> 给另一台服务器上的自己 / 下一轮对话用。  
> 日期：2026-08-18  
> 作者：李婉榕  
> 状态：设计已定，代码尚未在本机开工。跑完把「第 10 节」的结果带回即可继续改简历。

---

## 1. 这个项目到底是什么

做一个 **编码 Agent 的侧车 harness**，挂在开源项目 [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) 外面，**不 fork、不改它的本体**。

Harness 要补上 mini-swe-agent 故意不做的三件事：

1. **Agent Skill 渐进加载**（[Agent Skills 规范](https://agentskills.io)：先只注入 name + description，启用后再读完整 `SKILL.md`）
2. **MCP 工具桥**（把 MCP server 暴露成 bash CLI，例如 `mcp-call list-tools` / `mcp-call call`，符合 mini「只认 bash」的设计）
3. **工具白名单 + 小评测**（对比 bash-only vs Skill+MCP 的成功率、步数、token）

一句话：**不是再做一个 RAG 聊天机器人，而是把「Agent 怎么加载 Skill、怎么调工具、怎么限制权限、怎么量化效果」做成可公开的作品。**

---

## 2. 为什么做（和简历的关系）

### 求职方向

简历第一版 `resume/resume_v1.tex` 的求职意向已经定为：

**大模型应用开发 / AI Agent**

实习（ASML / Brion，内部 Agent Lumina）已经覆盖：LiteLLM、vLLM、MCP、Skill、CocoIndex RAG。  
缺的是一份 **可公开、能讲、有数字** 的 Agent 作品。Lumina 受保密限制，面试不能展开源码。

### 这个项目要补的缺口

| 实习里有、公开讲不清 | 这个项目要公开证明 |
|----------------------|-------------------|
| 改过内部 Skill Prompt | 实现过 Agent Skills 规范的渐进加载 |
| 接过 MCP | 自己做过 MCP→bash 桥，能讲协议和上下文膨胀问题 |
| Whitelist 配置化 | 公开版工具白名单（不要搬公司规则） |
| 没有评测数字 | 自建 10–20 条任务，给出 before/after |

### 明确不要做的

- 不要再做 Dify / RAG 知识库（和实习重复，简历已删）
- 不要 fork mini-swe-agent 加原生 tool-calling（和官方设计对着干；Harbor 已用 `mcp-call` 做过类似 MCP 桥）
- 不要跑完整 SWE-bench（贵，也不是卖点）
- 不要复制 Lumina / 公司 Skill / 产品文档 / Whitelist 业务规则
- 不要把「能 cat 一份 SKILL.md 进 prompt」当成完成——那是薄封装，面试经不起问

### 简历上最终要长成的样子（数字先空着）

项目名建议：**基于 mini-swe-agent 的 Skill / MCP Harness**  
时间：按实际开发填写，例如 `2026.08 ~ 2026.09`  
角色：个人项目  
技术关键词：`Python, mini-swe-agent, Agent Skills, MCP, LiteLLM`

三条 bullet 目标稿（跑完评测后填 Y）：

1. **Skill 渐进加载**：实现 Agent Skills 规范，启动时只注入 Skill 目录（name + description），按需再加载 `SKILL.md` / `references/`，避免把全部 Skill 塞进 context。
2. **MCP 工具桥**：将 MCP server（stdio / HTTP）暴露为 bash CLI，使 bash-only 的 mini-swe-agent 可发现并调用外部工具，并用白名单约束可调用工具。
3. **对比评测**：在 N 条自建编码任务上对比 bash-only vs Skill+MCP，成功率从 A% 到 B%，平均步数从 X 到 Y（或 token 下降 Z%）。

没有第 3 条的数字，这个项目在简历上会偏「接了个协议」；**评测是写入简历的硬条件。**

---

## 3. 已锁定的设计（不要改方向）

先前已确认：

- **Approach B：侧车 harness**，调用 mini-swe-agent，不改其 100 行循环
- GitHub：**先私有仓**，做完再考虑公开
- 仓库名建议：`mini-swe-harness`
- 本机 Mac（M2 16GB 统一内存）只适合写代码/跑单测，不适合跑 27B
- 现在改到 **另一台服务器** 上实现和评测

mini-swe-agent 的关键约束（写代码时必须遵守）：

- 唯一工具是 **bash**
- 不用模型原生 function calling
- 每个 action 是独立的 `subprocess.run` / `docker exec`，没有长期 shell session（`cd` 不会保持）
- 模型走 **LiteLLM**，所以本地 vLLM / Ollama / OpenAI 兼容接口都能接

MCP 的正确接法（官方 issue #563 + Harbor PR 的思路）：

- 不要在 Python 里给模型加 tools= 参数
- 把 MCP 做成环境里的 CLI，再在 prompt 里告诉模型有哪些命令
- Skill 也走文件系统：模型用 `cat skills/foo/SKILL.md` 加载正文（这就是渐进加载）

---

## 4. 架构

```
用户任务
   │
   ▼
┌─────────────────────────────────────────┐
│  mini-swe-harness（本项目）              │
│  1. 扫描 skills/*/SKILL.md → 目录注入     │
│  2. 读 mcp.yaml → 启动/登记 MCP           │
│  3. 写白名单 → 限制 mcp-call / 危险命令    │
│  4. 拼好 system prompt / 环境 PATH        │
│  5. 调用 mini-swe-agent 循环              │
│  6. 记录 trajectory → 评测指标            │
└─────────────────────────────────────────┘
   │  bash 命令
   ▼
mini-swe-agent DefaultAgent
   │
   ├─ cat skills/.../SKILL.md      （Skill 正文）
   ├─ mcp-call list-tools / call   （MCP）
   └─ 普通 git / pytest / sed 等
```

数据流：

1. Harness 启动时读 `skills/`，只把每个 Skill 的 `name`、`description` 写进 prompt 的「Available Skills」小节。
2. 模型若判断需要某 Skill，发 bash：`cat skills/<name>/SKILL.md`。Harness **不必**做特殊 tool，文件系统本身就是加载器。
3. MCP：harness 在环境 PATH 里放 `mcp-call`。模型先 `mcp-call list-tools <server>`，再 `mcp-call call <server> <tool> --args '...'`。
4. 白名单：`mcp-call` 和（可选）高危 bash 前缀在调用前检查，未授权则返回错误字符串给模型，不要直接抛崩。
5. 评测：同一批任务跑两轮（baseline：无 Skill/MCP；full：有），写出 JSON 报告。

---

## 5. 建议仓库结构

```
mini-swe-harness/
├── README.md
├── pyproject.toml
├── .gitignore
├── .env.example                 # 只放变量名，不放密钥
├── src/mini_swe_harness/
│   ├── __init__.py
│   ├── skills.py                # 扫描、校验、生成目录文本
│   ├── mcp_bridge.py            # mcp-call 的库逻辑
│   ├── policy.py                # 白名单
│   ├── prompt.py                # 把 Skill 目录 / MCP 说明拼进 prompt
│   ├── runner.py                # 组装环境并调用 mini-swe-agent
│   └── eval_report.py           # 汇总成功率/步数/token
├── bin/
│   └── mcp-call                 # CLI 入口（或 python -m）
├── skills/
│   ├── pytest-debug/SKILL.md
│   ├── git-commit-hygiene/SKILL.md
│   └── repo-qa/SKILL.md         # 至少 3 个，覆盖「何时用」
├── config/
│   ├── mcp.yaml                 # MCP server 列表
│   └── policy.yaml              # 允许的 server/tool/命令前缀
├── evals/
│   ├── tasks/                   # 每条任务一个 yaml
│   ├── run_eval.py
│   └── results/                 # gitignore 掉原始 trajectory 也可，保留汇总
├── tests/
│   ├── test_skills.py
│   ├── test_mcp_bridge.py
│   ├── test_policy.py
│   └── test_prompt.py
└── docs/
    └── design.md                # 可把本文精简放进去
```

Python：3.11+。依赖核心：`mini-swe-agent`、`litellm`、`pyyaml`、MCP 客户端库（如官方 `mcp`）、`pytest`。

---

## 6. 各模块规格（按这个实现，避免做成薄封装）

### 6.1 Skill 加载（必须做出渐进加载，这是区分度）

遵循 Agent Skills 规范：

- 每个 Skill 是目录，内含 `SKILL.md`
- YAML frontmatter 必填：`name`（小写+连字符，≤64）、`description`（≤1024，必须同时写 **做什么** 和 **何时用**）
- 可选：`scripts/`、`references/`、`assets/`
- **启动时**：prompt 里只有目录，大约每条 100 token 量级
- **启用后**：模型自己 `cat` 正文；不要在启动时把所有 SKILL.md 正文塞进 system prompt
- 正文建议 < 500 行；细节放到 `references/`，模型再按需读

校验失败（缺 name/description、name 和目录名不一致）的 Skill 应跳过并打日志，不要让整个 harness 起不来。

至少准备 3 个 **和编码任务真相关** 的 Skill，例如：

- `pytest-debug`：测失败时如何读报错、缩小范围、再跑单测
- `git-commit-hygiene`：何时提交、怎么看 diff、不要 `git add .` 乱提交
- `mcp-tool-use`：何时该用 `mcp-call` 而不是自己造轮子

不要写空泛的「你是有帮助的助手」。description 写不清，模型根本不会激活 Skill，评测会假阴性。

### 6.2 MCP 桥

配置示例（`config/mcp.yaml`）：

```yaml
servers:
  - name: filesystem
    transport: stdio
    command: ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp/eval-workspace"]
  - name: git
    transport: stdio
    command: ["npx", "-y", "@modelcontextprotocol/server-git"]
```

`mcp-call` 最少子命令：

```
mcp-call list-servers
mcp-call list-tools <server>
mcp-call call <server> <tool> --args '<json>'
```

要求：

- 支持 stdio；HTTP/SSE 有时间再加，stdio 优先（评测更好控）
- 工具 schema 用 `list-tools` 现场发现，不要写死在 prompt 里一份巨表（否则 context 爆炸，和 Skill 渐进加载理念冲突）
- 超时、非 JSON、server 挂掉：返回可读错误，让 Agent 能重试
- 评测环境里给 1–2 个真正有用的 server（filesystem / git 足够），不要堆 10 个 MCP 装门面

### 6.3 白名单（实习 Whitelist 的公开对应物）

`config/policy.yaml` 思路：

```yaml
allow_mcp_servers: [filesystem, git]
allow_mcp_tools:
  filesystem: [read_file, list_directory]
  git: [status, diff, log]
deny_command_prefixes:
  - "rm -rf /"
  - "sudo"
```

未授权调用：CLI 退出码非 0，stdout/stderr 说明被拒绝。这样模型能改策略，评测也能统计「拦截次数」。

### 6.4 Runner

- 组装：Skill 目录文本 + MCP 使用说明 + policy 说明 → 追加到 mini-swe-agent 的 instruction / system 模板
- 把 `bin/mcp-call` 和 `skills/` 放进工作目录（或 Docker 镜像）
- 通过 LiteLLM 配模型：环境变量 `LITELLM_MODEL`、`OPENAI_API_BASE`、`OPENAI_API_KEY` 等
- 保存每条任务的 trajectory（步数、每个 action、是否成功、token 若 LiteLLM 能拿到就记）

### 6.5 评测（写入简历的数据来源）

**不要跑官方 SWE-bench 全量。** 自建 10–20 条小任务，每条必须能自动判定对错。

任务设计原则：

- 有 **Skill 或 MCP 才能明显更好** 的任务，否则对比是平的，简历没法写
- 例如：约定好的仓库结构必须用 filesystem MCP 读到某个隐藏配置；或必须遵循 Skill 里写的测试顺序才过
- 同时也要有纯 bash 就能做的对照，证明不是「关了 MCP 就全崩」这种不公平对比
- 每条超时（如 3–5 分钟）、步数上限（如 30）

每条 task yaml 建议字段：

```yaml
id: pytest-fix-01
prompt: "修复 tests/test_foo.py 的失败并保证 pytest 通过"
cwd: ./eval_repos/foo
success_cmd: "pytest tests/test_foo.py -q"
timeout_s: 180
max_steps: 30
```

两轮：

| 轮次 | Skill | MCP |
|------|-------|-----|
| baseline | 关 | 关 |
| full | 开 | 开 |

输出一份 `evals/results/summary.json`，至少包含：

```json
{
  "model": "实际模型名",
  "n_tasks": 12,
  "baseline": {"success": 5, "success_rate": 0.42, "avg_steps": 18.2, "avg_tokens": 12000},
  "full":     {"success": 8, "success_rate": 0.67, "avg_steps": 12.1, "avg_tokens": 9000},
  "skill_activation_rate": 0.75,
  "mcp_calls": {"ok": 40, "denied": 6, "error": 2}
}
```

数字必须能解释口径：同一模型、同一任务集、同一超时。不要事后只挑好的任务报。

---

## 7. 推荐实施顺序（在服务器上按这个做）

单测不需要 GPU。接模型评测再占用 GPU。

1. **仓库骨架**：`pyproject.toml`、gitignore、README、空模块  
2. **`skills.py` + 测试**：扫描、校验 frontmatter、生成目录 markdown  
3. **`policy.py` + 测试**：允许/拒绝  
4. **`mcp_bridge.py` + `mcp-call` + 测试**：可用 fake/stdio mock server，不必一上来接真实 npx  
5. **`prompt.py`**：确认「启动时没有 Skill 正文」  
6. **`runner.py`**：先用 mock / 小模型跑通 1 条任务  
7. **写 10+ 条 eval 任务 + 3 个 Skill**  
8. **跑 baseline vs full，出 summary.json**  
9. **README：架构图、怎么跑、评测数字、面试能讲的设计取舍**

做到第 8 步才算「能写进简历」。只做到第 6 步只能当 demo。

---

## 8. 环境与模型（服务器上自己定）

Harness 开发：Python 3.11、pytest，CPU 即可。

本地推理（可选）：

- 有 NVIDIA GPU：优先 **vLLM** 或 **Ollama** 开 OpenAI 兼容接口，LiteLLM 去连
- 单卡 11GB（2080 Ti）：7B–13B 量化稳妥；不要一上来上 27B
- 双卡：只有框架真支持 tensor parallel 时才算 22GB，不要假设显存能相加
- Windows 机器请用 **WSL2 Ubuntu**，不要在原生 PowerShell 里跑 mini-swe-agent
- 没 GPU / 显存不够：**用 API**（OpenRouter 等）照样能出评测数字，简历写模型名即可

环境变量不要进 git。`.env.example` 只写：

```
LITELLM_MODEL=
OPENAI_API_BASE=
OPENAI_API_KEY=
```

---

## 9. GitHub

- 仓库名：`mini-swe-harness`
- **先私有**
- 提交要小步：`feat: skill catalog loader` 这种，不要一天一个巨型 commit
- 不要提交：`.env`、模型权重、`evals/results/` 里的原始超长 trajectory（汇总 json 可以留）
- 公开前再扫一遍：有无公司内部名称、Lumina、产品路径

本机此前未装 `gh` CLI；服务器若要建仓：`gh repo create mini-swe-harness --private --source . --remote origin --push`。

---

## 10. 你跑完后请带回的东西（下一轮对话要用）

请尽量原样贴或把文件发回来，不要只说「跑通了」：

1. **`evals/results/summary.json`**（或同等表格）：baseline vs full 的成功率、步数、token  
2. **实际用的模型名和量化**（例如 Qwen2.5-14B-Instruct AWQ / gpt-4.1-mini）  
3. **任务条数**、每条是否自动判定  
4. **Skill 是否真的被激活**（有多少任务 `cat` 了 SKILL.md）  
5. **MCP 调用次数、拒绝次数**  
6. **仓库路径 / GitHub 私有仓地址**（有的话）  
7. **README 链接或正文**  
8. 实现时若改了设计，写清 **改了什么、为什么**  
9. 失败案例 1–2 个（面试会问「什么时候 Skill 没帮上忙」）

有以上材料，就可以直接改 `resume_v1.tex` 的项目经历，把空着的数字填上。

---

## 11. 面试时要能讲的三句话（实现时按这个对齐）

1. mini-swe-agent 为什么保持 bash-only；MCP 为什么做成 CLI 而不是改 tool-calling。  
2. Skill 为什么必须渐进加载；全部塞进 prompt 会怎样。  
3. 评测怎么避免「开了 MCP 的任务本身更简单」这种作弊。

讲不清这三句，简历上的技术名词会被追问到穿。

---

## 12. 参考链接

- mini-swe-agent：https://github.com/SWE-agent/mini-swe-agent  
- 文档：https://mini-swe-agent.com/latest/  
- MCP 接入讨论：https://github.com/SWE-agent/mini-swe-agent/issues/563  
- Agent Skills 规范：https://agentskills.io  
- Claude Skills 渐进加载说明：https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview  

---

## 13. 和现有简历的衔接（回来后做，现在先别改 tex）

当前 `resume_v1.tex` 项目区只有「高并发恶意评论检测系统」。  
本项目完成后：

- **插入到项目经历最上方**（比 ONNX 更贴 Agent 岗）  
- ONNX 项目保留（证明会训小模型和推理加速）  
- 技能行可补：`Agent Skills`、`MCP client`（已有 MCP / Skill 字样则只加项目名）  
- 不要把实习里的 Lumina 细节写进这个开源项目 README

---

**下一台机器上的第一件事：** 按第 7 节从骨架 + `test_skills.py` 开始，不要先调模型。模型只为第 8 步服务。
