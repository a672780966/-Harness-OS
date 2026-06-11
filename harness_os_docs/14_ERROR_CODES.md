# Harness OS Error Codes Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Every failure must be structured, recoverable, observable, and user-actionable

---

# 1. 文档定位

本文件定义 Harness OS 的统一错误码体系。

它用于规范：

```text id="qrlrki"
Project Manager
Task Manager
Decision Manager
Context Engineering
MCP Skills
Governance and Security
Verification and Observability
Delivery Pipeline
State and Recovery
CLI
Config
Migration
```

所有模块在失败时必须返回结构化错误，而不是只返回普通字符串。

错误码必须帮助用户和 Codex 明确知道：

```text id="d872ke"
哪里失败
为什么失败
是否可恢复
应该怎么恢复
是否需要审批
是否应该写入报告
是否应该阻止后续流程
```

---

# 2. 设计目标

Error Codes 必须实现：

```text id="r3tqkk"
1. 为所有模块提供统一错误命名
2. 为 CLI 提供稳定退出语义
3. 为 Run Report 提供结构化失败原因
4. 为 Observability 提供可检索错误事件
5. 为 Codex 提供可执行 recovery hint
6. 为测试提供可断言的错误类型
7. 为 Delivery Guard 提供阻止依据
8. 为 Governance 提供审批/拒绝依据
9. 为用户提供清晰的人类可读提示
```

---

# 3. 非目标

本错误码体系不做：

```text id="m3k3m5"
替代日志系统
替代异常堆栈
替代测试失败详情
替代第三方工具错误码
替代系统级 errno
隐藏底层错误
自动修复所有错误
```

错误码是 Harness OS 的结构化错误边界。

底层错误仍可作为 cause 保存，但不得直接暴露 secrets。

---

# 4. 核心原则

## 4.1 Stable Error Code

错误码必须稳定。

一旦发布，不得随意改名。

如果语义变化，应新增错误码，而不是复用旧错误码。

---

## 4.2 Human-readable Message

每个错误码必须有面向人的说明。

例如：

```text id="2l8vzw"
ERR_PROJECT_NOT_FOUND
  Message: Project path does not exist or is not accessible.
```

---

## 4.3 Recovery Hint Required

每个错误码必须包含恢复建议。

例如：

```text id="xj24u7"
Recovery Hint:
  Check the path and run `harness open <path>` again.
```

---

## 4.4 Machine-readable Category

每个错误必须属于明确分类。

例如：

```text id="e03jiu"
project
task
decision
context
skill
governance
verification
observability
delivery
state
config
cli
internal
```

---

## 4.5 Redacted by Default

错误对象不得包含 secret。

所有错误 message、details、cause、stdout、stderr 在写入日志前必须经过 Secret Redactor。

---

# 5. 错误码命名规范

## 5.1 格式

统一格式：

```text id="b3xdcw"
ERR_<DOMAIN>_<REASON>
```

示例：

```text id="mrqkgd"
ERR_PROJECT_NOT_FOUND
ERR_APPROVAL_DENIED
ERR_SKILL_TIMEOUT
ERR_CONTEXT_OVER_BUDGET
ERR_VERIFICATION_FAILED
```

---

## 5.2 警告码格式

警告使用：

```text id="yxgu91"
WARN_<DOMAIN>_<REASON>
```

示例：

```text id="r5cn6w"
WARN_CONTEXT_TRIMMED
WARN_VERIFICATION_SKIPPED
WARN_GIT_DIRTY_STATE
```

---

## 5.3 信息码格式

信息码使用：

```text id="h7ztn7"
INFO_<DOMAIN>_<REASON>
```

示例：

```text id="kw4mwm"
INFO_PROJECT_REPAIRED
INFO_CONTEXT_REFRESHED
INFO_CHECKPOINT_CREATED
```

---

# 6. Error Object Schema

所有错误必须符合统一结构。

