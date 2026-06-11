# Harness OS Task / Decision / Project Manager Design

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Project-first, Task-driven, Decision-recorded, Git-backed

---

# 1. 模块定位

Task / Decision / Project Manager 是 Harness OS 的项目治理核心。

它负责把 Codex 的一次性对话执行，变成可追踪、可恢复、可审查、可交付的项目工程活动。

三个 Manager 的边界：

```text
Project Manager
  管理项目生命周期、项目结构、项目配置、项目状态。

Task Manager
  管理任务生命周期、任务上下文、任务执行状态、任务结果。

Decision Manager
  管理架构决策、产品决策、技术选型、重大变更记录。
```

它们共同保证：

```text
Codex 执行的是项目任务
而不是孤立聊天请求
```

---

# 2. 设计目标

## 2.1 Project Manager 目标

Project Manager 必须实现：

```text
1. 创建项目
2. 打开项目
3. 初始化项目 Harness 状态
4. 修复缺失项目结构
5. 识别项目技术栈
6. 维护项目 manifest
7. 注册项目可用 Skills
8. 建立项目 repository map
9. 管理项目级配置
10. 支持项目恢复、归档、迁移
```

## 2.2 Task Manager 目标

Task Manager 必须实现：

```text
1. 将用户请求转化为可执行任务
2. 创建 task record
3. 管理 task lifecycle
4. 关联 run、context、checkpoint、report
5. 记录 changed files
6. 记录 verification result
7. 支持 pause / resume / fail / complete
8. 生成 task summary
9. 避免任务历史只存在聊天里
```

## 2.3 Decision Manager 目标

Decision Manager 必须实现：

```text
1. 记录架构决策
2. 记录重大产品决策
3. 记录技术栈变更
4. 记录安全策略变更
5. 区分 proposed / accepted / rejected / superseded
6. 支持 Codex 提议决策，但不自动生效
7. 让 Context System 可读取相关决策
8. 让未来任务继承项目约束
```

---

# 3. 非目标

这三个模块不做：

```text
多 Agent 分工
模型路由
Workflow DAG 编排
独立知识库
外部 memory repo
向量数据库决策检索
自动无审批架构重写
自动部署决策
```

所有语义判断仍由 Codex 完成。

Manager 负责结构化、状态化、持久化、验证化。

---

# 4. 总体关系

```text
Harness OS
│
├── Project Manager
│   ├── owns project identity
│   ├── owns .project structure
│   ├── owns project manifest
│   └── owns repository map
│
├── Task Manager
│   ├── owns task records
│   ├── owns task lifecycle
│   ├── links run/context/checkpoint/report
│   └── owns task summary
│
└── Decision Manager
    ├── owns ADR records
    ├── owns decision lifecycle
    ├── owns architecture constraints
    └── feeds Context System
```

三者与其他系统关系：

```text
Project Manager
  -> Context System
  -> State System
  -> MCP Skill Runtime
  -> Verification System

Task Manager
  -> Context System
  -> Agent Runtime Adapter
  -> Checkpoint System
  -> Observability System
  -> Delivery System

Decision Manager
  -> Context System
  -> Governance System
  -> Approval Gate
  -> Delivery System
```

---

# 5. Project Repository Layout

每个被 Harness OS 管理的项目必须包含：

```text
repo/
│
├── AGENTS.md
├── .project/
│   ├── state/
│   │   ├── project.json
│   │   ├── project.md
│   │   ├── manifest.json
│   │   ├── tech-stack.md
│   │   └── repository-map.md
│   │
│   ├── tasks/
│   │   ├── active/
│   │   ├── completed/
│   │   └── failed/
│   │
│   ├── decisions/
│   │   ├── ADR-0001-*.md
│   │   └── ADR-0002-*.md
│   │
│   ├── reports/
│   │   ├── runs/
│   │   ├── verification/
│   │   └── delivery/
│   │
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

# 6. Project Manager Design

## 6.1 Responsibilities

Project Manager 负责项目生命周期：create project、open project、import project、repair project、archive project、restore project、migrate project、inspect project。

## 6.2 Project Lifecycle

```text
uninitialized
  -> initialized
  -> active
  -> paused
  -> archived
  -> restored
