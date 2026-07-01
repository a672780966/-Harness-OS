# Harness OS Design Document

Version: 1.0  
Target Runtime: Codex-first Project Operating System  
Primary Agent: Codex  
Architecture Principle: Single Agent, Single Model, Multi-Skill Harness

---

# 1. Executive Summary

Harness OS 是一个面向 Codex 的项目级运行时系统。

它不是聊天机器人，不是传统 workflow 编排器，不是 Dify 类节点系统，也不是多 Agent 平台。它的目标是为 Codex 构建一个完整、可治理、可恢复、可观测、可交付的项目操作系统。

Harness OS 的职责是：

```text id="9np5q0"
Workspace
Context
State
Skills
Governance
Verification
Observability
Delivery
```

Codex 的职责是：

```text id="2p19bd"
Reasoning
Planning
Coding
Review
Execution
Task Completion
```

最终形态：

```text id="mf1ma4"
Harness OS = Codex 的 Project Operating System
Codex = 唯一执行 Agent
MCP Skills = Harness 内部工具能力层
Project Repo = 业务代码 + 项目本地状态
Git = 长期事实源
```

---

# 2. Design Goals

## 2.1 Primary Goals

Harness OS 必须实现以下目标：

1. 创建和管理业务项目仓库。
2. 为 Codex 提供稳定的项目工作区。
3. 自动构建任务上下文。
4. 管理项目状态、任务状态、会话状态和恢复点。
5. 通过 MCP Skills 暴露可控工具能力。
6. 对高风险操作进行审批和安全拦截。
7. 执行 lint、typecheck、test、build、review 等验证流程。
8. 记录完整任务执行轨迹。
9. 支持任务 replay、resume、rollback。
10. 支持 commit、PR、release、deploy 等交付流程。

---

## 2.2 Non Goals

Harness OS 不做以下事情：

```text id="f5yof2"
Multi-Agent orchestration
Planner / Worker / Reviewer agent split
Model router
Multi-model workflow
Dify-style workflow DAG
External memory repository
Standalone vector database platform
GraphRAG platform
Prompt marketplace
Autonomous unapproved deployment
```

如果未来确实需要这些能力，必须作为明确的架构变更进入 ADR，而不是默认进入核心系统。

---

# 3. Core Principles

## 3.1 Single Agent

系统中只有一个执行 Agent：

```text id="nmeoya"
Codex
```

不拆成：

```text id="4nosdq"
Planner Agent
Coder Agent
Reviewer Agent
Research Agent
Supervisor Agent
```

所有规划、编码、总结、Review、失败分析都由 Codex 完成。

---

## 3.2 Single Model

核心执行链只使用一个主模型。

不采用：

```text id="2axe2x"
Claude planning
Gemini search
Codex coding
Small model classification
Embedding model retrieval
Reranker model selection
```

语义判断由 Codex 完成。

确定性任务由 Harness 完成。

---

## 3.3 Skills Instead of Agents

系统扩展方式不是增加 Agent，而是增加 Skill。

```text id="82e616"
Agent = Codex
Capabilities = MCP Skills
```

Skill 是工具，不是智能体。

---

## 3.4 Workspace First

所有项目事实和项目状态必须落在项目工作区或 Harness 管理的本地状态中。

不依赖聊天历史作为项目状态源。

---

## 3.5 Git First

Git 是长期事实源。

代码、项目协议、任务摘要、决策记录、状态文件都应可以被 Git 追踪、审查、回滚。

---

## 3.6 Approval First for Risky Actions

高风险操作必须审批。

例如：

```text id="ggaqfi"
修改 AGENTS.md
删除文件
修改架构决策
新增重大依赖
数据库迁移
部署
push main
force push
```

---

# 4. System Overview

Harness OS 总体架构：

```text id="3nzd4i"
Harness Runtime
│
├── CLI / API Layer
├── Project Manager
├── Agent Runtime Adapter
├── Context System
├── State System
├── MCP Skill Runtime
├── Governance System
├── Verification System
├── Observability System
└── Delivery System
```

项目仓库结构：

```text id="jz5apg"
project-repo/
│
├── AGENTS.md
├── .project/
│   ├── state/
│   ├── tasks/
│   ├── decisions/
│   ├── reports/
│   ├── checkpoints/
│   ├── sessions/
│   └── context/
│
├── src/
├── tests/
├── docs/
└── README.md
```

---

# 5. Repository Boundary