```ts id="m92gc2"
export interface HarnessError {
  code: HarnessErrorCode

  category:
    | "project"
    | "task"
    | "decision"
    | "context"
    | "skill"
    | "governance"
    | "verification"
    | "observability"
    | "delivery"
    | "state"
    | "config"
    | "migration"
    | "cli"
    | "internal"

  severity:
    | "info"
    | "warning"
    | "error"
    | "fatal"

  message: string

  recoveryHint: string

  recoverable: boolean

  retryable: boolean

  userActionRequired: boolean

  approvalRequired?: boolean

  details?: Record<string, unknown>

  cause?: {
    code?: string
    message: string
    stack?: string
  }

  related?: {
    projectId?: string
    taskId?: string
    runId?: string
    sessionId?: string
    decisionId?: string
    approvalId?: string
    skillName?: string
    toolName?: string
    filePath?: string
    command?: string
  }

  reportPath?: string

  createdAt: string
}
```

---

# 7. Severity 语义

## 7.1 info

表示成功但需要记录的信息。

例如：

```text id="wknnm8"
INFO_PROJECT_REPAIRED
INFO_CHECKPOINT_CREATED
```

---

## 7.2 warning

表示流程可继续，但存在风险或不完整。

例如：

```text id="eo9tdb"
WARN_CONTEXT_TRIMMED
WARN_VERIFICATION_SKIPPED
WARN_GIT_DIRTY_STATE
```

---

## 7.3 error

表示当前操作失败，但系统仍可继续运行。

例如：

```text id="d4mmth"
ERR_APPROVAL_DENIED
ERR_VERIFICATION_FAILED
ERR_SKILL_TIMEOUT
```

---

## 7.4 fatal

表示 Harness OS 当前流程不能继续。

例如：

```text id="ap6tpv"
ERR_PROJECT_CORRUPTED
ERR_STATE_STORE_UNAVAILABLE
ERR_INTERNAL_INVARIANT_BROKEN
```

---

# 8. CLI Exit Code Mapping

CLI 必须将错误码映射为稳定退出码。

```ts id="v8sacw"
export enum HarnessExitCode {
  OK = 0,

  USER_INPUT_ERROR = 10,
  PROJECT_ERROR = 20,
  TASK_ERROR = 30,
  CONTEXT_ERROR = 40,
  SKILL_ERROR = 50,
  GOVERNANCE_ERROR = 60,
  VERIFICATION_ERROR = 70,
  DELIVERY_ERROR = 80,
  STATE_ERROR = 90,
  CONFIG_ERROR = 100,
  INTERNAL_ERROR = 120
}
```

---

## 8.1 Exit Code Rules

```text id="5adz3k"
0
  成功。

10
  用户输入错误，例如参数缺失、命令无效。

20
  项目错误，例如项目不存在、AGENTS.md 缺失。

30
  任务错误，例如 task state 无效。

40
  Context 错误，例如 Context Pack 构建失败。

50
  Skill 错误，例如 Skill 不存在、执行超时。

60
  Governance 错误，例如策略拒绝、审批拒绝。

70
  Verification 错误，例如测试失败。

80
  Delivery 错误，例如交付被阻止。

90
  State 错误，例如 checkpoint 读取失败。

100
  Config 错误，例如配置非法。

120
  Harness 内部错误。
```

---

# 9. Project Error Codes

## 9.1 ERR_PROJECT_NOT_FOUND

```text id="fqy4s4"
Category: project
Severity: error
Recoverable: true
Retryable: true
User Action Required: true
```

Message:

```text id="l3v5ak"
Project path does not exist or is not accessible.
```

Recovery Hint:

```text id="ses15r"
Check the project path and run `harness open <path>` again.
```

---

## 9.2 ERR_PROJECT_NOT_GIT_REPO

Message:

```text id="41ev67"
The target directory is not a Git repository.
```

Recovery Hint:

