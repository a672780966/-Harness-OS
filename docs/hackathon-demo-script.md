# Harness OS — 5-Minute Hackathon Demo Script

> **准备时间**: 2026-06-26
> **版本**: v1.4-loop-installer-mvp (main @ 03c1433)
> **演示者**: Wu Le (武乐)

---

## Demo 核心理念

**一句话定位**：
> Harness OS 不是另一个自动写代码的 AI Agent，而是一个**可治理的 Agent 工程运行底座**——每个 Agent 动作都必须经过规划、分配、审查、证据、关卡，才能算完成。

**凭什么和别的 AI Agent 不一样**：
- 其他工具：优化生成代码的速度
- Harness OS：优化**控制代码生成过程的能力**

---

## 5 分钟流程

### 🎬 Minute 0:00–0:30 — 开场 & What

> **目标**: 30 秒说清楚这是什么

**话术**：
"大家好，这是 Harness OS——一个让 AI Agent 工作可控、可追溯、可审查的运行底座。它不是又一个写代码的 AI，而是管理写代码 AI 的操作系统。"

**操作**：打开终端/Terminal 窗口

---

### ⚡ Minute 0:30–1:30 — 现场验证（version + doctor）

> **目标**: 证明这是真系统，不是 PPT

**话术**：
"我们直接现场验证——先看版本，做个体检。"

**操作**：
```bash
# 在项目根目录
python -m harness.copilot.cli version --json
```

**预期输出**：
```
Harness Copilot vv1.4-loop-installer-mvp
```

**话术**：
"体检一下环境是否就绪："

```bash
python -m harness.copilot.cli doctor
```

**预期输出**：5/7 ✅，2 个 ⚠️（config 和 runtime 目录——首次运行会自动创建，正常现象）

**关键台词**：
"5 项核心检查全过——Python、Git、pytest、OS、OpenCode 都就绪。"

---

### 🗺️ Minute 1:30–2:30 — 能力概览（help + dashboard）

> **目标**: 展示 Harness OS 覆盖多少能力

**话术**：
"Harness OS CLI 有 35+ 个命令——从项目检查、差异分析、合并就绪度到 PR 草稿、实时仪表盘。看一下全局状态："

**操作**：
```bash
python -m harness.copilot.cli dashboard .
```

**Highlight 关键输出**：
- Agent 生命周期状态
- 合并就绪度（显示有阻塞，证明真的在审查）
- 最近修改概览
- 重点模块

**关键台词**：
"看这里——Agent 生命周期状态、合并就绪度、风险等级。这不是编的，是真实的项目状态。"

---

### 🔬 Minute 2:30–3:30 — Loop 证据链（这是核心差异化）

> **目标**: 展示一个完整的 Agent 任务从规划到完成的证据链

**话术**：
"这是 Harness OS 最不一样的地方——每个 Agent 任务都有完整的证据链，从规划、执行、审查到最终关卡。"

**操作**：打开一个 DONE task 的证据目录
```bash
ls .harness/temp_loop/e1b40fbb0476/
```

**逐条展示**（边说边指）：
1. **Planner** → `planner_response.json` — Codex 规划
2. **Task Envelope** → `task_envelope.json` — 任务合同
3. **Worker** → `opencode_worker_response.json` — 执行结果
4. **Reviewer** → `opencode_reviewer_response.json` — 第一次审查
5. **Codex Review** → `codex_review_response.json` — 高级审查
6. **Final Gate** → `final_evidence.json` — 最终关卡
7. **Audit** → `audit_events.jsonl` — 审计追踪
8. **State Machine** → `state_transitions.jsonl` — 状态机流转
9. **3 轮 Repair** → `repair_round_1/2/3/` — 修复记录

**看 summary**：
```bash
cat .harness/temp_loop/e1b40fbb0476/_summary.json
```

**关键台词**：
"这说明什么？AI 写代码不是黑盒——每一步都有证据。Worker 说'完成了'不算，Reviewer 确认通过、Final Gate 验证通过，才算。"

---

### 📊 Minute 3:30–4:30 — 审查与关卡

> **目标**: 展示审查层的实际工作

**话术**：
"看一看 Codex 审查是怎么运作的："

**操作**：
```bash
# 看 reviewer 发现了什么问题
cat .harness/temp_loop/e1b40fbb0476/opencode_reviewer_response.json | head -30
```

**关键台词**：
"Codex Review 会列阻塞性问题（blocking）和非阻塞性问题（non-blocking）。有阻塞→打回修复→最多 3 轮→再审查。"

---

### 🎯 Minute 4:30–5:00 — 总结 & Demo 完成

**话术**：
"总结一下 Harness OS 做了什么：
1. **规划** → Codex 出任务合同
2. **执行** → Worker 按合同干活
3. **审查** → Reviewer 检查堵漏
4. **关卡** → Final Gate 确认通过
5. **审计** → 全流程可追溯

每个 AI Agent 动作都有证据，每个关卡都有判断，每个判断都有理由。"

---

## 现场演示 Checklist

### 前置准备

- [ ] 终端已打开，位于 `/home/ctyun/-Harness-OS`
- [ ] `.venv` 已激活（`source .venv/bin/activate`）
- [ ] `python -m harness.copilot.cli version` 确认可用
- [ ] 字体调大到可投影（推荐 16-18pt）
- [ ] 终端背景色：深色（推荐）
- [ ] 避免网络演示（离线也能跑）

### 关键位置速查

| 文件 | 路径 |
|:-----|:------|
| DONE task 证据 | `.harness/temp_loop/e1b40fbb0476/` |
| 另一个 DONE task | `.harness/temp_loop/fa2ace05d055/` |
| Dashboard | `python -m harness.copilot.cli dashboard .` |
| CLI 命令列表 | `python -m harness.copilot.cli --help` |
| 项目体检 | `python -m harness.copilot.cli doctor` |

### 可能的现场问题 & 应对

| 问题 | 回答 |
|:-----|:------|
| "这是不是只是一个 CLI 工具？" | "底层是 CLI，核心是治理框架——CLI 只是交互方式。" |
| "和其他 Agent 框架比优势在哪？" | "别人优化生成速度，我们优化控制能力。审计、关卡、证据链是专业软件开发的标准。" |
| "生产环境能用吗？" | "当前是 local-first MVP，已验证 2 个完整 loop 周期。路线图下一步是安装自动化和公开文档。" |
| "需要什么依赖？" | "Python 3.11+ 和 Git。Node/pnpm 是可选的额外 CLI 路径。" |
| "是开源的吗？" | "ISC 许可证，代码在 GitHub 上。" |

---

## 技术速查卡（演示者用）

```bash
# ====== 核心命令 ======
python -m harness.copilot.cli version --json    # 版本
python -m harness.copilot.cli doctor             # 体检
python -m harness.copilot.cli dashboard .        # 全局状态
python -m harness.copilot.cli inspect .          # 项目扫描
python -m harness.copilot.cli --help             # 所有命令

# ====== 证据链展示 ======
ls .harness/temp_loop/e1b40fbb0476/             # 完整证据目录
cat .harness/temp_loop/e1b40fbb0476/_summary.json # 任务摘要
cat .harness/temp_loop/e1b40fbb0476/task_envelope.json | head -20  # 任务合同

# ====== Node CLI（备选） ======
pnpm install && pnpm build
./dist/index.js version
./dist/index.js doctor
```