```

状态说明：uninitialized 是普通 repo，还没有 AGENTS.md 或 .project/；initialized 已注入 AGENTS.md 和 .project/，但未运行任务；active 当前正在被 Harness 管理；paused 没有 active run，但可恢复；archived 项目被归档；restored 从归档或备份恢复。

## 6.3 Project Create Flow

命令：

```bash
harness create <project-name>
```

流程：

```text
1. 创建项目目录
2. 初始化 Git repo
3. 写入 AGENTS.md 模板
4. 创建 .project/ 结构
5. 写入 .project/state/project.json
6. 写入 .project/state/project.md
7. 写入 .project/state/manifest.json
8. 检测技术栈
9. 写入 .project/state/tech-stack.md
10. 扫描仓库
11. 写入 .project/state/repository-map.md
12. 注册默认 Skills
13. 创建 initial checkpoint
14. 生成 project-created report
```

## 6.4 Project Open Flow

命令：

```bash
harness open <repo-path>
```

流程：

```text
1. 校验路径存在
2. 校验是否 Git repo
3. 检查 AGENTS.md
4. 检查 .project/
5. 读取 manifest
6. 检测技术栈
7. 刷新 repository map
8. 读取 git status
9. 检查 active tasks
10. 检查 resumable sessions
11. 生成 project open summary
```

如果缺失 AGENTS.md，阻止执行 run，提示 harness init。如果缺失部分 .project/ 子目录，自动 repair 并记录 repair report。

## 6.5 Project Repair Flow

命令：

```bash
harness repair
```

修复内容：创建缺失目录、补齐 manifest 字段、刷新 repository map、重建 tech-stack.md、检查 task/report/checkpoint 索引、检查 AGENTS.md 必填章节。

不得自动覆盖 AGENTS.md、decisions/*、已存在 task records、已存在 reports，除非用户明确批准。

## 6.6 Project Manifest

路径：

```text
.project/state/manifest.json
```

Schema：

```ts
export interface ProjectManifest {
  schemaVersion: string
  projectId: string
  projectName: string
  projectType:
    | "web-app"
    | "backend-service"
    | "cli"
    | "library"
    | "agent-harness"
    | "unknown"

  rootPath: string
  defaultBranch: string

  language: {
    primary: string
    secondary: string[]
  }

  runtime: {
    name: string
    version?: string
  }

  packageManager?: {
    name: "pnpm" | "npm" | "yarn" | "uv" | "pip" | "poetry" | "go" | "cargo" | "unknown"
    lockfile?: string
  }

  commands: {
    install?: string
    dev?: string
    build?: string
    lint?: string
    typecheck?: string
    test?: string
    e2e?: string
  }

  skills: {
    enabled: string[]
    disabled: string[]
  }

  paths: {
    source: string[]
    tests: string[]
    docs: string[]
    config: string[]
  }

  createdAt: string
  updatedAt: string
}
```

## 6.7 Project State Markdown

路径：`.project/state/project.md`

格式：

```markdown
# Project State

## Identity

## Purpose

## Current Status

## Architecture Summary

## Tech Stack

## Important Constraints

## Active Work

## Known Risks

## Last Updated
```

该文件供 Codex 快速读取项目当前状态。

## 6.8 Repository Map

路径：`.project/state/repository-map.md`

包含主要目录、主要模块、入口文件、测试目录、配置文件、构建脚本、关键依赖、已知边界。Repository Map 由 Repo Scanner Skill 生成和更新。

---

# 7. Task Manager Design

## 7.1 Responsibilities

Task Manager 负责把用户请求变成项目任务：create task、normalize task、start task、pause task、resume task、block task、complete task、fail task、summarize task、link task to runs、link task to reports、link task to changed files。

## 7.2 Task Lifecycle

```text
created
  -> ready
  -> running
  -> blocked
  -> paused
  -> verifying
  -> completed