```text id="a8yuo6"
Initialize Git with `git init`, or run `harness create <name>` for a new project.
```

---

## 9.3 ERR_PROJECT_MISSING_AGENTS_MD

Message:

```text id="lansy9"
AGENTS.md is missing from the project root.
```

Recovery Hint:

```text id="x6rhdz"
Run `harness repair` or `harness init` to create AGENTS.md before starting a Codex run.
```

---

## 9.4 ERR_PROJECT_INVALID_MANIFEST

Message:

```text id="zqi8cy"
.project/state/manifest.json is missing, invalid, or does not match the expected schema.
```

Recovery Hint:

```text id="gal62l"
Run `harness repair` to regenerate or fix the project manifest.
```

---

## 9.5 ERR_PROJECT_CORRUPTED

Message:

```text id="3oulmk"
The project state directory is corrupted or incomplete.
```

Recovery Hint:

```text id="udvfki"
Run `harness doctor` or `harness repair`. If repair fails, restore from Git or checkpoint.
```

---

# 10. Task Error Codes

## 10.1 ERR_TASK_NOT_FOUND

Message:

```text id="xwbrsj"
The requested task does not exist.
```

Recovery Hint:

```text id="mq6izu"
Run `harness task list` and retry with a valid task id.
```

---

## 10.2 ERR_TASK_INVALID_STATE

Message:

```text id="riqqgl"
The task is in a state that does not allow this operation.
```

Recovery Hint:

```text id="w0e7c5"
Inspect the task with `harness task show <task-id>` and continue only from an allowed lifecycle state.
```

---

## 10.3 ERR_TASK_ALREADY_RUNNING

Message:

```text id="y5hyvb"
The task is already running.
```

Recovery Hint:

```text id="n4jm3k"
Use `harness status` to inspect the current run, or pause/resume the existing run.
```

---

## 10.4 ERR_TASK_COMPLETION_BLOCKED

Message:

```text id="xt0ks1"
The task cannot be completed because required checks have not passed.
```

Recovery Hint:

```text id="hcmwou"
Review verification results, risk notes, and unresolved approvals before completing the task.
```

---

## 10.5 ERR_TASK_REPORT_WRITE_FAILED

Message:

```text id="59z7d7"
Harness failed to write the task report.
```

Recovery Hint:

```text id="v9d3f0"
Check filesystem permissions and ensure .project/tasks/ is writable.
```

---

# 11. Decision Error Codes

## 11.1 ERR_DECISION_NOT_FOUND

Message:

```text id="3ck9f5"
The requested decision record does not exist.
```

Recovery Hint:

```text id="5we9bi"
Run `harness decision list` and retry with a valid decision id.
```

---

## 11.2 ERR_DECISION_INVALID_ADR

Message:

```text id="qc2p2a"
The ADR file is missing required sections or metadata.
```

Recovery Hint:

```text id="q61l0z"
Regenerate the ADR using the approved ADR template.
```

---

## 11.3 ERR_DECISION_ACCEPTANCE_REQUIRES_APPROVAL

Message:

```text id="uo9g4r"
This decision cannot be accepted without approval.
```

Recovery Hint:

```text id="yf6fyu"
Submit the decision through Approval Gate before marking it accepted.
```

---

## 11.4 ERR_DECISION_ACCEPTED_RECORD_PROTECTED

Message:

```text id="85sdwa"
Accepted decision records cannot be modified without approval.
```

Recovery Hint:

```text id="6vt3k4"
Create a proposed superseding ADR or request approval to modify the accepted decision.
```

---

## 11.5 ERR_DECISION_DUPLICATE_NUMBER

Message:

```text id="qm2zwa"
An ADR with the same number already exists.
```

Recovery Hint:

```text id="ftil7s"
Use the next available ADR number.
```

---

# 12. Context Error Codes

## 12.1 ERR_CONTEXT_BUILD_FAILED

Message:

