# Harness OS CLI Output Contract

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: CLI output must be stable for machines, readable for humans, safe for logs, and consistent across modules

---

# 1. 文档定位

本文件定义 Harness OS 的 CLI 输出契约。

它用于规范所有 `harness` 命令在成功、失败、阻止、审批、验证、交付、恢复等场景下的输出格式、退出码、JSON schema、交互行为和日志安全规则。

覆盖范围包括：

```text id="h3wj2p"
harness create
harness open
harness run
harness resume
harness status
harness verify
harness report
harness deliver
harness repair
harness checkpoint
harness rollback
harness task
harness decision
harness skills
harness events
harness replay
harness migrate
harness config
```

CLI Output Contract 是 Harness OS 对用户、Codex、脚本、CI、测试系统的稳定接口。

---

# 2. 设计目标

CLI 输出契约必须实现：

```text id="dg6hft"
1. 定义统一输出模式
2. 定义统一成功输出结构
3. 定义统一错误输出结构
4. 定义统一 warning 输出结构
5. 定义统一进度输出结构
6. 定义统一审批提示格式
7. 定义统一 JSON 输出 schema
8. 定义统一退出码语义
9. 定义非交互模式行为
10. 定义 CI 环境行为
11. 定义 secret redaction 规则
12. 定义可测试的输出快照规范
```

---

# 3. 非目标

本文件不做：

```text id="xfbqij"
替代 Error Codes 规范
替代 Observability Event Log
替代 Run Report
替代 Verification Report
替代 Delivery Report
替代日志系统
替代 UI 设计规范
```

CLI 输出是用户与自动化系统的前台接口。

Event Log 和 Reports 是后台审计事实源。

---

# 4. 核心原则

## 4.1 Human-readable by Default

默认输出应适合人类阅读。

默认模式：

```text id="fczpfq"
--pretty
```

---

## 4.2 Machine-readable When Requested

当用户指定：

```bash id="byp1ln"
--json
```

CLI 必须输出稳定 JSON。

不得混入 spinner、颜色控制符、说明文字、调试日志。

---

## 4.3 Quiet Means Quiet

当用户指定：

```bash id="wa29n3"
--quiet
```

CLI 只输出必要结果。

成功时可以无输出。

失败时只输出最小错误摘要，或在 `--json --quiet` 下输出结构化错误。

---

## 4.4 Redacted by Default

CLI 输出不得泄露 secrets。

必须脱敏：

```text id="zaqaxw"
API keys
tokens
passwords
private keys
database URLs
OAuth tokens
cloud credentials
session cookies
.env values
```

统一替换为：

```text id="kabggq"
[REDACTED]
```

---

## 4.5 Stable for Tests

CLI 输出必须可测试。

要求：

```text id="a54er3"
JSON 字段稳定
错误码稳定
退出码稳定
表格列稳定
非确定性字段可配置隐藏或标准化
路径输出可相对化
时间戳使用 ISO-8601
```

---

# 5. 输出模式

Harness OS CLI 支持三种标准输出模式。

```text id="z3boqq"
--pretty
--json
--quiet
```

---

## 5.1 Pretty Mode

默认模式。

适合人类阅读。

特征：

```text id="hjpkhj"
使用标题
使用段落
使用表格
可使用颜色
可使用 spinner
可显示进度
可显示 recovery hint
```

示例：

```text id="m8xt35"
Harness OS

Project opened: demo
Path: /workspace/demo
Git branch: main
Status: ready

Next:
  harness run "your task"
```

---

## 5.2 JSON Mode

适合脚本、CI、Codex、自动化系统读取。

特征：

```text id="jz8soj"
只输出 JSON
不得输出颜色
不得输出 spinner
不得输出非 JSON 文本
必须符合 schema
错误也必须是 JSON
```

示例：

```json id="lekl72"
{
  "ok": true,
  "command": "open",
  "status": "ready",
  "data": {
    "projectId": "project_demo",
    "path": "/workspace/demo",
    "branch": "main"
  },
  "warnings": [],
  "reports": [],
  "events": []
}
```

---

## 5.3 Quiet Mode

适合 shell 管道和 CI。

特征：

