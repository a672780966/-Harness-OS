# Harness OS Verification and Observability Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Every task must be verifiable, traceable, replayable, and reportable

---

# 1. 模块定位

Verification and Observability 是 Harness OS 的质量保障与审计核心。

它的目标是确保 Codex 对项目的每一次执行，都不是不可追踪的聊天输出，而是可验证、可追踪、可审计、可恢复、可回放、可交付。

Verification 负责回答：这次修改是否正确？测试是否通过？构建是否通过？类型检查是否通过？还有哪些风险？

Observability 负责回答：Codex 做了什么？用了哪些上下文？调用了哪些 Skills？改了哪些文件？哪里失败了？为什么被审批或阻止？如何重放这次执行？

---

# 2. 设计目标

```text
1. 为每个 task/run 建立验证流程
2. 自动发现 lint/typecheck/test/build 命令
3. 运行验证命令并记录结果
4. 支持 partial/skipped/failed/passed 状态
5. 将验证结果绑定到 task、run、delivery
6. 记录每次 run 的事件流
7. 记录 Context Pack 使用情况
8. 记录每次 Skill 调用
9. 记录文件变更、审批、阻止、失败事件
10. 生成 Run Report
11. 生成 Verification Report
12. 支持 replay 和 failure diagnosis
```

---

# 3. 非目标

不替代测试框架、CI/CD 平台、外部 APM、完整 SIEM；不自动证明代码完全正确；不做无审批自动部署；不做多 Agent Review、独立 Reviewer Agent、独立评测模型。

Codex 仍然是唯一执行 Agent。Verification System 负责确定性验证。Observability System 负责记录和审计。

---

# 4. 核心原则

Verify Before Complete：任何代码任务在完成前必须验证，至少生成 changed files、verification status、risk notes、run report。

Deterministic Verification First：优先使用项目已有命令：lint、typecheck、test、build、e2e。不得凭空编造验证命令。命令来源优先级为 AGENTS.md、manifest、package/pyproject/Makefile/go.mod/Cargo.toml、README/docs、Codex 推断并标记 uncertainty。

Observable by Default：每个 run 必须有 event log；每次工具调用、文件修改、验证、审批、失败都必须记录。

Replayable Runs：Harness OS 必须保存足够信息，使后续可以回答执行过程、上下文、工具调用、验证、失败和恢复路径。

Verification Does Not Mean Deployment：验证通过不等于自动交付或自动部署。Delivery 仍需遵守 Governance 和 Approval Gate。

---

# 5. 总体架构

```text
Verification and Observability
│
├── Verification System
│   ├── Command Detector
│   ├── Verification Planner
│   ├── Verification Runner
│   ├── Result Parser
│   ├── Risk Analyzer
│   └── Verification Reporter
│
└── Observability System
    ├── Event Logger
    ├── Run Trace Store
    ├── Tool Call Recorder
    ├── Context Usage Recorder
    ├── File Change Recorder
    ├── Approval Recorder
    ├── Failure Recorder
    ├── Replay Store
    └── Run Reporter
```

---

# 6. Verification System

负责检测验证命令、生成验证计划、执行命令、记录 stdout/stderr 摘要、解析 exit code、判断验证状态、生成 verification report、把结果绑定 task/run/delivery。

验证命令来源：AGENTS.md、`.project/state/manifest.json`、package.json、pnpm-lock.yaml、yarn.lock、package-lock.json、pyproject.toml、requirements.txt、Makefile、go.mod、Cargo.toml、README.md、CI config。

Command Types：install、lint、typecheck、unit-test、integration-test、e2e-test、build、format-check、security-check、custom。

```ts
export type VerificationStatus = "pending" | "running" | "passed" | "failed" | "partial" | "skipped" | "blocked"
```

pending 尚未开始；running 正在验证；passed 所有必须验证项通过；failed 至少一个必须验证项失败；partial 部分通过，部分未运行或失败；skipped 验证被跳过且必须说明原因；blocked 缺少依赖、命令不可用、权限不足或等待审批。

---

# 7. Verification Plan

```ts
export interface VerificationPlan {
  id: string
  projectId: string
  taskId: string
  runId: string
  commands: VerificationCommand[]
  required: string[]
  optional: string[]
  source: "agents-md" | "manifest" | "package-manifest" | "makefile" | "ci-config" | "inferred"
  uncertainty: string[]
  createdAt: string
}

export interface VerificationCommand {
  id: string
  name: string
  type: "install" | "lint" | "typecheck" | "unit-test" | "integration-test" | "e2e-test" | "build" | "format-check" | "security-check" | "custom"
  command: string
  cwd: string
  required: boolean
  timeoutMs: number
  source: "agents-md" | "manifest" | "package-json" | "makefile" | "pyproject" | "go-mod" | "cargo" | "readme" | "ci" | "inferred"
}
```

---

# 8. Verification Flow