```text id="j4pkbh"
Context Pack generation failed.
```

Recovery Hint:

```text id="jw0p6d"
Inspect the context builder logs and verify AGENTS.md, manifest, git status, and project state files.
```

---

## 12.2 ERR_CONTEXT_MISSING_REQUIRED_SOURCE

Message:

```text id="lf6qgy"
A required context source is missing.
```

Recovery Hint:

```text id="z7gnch"
Run `harness repair` if AGENTS.md, manifest, project state, or task record is missing.
```

---

## 12.3 ERR_CONTEXT_OVER_BUDGET

Message:

```text id="5uxzfz"
Context Pack exceeds the configured token budget.
```

Recovery Hint:

```text id="pb8b69"
Trim low-priority sources or reduce included file content. P0 context must be preserved.
```

---

## 12.4 WARN_CONTEXT_TRIMMED

Message:

```text id="njkr5t"
Context Pack was trimmed to fit the budget.
```

Recovery Hint:

```text id="kuvy1i"
Review the Context Report to confirm important sources were preserved.
```

---

## 12.5 ERR_CONTEXT_SNAPSHOT_WRITE_FAILED

Message:

```text id="hm7624"
Harness failed to write the Context Pack snapshot.
```

Recovery Hint:

```text id="bksgwa"
Check filesystem permissions and ensure .project/context/ is writable.
```

---

# 13. Skill Error Codes

## 13.1 ERR_SKILL_NOT_FOUND

Message:

```text id="bzb1sg"
The requested Skill is not registered or not enabled for this project.
```

Recovery Hint:

```text id="j0vh8i"
Run `harness skills list` and enable the required Skill in project manifest if allowed.
```

---

## 13.2 ERR_SKILL_TOOL_NOT_FOUND

Message:

```text id="olh8wf"
The requested tool does not exist in the selected Skill.
```

Recovery Hint:

```text id="p42cnv"
Check the Skill manifest and Context Pack skill declaration.
```

---

## 13.3 ERR_SKILL_INVALID_INPUT

Message:

```text id="7iquhh"
Skill input does not match the declared input schema.
```

Recovery Hint:

```text id="hfgweq"
Validate the tool call arguments against the Skill manifest input schema.
```

---

## 13.4 ERR_SKILL_TIMEOUT

Message:

```text id="2uxdba"
Skill execution timed out.
```

Recovery Hint:

```text id="54kdu9"
Retry with a smaller operation, increase timeout through policy if appropriate, or inspect partial output.
```

---

## 13.5 ERR_SKILL_EXECUTION_FAILED

Message:

```text id="1vb9bg"
Skill execution failed.
```

Recovery Hint:

```text id="baiu6g"
Inspect the Skill result, stderr summary, and related event log.
```

---

## 13.6 ERR_SKILL_POLICY_BYPASS_ATTEMPT

Message:

```text id="trdbb7"
A Skill execution was attempted without passing through Policy Engine.
```

Recovery Hint:

```text id="xjm3kb"
Route all Skill calls through Skill Runtime and Policy Engine. Direct execution is not allowed.
```

---

# 14. Governance Error Codes

## 14.1 ERR_POLICY_DENIED

Message:

```text id="59dx9p"
The requested operation was denied by policy.
```

Recovery Hint:

```text id="a0sjhp"
Review the policy decision, affected paths, command, and project governance rules.
```

---

## 14.2 ERR_APPROVAL_REQUIRED

Message:

```text id="8kwzoo"
The requested operation requires approval.
```

Recovery Hint:

```text id="rn1jda"
Approve or deny the request through the Approval Gate.
```

---

## 14.3 ERR_APPROVAL_DENIED

Message:

```text id="q9f48h"
The approval request was denied.
```

Recovery Hint:

```text id="u7cyih"
Choose a safer alternative or modify the task plan.
```

---

## 14.4 ERR_PROTECTED_PATH