```text id="qlv3sy"
成功时最少输出
失败时输出错误码和简短 message
不显示 progress
不显示建议性说明
```

示例：

```text id="42a2b5"
ERR_VERIFICATION_FAILED: One or more verification commands failed.
```

---

# 6. 输出目标流

CLI 必须区分 stdout 和 stderr。

```text id="x5t6hm"
stdout:
  正常结果
  JSON 输出
  成功摘要
  查询结果

stderr:
  错误
  warning
  progress
  spinner
  debug logs
  approval prompt
```

规则：

```text id="l1gqwh"
--json 模式下 stdout 只能包含 JSON。
--json 模式下 stderr 可包含调试信息，但默认不得输出。
CI 环境中 progress 默认关闭。
```

---

# 7. 全局输出 Schema

所有 `--json` 输出必须遵守统一根结构。

```ts id="pav713"
export interface CliJsonOutput<T = unknown> {
  ok: boolean

  command: string

  status:
    | "success"
    | "failed"
    | "blocked"
    | "requires-approval"
    | "partial"
    | "skipped"

  data?: T

  error?: HarnessError

  warnings: CliWarning[]

  reports: CliReportRef[]

  events: CliEventRef[]

  meta: CliOutputMeta
}
```

---

## 7.1 Warning Schema

```ts id="2gqp00"
export interface CliWarning {
  code: string
  message: string
  recoveryHint?: string
}
```

---

## 7.2 Report Reference Schema

```ts id="mm35d6"
export interface CliReportRef {
  type:
    | "run"
    | "verification"
    | "delivery"
    | "task"
    | "decision"
    | "migration"
    | "error"

  path: string
  summary?: string
}
```

---

## 7.3 Event Reference Schema

```ts id="ri5y7c"
export interface CliEventRef {
  type: string
  eventId?: string
  path?: string
}
```

---

## 7.4 Output Meta Schema

```ts id="8hvzdi"
export interface CliOutputMeta {
  version: string
  outputMode: "pretty" | "json" | "quiet"
  generatedAt: string
  durationMs?: number
  cwd?: string
  projectId?: string
  taskId?: string
  runId?: string
  redacted: boolean
}
```

---

# 8. 成功输出契约

## 8.1 Pretty Success Format

格式：

```text id="2t0u1l"
<Title>

<Primary result>

<Important details>

Reports:
  <report refs>

Next:
  <suggested next commands>
```

示例：

```text id="7r34jg"
Task completed

Task: task_123
Run: run_123
Verification: passed
Changed files: 3

Reports:
  Run Report: .project/reports/runs/run_123.md
  Verification Report: .project/reports/verification/run_123.md

Next:
  harness deliver --pr
```

---

## 8.2 JSON Success Format

```json id="f2tzrf"
{
  "ok": true,
  "command": "run",
  "status": "success",
  "data": {
    "taskId": "task_123",
    "runId": "run_123",
    "verificationStatus": "passed",
    "changedFiles": ["src/index.ts", "tests/index.test.ts"]
  },
  "warnings": [],
  "reports": [
    {
      "type": "run",
      "path": ".project/reports/runs/run_123.md"
    }
  ],
  "events": [],
  "meta": {
    "version": "1.0",
    "outputMode": "json",
    "generatedAt": "2026-06-11T00:00:00.000Z",
    "redacted": true
  }
}
```

---

# 9. 错误输出契约

## 9.1 Pretty Error Format

格式：

```text id="pg2b9z"
Error: <ERROR_CODE>

<Message>

Recovery:
<Recovery hint>

Details:
<safe details>

Report:
<optional report path>
```

示例：

```text id="ztc9pu"
Error: ERR_PROJECT_MISSING_AGENTS_MD

AGENTS.md is missing from the project root.

Recovery:
Run `harness repair` or `harness init` to create AGENTS.md before starting a Codex run.
```

---

## 9.2 JSON Error Format