## 5.1 Harness Repository

Harness 仓库存放 Harness OS 产品代码。

内容包括：

```text id="okvh6g"
runtime/
cli/
api/
skills/
templates/
schemas/
policies/
context/
state/
verification/
observability/
delivery/
docs/
tests/
```

Harness 仓库不存具体业务项目的长期记忆。

---

## 5.2 Project Repository

业务项目仓库存放：

```text id="ob9m6e"
业务代码
AGENTS.md
.project/state
.project/tasks
.project/decisions
.project/reports
.project/checkpoints
.project/sessions
.project/context
```

每个业务项目有自己的项目本地状态。

---

## 5.3 One Harness, Many Projects

最终模型：

```text id="genf26"
Global Harness OS
  ├── manages project-a
  ├── manages project-b
  ├── manages project-c
  └── manages project-n
```

每个项目：

```text id="s7yl28"
Project Repo
  ├── source code
  ├── AGENTS.md
  └── .project/
```

---

# 6. Runtime Components

本章定义 CLI / API Layer、Project Manager、Agent Runtime Adapter、Context System、State System、MCP Skill Runtime、Governance System、Verification System、Observability System、Delivery System 的职责、接口、核心流程和数据模型。

## 6.1 CLI / API Layer

负责接收用户命令、解析参数、调用 Project Manager、启动 Codex Run、显示审批请求、显示运行状态、显示最终报告。

Required Commands:

```bash id="92dcdf"
harness create <project-name>
harness open <repo-path>
harness run "<task>"
harness resume <run-id>
harness status
harness checkpoint
harness rollback <checkpoint-id>
harness report <run-id>
harness verify
harness deliver
```

Optional Commands:

```bash id="2csd3t"
harness init
harness repair
harness archive
harness restore
harness doctor
harness skills list
harness skills enable <skill>
harness skills disable <skill>
```

## 6.2 Project Manager

Project Manager 负责项目生命周期：创建项目、打开项目、导入项目、初始化项目状态、修复缺失结构、检测项目技术栈、建立项目 manifest、维护项目配置。

Project Create Flow:

```text id="lece1m"
User: harness create my-app

1. 创建本地项目目录
2. 初始化 Git 仓库
3. 注入 AGENTS.md
4. 创建 .project/ 目录
5. 创建初始 project state
6. 创建初始 task/state/report 模板
7. 扫描仓库
8. 生成 repository map
9. 注册默认 skills
10. 创建初始 checkpoint
```

Project Open Flow:

```text id="e6zod9"
User: harness open ./my-app

1. 校验 repo
2. 读取 AGENTS.md
3. 检查 .project/
4. 修复缺失目录
5. 读取 project manifest
6. 刷新 repository map
7. 读取 git status
8. 恢复最近 session
9. 准备 Codex context
```

## 6.3 Agent Runtime Adapter

Agent Runtime Adapter 负责把 Harness OS 和 Codex 连接起来。它不做推理，不做规划，不做编码。

```ts id="68qsfh"
interface AgentRuntimeAdapter {
  startRun(input: AgentRunInput): Promise<AgentRun>
  resumeRun(runId: string): Promise<AgentRun>
  stopRun(runId: string): Promise<void>
  sendToolResult(runId: string, result: ToolResult): Promise<void>
}
```

```ts id="0feus5"
interface AgentRunInput {
  projectId: string
  taskId: string
  userInstruction: string
  contextPack: ContextPack
  availableSkills: SkillManifest[]
  policy: RuntimePolicy
}
```

## 6.4 Context System

Context System 负责读取 AGENTS.md、project state、current task、decisions、recent reports、git status / diff、相关文件、测试、构建 Context Pack、控制上下文长度、生成上下文摘要、保存 context snapshot。

Context Pack Schema:

```ts id="87mmj9"
interface ContextPack {
  project: ProjectContext
  task: TaskContext
  constraints: ConstraintContext
  relevantFiles: FileContext[]
  relevantDecisions: DecisionContext[]
  recentRuns: RunSummary[]
  git: GitContext
  verification: VerificationContext
  availableSkills: SkillManifest[]
}
```

Context Pack 必须写入：

```text id="wp6418"
.project/context/<run-id>.json
.project/context/<run-id>.md
```

## 6.5 State System

State System 负责 Project State、Session State、Task State、Run State、Checkpoint State、Skill State、Verification State、Delivery State。

默认使用：