Message:

```text id="mbj1s0"
The requested path is protected by project policy.
```

Recovery Hint:

```text id="lz11pd"
Request approval or choose a non-protected path.
```

---

## 14.5 ERR_WORKSPACE_ESCAPE

Message:

```text id="5iz7is"
The requested path escapes the workspace boundary.
```

Recovery Hint:

```text id="s1sznx"
Use a path inside the project workspace. Absolute paths and ../ escapes are not allowed by default.
```

---

## 14.6 ERR_SECRET_ACCESS_BLOCKED

Message:

```text id="snz8wk"
The requested operation would access a protected secret or credentials file.
```

Recovery Hint:

```text id="uapzhn"
Avoid reading secret values. If necessary, request approval and only check whether the secret exists.
```

---

## 14.7 ERR_DANGEROUS_COMMAND

Message:

```text id="e00wje"
The shell command is classified as dangerous.
```

Recovery Hint:

```text id="0apmhj"
Use a declared safe command, request approval, or explain why the command is required.
```

---

# 15. Verification Error Codes

## 15.1 ERR_VERIFICATION_COMMAND_NOT_FOUND

Message:

```text id="pywkmd"
No verification command could be found.
```

Recovery Hint:

```text id="whk011"
Declare verification commands in AGENTS.md or .project/state/manifest.json.
```

---

## 15.2 ERR_VERIFICATION_FAILED

Message:

```text id="4l831n"
One or more verification commands failed.
```

Recovery Hint:

```text id="zybf55"
Inspect the verification report, fix the failing checks, and run verification again.
```

---

## 15.3 WARN_VERIFICATION_SKIPPED

Message:

```text id="dolz7p"
Verification was skipped.
```

Recovery Hint:

```text id="3bf5fo"
Record the reason in the verification report and request approval before delivery if required.
```

---

## 15.4 ERR_VERIFICATION_BLOCKED

Message:

```text id="k7mksv"
Verification could not run because it was blocked by policy, missing dependencies, or unavailable commands.
```

Recovery Hint:

```text id="kqf3tr"
Resolve the blocking condition and rerun `harness verify`.
```

---

## 15.5 ERR_VERIFICATION_REPORT_WRITE_FAILED

Message:

```text id="95t9cs"
Harness failed to write the verification report.
```

Recovery Hint:

```text id="linpaz"
Check filesystem permissions and ensure .project/reports/verification/ is writable.
```

---

# 16. Observability Error Codes

## 16.1 ERR_EVENT_LOG_WRITE_FAILED

Message:

```text id="yzz4re"
Harness failed to write to the event log.
```

Recovery Hint:

```text id="cno4j4"
Check filesystem permissions and ensure .project/reports/events/ is writable.
```

---

## 16.2 ERR_TRACE_WRITE_FAILED

Message:

```text id="wv9vzf"
Harness failed to write the run trace.
```

Recovery Hint:

```text id="l8ggtn"
Check filesystem permissions and ensure .project/reports/traces/ is writable.
```

---

## 16.3 ERR_RUN_REPORT_WRITE_FAILED

Message:

```text id="wj56nl"
Harness failed to write the run report.
```

Recovery Hint:

```text id="hscue0"
Check filesystem permissions and ensure .project/reports/runs/ is writable.
```

---

## 16.4 ERR_REPLAY_SOURCE_MISSING

Message:

```text id="ri7crq"
Replay cannot start because required trace, event log, context snapshot, or report files are missing.
```

Recovery Hint:

```text id="r94hui"
Inspect the run id and ensure observability artifacts were generated.
```

---

# 17. Delivery Error Codes

## 17.1 ERR_DELIVERY_BLOCKED

Message:

```text id="ksyae7"
Delivery was blocked by Delivery Guard.
```

Recovery Hint:

```text id="nadr5m"
Inspect verification status, approval state, run report, and risk notes.
```

---