```json id="zpzax1"
{
  "ok": false,
  "command": "open",
  "status": "failed",
  "error": {
    "code": "ERR_PROJECT_MISSING_AGENTS_MD",
    "category": "project",
    "severity": "error",
    "message": "AGENTS.md is missing from the project root.",
    "recoveryHint": "Run `harness repair` or `harness init` to create AGENTS.md before starting a Codex run.",
    "recoverable": true,
    "retryable": true,
    "userActionRequired": true,
    "createdAt": "2026-06-11T00:00:00.000Z"
  },
  "warnings": [],
  "reports": [],
  "events": [],
  "meta": {
    "version": "1.0",
    "outputMode": "json",
    "generatedAt": "2026-06-11T00:00:00.000Z",
    "redacted": true
  }
}
```

---

# 10. Warning 输出契约

Warnings 表示流程可以继续，但存在风险。

Pretty 示例：

```text id="irm1u9"
Warning: WARN_GIT_DIRTY_STATE

The workspace has uncommitted changes.

Recovery:
Inspect git status before modifying files.
```

JSON 示例：

```json id="vsxakc"
{
  "warnings": [
    {
      "code": "WARN_GIT_DIRTY_STATE",
      "message": "The workspace has uncommitted changes.",
      "recoveryHint": "Inspect git status before modifying files."
    }
  ]
}
```

---

# 11. Progress 输出契约

## 11.1 Pretty Progress

交互式终端可显示 progress。

示例：

```text id="wwgkjs"
Building Context Pack...
Running verification...
Writing Run Report...
```

允许 spinner，但必须满足：

```text id="zdcx6f"
仅在 TTY 中显示
不得出现在 --json stdout
不得出现在 --quiet
CI 环境默认禁用
```

---

## 11.2 JSON Progress

默认 JSON 模式不输出中间 progress。

如果未来支持流式 JSON，必须使用 NDJSON。

格式：

```jsonl id="xi6r8q"
{"type":"progress","stage":"context.build.started","message":"Building Context Pack..."}
{"type":"progress","stage":"verification.started","message":"Running verification..."}
{"type":"result","ok":true,"status":"success"}
```

NDJSON 必须通过显式参数启用：

```bash id="zl63lj"
harness run "task" --json --stream
```

---

# 12. Approval Prompt Contract

需要审批时，CLI 必须显示结构化审批提示。

## 12.1 Pretty Approval Prompt

```text id="q0x7dq"
Approval required

Action:
  Modify AGENTS.md

Risk:
  high

Reason:
  AGENTS.md is protected by project policy.

Affected paths:
  AGENTS.md

Approve? [y/N]
```

---

## 12.2 JSON Approval Required Output

非交互模式或 `--json` 模式下，不得阻塞等待输入，除非显式允许。

```json id="x6vz18"
{
  "ok": false,
  "command": "run",
  "status": "requires-approval",
  "error": {
    "code": "ERR_APPROVAL_REQUIRED",
    "category": "governance",
    "severity": "error",
    "message": "The requested operation requires approval.",
    "recoveryHint": "Approve or deny the request through the Approval Gate.",
    "recoverable": true,
    "retryable": true,
    "userActionRequired": true,
    "approvalRequired": true
  },
  "data": {
    "approvalId": "approval_123",
    "action": "Modify AGENTS.md",
    "riskLevel": "high",
    "affectedPaths": ["AGENTS.md"]
  },
  "warnings": [],
  "reports": [],
  "events": [],
  "meta": {
    "version": "1.0",
    "outputMode": "json",
    "generatedAt": "2026-06-11T00:00:00.000Z",
    "redacted": true
  }
}
```

---

# 13. Non-interactive Mode

非交互模式由以下方式启用：

```text id="b5v95h"
--non-interactive
HARNESS_NON_INTERACTIVE=true
CI=true
```

规则：

```text id="u5nmyq"
不得弹出交互式 prompt
approval required 必须返回 ERR_CLI_NON_INTERACTIVE_APPROVAL_REQUIRED 或 ERR_APPROVAL_REQUIRED
不得等待用户输入
不得显示 spinner
必须返回稳定 exit code
```

---

# 14. CI Mode

CI 环境中默认行为：

```text id="g1y0x3"
outputMode = json or quiet if configured
interactive = false
color = false
spinner = false
progress = minimal
approval prompts disabled
raw stdout/stderr limited
reports always written
```

CI 中如果交付需要审批：

