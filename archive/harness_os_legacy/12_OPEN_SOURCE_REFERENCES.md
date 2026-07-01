# Harness OS Open Source References

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Borrow patterns, not architecture blindly

---

# 1. 文档定位

本文件定义 Harness OS 可参考的开源项目、SDK、框架和工程模式。

目标不是把外部项目拼接成 Harness OS，而是明确哪些模式可以借鉴、哪些能力可以复用、哪些边界不能继承、哪些设计不应进入核心架构。

Harness OS 核心方向：Codex-first、Single Agent、Single Model、Project Operating System、MCP Skills as tool layer、Git as long-term truth、`.project/` as project-local state、AGENTS.md as project protocol。

所有外部参考都必须服从 Harness OS 的核心原则。

---

# 2. 总体原则

Borrow Patterns, Not Products：外部项目只能作为模式来源，不得直接照搬完整架构、产品定位、默认运行假设、多 Agent 编排方式、模型路由方式、外部记忆系统、Workflow DAG 核心。

Codex-first Constraint：不得改变 Codex 是唯一执行 Agent、Codex 使用单一主模型、Harness 只做确定性工程运行时、Skills 是工具不是 Agent。

Workspace-first Constraint：外部参考必须落入 AGENTS.md、`.project/`、Git、Context Pack、Task Record、Decision Record、Run Report、Verification Report、Delivery Report。不得默认引入独立项目记忆仓库、独立知识库或外部 vector memory 系统。

Governance-first Constraint：任何外部工具能力进入 Harness OS 后，必须经过 Policy Engine、Approval Gate、Secret Redactor、Event Logger、Context Pack declaration、Workspace boundary check。

---

# 3. Reference Map

```text
1. iii Harness / iii Workers
2. Claude Code / Claude Agent SDK
3. OpenAI Agents SDK
4. LangGraph
5. Aider
6. Continue
7. OpenCode
8. Dify
9. LLM Wiki / Markdown knowledge pattern
10. MCP ecosystem
```

---

# 4. iii Harness / iii Workers

Reference Role：Harness as backend、Worker runtime、Agent harness engineering、Long-running agent support、Project runtime patterns。

Borrow：Harness 作为 Agent 后端运行时，Worker 作为任务执行容器，长任务执行需要状态、恢复、事件记录，Agent 需要外部运行环境，项目任务需要 runtime、tooling、context、state、reporting。

Do Not Borrow Blindly：完整后端架构、完整 worker 调度模型、多 worker 复杂编排、外部服务假设、非 Codex-first 的 agent abstraction。

Harness OS Mapping：iii Harness idea -> Harness Runtime；Worker runtime -> Skill Execution Engine / Run Executor；Long-running task -> Task Manager + State System + Checkpoint；Execution report -> Run Report + Observability。

---

# 5. Claude Code / Claude Agent SDK

Reference Role：workspace-first coding、tool runtime、permission model、session continuity、MCP integration、hooks、agent execution loop。

Borrow：围绕 workspace 工作；工具调用受权限控制；文件编辑和 shell 命令需要审批边界；Session 支持长任务恢复；MCP 作为工具协议层；Hooks 用于事件和治理接入点；Agent SDK 抽象消息、工具、结果和状态。

Do Not Borrow Blindly：Claude 默认模型、Claude 产品级交互假设、不可控工具调用、绕过 Harness Governance 的权限模式、把 SDK 当完整 Harness 架构。

Mapping：workspace model -> Harness Workspace；permission idea -> Approval Gate；tools -> MCP Skills；sessions -> Session State；hooks -> Event Hooks。

---

# 6. OpenAI Agents SDK

Reference Role：agent run abstraction、tools、sessions、tracing、guardrails、handoffs terminology、structured outputs。

Borrow：Run 是一次可追踪的 Agent 执行；Tool 调用应有结构化输入输出；Session 用于连续任务状态；Tracing 用于调试和审计；Guardrails 可作为治理边界参考；Structured outputs 可用于规范化报告和状态。

Do Not Borrow Blindly：multi-agent handoff 核心架构、多 Agent 编排默认模式、模型路由、把 Agents SDK 当完整项目操作系统。

Harness OS 中 handoff 不作为多 Agent 转交，只用于状态转移、任务阶段切换、工具执行结果回传、审批流程切换。

Mapping：Agent Run -> Harness Run；Sessions -> Session State；Tracing -> Event Log / Run Trace；Guardrails -> Policy Engine；Tools -> MCP Skills；Structured output -> JSON schemas。