## 17.2 ERR_DELIVERY_MISSING_VERIFICATION

Message:

```text id="v5hnns"
Delivery cannot proceed because verification result is missing.
```

Recovery Hint:

```text id="s2fip6"
Run `harness verify` before delivery.
```

---

## 17.3 ERR_DELIVERY_VERIFICATION_FAILED

Message:

```text id="xozsjt"
Delivery cannot proceed because verification failed.
```

Recovery Hint:

```text id="hp6ix3"
Fix failing checks and rerun verification before delivery.
```

---

## 17.4 ERR_DELIVERY_MISSING_RUN_REPORT

Message:

```text id="1e08cp"
Delivery cannot proceed because the run report is missing.
```

Recovery Hint:

```text id="q4x4v3"
Generate or repair the run report before creating a PR or release.
```

---

## 17.5 ERR_DELIVERY_REQUIRES_APPROVAL

Message:

```text id="a8gc8v"
This delivery action requires approval.
```

Recovery Hint:

```text id="bsk6nb"
Approve the delivery action before continuing.
```

---

## 17.6 ERR_DELIVERY_EXTERNAL_PROVIDER_FAILED

Message:

```text id="e8pjlk"
External delivery provider operation failed.
```

Recovery Hint:

```text id="7galhs"
Inspect provider error details, authentication status, and retry if recoverable.
```

---

# 18. State and Recovery Error Codes

## 18.1 ERR_STATE_STORE_UNAVAILABLE

Message:

```text id="j15k38"
The state store is unavailable.
```

Recovery Hint:

```text id="c162dq"
Check SQLite or filesystem state storage and retry.
```

---

## 18.2 ERR_SESSION_NOT_FOUND

Message:

```text id="a99yog"
The requested session does not exist.
```

Recovery Hint:

```text id="6k50xa"
Run `harness status` or inspect .project/sessions/ for available sessions.
```

---

## 18.3 ERR_RUN_NOT_FOUND

Message:

```text id="29i3rz"
The requested run does not exist.
```

Recovery Hint:

```text id="hthrt9"
Run `harness report` or inspect .project/reports/runs/ for available run ids.
```

---

## 18.4 ERR_CHECKPOINT_NOT_FOUND

Message:

```text id="bpf9dz"
The requested checkpoint does not exist.
```

Recovery Hint:

```text id="jcdo7z"
Run `harness checkpoint list` and retry with a valid checkpoint id.
```

---

## 18.5 ERR_CHECKPOINT_RESTORE_FAILED

Message:

```text id="l4k1vm"
Checkpoint restore failed.
```

Recovery Hint:

```text id="wqi5h8"
Inspect checkpoint metadata, git status, and conflicting workspace changes.
```

---

## 18.6 ERR_RESUME_FAILED

Message:

```text id="p9chml"
Harness failed to resume the run.
```

Recovery Hint:

```text id="itdn12"
Inspect run state, context snapshot, checkpoint metadata, and event log.
```

---

# 19. Config Error Codes

## 19.1 ERR_CONFIG_NOT_FOUND

Message:

```text id="4a8rpq"
The required configuration file was not found.
```

Recovery Hint:

```text id="m3t248"
Run `harness repair` or create the missing configuration file.
```

---

## 19.2 ERR_CONFIG_INVALID

Message:

```text id="6a6u9m"
The configuration file is invalid.
```

Recovery Hint:

```text id="4d5lpw"
Validate the configuration against the schema and fix invalid fields.
```

---

## 19.3 ERR_CONFIG_UNSUPPORTED_VERSION

Message:

```text id="sz2ajh"
The configuration schema version is not supported.
```

Recovery Hint:

```text id="38ung9"
Run `harness migrate` or upgrade Harness OS.
```

---

## 19.4 ERR_CONFIG_PERMISSION_DENIED

Message:

```text id="9pu4pj"
The configuration cannot be modified due to permissions or policy.
```