```text id="nwerze"
返回 blocked 或 requires-approval
退出码非 0
不继续执行高风险动作
```

---

# 15. Color and Formatting

Pretty mode 可使用颜色，但必须可关闭。

关闭方式：

```text id="j8g6cb"
--no-color
NO_COLOR=1
HARNESS_NO_COLOR=true
CI=true
```

颜色不得承载唯一语义。

例如：

```text id="zjfxo9"
不能只用红色表示失败。
必须同时输出 failed / error / blocked 等文本。
```

---

# 16. Tables

Pretty mode 可以使用表格。

表格必须：

```text id="btf2po"
列名稳定
列顺序稳定
内容可复制
窄终端可降级为 list
不得截断关键 ID
```

示例：

```text id="j2mahw"
Tasks

| ID       | Status    | Title                  |
|----------|-----------|------------------------|
| task_123 | completed | Fix loading state      |
| task_124 | blocked   | Update deployment rule |
```

JSON mode 不得输出表格，必须输出数组。

---

# 17. Path Output Rules

路径输出规则：

```text id="6xea4a"
默认优先输出相对 workspace 的路径
涉及全局配置时可输出 ~ 展开前路径
不得输出敏感 home path 到 Context Pack
--json 中路径必须稳定
跨平台路径应标准化为 POSIX 风格，除非显示原生路径必要
```

示例：

```text id="kjqo2o"
.project/reports/runs/run_123.md
```

而不是默认输出：

```text id="fmdmrj"
/Users/alice/private/project/.project/reports/runs/run_123.md
```

---

# 18. Timestamp Rules

所有 JSON 时间必须使用 ISO-8601 UTC。

示例：

```text id="ds3myy"
2026-06-11T00:00:00.000Z
```

Pretty mode 可以显示本地时间，但报告和 JSON 必须使用 UTC。

---

# 19. ID Output Rules

CLI 输出中的 ID 必须完整可复制。

不得截断：

```text id="fk9zbs"
task id
run id
session id
approval id
checkpoint id
decision id
delivery id
event id
```

Pretty mode 可以额外显示短 ID，但必须至少提供完整 ID。

---

# 20. Command-specific Output Contracts

## 20.1 harness create

Pretty success:

```text id="ovyfc3"
Project created

Name: demo
Path: demo
AGENTS.md: created
.project/: created
Initial checkpoint: checkpoint_123

Next:
  cd demo
  harness run "your task"
```

JSON data:

```ts id="fz25pf"
export interface CreateProjectOutput {
  projectId: string
  name: string
  path: string
  agentsMdCreated: boolean
  projectDirCreated: boolean
  manifestPath: string
  checkpointId?: string
}
```

---

## 20.2 harness open

JSON data:

```ts id="sb0wl3"
export interface OpenProjectOutput {
  projectId: string
  path: string
  name: string
  branch?: string
  gitStatus?: string
  ready: boolean
  warnings: string[]
}
```

---

## 20.3 harness run

JSON data:

```ts id="gv6bzq"
export interface RunOutput {
  taskId: string
  runId: string
  status: "completed" | "failed" | "blocked" | "paused"
  contextPackPath?: string
  runReportPath?: string
  verificationReportPath?: string
  changedFiles: string[]
  verificationStatus?: string
  risks: string[]
}
```

---

## 20.4 harness resume

JSON data:

```ts id="xfal4h"
export interface ResumeOutput {
  runId: string
  taskId: string
  resumedFromCheckpoint?: string
  contextPackPath?: string
  status: "running" | "completed" | "failed" | "blocked"
}
```

---

## 20.5 harness status

JSON data:

```ts id="6egsg0"
export interface StatusOutput {
  projectId: string
  activeRunId?: string
  activeTaskId?: string
  branch?: string
  hasUserChanges: boolean
  tasks: {
    active: number
    completed: number
    failed: number
    blocked: number
  }
}
```

---

## 20.6 harness verify

JSON data:

```ts id="eyj4vm"
export interface VerifyOutput {
  runId?: string
  taskId?: string
  status: "passed" | "failed" | "partial" | "skipped" | "blocked"
  reportPath: string
  commands: {
    name: string
    command: string
    status: string
    exitCode: number | null
    durationMs: number
  }[]
}
```