---

# 7. LangGraph

Reference Role：state machine、checkpointing、durable execution、recoverable graph state。

Borrow：长任务需要显式状态；状态转移应可恢复；checkpoint 是恢复关键；执行过程可表示为状态机；失败后应能定位阶段并继续。

Do Not Borrow Blindly：multi-agent graph as core、supervisor pattern、复杂 DAG 工作流作为核心、节点即 Agent、GraphRAG。

Mapping：Graph state -> Run State / Task State；Checkpoint -> Harness Checkpoint；Node transition -> Task/Delivery Lifecycle；Durable execution -> Resume / Replay / Recovery。

---

# 8. Aider

Reference Role：repo-first coding、Git-first workflow、diff awareness、commit message generation、terminal coding UX、single-agent coding loop。

Borrow：以 Git repo 为中心；理解 diff；交付以 commit 为单位；CLI 是高效入口；Agent 围绕文件、diff、测试循环；根据 diff 和任务生成 commit message。

Do Not Borrow Blindly：只面向 pair programming 的产品边界、缺少项目级 state、缺少完整 governance、把聊天历史作为主要记忆。

Harness OS 在 Aider Git-first 思想上增加 Project Manager、Task Manager、Decision Manager、Context Pack、Governance、Verification、Observability、Delivery Pipeline。

Mapping：Repo-first -> Git as long-term truth；Diff awareness -> Git Skill + Context System；Commit generation -> Delivery Pipeline；CLI coding loop -> Harness CLI；Single agent loop -> Codex。

---

# 9. Continue

Reference Role：workspace awareness、codebase indexing、editor-integrated AI development、context selection、developer-facing AI UX。

Borrow：AI 开发必须理解代码库结构；Context selection 是核心能力；Workspace indexing 帮助定位相关文件；开发者需要可解释上下文来源；Codebase map 有助于任务启动。

Do Not Borrow Blindly：IDE 插件作为唯一入口、仅交互式补全定位、无项目治理状态、上下文选择不可审计。

Mapping：Codebase awareness -> Repo Scanner Skill；Indexing -> Repository Map / Symbol Index；Context selection -> Context Engineering；Developer UX -> CLI / future UI；AI review/checks -> Verification + Codex risk review。

---

# 10. OpenCode

Reference Role：terminal-first coding agent UX、workspace runtime、local execution、developer-controlled agent coding、tool-driven code changes。

Borrow：Terminal-first 是合理初始入口；本地 workspace 执行适合项目开发；工具调用应透明；开发者能看到 agent 做什么；项目执行围绕命令、文件、Git 状态展开。

Do Not Borrow Blindly：只做 terminal agent 产品、缺少 Harness OS 项目治理层、缺少完整 Task/Decision/Delivery 状态、缺少强审批和恢复边界。

Mapping：Terminal UX -> Harness CLI；Local execution -> Project Workspace；Tool transparency -> Observability；Command/file/git loop -> Shell Skill + Filesystem Skill + Git Skill。

---

# 11. Dify

Reference Role：Dify 可作为外围参考，但不是 Harness OS 核心。适合参考 UI forms、approval front door、human workflow input、external integration surface、simple admin interface。

Borrow：表单化任务输入、审批界面、简单管理 UI、外部系统集成入口、非核心人机交互层。

Do Not Borrow Blindly：Dify-style workflow DAG as core、节点式 Agent 编排、LLM workflow 平台定位、多模型链式节点、把 Harness Runtime 放进 Dify workflow。

Dify 只能作为 External UI、Approval UI、Task intake surface、Admin panel candidate，不能作为 Core scheduler、Core runtime、Context engine、Agent orchestrator。

Mapping：Dify form -> Task intake UI；approval-like UI -> Approval frontend candidate；workflow -> not adopted as core；integrations -> optional external connector surface。

---

# 12. LLM Wiki / Markdown Knowledge Pattern

Reference Role：Markdown-first knowledge、LLM-readable documents、versioned memory、human-readable + machine-readable project facts。

Borrow：Markdown 是项目长期知识的好格式；文档适合人类和 LLM 阅读；Git versioning 适合保存项目记忆；项目事实结构化、分文件、可引用；决策和任务记录可长期追踪。

Do Not Borrow Blindly：不得把 Harness OS 变成通用知识库、百科系统、文档站生成器、外部 memory repo、纯 Markdown RAG 系统。