Standard Flow：Task Manager 请求验证；Verification System 检测命令并创建计划；Governance 检查命令安全；Shell/Test Runner Skill 执行命令；Observability 记录事件；Result Parser 解析输出；Verification Reporter 写报告；Task Manager 更新状态；Delivery System 读取结果。

Verification Order：static inspection、lint、typecheck、unit tests、integration tests、e2e tests、build、AI risk review by Codex、final risk summary。

When Commands Are Missing：标记 skipped 或 blocked，说明未发现命令，记录查找过的文件，提供建议命令，不得谎称验证通过。

When Verification Fails：标记 failed，保存 stdout/stderr 摘要，记录失败命令和阶段，生成 failure notes，创建 checkpoint，通知 Task Manager，允许 Codex 继续修复或请求用户确认。

---

# 9. Verification Result

```ts
export interface VerificationResult {
  id: string
  projectId: string
  taskId: string
  runId: string
  status: "passed" | "failed" | "partial" | "skipped" | "blocked"
  commands: VerificationCommandResult[]
  summary: string
  risks: string[]
  skippedReasons: string[]
  reportPath: string
  startedAt: string
  endedAt: string
  durationMs: number
}

export interface VerificationCommandResult {
  commandId: string
  name: string
  type: string
  command: string
  cwd: string
  exitCode: number | null
  status: "passed" | "failed" | "skipped" | "blocked" | "timeout"
  stdoutSummary: string
  stderrSummary: string
  outputPath?: string
  durationMs: number
}
```

---

# 10. Verification Report

路径：`.project/reports/verification/<run-id>.md`

```markdown
# Verification Report: <run-id>

## Task

## Verification Status

## Commands Run

| Name | Command | Status | Exit Code | Duration |
|---|---|---|---|---|

## Output Summary

## Failures

## Skipped Checks

## Risks

## Final Assessment
```

---

# 11. Observability System

负责记录 run lifecycle、task lifecycle、context build、skill calls、file changes、git operations、approval events、policy decisions、verification commands、delivery actions、failures、checkpoints。

Event Log Storage：`.project/reports/events/<run-id>.jsonl`。每行一个事件，便于流式写入和重放。

Run Trace Storage：`.project/reports/traces/<run-id>.json`。用于聚合视图和 replay。

---

# 12. Event Model

Event Types：run.started、run.paused、run.resumed、run.completed、run.failed；task.created、task.ready、task.started、task.blocked、task.verifying、task.completed、task.failed；context.build.started、context.build.completed、context.refreshed、context.snapshot.saved；skill.called、skill.completed、skill.failed、skill.blocked；file.read、file.written、file.edited、file.deleted、file.blocked；git.status.read、git.diff.read、git.commit.created、git.operation.blocked；policy.checked、policy.allowed、policy.denied、approval.requested、approval.granted、approval.denied；verification.started、verification.command.started、verification.command.completed、verification.command.failed、verification.completed、verification.failed；delivery.started、delivery.commit.generated、delivery.pr.generated、delivery.completed、delivery.blocked；checkpoint.created、checkpoint.restored；secret.redacted、security.violation。

```ts
export interface HarnessEvent {
  eventId: string
  projectId: string
  taskId?: string
  runId?: string
  sessionId?: string
  type: string
  timestamp: string
  actor: "user" | "codex" | "harness" | "skill" | "system"
  summary: string
  payload?: unknown
  riskLevel?: "low" | "medium" | "high"
  relatedPaths?: string[]
  relatedCommand?: string
  redacted: boolean
}
```

---

# 13. Run Trace

```ts
export interface RunTrace {
  runId: string
  projectId: string
  taskId: string
  sessionId?: string
  status: "running" | "paused" | "completed" | "failed" | "blocked"
  startedAt: string
  endedAt?: string
  contextPackIds: string[]
  checkpointIds: string[]
  verificationResultIds: string[]
  eventsPath: string
  reportPath?: string
  summary: string
}
```

---

# 14. Tool Call Recording

每次 Skill 调用必须记录 skill name、tool name、input summary、output summary、status、duration、risk level、approval id、error、artifacts。不得记录完整 secret。

---

# 15. Context Usage Recording

每次 run 必须记录 Context Pack id/path、included sources/files/decisions/task summaries、excluded files if relevant、context budget、trimming applied。Run Report 必须包含 Context Used。

---

# 16. File Change Recording

文件变更必须记录 path、operation、before hash、after hash、diff summary、skill/tool、run id、task id、timestamp。删除文件必须包含 approval id。

---

# 17. Approval Recording

审批事件必须记录 approval id、action、reason、risk level、affected paths、command if any、requested at、resolved at、status、resolved by。

---

# 18. Failure Recording

失败必须记录 failure type、failure stage、failed command、exit code、error summary、recoverable、recommended recovery path、checkpoint id。

Failure types：context_failure、skill_failure、verification_failure、approval_denied、policy_denied、git_conflict、timeout、unknown。

---

