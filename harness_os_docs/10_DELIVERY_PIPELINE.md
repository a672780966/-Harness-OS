# Harness OS Delivery Pipeline Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Delivery must be verified, governed, traceable, and reversible

---

# 1. 模块定位

Delivery Pipeline 是 Harness OS 的交付核心。它负责把 Codex 完成的工程任务，从本地修改转化为可审查、可追踪、可审批、可发布、可回滚的交付产物。

Delivery Pipeline 不只是执行 `git commit` 或创建 PR。它必须保证每次交付都具备任务来源、上下文来源、变更摘要、验证结果、风险说明、审批记录、交付报告、恢复路径。

最终定义：Codex 负责实现修改；Verification 负责质量门；Governance 负责审批边界；Delivery Pipeline 负责把结果变成可交付产物；Git / GitHub 负责承载交付事实；Observability 负责记录交付过程。

---

# 2. 设计目标

```text
1. 从 Task Manager 读取任务结果
2. 从 Verification System 读取验证结果
3. 从 Observability System 读取 run report
4. 从 Governance System 读取审批状态
5. 从 Git Skill 读取 diff 和 changed files
6. 生成 commit message
7. 生成 PR body
8. 生成 release notes
9. 生成 delivery report
10. 支持 commit / PR / release / deploy / rollback
11. 阻止未经验证或未经审批的高风险交付
12. 确保交付过程可审计、可恢复、可回放
```

---

# 3. 非目标

不做无审批自动部署、无验证自动合并、替代完整 CI/CD 平台、替代 GitHub / GitLab、替代 release manager、替代生产监控系统、绕过 Governance、绕过 Verification、直接修改远端 protected branch。

---

# 4. 核心原则

Verify Before Deliver：没有 verification result、changed files、run report、risk summary 不得交付。验证被跳过必须说明原因，并由 Governance 判断是否允许交付。

Approval Before Risky Delivery：push main、release、deploy、rollback deploy、force push、tag release、publish package、database migration delivery 必须审批。

Git Is Delivery Truth：交付事实必须以 Git 为基础，必须读取 current branch、git status、git diff、changed files、recent commits。

Report Everything：每次交付必须生成 Delivery Report，记录 task、run、commit、PR、verification、approval、risks、artifacts、final status。

Reversible Delivery：高风险交付必须有 rollback path、previous version、target environment、approval status、verification status。

---

# 5. 总体架构

```text
Delivery Pipeline
│
├── Delivery Planner
├── Delivery Guard
├── Git Delivery Adapter
├── GitHub Delivery Adapter
├── Commit Message Generator
├── PR Body Generator
├── Release Notes Generator
├── Deploy Adapter
├── Rollback Planner
├── Delivery Reporter
└── Delivery Event Recorder
```

---

# 6. Delivery Inputs

Delivery Pipeline 读取：Task Manager 的 task record/summary/changed files/status；Verification System 的 result/report；Observability System 的 run report/event log/trace；Governance System 的 approval events/policy decisions/risk status；Decision Manager 的 related decisions/active constraints；Git Skill 的 status/diff/branch/commit metadata；Context System 的 context pack path/context used summary。

---

# 7. Delivery Outputs

生成 commit message、git commit、PR body、pull request、release notes、release、deployment request、deployment event、rollback plan、delivery report。

---

# 8. Delivery Lifecycle

```text
draft
  -> planned
  -> guarded
  -> ready
  -> committed
  -> pull-requested
  -> released
  -> deployed
  -> completed

任何状态
  -> blocked
  -> failed
  -> rolled-back
```

---

# 9. Delivery Plan

```ts
export interface DeliveryPlan {
  id: string
  projectId: string
  taskId: string
  runId: string
  type: "commit" | "pull-request" | "release" | "deploy" | "rollback"
  status: "draft" | "planned" | "guarded" | "ready" | "blocked" | "failed" | "completed"
  source: { taskPath: string; runReportPath: string; verificationReportPath?: string; contextPackPath?: string }
  git: { branch: string; baseBranch?: string; changedFiles: string[]; diffStat: string; hasUserChanges: boolean }
  verification: { status: "passed" | "failed" | "partial" | "skipped" | "blocked"; reportPath?: string }
  approvals: { required: boolean; approvalIds: string[]; status: "not-required" | "pending" | "approved" | "denied" }
  risks: string[]
  artifacts: DeliveryArtifact[]
  createdAt: string
  updatedAt: string
}

export interface DeliveryArtifact {
  type: "commit-message" | "commit" | "pr-body" | "pull-request" | "release-notes" | "release" | "deploy-log" | "rollback-plan" | "delivery-report"
  path?: string
  url?: string
  summary: string
}
```