Mapping：Markdown knowledge -> `.project/state/*.md`；Decision records -> `.project/decisions/ADR-*.md`；Task memory -> `.project/tasks/*.md`；Run report -> `.project/reports/*.md`；LLM-readable docs -> Context Pack Markdown Snapshot。

---

# 13. MCP Ecosystem

Reference Role：tool protocol、structured tool declaration、external tool connection、filesystem/shell/git/github/browser/database skill surface。

Borrow：工具能力应有统一协议；工具输入输出结构化；工具可以按能力注册；Agent 通过协议调用工具；工具层可与 runtime 解耦。

Do Not Borrow Blindly：接入 MCP 不等于完成 Harness；所有 MCP server 不可默认启用；MCP server 不可绕过治理；MCP tool 不可自行推理；外部 MCP 不可直接访问项目敏感资源。

Mapping：MCP tool -> Harness Skill Tool；MCP server -> Skill provider；Tool schema -> Skill manifest；Tool call -> Governed Skill Execution；MCP permission -> Policy Engine + Approval Gate。

---

# 14. Reference-to-Module Matrix

| Reference | Borrow | Harness OS Module |
|---|---|---|
| iii Harness | Harness as backend, worker runtime | Harness Runtime |
| iii Workers | long-running execution, worker model | Run Executor / Skill Runtime |
| Claude Code | workspace, permissions, sessions | Workspace / Governance / State |
| Claude Agent SDK | MCP, hooks, tool loop | MCP Skills / Event Hooks |
| OpenAI Agents SDK | run, sessions, tracing, guardrails | Runtime Adapter / State / Observability / Governance |
| LangGraph | state machine, checkpoint | State / Recovery |
| Aider | Git-first coding, diff awareness | Git Skill / Delivery |
| Continue | codebase awareness, context selection | Repo Scanner / Context Engineering |
| OpenCode | terminal UX, local execution | CLI / Workspace Runtime |
| Dify | forms, approval UI | Optional UI Layer |
| LLM Wiki | Markdown versioned knowledge | .project Markdown State |
| MCP | tool protocol | Skill Runtime |

---

# 15. Anti-Patterns

```text
1. 多 Agent supervisor 架构
2. Planner / Worker / Reviewer Agent 拆分
3. Model router
4. 多模型链路
5. Workflow DAG 作为核心 runtime
6. External memory repo
7. Vector DB as default memory
8. GraphRAG as project state
9. Dify as scheduler
10. Tool server bypassing Governance
11. Agent self-approval
12. Deployment without verification
13. PR without run report
14. Context selection without audit
15. Markdown memory without Git tracking
```

---

# 16. Adopted Patterns Summary

明确采用：Workspace-first、Git-first、Markdown-readable project state、Project-local `.project/`、AGENTS.md project protocol、Context Pack、Task Record、Decision Record、Run Report、Verification Report、Delivery Report、MCP Skills、Approval Gate、Event Log、Checkpoint、Replay。

明确不采用：Multi-agent core、Model routing core、Workflow DAG core、External memory repo、Default vector memory、Uncontrolled shell、Unapproved deploy、Untraceable tool calls。

---

# 17. Implementation Guidance for Codex

Codex 实现 Harness OS 时应先读取 Harness OS 自身文档，再读取本 Open Source References。遇到外部项目模式时，先判断是否符合 Single Agent / Single Model / Governance-first；只提取可映射到 Harness OS 模块的设计；不得改变核心架构原则；不得为了适配外部项目引入多 Agent 或模型路由；不得让外部工具绕过 Policy Engine；所有外部能力进入系统后都必须表现为 Skill；所有外部状态进入系统后都必须写入 `.project/` 或 Harness local state；所有交付动作必须进入 Delivery Pipeline。

---

# 18. Future Reference Intake Process

未来新增参考项目时，必须按以下模板评估：

```markdown
# Reference: <name>

## What it is

## Why it matters

## Borrowable Patterns

## Non-borrowable Patterns

## Harness OS Mapping

## Governance Requirements

## Decision

Status: accepted / rejected / proposed
```

如果新增参考项目会改变核心架构，必须创建 ADR。

---

# 19. Final Definition

Open Source References = 为 Harness OS 提供可复用工程模式的参考集合，而不是架构来源本身。

最终边界：Harness OS 的架构由本项目原则决定；外部项目只能提供模式；Codex 只能借鉴，不得照搬；所有借鉴必须落入 Workspace、Context、State、Skills、Governance、Verification、Observability、Delivery 这些模块。