```text id="yirp4j"
SQLite + JSON + Markdown
```

推荐结构：

```text id="5i9csf"
.project/
  state/
    project.json
    project.md
    manifest.json
  sessions/
    <session-id>.json
  tasks/
    active/
    completed/
  checkpoints/
    <checkpoint-id>.json
  reports/
    <run-id>.md
```

## 6.6 MCP Skill Runtime

MCP Skill Runtime 是 Harness OS 的能力层。Skill 是工具，不是 Agent。

Core Skills:

```text id="nznohz"
filesystem
shell
git
github
browser
repo-scanner
test-runner
database
delivery
```

```ts id="09q7go"
interface Skill {
  name: string
  description: string
  inputSchema: JSONSchema
  outputSchema: JSONSchema
  riskLevel: "low" | "medium" | "high"
  requiresApproval: boolean
  execute(input: unknown, context: SkillExecutionContext): Promise<SkillResult>
}
```

## 6.7 Governance System

Governance System 负责 Tool Policy、Filesystem Policy、Shell Policy、Git Policy、Network Policy、Secret Policy、Budget Policy、Delivery Policy。

Always Requires Approval:

```text id="h3a4jx"
修改 AGENTS.md
修改 architecture decision
删除文件
删除测试
新增重大依赖
数据库迁移
部署
push main
force push
git reset --hard
git clean -fd
修改安全策略
新增外部 memory/vector 系统
引入 multi-agent 架构
引入 model router
```

## 6.8 Verification System

Verification Pipeline:

```text id="yblcx0"
1. static inspection
2. lint
3. typecheck
4. unit tests
5. integration tests
6. e2e tests
7. build
8. AI review
9. risk report
```

## 6.9 Observability System

Event Types:

```text id="82d47h"
run.started
run.completed
run.failed
task.created
context.built
tool.called
tool.completed
tool.failed
approval.requested
approval.granted
approval.denied
file.changed
verification.started
verification.completed
delivery.created
checkpoint.created
```

## 6.10 Delivery System

Delivery Actions:

```text id="mcwgg3"
commit
pull request
release note
changelog
deploy
rollback
```

---

# 7. Project Local Files

AGENTS.md 是项目最高优先级操作协议。.project/state/ 保存项目当前事实。.project/tasks/ 保存任务记录。.project/decisions/ 保存架构决策。.project/reports/ 保存 run report、verification report、delivery report。.project/checkpoints/ 保存恢复点。.project/context/ 保存每次 run 的 Context Pack。

---

# 8. Core Workflows

## 8.1 Create Project

```text id="np9cqu"
harness create <project>

1. Project Manager 创建 repo
2. 初始化 Git
3. 注入 AGENTS.md
4. 创建 .project/
5. 生成 manifest
6. Repo Scanner 扫描结构
7. Context System 生成初始 context
8. State System 创建 session
9. 创建 checkpoint
10. 输出项目创建报告
```

## 8.2 Open Project

```text id="dq0xio"
harness open <repo>

1. 验证 Git repo
2. 读取 AGENTS.md
3. 校验 .project/
4. 修复缺失结构
5. 读取 state
6. 刷新 repository map
7. 检查 git status
8. 恢复 session
9. 准备 context
```

## 8.3 Run Task

```text id="gdzjle"
harness run "<task>"

1. 创建 task record
2. 创建 run record
3. 读取 AGENTS.md
4. 构建 Context Pack
5. 启动 Codex
6. Codex 调用 Skills
7. Governance 拦截高风险操作
8. Verification 执行验证
9. Observability 记录事件
10. Delivery 准备 commit/PR
11. 写 task summary
12. 写 run report
```

## 8.4 Resume Task

```text id="ksyjba"
harness resume <run-id>

1. 读取 run state
2. 读取 latest checkpoint
3. 校验 git state
4. 恢复 context summary
5. 恢复 Codex session
6. 继续执行
```

## 8.5 Rollback

```text id="9379le"
harness rollback <checkpoint-id>

1. 读取 checkpoint
2. 展示将回滚内容
3. 请求审批
4. 恢复 git state
5. 恢复 session state
6. 写 rollback report
```

## 8.6 Deliver

```text id="hup9wi"
harness deliver

1. 检查 task status
2. 检查 verification result
3. 生成 commit message
4. 生成 PR body
5. 请求审批
6. 创建 commit
7. 创建 PR
8. 写 delivery report
```

---

# 9. Data Model