Recovery Hint:

```text id="tsgo7p"
Request approval or modify only allowed fields.
```

---

# 20. Migration Error Codes

## 20.1 ERR_MIGRATION_REQUIRED

Message:

```text id="mrxs2l"
Project state uses an older schema and requires migration.
```

Recovery Hint:

```text id="zkw2ol"
Run `harness migrate` before continuing.
```

---

## 20.2 ERR_MIGRATION_FAILED

Message:

```text id="3qc1r4"
Project migration failed.
```

Recovery Hint:

```text id="hswk98"
Inspect the migration report and restore from the pre-migration checkpoint if needed.
```

---

## 20.3 ERR_MIGRATION_UNSUPPORTED_DOWNGRADE

Message:

```text id="rgkybd"
Downgrading this project schema is not supported.
```

Recovery Hint:

```text id="ew2mfq"
Use a compatible Harness OS version or restore from backup.
```

---

# 21. CLI Error Codes

## 21.1 ERR_CLI_INVALID_ARGUMENTS

Message:

```text id="jfz3v3"
The CLI command arguments are invalid.
```

Recovery Hint:

```text id="p7rqk0"
Run the command with `--help` and provide required arguments.
```

---

## 21.2 ERR_CLI_NON_INTERACTIVE_APPROVAL_REQUIRED

Message:

```text id="fkm3qb"
This operation requires approval, but the CLI is running in non-interactive mode.
```

Recovery Hint:

```text id="x5lwt8"
Run interactively, provide a pre-approved approval id, or disable the high-risk operation.
```

---

## 21.3 ERR_CLI_OUTPUT_MODE_INVALID

Message:

```text id="juqta0"
The requested output mode is not supported.
```

Recovery Hint:

```text id="ioetlm"
Use one of: --pretty, --json, or --quiet.
```

---

# 22. Internal Error Codes

## 22.1 ERR_INTERNAL_INVARIANT_BROKEN

Message:

```text id="izebgg"
An internal Harness OS invariant was broken.
```

Recovery Hint:

```text id="xx96vz"
File a bug report with the run id, event log, and sanitized error details.
```

---

## 22.2 ERR_INTERNAL_UNHANDLED_EXCEPTION

Message:

```text id="olz386"
Harness OS encountered an unhandled exception.
```

Recovery Hint:

```text id="ng9gd0"
Retry if safe. If it persists, file a bug report with sanitized logs.
```

---

## 22.3 ERR_INTERNAL_NOT_IMPLEMENTED

Message:

```text id="m0z9dq"
This feature is not implemented yet.
```

Recovery Hint:

```text id="7ld83f"
Use the documented fallback path or implement the missing feature in a future milestone.
```

---

# 23. Warning Codes

## 23.1 WARN_GIT_DIRTY_STATE

Message:

```text id="o6m3sk"
The workspace has uncommitted changes.
```

Recovery Hint:

```text id="9r3a1q"
Inspect git status before modifying files. Do not overwrite user changes.
```

---

## 23.2 WARN_DEPENDENCY_ADDED

Message:

```text id="x1lpg4"
A new dependency was added.
```

Recovery Hint:

```text id="2g0x17"
Record dependency purpose, version, risk, and alternatives considered.
```

---

## 23.3 WARN_CONTEXT_SOURCE_SKIPPED

Message:

```text id="xzcq85"
A context source was skipped.
```

Recovery Hint:

```text id="8xqh3a"
Review Context Report to confirm the skipped source was not required.
```

---

## 23.4 WARN_DELIVERY_PARTIAL_VERIFICATION

Message:

```text id="65115i"
Delivery is being prepared with partial verification.
```

Recovery Hint:

```text id="nz1otn"
Request approval and clearly document remaining risks.
```

---

# 24. Error Event Integration

每个错误必须写入 Observability。

事件类型：

```text id="v1k0b7"
error.created
warning.created
fatal.created
```