---

## 20.7 harness report

JSON data:

```ts id="lgzbs8"
export interface ReportOutput {
  runId: string
  reportPath: string
  verificationReportPath?: string
  deliveryReportPath?: string
  status: string
}
```

---

## 20.8 harness deliver

JSON data:

```ts id="yh4oyx"
export interface DeliverOutput {
  deliveryId: string
  type: "commit" | "pull-request" | "release" | "deploy" | "rollback"
  status: "completed" | "blocked" | "failed" | "requires-approval"
  reportPath: string
  commitHash?: string
  prUrl?: string
  releaseUrl?: string
  deploymentUrl?: string
}
```

---

## 20.9 harness replay

JSON data:

```ts id="xfl7t9"
export interface ReplayOutput {
  runId: string
  tracePath: string
  eventLogPath: string
  events: number
  finalStatus: string
}
```

---

## 20.10 harness config

JSON data:

```ts id="y9as2s"
export interface ConfigOutput {
  scope: "global" | "project" | "effective"
  configPath?: string
  effectiveConfig: Record<string, unknown>
  redacted: boolean
}
```

---

# 21. Exit Code Contract

CLI 必须使用统一退出码。

```text id="z2wub4"
0    success
10   user input error
20   project error
30   task error
40   context error
50   skill error
60   governance error
70   verification error
80   delivery error
90   state error
100  config error
110  migration error
120  internal error
```

规则：

```text id="npb3fy"
warning 不导致非 0 exit code，除非配置为 strict。
blocked 必须非 0。
requires-approval 必须非 0，除非交互审批后继续成功。
verification failed 必须返回 70。
delivery blocked 必须返回 80。
policy denied 必须返回 60。
```

---

# 22. Log Level Contract

CLI 支持：

```text id="hthgr4"
--log-level debug
--log-level info
--log-level warn
--log-level error
```

默认：

```text id="lgjpjc"
info
```

规则：

```text id="rw7stj"
debug 不得输出 secrets
debug 默认写 stderr
--json stdout 不得混入 debug
CI 默认 warn 或 error
```

---

# 23. Secret Redaction in CLI

CLI 输出前必须经过 Redactor。

必须处理：

```text id="q8ff4s"
stdout summary
stderr summary
error details
report preview
config output
event preview
command echo
environment variable display
```

命令输出中出现 secret 时：

```text id="lcfdil"
显示 [REDACTED]
记录 secret.redacted event
不得在 JSON details 中保留原值
```

---

# 24. Large Output Handling

如果命令输出很大：

```text id="kly9zn"
CLI 只显示摘要
完整输出写入 artifact 文件
报告引用 artifact path
JSON 输出包含 outputPath
```

示例：

```json id="ogtm4x"
{
  "stdoutSummary": "120 tests passed, 1 failed.",
  "outputPath": ".project/reports/artifacts/run_123/test-output.txt"
}
```

限制：

```text id="pnq9zv"
Pretty 默认最多显示 200 行
JSON 默认不内联超大 stdout/stderr
Raw output 必须可配置是否保留
```

---

# 25. Streaming Output

默认不启用稳定流式协议。

未来支持时必须使用：

```text id="kqkjyp"
--stream
```

模式：

```text id="jp5n30"
pretty stream:
  human progress

json stream:
  NDJSON only
```

NDJSON 事件类型：

```text id="8dftqb"
progress
event
warning
error
result
```

---

# 26. Approval Output and Exit Behavior

审批场景输出规则：

```text id="x6lwij"
interactive pretty:
  显示 prompt，等待用户选择

interactive json:
  默认返回 requires-approval，不等待
  除非 --allow-prompts 显式启用

non-interactive:
  返回 requires-approval 或 blocked
  exit code = 60

approval denied:
  返回 ERR_APPROVAL_DENIED
  exit code = 60

approval granted and action succeeds:
  返回 success
  exit code = 0
```

---

# 27. Report Reference Rules

当命令生成报告，CLI 必须输出报告路径。

包括：

```text id="sbgqie"
Run Report
Verification Report
Delivery Report
Task Report
Decision Report
Migration Report
Failure Report
```

Pretty 示例：