running
  -> failed

blocked
  -> running

paused
  -> running
```

状态说明：created 用户请求已记录但未构建 context；ready context 已准备；running Codex 正在执行；blocked 等待审批、用户确认或缺失信息；paused 主动暂停；verifying 正在验证；completed 已完成并生成报告；failed 任务失败并生成失败报告。

## 7.3 Task Create Flow

命令：

```bash
harness run "<user task>"
```

流程：

```text
1. 接收用户原始任务
2. 生成 task id
3. 规范化任务标题
4. 推断 task type
5. 提取显式文件、命令、验收暗示
6. 写入 .project/tasks/active/<task-id>.md
7. 写入 task state JSON
8. 创建 run id
9. 通知 Context System 构建 Context Pack
10. 状态变为 ready
```

## 7.4 Task Types

```ts
export type TaskType =
  | "feature"
  | "bugfix"
  | "refactor"
  | "test"
  | "docs"
  | "investigation"
  | "delivery"
  | "maintenance"
  | "architecture"
  | "unknown"
```

## 7.5 Task Record Markdown

路径：`.project/tasks/active/<task-id>.md`

模板：

```markdown
# Task: <title>

Task ID: <task-id>  
Status: <status>  
Type: <type>  
Created At: <created-at>  
Updated At: <updated-at>

## User Instruction

<original user instruction>

## Normalized Goal

<normalized task goal>

## Acceptance Criteria

- <criterion 1>
- <criterion 2>

## Context Links

- Context Pack:
- Related Decisions:
- Related Reports:

## Execution Runs

- <run-id>

## Changed Files

- <path>

## Verification

Status: pending

Commands:

Results:

## Risks

- <risk>

## Follow-up

- <item>

## Final Summary

<pending>
```

## 7.6 Task State JSON

路径：`.project/tasks/active/<task-id>.json`

Schema：

```ts
export interface TaskState {
  taskId: string
  projectId: string
  title: string
  type: TaskType
  status:
    | "created"
    | "ready"
    | "running"
    | "blocked"
    | "paused"
    | "verifying"
    | "completed"
    | "failed"

  userInstruction: string
  normalizedGoal: string
  acceptanceCriteria: string[]

  explicitFiles: string[]
  explicitCommands: string[]

  runIds: string[]
  contextPackIds: string[]
  checkpointIds: string[]
  reportIds: string[]
  decisionIds: string[]

  changedFiles: string[]

  verification: {
    status: "pending" | "passed" | "failed" | "partial" | "skipped"
    commands: string[]
    reportPath?: string
  }

  risks: string[]
  followUps: string[]

  createdAt: string
  updatedAt: string
  completedAt?: string
}
```

## 7.7 Task Completion Flow

当 Codex 认为任务完成时，Task Manager 必须收集 changed files、收集 git diff summary、触发 Verification System、写 verification result、生成 task summary、生成 run report、更新 task markdown、移动 active -> completed、写 completion event、通知 Delivery System。如果验证失败，则状态变为 failed 或 blocked，写 failure report，保存 checkpoint，提供 recovery path。

## 7.8 Task Directory Movement Rules

完成任务：`.project/tasks/active/<task-id>.md` -> `.project/tasks/completed/<task-id>.md`。失败任务：`.project/tasks/active/<task-id>.md` -> `.project/tasks/failed/<task-id>.md`。JSON 同步移动。移动必须由 Task Manager 完成，不允许 Codex 直接随意移动。

---

# 8. Decision Manager Design

## 8.1 Responsibilities

Decision Manager 管理项目长期决策，包括 architecture decisions、product decisions、technical stack decisions、security decisions、delivery decisions、governance decisions。

## 8.2 Decision Lifecycle

```text
proposed
  -> accepted
  -> rejected
  -> superseded