---

# 10. Delivery Guard

Guard Checks：task status、verification status、git status、changed files、protected branch、approval requirements、risk notes、secret redaction、delivery policy。

Blocking Conditions：verification failed、task failed、missing run report、missing changed files for code task、unresolved approval、approval denied、dirty git state conflicts、secret detected in diff、attempt to push protected branch without approval、attempt to deploy without approval、attempt to release without approval。

Warning Conditions：verification skipped with reason、verification partial、no tests found、documentation-only change、generated files changed、large diff、dependency added、architecture decision proposed but not accepted。

---

# 11. Commit Pipeline

Commit Preconditions：task summary、changed files、git diff、verification result、risk summary、run report；项目策略要求时必须有 approval。

Commit Message Format：`<type>(<scope>): <summary>`。Allowed types：feat、fix、refactor、test、docs、chore、build、ci、perf、revert。

```ts
export interface CommitMessageInput {
  taskTitle: string
  taskType: string
  changedFiles: string[]
  diffSummary: string
  verificationStatus: string
  relatedDecisions: string[]
}
export interface CommitMessageOutput { message: string; type: string; scope?: string; summary: string; body?: string }
```

Commit Flow：读取 task summary、git status、git diff、verification result，生成 message，运行 Delivery Guard，需要时审批，git add selected files，git commit，记录事件，写 delivery report。

---

# 12. Pull Request Pipeline

PR Preconditions：commit or committed changes、run report、verification report、changed files、risk notes、related decisions、target branch。

PR Body Required Sections：Task、Summary、Changed Files、Verification、Decisions、Risks、Follow-up、Run Report。

```ts
export interface PullRequestBodyInput {
  taskTitle: string
  taskSummary: string
  changedFiles: string[]
  verificationStatus: string
  verificationReportPath?: string
  runReportPath: string
  relatedDecisions: string[]
  risks: string[]
  followUps: string[]
}
```

PR Flow：检查分支且不是 protected target branch，读取 run/verification report，生成 PR body，运行 Delivery Guard，需要时审批，通过 GitHub Skill 创建 PR，记录 PR URL，写 delivery report。

---

# 13. Release Pipeline

Release Preconditions：accepted delivery plan、verification passed or approved exception、release notes、target version、target branch、approval、changelog entry、rollback plan。

Release Notes Required Sections：Summary、Changes、Fixes、Breaking Changes、Verification、Risks、Rollback Plan。

Release Flow：确定版本，读取上次 release 后完成任务，生成 release notes，检查验证状态，运行 Delivery Guard，请求审批，创建 tag，创建 release，写 delivery report，记录事件。

---

# 14. Deploy Pipeline

Deploy Preconditions：verification passed、delivery plan、target environment、approval、rollback path、deployment command/provider、run report、release notes if applicable。

Deploy Risk Levels：development deploy medium risk；staging deploy medium risk；production deploy high risk。

Deploy Flow：识别环境，读取 verification result 和 policy，生成 deployment plan 和 rollback plan，请求审批，通过 Delivery Skill 部署，记录日志，写 deployment report，标记 completed 或 failed。

---

# 15. Rollback Pipeline

Rollback Preconditions：failed or risky deployment、previous known good version、rollback method、approval、deployment report、affected environment。

Rollback Flow：读取部署报告，识别 previous version，生成 rollback plan，请求审批，执行 rollback，验证结果，写报告，记录事件。

---

# 16. Delivery Report

Path：`.project/reports/delivery/<delivery-id>.md`

```markdown
# Delivery Report: <delivery-id>

## Task

## Run

## Delivery Type

## Final Status

## Git State

## Changed Files

## Verification

## Approvals

## Artifacts

## Risks

## Follow-up

## Rollback Plan

## Events
```

---

# 17. Delivery Event Model

Event Types：delivery.planned、delivery.guard.started、delivery.guard.passed、delivery.guard.blocked、delivery.commit.generated、delivery.commit.created、delivery.pr.generated、delivery.pr.created、delivery.release.generated、delivery.release.created、delivery.deploy.started、delivery.deploy.completed、delivery.deploy.failed、delivery.rollback.planned、delivery.rollback.completed、delivery.failed、delivery.completed。

```ts
export interface DeliveryEvent {
  eventId: string
  projectId: string
  taskId?: string
  runId?: string
  deliveryId: string
  type: string
  timestamp: string
  actor: "codex" | "harness" | "skill" | "user"
  summary: string
  artifact?: DeliveryArtifact
  riskLevel?: "low" | "medium" | "high"
  approvalId?: string
}
```