```text id="w1up89"
Reports:
  Run Report: .project/reports/runs/run_123.md
  Verification Report: .project/reports/verification/run_123.md
```

JSON 示例：

```json id="fz1lwh"
{
  "reports": [
    {
      "type": "run",
      "path": ".project/reports/runs/run_123.md"
    },
    {
      "type": "verification",
      "path": ".project/reports/verification/run_123.md"
    }
  ]
}
```

---

# 28. Event Reference Rules

CLI 不应输出完整 event log。

CLI 只输出：

```text id="khjq36"
event log path
关键 event id
关键 event type
summary
```

完整事件由以下命令读取：

```bash id="k0sbrj"
harness events <run-id>
harness replay <run-id>
```

---

# 29. Internationalization

P0 默认语言：

```text id="jwhbma"
English
```

P1 可支持：

```text id="2hrbic"
localized human-readable message
```

但以下内容不得本地化：

```text id="yu8bhy"
error code
JSON field name
status enum
event type
config key
report path
CLI flags
```

---

# 30. Backward Compatibility

CLI 输出契约必须版本化。

规则：

```text id="ilechl"
JSON schema breaking change 必须提升 contract version
新增字段允许
删除字段不允许
改变字段类型不允许
改变 enum 语义不允许
Pretty 输出可微调，但测试快照需更新
Exit code 不得随意改变
```

---

# 31. Testing Requirements

必须测试：

```text id="z5x2h3"
pretty success output
pretty error output
json success schema
json error schema
quiet output
exit code mapping
non-interactive approval
CI mode no spinner
secret redaction
large output summary
report refs
event refs
stable command-specific data schemas
```

---

# 32. Snapshot Testing

适合 snapshot 的输出：

```text id="efqj7q"
pretty table
pretty report summary
JSON success output with fixed clock
JSON error output with fixed clock
approval prompt
quiet error output
```

Snapshot 测试必须固定：

```text id="l60et9"
clock
uuid
workspace path
terminal width
color enabled/disabled
```

---

# 33. Implementation Checklist

## P0

```text id="yk25uv"
output mode parser
pretty formatter
json formatter
quiet formatter
stderr/stdout separation
exit code mapper
error output integration
warning output integration
report ref output
secret redaction
CI mode detection
non-interactive mode behavior
```

---

## P1

```text id="tsp954"
approval prompt formatter
NDJSON stream mode
large output artifact handling
terminal width adaptation
config command output
snapshot test fixtures
localized messages
```

---

## P2

```text id="mqfxwt"
rich TUI output
machine-readable schema publishing
CLI output compatibility tests across versions
custom output templates
structured telemetry export
```

---

# 34. Acceptance Criteria

CLI Output Contract 完成标准：

```text id="ryvh8t"
1. CLI 支持 --pretty、--json、--quiet
2. 默认输出模式为 --pretty
3. --json stdout 只输出 JSON
4. --quiet 成功时最少输出
5. 所有错误输出包含错误码
6. 所有错误输出包含 recovery hint
7. JSON 成功输出符合 CliJsonOutput schema
8. JSON 错误输出符合 HarnessError schema
9. stdout/stderr 分离明确
10. 非交互模式不得等待输入
11. CI 模式不得显示 spinner
12. Approval required 有稳定输出
13. Exit code 映射稳定
14. Secret 必须 redacted
15. 大输出必须摘要化
16. 报告路径必须输出
17. Event log 不直接内联输出
18. CLI 输出可 snapshot 测试
19. 命令级 data schema 明确
20. 破坏性输出变更必须版本化
```

---

# 35. Final Definition

Harness OS CLI Output Contract 的最终定义：

```text id="el6pt9"
CLI Output Contract
=
把 Harness OS 的所有命令结果转化为人类可读、机器可读、安全脱敏、退出码稳定、可测试的前台接口。
```

边界关系：

```text id="w38ylu"
CLI 负责展示。
Error Codes 负责结构化失败。
Config 负责输出模式。
Governance 负责审批和阻止。
Observability 负责事件事实源。
Reports 负责长期记录。
Tests 负责锁定输出契约。
Codex 和 CI 通过 JSON 输出安全读取结果。
```