# 19. Replay

Replay 的目标不是重新调用 Codex，而是重建执行过程。

Replay 应展示任务、上下文、工具调用、工具返回摘要、文件变更、审批、验证命令、失败位置和最终状态。

Replay Inputs：`.project/context/<run-id>.json`、`.project/reports/events/<run-id>.jsonl`、`.project/reports/traces/<run-id>.json`、`.project/reports/runs/<run-id>.md`、`.project/reports/verification/<run-id>.md`、`.project/checkpoints/<checkpoint-id>.json`。

---

# 20. Run Report

路径：`.project/reports/runs/<run-id>.md`

```markdown
# Run Report: <run-id>

## Task

## Final Status

## Context Used

## Execution Summary

## Skill Calls

## File Changes

## Git Changes

## Verification

## Approval Events

## Security / Governance Events

## Failures

## Risks

## Follow-up

## Artifacts
```

---

# 21. Observability and Governance Integration

Governance System 必须写入 policy.checked、policy.denied、approval.requested、approval.granted、approval.denied、path.blocked、command.blocked、secret.redacted、security.violation。

---

# 22. Observability and Task Manager Integration

Task Manager 必须在 task record 中关联 run id、report id、verification status、风险摘要，并在任务完成时引用 run report。

---

# 23. Observability and Delivery Integration

Delivery System 必须读取 run report、verification report、approval events、changed files、risk notes。交付前必须确保 verification status 不为 failed、高风险 delivery action 已审批、PR body 包含 run report 路径。

---

# 24. Data Retention

默认保留所有 task records、decision records、run reports、verification reports、context snapshots、checkpoint metadata。可清理超大 stdout/stderr 原始输出、旧 build artifacts、临时 cache、重复 trace 聚合文件，但必须保留摘要。

---

# 25. Redaction in Observability

所有日志和报告必须脱敏 API keys、tokens、passwords、private keys、.env values、database URLs、OAuth tokens、session cookies、cloud credentials，统一输出 `[REDACTED]`。

---

# 26. Configuration

Verification Config 位于 `.project/state/manifest.json`。

```json
{
  "verification": {
    "commands": {
      "lint": "pnpm lint",
      "typecheck": "pnpm typecheck",
      "test": "pnpm test",
      "build": "pnpm build"
    },
    "required": ["lint", "typecheck", "test"],
    "optional": ["build"],
    "timeoutMs": {
      "lint": 120000,
      "typecheck": 180000,
      "test": 300000,
      "build": 300000
    }
  }
}
```

Observability Config：

```json
{
  "observability": {
    "eventLog": true,
    "runTrace": true,
    "recordToolCalls": true,
    "recordContextUsage": true,
    "redactSecrets": true,
    "retainRawOutputs": false
  }
}
```

---

# 27. CLI Commands

Verification Commands：`harness verify`、`harness verify --task <task-id>`、`harness verify --run <run-id>`、`harness verify --command test`。

Observability Commands：`harness report <run-id>`、`harness trace <run-id>`、`harness events <run-id>`、`harness replay <run-id>`、`harness failures`。

---

# 28. Implementation Checklist

P0 Verification：detect commands from AGENTS.md / manifest / package files；create verification plan；run lint/typecheck/test/build through Shell/Test Runner Skill；capture exit code；capture stdout/stderr summary；write verification report；update task verification status。

P0 Observability：event logger；JSONL event store；run trace store；skill call recording；context usage recording；file change recording；approval recording；run report generation；secret redaction in logs。

P1：failure diagnosis；replay command；trace viewer data model；verification command inference；verification history；risk trend summary；large output artifact handling。

P2：OpenTelemetry exporter；dashboard；CI integration；advanced flaky test tracking；performance regression tracking；team audit review。

---

# 29. Acceptance Criteria

```text
1. 每个 run 必须有 event log
2. 每个 run 必须有 run trace
3. 每个 task 完成前必须生成 verification result
4. 验证命令不得凭空编造
5. 验证失败不得标记任务完成
6. 验证 skipped 必须说明原因
7. stdout/stderr 必须有摘要
8. Skill call 必须记录
9. Context Pack 使用必须记录
10. 文件变更必须记录
11. 审批事件必须记录
12. 安全事件必须记录
13. Run Report 必须生成
14. Verification Report 必须生成
15. Replay 必须能重建执行过程
16. Secrets 必须 redacted
17. Delivery 必须读取 verification result
18. 失败必须包含 recovery path
19. Task record 必须引用 run report
20. Observability 不能绕过 Governance
```

---

# 30. Final Definition

Verification = 证明这次 Codex 执行是否通过项目质量门。

Observability = 记录这次 Codex 执行的完整过程，使其可审计、可恢复、可回放。

边界关系：Codex 负责修改和解释；Verification 负责质量门；Observability 负责事实记录；Governance 负责安全边界；Task Manager 负责任务状态；Delivery 负责交付前读取验证结果。