```

proposed 表示 Codex 或用户提出但尚未生效；accepted 表示用户或审批规则确认，成为项目约束；rejected 表示明确拒绝；superseded 表示被新 decision 替代。

## 8.3 Decision Types

```ts
export type DecisionType =
  | "architecture"
  | "product"
  | "technology"
  | "security"
  | "delivery"
  | "governance"
  | "process"
```

## 8.4 ADR File Naming

路径：`.project/decisions/`

格式：

```text
ADR-0001-use-single-agent-runtime.md
ADR-0002-use-sqlite-for-local-state.md
ADR-0003-protect-agents-md-with-approval.md
```

编号必须递增。

## 8.5 ADR Markdown Template

```markdown
# ADR-0001: <Decision Title>

Status: proposed  
Type: architecture  
Created At: <created-at>  
Updated At: <updated-at>  
Related Tasks:
- <task-id>

## Context

Why this decision is needed.

## Decision

What decision is being made.

## Options Considered

### Option A

Pros:
- 

Cons:
- 

### Option B

Pros:
- 

Cons:
- 

## Consequences

Positive:
- 

Negative:
- 

Risks:
- 

## Approval

Approved By:
Approved At:

## Supersedes

None

## Superseded By

None
```

## 8.6 Decision State JSON

```ts
export interface DecisionState {
  id: string
  number: number
  title: string
  slug: string
  type: DecisionType
  status: "proposed" | "accepted" | "rejected" | "superseded"

  context: string
  decision: string
  options: DecisionOption[]
  consequences: {
    positive: string[]
    negative: string[]
    risks: string[]
  }

  relatedTasks: string[]
  relatedFiles: string[]

  supersedes?: string[]
  supersededBy?: string

  approval?: {
    approvedBy?: string
    approvedAt?: string
    approvalRunId?: string
  }