```ts id="3lg31j"
interface Project {
  id: string
  name: string
  rootPath: string
  repoUrl?: string
  defaultBranch: string
  createdAt: string
  updatedAt: string
}
```

```ts id="3hd4et"
interface Run {
  id: string
  projectId: string
  taskId: string
  sessionId: string
  status: "running" | "paused" | "completed" | "failed"
  startedAt: string
  endedAt?: string
  contextPackPath: string
  reportPath?: string
}
```

```ts id="a7c87n"
interface Task {
  id: string
  projectId: string
  title: string
  instruction: string
  status: "pending" | "running" | "blocked" | "completed" | "failed"
  createdAt: string
  updatedAt: string
  runIds: string[]
}
```

```ts id="30ujb6"
interface Approval {
  id: string
  runId: string
  action: string
  riskLevel: "medium" | "high"
  reason: string
  status: "pending" | "approved" | "denied"
  requestedAt: string
  resolvedAt?: string
}
```

---

# 10. Technology Stack

Core Runtime: TypeScript, Node.js. CLI: Commander, Ink. Validation: Zod. Storage: SQLite, JSON files, Markdown files. Logging: Pino, OpenTelemetry-compatible event model. Git: Git CLI, simple-git, GitHub API. Code Search: ripgrep, tree-sitter. Testing: Vitest, Playwright. Packaging: pnpm, tsx, tsup.

---

# 11. Open Source Reference Mapping

Claude Code 借鉴 workspace-first execution、tool runtime、permission model、context management、session continuity。Claude Agent SDK 借鉴 agent loop exposure、tool runtime concepts、MCP integration、hooks。OpenAI Agents SDK 借鉴 sessions、tracing、guardrails、tool abstraction、run model。iii Harness / iii Workers 借鉴 Harness as backend、worker runtime、project runtime thinking。Aider 借鉴 repo-first coding、Git-first workflow、automatic diff awareness、commit message generation。Continue 借鉴 workspace awareness、codebase indexing、AI review/checks concept。OpenCode 借鉴 terminal-first coding agent UX、workspace runtime、privacy-oriented local execution。LangGraph 仅借鉴 state machine、checkpoint、persistence，不采用 multi-agent graph、supervisor pattern、DAG-based agent architecture。

---

# 12. Security Design

Filesystem Security：禁止写 workspace 外部路径，禁止修改敏感系统路径，删除文件需审批，修改配置文件需审批。Shell Security：所有命令必须 timeout，所有命令必须记录 stdout/stderr，危险命令必须审批，禁止 curl | sh / wget | sh 自动执行，禁止 sudo 默认执行。Secret Security：不得读取或打印 secrets，日志必须 redaction，.env 内容不得进入 report，私钥不得进入 context pack。Network Security：Browser skill 默认只读，外部访问必须记录，抓取来源必须进入 report，敏感请求需审批。

---

# 13. Acceptance Criteria

P0 Runtime：harness create 可创建项目，harness open 可打开项目，harness run 可执行任务，harness resume 可恢复任务，harness rollback 可回滚任务。

P0 Context：可读取 AGENTS.md，可生成 Context Pack，可根据任务选择相关文件，可保存 context snapshot。

P0 State：可创建 session，可保存 task state，可创建 checkpoint，可恢复 checkpoint。

P0 Skills：filesystem 可读写，shell 可执行受控命令，git 可 status/diff/commit，github 可创建 PR，repo-scanner 可生成 repository map。

P0 Governance：高风险操作可拦截，审批记录可保存，secret 可 redacted，危险命令默认禁止。

P0 Verification：可运行 lint，可运行 typecheck，可运行 tests，可生成 verification report。

P0 Observability：所有 run 有 event log，所有 tool call 有记录，所有 approval 有记录，可生成 run report。

P0 Delivery：可生成 commit message，可生成 PR body，可创建 delivery report。

---

# 14. Final Definition

Harness OS 的最终定义：

```text id="th1uik"
Harness OS
=
Workspace Manager
+
Context Builder
+
State Manager
+
MCP Skill Runtime
+
Governance Engine
+
Verification Pipeline
+
Observability / Replay
+
Delivery Pipeline
```

Codex 的最终定义：

```text id="ar6ix8"
Codex
=
唯一执行 Agent
```

项目最终目标：

```text id="8rfaub"
让 Codex 能够在一个受控、可恢复、可观测、可验证的工程环境中长期维护和交付真实项目。
```