---

# 18. Delivery Config

Project Delivery Config 位于 `.project/state/manifest.json`：

```json
{
  "delivery": {
    "defaultBaseBranch": "main",
    "allowAutoCommit": false,
    "allowAutoPush": false,
    "allowAutoPR": false,
    "allowDeploy": false,
    "requireApprovalForRelease": true,
    "requireApprovalForDeploy": true,
    "protectedBranches": ["main", "master"],
    "commitMessageFormat": "conventional"
  }
}
```

Global Delivery Config 位于 `~/.harness/delivery.json`：

```json
{
  "defaultPRProvider": "github",
  "requireApprovalForPushMain": true,
  "requireApprovalForProductionDeploy": true,
  "allowForcePush": false
}
```

---

# 19. Delivery Integration with Task Manager

Task Manager 提供 task id、title、type、summary、changed files、verification status、risks、follow-ups。Delivery 完成后，Task Manager 必须更新 delivery id/status、commit hash、PR URL、release URL、deployment status。

---

# 20. Delivery Integration with Verification

verification failed 或 blocked 阻止交付；verification skipped 需要审批或标记 high risk；verification partial 需要 risk note 和可能审批；verification passed 允许进入下一步 guard checks。

---

# 21. Delivery Integration with Governance

commit/PR 根据项目策略判断是否审批；release、deploy、rollback deploy、push main 必须审批；force push 默认禁止。

---

# 22. Delivery Integration with Observability

Delivery 必须记录 delivery events、approval events、git operations、artifact paths、external URLs、final delivery status。Run Report 必须引用 Delivery Report，Delivery Report 必须引用 Run Report 和 Verification Report。

---

# 23. Delivery Integration with Decision Manager

架构变更交付必须检查 related ADR 是否存在和 accepted。若没有 ADR 但 diff 显示重大架构变化，应要求创建 proposed ADR。

---

# 24. Delivery Integration with GitHub Skill

GitHub Skill 执行 create_pr、update_pr、comment_pr、request_review、create_release。Delivery Pipeline 负责准备内容、检查验证、审批、组织报告、记录结果。GitHub Skill 不负责决策。

---

# 25. Delivery Failure Handling

Commit Failure 记录 git status、failed command、stderr summary、recoverable、suggested fix。

PR Failure 记录 target branch、provider error、auth status、recoverable、suggested fix。

Release Failure 记录 version、tag status、provider error、recoverable、suggested fix。

Deploy Failure 记录 environment、deployment command/provider、failure stage、logs summary、rollback path、checkpoint id。

---

# 26. CLI Commands

Delivery Commands：`harness deliver`、`harness deliver --commit`、`harness deliver --pr`、`harness deliver --release`、`harness deliver --deploy <environment>`、`harness deliver --rollback <deployment-id>`。

Inspection Commands：`harness delivery status`、`harness delivery report <delivery-id>`、`harness delivery plan <run-id>`。

---

# 27. Implementation Checklist

P0：Delivery plan schema、Delivery Guard、commit message generator、PR body generator、delivery report writer、Task Manager 集成、Verification Result 集成、Governance approval 集成、Git Skill 集成、delivery event logging。

P1：GitHub PR creation、release notes generator、release flow、rollback plan generation、delivery config、delivery CLI commands、run report linking。

P2：deploy adapters、environment policy、package publishing、advanced release automation、multi-provider Git hosting、delivery dashboard。

---

# 28. Acceptance Criteria

```text
1. 没有 verification result 不得交付
2. verification failed 不得交付
3. run report 缺失不得创建 PR
4. release 必须审批
5. deploy 必须审批
6. push main 必须审批
7. force push 默认禁止
8. PR body 必须包含任务、变更、验证、风险、报告
9. Delivery Report 必须生成
10. Delivery Event 必须记录
11. Delivery 必须读取 Task Manager 状态
12. Delivery 必须读取 Verification Result
13. Delivery 必须经过 Governance
14. Delivery 必须记录外部 artifact URL
15. 部署必须有 rollback plan
16. 失败交付必须写 failure details
17. 交付不得绕过 Git
18. GitHub Skill 不得自行决策
19. 架构变更交付必须关联 ADR
20. Delivery Report 必须可被 Run Report 引用
```

---

# 29. Final Definition

Delivery Pipeline = 把 Codex 完成的工程变更，在验证、审批、审计和恢复边界内转化为可交付产物。

边界关系：Codex 负责实现；Verification 负责质量门；Governance 负责审批；Git 负责事实；GitHub / Delivery Skill 负责外部动作；Observability 负责记录；Delivery Pipeline 负责组织交付。