  createdAt: string
  updatedAt: string
}
```

## 8.7 Decision Creation Rules

Codex 可以创建 proposed 决策。Codex 不得自动把重大决策设为 accepted。需要审批的决策包括改变系统架构、新增核心依赖、改变状态存储、改变权限模型、改变任务流程、改变交付流程、引入 multi-agent、引入 model router、引入外部 memory/vector 系统、修改 AGENTS.md 规则。

## 8.8 Decision Acceptance Flow

```text
1. Codex 或用户创建 proposed ADR
2. Decision Manager 校验格式
3. Governance System 判断是否需要审批
4. 用户审批
5. Decision Manager 更新 status = accepted
6. 写 approval metadata
7. Context System 后续加载该 ADR
8. Observability 记录 decision.accepted 事件
```

## 8.9 Decision Supersede Flow

```text
1. 创建新 proposed ADR
2. 在新 ADR 标记 supersedes: old ADR
3. 审批新 ADR
4. 新 ADR 变 accepted
5. 旧 ADR 变 superseded
6. 旧 ADR 写 supersededBy
7. Context System 不再把旧 ADR 作为 active constraint
```

---

# 9. Manager APIs

```ts
export interface ProjectManager {
  create(input: CreateProjectInput): Promise<Project>
  open(input: OpenProjectInput): Promise<Project>
  inspect(projectId: string): Promise<ProjectInspection>
  repair(projectId: string): Promise<ProjectRepairResult>
  archive(projectId: string): Promise<void>
  restore(projectId: string): Promise<Project>
  updateManifest(projectId: string, patch: Partial<ProjectManifest>): Promise<ProjectManifest>
}
```

```ts
export interface TaskManager {
  create(input: CreateTaskInput): Promise<TaskState>
  start(taskId: string): Promise<TaskState>
  pause(taskId: string, reason: string): Promise<TaskState>
  resume(taskId: string): Promise<TaskState>
  block(taskId: string, reason: string): Promise<TaskState>
  complete(taskId: string, input: CompleteTaskInput): Promise<TaskState>
  fail(taskId: string, input: FailTaskInput): Promise<TaskState>
  linkRun(taskId: string, runId: string): Promise<TaskState>
  linkContext(taskId: string, contextPackId: string): Promise<TaskState>
  linkCheckpoint(taskId: string, checkpointId: string): Promise<TaskState>
  linkDecision(taskId: string, decisionId: string): Promise<TaskState>
}
```

```ts
export interface DecisionManager {
  propose(input: ProposeDecisionInput): Promise<DecisionState>
  accept(decisionId: string, approval: DecisionApproval): Promise<DecisionState>
  reject(decisionId: string, reason: string): Promise<DecisionState>
  supersede(oldDecisionId: string, newDecisionId: string): Promise<void>
  listActive(projectId: string): Promise<DecisionState[]>
  findRelevant(input: FindRelevantDecisionsInput): Promise<DecisionState[]>
}
```

---

# 10. Data Models

包含 Project、CreateProjectInput、CreateTaskInput、ProposeDecisionInput 等 TypeScript 数据结构，用于实现 Project/Task/Decision 三个 Manager 的持久化与接口契约。

---

# 11. Event Model

Managers 必须产生事件：project.created、project.opened、project.repaired、project.archived、project.restored、project.manifest.updated、project.repository_map.updated、task.created、task.ready、task.started、task.paused、task.resumed、task.blocked、task.verifying、task.completed、task.failed、task.summary.created、decision.proposed、decision.accepted、decision.rejected、decision.superseded、decision.updated。

```ts
export interface ManagerEvent {
  eventId: string
  projectId: string
  taskId?: string
  decisionId?: string
  runId?: string
  type: string
  timestamp: string
  payload: unknown
}
```

所有事件进入 Observability System。

---

# 12. Integration with Context System

Context System 必须读取 Project Manager 的 project manifest、project state、repository map、tech stack；Task Manager 的 current task、active task records、recent completed tasks、failed task reports；Decision Manager 的 accepted decisions、related proposed decisions、superseded decision metadata。Context Pack 必须包含 project summary、current task、active constraints、relevant decisions、recent task lessons、known failures。

---

# 13. Integration with Governance System

Governance System 必须保护 AGENTS.md、.project/decisions/、.project/state/manifest.json、.project/state/project.md、delivery settings、security settings。需要审批的 Manager 操作包括 modify AGENTS.md、accept ADR、supersede ADR、archive project、restore project、delete task record、delete decision record、modify completed task、modify accepted decision、change project manifest core fields。

---

# 14. Integration with Delivery System

Task 完成后，Delivery System 读取 task summary、changed files、verification report、risk notes、related decisions，生成 commit message、PR body、release note、delivery report。

PR Body 必须包含 Task、Summary、Changed Files、Verification、Decisions、Risks、Follow-up。

---

# 15. CLI Commands

Project Commands：`harness create <name>`、`harness open <path>`、`harness inspect`、`harness repair`、`harness archive`、`harness restore`。

Task Commands：`harness task list`、`harness task show <task-id>`、`harness task run "<instruction>"`、`harness task pause <task-id>`、`harness task resume <task-id>`、`harness task complete <task-id>`、`harness task fail <task-id>`。Alias：`harness run "<instruction>"`、`harness resume <task-id>`。

Decision Commands：`harness decision list`、`harness decision show <decision-id>`、`harness decision propose`、`harness decision accept <decision-id>`、`harness decision reject <decision-id>`、`harness decision supersede <old-id> <new-id>`。

---

# 16. File Protection Rules

以下文件不得被 Codex 直接无审批修改：AGENTS.md、.project/state/manifest.json、.project/decisions/*.md when status = accepted、.project/decisions/*.json when status = accepted、.project/tasks/completed/*、.project/tasks/failed/*。

允许 Codex 自动写入：.project/tasks/active/*、.project/reports/runs/*、.project/reports/verification/*、.project/context/*、.project/checkpoints/*。

---

# 17. Failure Handling

Project Open Failure 的原因包括 missing AGENTS.md、invalid manifest、not a git repo、corrupted .project、unsupported permissions。处理：生成 project-open-failure report，提示 repair/init，不得启动 Codex run。

Task Failure 的原因包括 context build failed、tool call failed、test failed、approval denied、conflicting instructions、workspace dirty conflict。处理：状态变为 failed 或 blocked，写 failure report，保存 checkpoint，记录 recovery path。

Decision Failure 的原因包括 invalid ADR format、duplicate ADR number、acceptance without approval、supersede missing target、attempt to modify accepted ADR directly。处理：阻止写入，写 decision error event，返回修复建议。

---

# 18. Reports

Project Report 路径：`.project/reports/project/<timestamp>-project-report.md`，包含 Project、State、Tech Stack、Repository Map、Active Tasks、Active Decisions、Risks。

Task Report 路径：`.project/reports/runs/<run-id>.md`，包含 Task、Context Used、Execution Summary、Tool Calls、Changed Files、Verification、Decisions、Risks、Final Status。

Decision Report 路径：`.project/reports/decisions/<decision-id>.md`，包含 Decision、Status、Approval、Related Tasks、Consequences、Current Active Constraints。

---

# 19. Implementation Checklist

P0 Project Manager：create project、open project、validate AGENTS.md、create .project structure、read/write manifest、detect tech stack、generate repository map、repair missing directories。

P0 Task Manager：create task、normalize task、write active task markdown、write task json、link run id、link context pack id、track changed files、complete task、fail task、move active -> completed/failed。

P0 Decision Manager：create proposed ADR、validate ADR schema、list active accepted decisions、find relevant decisions by keyword/path、accept decision with approval metadata、reject decision、supersede decision。

P1 Project Manager：archive project、restore project、project migration、multi-project registry、project doctor。

P1 Task Manager：task dependency、task priority、task resume from checkpoint、task report index、task search。

P1 Decision Manager：decision graph、decision impact analysis、decision conflict detection、decision timeline。

---

# 20. Acceptance Criteria

Project Manager Acceptance：新项目可通过 harness create 创建，已有项目可通过 harness open 打开，缺失 .project 子目录可自动 repair，缺失 AGENTS.md 时必须阻止任务执行，manifest.json 必须可读写和校验，tech-stack.md 可自动生成，repository-map.md 可自动生成，项目状态可进入 Context Pack。

Task Manager Acceptance：用户任务必须生成 task id，每个任务必须有 markdown record，每个任务必须有 JSON state，每个任务必须关联 run id，每个任务必须关联 context pack，任务完成必须生成 summary，任务失败必须生成 failure report，完成任务必须移动到 completed，失败任务必须移动到 failed，任务状态必须可恢复。

Decision Manager Acceptance：Codex 可创建 proposed ADR，accepted ADR 必须经过审批，active decisions 可被 Context System 读取，superseded ADR 不应作为 active constraint，ADR 编号必须递增，ADR 格式必须校验，accepted ADR 不能无审批修改，架构变更必须生成或更新 ADR。

---

# 21. Final Definition

Project Manager 让 Codex 知道：

```text
我在哪个项目里工作。
```

Task Manager 让 Codex 知道：

```text
我正在完成哪个工程任务。
```

Decision Manager 让 Codex 知道：

```text
我必须遵守哪些长期项目决策。
```

三者共同构成 Harness OS 的项目治理骨架：

```text
Project = 项目事实源
Task = 当前执行单元
Decision = 长期约束源
```

它们把 Codex 的执行从“聊天响应”提升为“项目操作”。