Event payload 必须包含：

```text id="5sdekh"
error code
category
severity
recoverable
retryable
userActionRequired
related ids
redacted details
```

---

# 25. Run Report Integration

Run Report 必须包含错误摘要。

格式：

```markdown id="ed1a8j"
## Errors

| Code | Severity | Message | Recovery |
|---|---|---|---|
| ERR_VERIFICATION_FAILED | error | One or more verification commands failed. | Inspect the verification report. |
```

---

# 26. CLI Output Integration

## 26.1 Pretty Output

```text id="ly57gr"
Error: ERR_PROJECT_MISSING_AGENTS_MD

AGENTS.md is missing from the project root.

Recovery:
Run `harness repair` or `harness init` to create AGENTS.md before starting a Codex run.
```

---

## 26.2 JSON Output

```json id="kob5ae"
{
  "ok": false,
  "error": {
    "code": "ERR_PROJECT_MISSING_AGENTS_MD",
    "category": "project",
    "severity": "error",
    "message": "AGENTS.md is missing from the project root.",
    "recoveryHint": "Run `harness repair` or `harness init` to create AGENTS.md before starting a Codex run.",
    "recoverable": true,
    "retryable": true,
    "userActionRequired": true
  }
}
```

---

# 27. Testing Requirements

Error Codes 必须有测试。

必须覆盖：

```text id="p7qkaq"
1. 所有错误码唯一
2. 所有错误码有 message
3. 所有错误码有 recoveryHint
4. 所有错误码有 category
5. 所有错误码有 severity
6. 所有错误码可映射 CLI exit code
7. JSON 输出符合 schema
8. Pretty 输出可读
9. Secret 不出现在 error details
10. Run Report 可渲染错误摘要
```

---

# 28. Implementation Checklist

## P0

```text id="zwjtxb"
HarnessError schema
error code enum
error factory
CLI exit code mapping
pretty output formatter
JSON output formatter
secret redaction in errors
Project errors
Task errors
Context errors
Skill errors
Governance errors
Verification errors
Delivery errors
```

---

## P1

```text id="loou5v"
Observability error events
Run Report error table
State/Recovery errors
Decision errors
Config errors
Migration errors
Warning codes
Error tests
```

---

## P2

```text id="5ewofi"
localized messages
error documentation generator
machine-readable error registry
error analytics
error trend reports
```

---

# 29. Acceptance Criteria

Error Codes 模块完成标准：

```text id="94ob36"
1. 所有模块错误都使用 HarnessError
2. 所有错误码必须唯一
3. 所有错误码必须稳定
4. 所有错误码必须有 category
5. 所有错误码必须有 severity
6. 所有错误码必须有 human-readable message
7. 所有错误码必须有 recovery hint
8. 所有错误码必须声明 recoverable
9. 所有错误码必须声明 retryable
10. 所有错误码必须声明 userActionRequired
11. CLI 必须将错误映射到稳定 exit code
12. --json 输出必须包含结构化 error
13. --pretty 输出必须包含 recovery hint
14. Run Report 必须包含错误摘要
15. Observability 必须记录错误事件
16. Secret 不得出现在错误对象中
17. 测试必须覆盖错误码唯一性
18. 测试必须覆盖格式化输出
19. 新增模块错误必须先注册错误码
20. 不允许只抛普通字符串错误
```

---

# 30. Final Definition

Harness OS Error Codes 的最终定义：

```text id="d7jjso"
Error Codes
=
把 Harness OS 的所有失败转换成稳定、结构化、可恢复、可审计、可测试的工程信号。
```

边界关系：

```text id="fh5unk"
Errors 负责表达失败。
Recovery Hint 负责指导下一步。
Observability 负责记录错误。
Run Report 负责展示错误。
CLI 负责返回稳定退出码。
Governance 负责决定是否阻止。
Codex 负责根据错误信息调整执行计划。
```
