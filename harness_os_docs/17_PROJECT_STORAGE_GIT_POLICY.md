# Harness OS Project Storage and Git Policy

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Git is the long-term truth; runtime artifacts must not pollute project history

---

# 1. 文档定位

本文件定义 Harness OS 项目存储与 Git 追踪策略。

它用于回答：

```text id="cccb7a"
哪些 .project/ 文件应该被 Git 追踪
哪些 .project/ 文件应该被 .gitignore
哪些文件是长期项目事实
哪些文件只是运行时状态
哪些文件可能包含敏感信息
哪些文件可以进入 Context Pack
哪些文件可以进入 Run Report
哪些文件可以进入 Delivery Pipeline
```

Harness OS 使用 `.project/` 作为项目本地状态目录。

但 `.project/` 中并不是所有内容都应该进入 Git。

本文件的目标是防止：

```text id="u3ukpq"
上下文快照污染 Git 历史
事件日志产生大量噪声
checkpoint 泄露本地状态
session 状态被误提交
secrets 或 raw outputs 被提交
运行时缓存进入长期项目事实
```

---

# 2. 设计目标

Project Storage and Git Policy 必须实现：

```text id="iq89mu"
1. 明确 .project/ 目录结构
2. 明确 Git tracked / ignored / optional tracked 规则
3. 明确长期事实与运行时状态边界
4. 明确敏感数据不得进入 Git
5. 明确大文件与 raw output 处理规则
6. 明确 task、decision、report、context、checkpoint 的追踪策略
7. 明确 .gitignore 模板
8. 明确 Codex 修改 .project/ 文件的权限
9. 明确 Delivery Pipeline 如何引用报告
10. 明确 Context Pack 如何读取 tracked 与 ignored 文件
11. 明确 archive/export 机制
12. 明确测试和 CI 如何校验存储策略
```

---

# 3. 非目标

本文件不做：

```text id="g8nuqx"
替代 Git
替代备份系统
替代文档系统
替代数据库
替代 artifact storage
替代 secret manager
替代外部日志平台
```

Harness OS 只定义项目本地状态与 Git 的关系。

---

# 4. 核心原则

## 4.1 Git Is Long-term Truth

Git 保存长期项目事实。

长期事实包括：

```text id="5kgawx"
项目协议
架构决策
项目配置
稳定文档
可审查任务总结
可复现的模板与 schema
```

Git 不应保存短期运行状态。

---

## 4.2 Runtime State Is Local by Default

运行时状态默认本地保存，不进入 Git。

运行时状态包括：

```text id="5im0u9"
active session
active run
context snapshot
event log
trace
checkpoint
raw stdout/stderr
临时缓存
本地索引
```

---

## 4.3 Human-readable Facts Are Preferably Tracked

如果一个文件满足以下条件，默认可以被 Git 追踪：

```text id="ob3lx9"
人类可读
不含 secret
不含绝对本地路径
不含 raw 大输出
对未来维护有长期价值
能作为项目事实被审查
```

---

## 4.4 Machine Runtime Artifacts Are Ignored

如果一个文件主要用于恢复、重放、缓存或调试，默认不进入 Git。

例如：

```text id="jj6wex"
.project/context/<run-id>.json
.project/reports/events/<run-id>.jsonl
.project/reports/traces/<run-id>.json
.project/checkpoints/<checkpoint-id>.json
.project/sessions/<session-id>.json
```

---

## 4.5 Secrets Never Enter Git

以下内容不得进入 Git：

```text id="zqge12"
.env
.env.*
*.pem
*.key
id_rsa
id_ed25519
credentials.json
service-account.json
tokens
database URLs
cloud credentials
raw environment variables
session cookies
```

如果检测到 secret，应：

```text id="wlz6v8"
阻止提交
记录 secret detected event
写入安全报告
提示用户清理历史
```

---

# 5. .project/ 目录分类

Harness OS 将 `.project/` 内容分为四类。

```text id="gpl3lx"
A. Versioned Project Facts
B. Reviewable Project Memory
C. Local Runtime State
D. Sensitive / Large / Temporary Artifacts
```

---

## 5.1 A 类：Versioned Project Facts

默认应进入 Git。

这些文件是项目长期事实。

```text id="x7r286"
AGENTS.md
.project/state/manifest.json
.project/state/project.md
.project/state/project.json
.project/state/tech-stack.md
.project/state/repository-map.md
.project/state/policy.json
.project/state/skills.json
.project/decisions/*.md
.project/decisions/*.json
.project/templates/**
.project/schemas/**
```

---

## 5.2 B 类：Reviewable Project Memory

默认可进入 Git，但允许项目关闭。

这些文件是可审查的项目记忆。

```text id="idtxh4"
.project/tasks/completed/*.md
.project/tasks/completed/*.json
.project/tasks/failed/*.md
.project/reports/delivery/*.md
.project/reports/verification/*.md
.project/reports/runs/*.md
```

说明：

```text id="k40axm"
B 类文件具有长期价值，但可能产生 Git 噪声。
项目可以选择只追踪 completed task summary 和 delivery report。
raw event、trace、artifact 不属于 B 类。
```

---

## 5.3 C 类：Local Runtime State

默认不进入 Git。

```text id="d5owrq"
.project/state/runtime.json
.project/tasks/active/**
.project/context/**
.project/sessions/**
.project/checkpoints/**
.project/reports/events/**
.project/reports/traces/**
.project/reports/artifacts/**
.project/cache/**
.project/tmp/**
.project/index/**
```

---

## 5.4 D 类：Sensitive / Large / Temporary Artifacts

必须忽略，禁止进入 Git。

```text id="jgqdd4"
.project/**/raw-output/**
.project/**/stdout-raw.*
.project/**/stderr-raw.*
.project/**/secrets/**
.project/**/credentials/**
.project/**/.env
.project/**/*.pem
.project/**/*.key
.project/**/*.sqlite-wal
.project/**/*.sqlite-shm
```

---

# 6. 默认 .project/ 结构

推荐结构：

```text id="zs954f"
.project/
  state/
    manifest.json
    project.md
    project.json
    tech-stack.md
    repository-map.md
    policy.json
    skills.json
    runtime.json

  tasks/
    active/
    completed/
    failed/

  decisions/
    ADR-0001-title.md
    ADR-0001-title.json

  context/
    <run-id>.md
    <run-id>.json

  reports/
    runs/
    verification/
    delivery/
    events/
    traces/
    artifacts/

  checkpoints/
    <checkpoint-id>.json

  sessions/
    <session-id>.json

  schemas/
  templates/
  cache/
  tmp/
  index/
```

---

# 7. Git Tracking Matrix

| Path | Default Git Policy | Reason |
|---|---|---|
| AGENTS.md | track | Project protocol |
| .project/state/manifest.json | track | Machine-readable project config |
| .project/state/project.md | track | Human-readable project identity |
| .project/state/project.json | track | Machine-readable project state facts |
| .project/state/tech-stack.md | track | Long-term project knowledge |
| .project/state/repository-map.md | track | Repository structure knowledge |
| .project/state/policy.json | track | Project governance policy |
| .project/state/skills.json | track | Project skill config |
| .project/state/runtime.json | ignore | Local runtime state |
| .project/decisions/*.md | track | ADR history |
| .project/decisions/*.json | track | ADR machine state |
| .project/tasks/active/** | ignore | Runtime task state |
| .project/tasks/completed/*.md | optional-track | Project memory |
| .project/tasks/completed/*.json | optional-track | Structured project memory |
| .project/tasks/failed/*.md | optional-track | Failure memory |
| .project/context/** | ignore | Large context snapshots |
| .project/reports/runs/*.md | optional-track | Reviewable run summary |
| .project/reports/verification/*.md | optional-track | Verification evidence |
| .project/reports/delivery/*.md | optional-track | Delivery evidence |
| .project/reports/events/** | ignore | Large append-only runtime logs |
| .project/reports/traces/** | ignore | Runtime trace artifacts |
| .project/reports/artifacts/** | ignore | Large/raw outputs |
| .project/checkpoints/** | ignore | Local recovery state |
| .project/sessions/** | ignore | Local session state |
| .project/cache/** | ignore | Cache |
| .project/tmp/** | ignore | Temporary files |
| .project/index/** | ignore | Local generated index |
| .project/schemas/** | track | Stable schema |
| .project/templates/** | track | Stable templates |

---

# 8. 默认 .gitignore 模板

Harness OS 应在项目创建或修复时生成 `.gitignore` 建议块。

```gitignore id="s1ngag"
# Harness OS local runtime state
.project/state/runtime.json
.project/tasks/active/
.project/context/
.project/sessions/
.project/checkpoints/
.project/cache/
.project/tmp/
.project/index/

# Harness OS event and trace logs
.project/reports/events/
.project/reports/traces/
.project/reports/artifacts/

# Harness OS raw outputs and sensitive runtime data
.project/**/raw-output/
.project/**/stdout-raw.*
.project/**/stderr-raw.*
.project/**/secrets/
.project/**/credentials/
.project/**/.env
.project/**/*.pem
.project/**/*.key
.project/**/*.sqlite-wal
.project/**/*.sqlite-shm
```

---

## 8.1 Optional Track Block

如果项目希望追踪可审查报告，可以不要忽略以下目录：

```gitignore id="jy51nf"
# Optional: ignore reviewable reports if your team does not want them in Git
# .project/reports/runs/
# .project/reports/verification/
# .project/reports/delivery/
# .project/tasks/completed/
# .project/tasks/failed/
```

默认推荐：

```text id="lqq21p"
团队项目：
  track completed task summaries and delivery reports
  ignore run reports unless needed

个人项目：
  track completed task summaries
  optionally track run reports

CI-heavy 项目：
  ignore run/verification reports
  publish reports as CI artifacts
```

---

# 9. Source of Truth Rules

## 9.1 Project Protocol

```text id="k151y1"
Source of Truth:
  AGENTS.md
```

AGENTS.md 必须进入 Git。

修改 AGENTS.md 必须审批。

---

## 9.2 Project Config

```text id="c5adnu"
Source of Truth:
  .project/state/manifest.json
  .project/state/policy.json
  .project/state/skills.json
```

这些文件默认进入 Git。

修改安全相关字段必须经过 Governance。

---

## 9.3 Architecture Decisions

```text id="nhndmu"
Source of Truth:
  .project/decisions/*.md
  .project/decisions/*.json
```

accepted ADR 必须进入 Git。

accepted ADR 修改必须审批。

---

## 9.4 Runtime State

```text id="omyljb"
Source of Truth:
  Local .project runtime files
```

但 runtime state 不是长期项目事实。

它用于：

```text id="dbwtyc"
resume
replay
debug
failure diagnosis
local recovery
```

默认不进入 Git。

---

## 9.5 Delivery Evidence

```text id="sttotx"
Source of Truth:
  Git commit
  PR
  release
  delivery report
```

Delivery Report 可进入 Git，也可作为 CI artifact。

但 PR body 必须引用 Run Report / Verification Report / Delivery Report 的路径或摘要。

---

# 10. Context Pack Git Policy

Context Pack 默认不进入 Git。

路径：

```text id="sw0jy1"
.project/context/<run-id>.md
.project/context/<run-id>.json
```

原因：

```text id="qgsh05"
可能很大
可能包含任务局部上下文
可能包含本地路径摘要
频繁生成导致 Git 噪声
可由 tracked facts + run state 重建
```

Context Pack 可以进入 Run Report 摘要，但不得全文进入 Git。

---

## 10.1 Context Pack Exception

以下情况可导出 Context Pack：

```text id="nn3uhk"
debug reproduction
external review
benchmark fixture
regression test fixture
```

导出必须：

```text id="fy2bw7"
脱敏
移除绝对路径
移除 secrets
写入 export/ 或 test fixture
由人工审查后提交
```

---

# 11. Event Log and Trace Git Policy

Event Log 和 Trace 默认不进入 Git。

路径：

```text id="skbahq"
.project/reports/events/<run-id>.jsonl
.project/reports/traces/<run-id>.json
```

原因：

```text id="pnt3bn"
文件可能快速变大
包含大量运行时细节
每次 run 都变化
不适合作为长期 Git 历史
```

长期保留方式：

```text id="i8l1tn"
本地保留
CI artifact
压缩归档
外部 observability backend
```

---

# 12. Checkpoint Git Policy

Checkpoint 默认不进入 Git。

路径：

```text id="rki8us"
.project/checkpoints/<checkpoint-id>.json
```

原因：

```text id="r0zbz6"
包含本地恢复状态
可能包含绝对路径
可能包含临时 diff metadata
可能体积较大
可能与用户本地环境绑定
```

Checkpoint 可用于本地恢复，但不是长期项目事实。

---

# 13. Session State Git Policy

Session State 默认不进入 Git。

路径：

```text id="gwcpfx"
.project/sessions/<session-id>.json
```

原因：

```text id="iu2s3n"
包含本地运行上下文
可能与 Codex CLI 会话绑定
无法跨机器稳定复用
可能包含本地路径和临时状态
```

---

# 14. Task Record Git Policy

Task Record 分层处理。

## 14.1 Active Tasks

```text id="zpya8o"
.project/tasks/active/
```

默认忽略。

原因：

```text id="y8zte2"
active task 是运行时状态
频繁变化
中断后可由本地 state 恢复
不适合作为团队长期事实
```

---

## 14.2 Completed Tasks

```text id="axkxak"
.project/tasks/completed/
```

默认 optional-track。

推荐策略：

```text id="oetgfp"
如果团队希望保留项目执行记忆：
  track completed task markdown summaries

如果团队不希望 Git 噪声：
  ignore completed tasks and rely on reports/artifacts
```

Completed Task 可以作为长期知识进入 Context Pack。

---

## 14.3 Failed Tasks

```text id="tewm8e"
.project/tasks/failed/
```

默认 optional-track。

建议：

```text id="hx5xur"
只追踪有长期价值的 failure summary
忽略 raw logs 和 trace
失败中可能包含敏感路径或输出，提交前必须 redacted
```

---

# 15. Report Git Policy

Reports 分三类。

## 15.1 Run Report

```text id="xmlnyn"
.project/reports/runs/<run-id>.md
```

默认 optional-track。

用途：

```text id="a34yt0"
审查一次 Codex run
生成 PR body
支持人工复盘
```

如果追踪，必须：

```text id="ze0a9z"
脱敏
摘要化
不包含 raw stdout/stderr
不包含完整 Context Pack
不包含 secret
```

---

## 15.2 Verification Report

```text id="ohucpr"
.project/reports/verification/<run-id>.md
```

默认 optional-track。

建议：

```text id="twy1ul"
本地开发可忽略
PR/release 相关 verification report 可追踪或作为 CI artifact
```

---

## 15.3 Delivery Report

```text id="hjmv9d"
.project/reports/delivery/<delivery-id>.md
```

默认 optional-track，推荐在 release/deploy 场景追踪或归档。

Delivery Report 是交付证据。

---

## 15.4 Raw Artifacts

```text id="zef5j6"
.project/reports/artifacts/
```

必须忽略。

包括：

```text id="iopocs"
raw stdout
raw stderr
large test output
coverage output
build logs
temporary screenshots
debug dumps
```

---

# 16. Decision Record Git Policy

Decision Records 必须进入 Git。

包括：

```text id="z4qz96"
.project/decisions/ADR-*.md
.project/decisions/ADR-*.json
```

规则：

```text id="h6w7i8"
proposed ADR 可以进入 Git
accepted ADR 必须进入 Git
rejected ADR 可以进入 Git 作为历史
superseded ADR 必须保留
accepted ADR 修改必须审批
supersede accepted ADR 必须审批
```

Decision Records 是长期架构事实。

---

# 17. State File Git Policy

## 17.1 Tracked State Files

```text id="oc7szw"
.project/state/manifest.json
.project/state/project.md
.project/state/project.json
.project/state/tech-stack.md
.project/state/repository-map.md
.project/state/policy.json
.project/state/skills.json
```

这些文件描述项目长期状态。

---

## 17.2 Ignored State Files

```text id="s96pzn"
.project/state/runtime.json
.project/state/local.json
.project/state/locks.json
```

这些文件描述本地运行状态，不进入 Git。

---

# 18. Local Database Policy

如果 Harness OS 使用 SQLite，本地数据库默认不进入 Git。

路径示例：

```text id="uqf673"
.project/state/harness.sqlite
.project/state/harness.sqlite-wal
.project/state/harness.sqlite-shm
```

默认忽略。

如果需要长期事实，必须导出为：

```text id="aqdhfh"
Markdown
JSON
Report
ADR
Task Record
```

SQLite 只是运行时索引或状态存储，不是 Git 长期事实。

---

# 19. Index and Cache Policy

以下目录默认忽略：

```text id="of6xq2"
.project/index/
.project/cache/
.project/tmp/
```

说明：

```text id="h70pqm"
Repository symbol index 可以重建。
cache 可以重建。
tmp 没有长期价值。
```

如果需要可复现测试，应将最小 fixture 单独导出到：

```text id="jcewxe"
tests/fixtures/
```

---

# 20. Storage Policy Config

项目可以在 manifest 中配置存储策略。

路径：

```text id="ginowx"
.project/state/manifest.json
```

示例：

```json id="vnwzzu"
{
  "storage": {
    "trackCompletedTasks": true,
    "trackFailedTasks": false,
    "trackRunReports": false,
    "trackVerificationReports": false,
    "trackDeliveryReports": true,
    "ignoreContextSnapshots": true,
    "ignoreCheckpoints": true,
    "ignoreSessions": true,
    "ignoreRawArtifacts": true,
    "maxReportSizeKb": 256
  }
}
```

---

## 20.1 Storage Config Schema

```ts id="vfe5d9"
export interface StoragePolicyConfig {
  trackCompletedTasks: boolean
  trackFailedTasks: boolean
  trackRunReports: boolean
  trackVerificationReports: boolean
  trackDeliveryReports: boolean

  ignoreContextSnapshots: boolean
  ignoreCheckpoints: boolean
  ignoreSessions: boolean
  ignoreRawArtifacts: boolean

  maxReportSizeKb: number
  requireRedactionBeforeTrack: boolean
}
```

默认值：

```json id="haw8w9"
{
  "trackCompletedTasks": true,
  "trackFailedTasks": false,
  "trackRunReports": false,
  "trackVerificationReports": false,
  "trackDeliveryReports": true,
  "ignoreContextSnapshots": true,
  "ignoreCheckpoints": true,
  "ignoreSessions": true,
  "ignoreRawArtifacts": true,
  "maxReportSizeKb": 256,
  "requireRedactionBeforeTrack": true
}
```

---

# 21. Git Preflight Checks

在以下动作前必须执行 Git preflight：

```text id="m7jbum"
harness run
harness verify
harness deliver
harness migrate
harness repair
修改 AGENTS.md
修改 accepted ADR
修改 manifest/policy
```

必须检查：

```text id="bdr8yc"
current branch
git status
tracked .project changes
ignored .project changes
untracked sensitive files
dirty state
protected branch
```

---

# 22. Git Safety Rules

Harness OS 必须遵守：

```text id="q9q57y"
不得覆盖用户未提交修改
不得自动 git add ignored runtime artifacts
不得自动提交 secrets
不得自动提交 context snapshots
不得自动提交 checkpoints
不得自动提交 sessions
不得自动提交 raw outputs
不得自动提交 event logs/traces
```

---

# 23. Delivery Integration

Delivery Pipeline 必须读取 Storage Policy。

创建 PR 前必须确认：

```text id="xb017o"
未提交 runtime artifacts
未提交 secrets
未提交 raw outputs
未提交 context snapshots
未提交 checkpoints
tracked .project files 符合 storage policy
Delivery Report 已生成或已引用
Verification Report 已生成或已引用
```

如果发现不应提交的文件：

```text id="pl3b71"
阻止 delivery
返回 ERR_DELIVERY_BLOCKED
记录 storage.policy.violation
提示更新 .gitignore 或移除文件
```

---

# 24. Context Integration

Context Builder 可以读取 tracked facts 和 local runtime state。

但必须区分：

```text id="gzp1bx"
tracked project facts
local runtime facts
ignored artifacts
sensitive blocked files
```

Context Pack 中必须标记来源类型：

```ts id="wtrktz"
export type ContextSourceStorageClass =
  | "tracked-fact"
  | "optional-memory"
  | "local-runtime"
  | "ignored-artifact"
  | "blocked-sensitive"
```

规则：

```text id="tpk7l6"
blocked-sensitive 不得进入 Context Pack
ignored-artifact 默认不得进入 Context Pack
local-runtime 只能进入摘要
tracked-fact 可作为核心上下文
optional-memory 可按任务相关性进入上下文
```

---

# 25. Governance Integration

以下操作必须经过 Governance：

```text id="ur6h2q"
修改 AGENTS.md
修改 .project/state/manifest.json
修改 .project/state/policy.json
修改 .project/state/skills.json
修改 accepted ADR
将 ignored artifact 加入 Git
将 context snapshot 加入 Git
将 checkpoint 加入 Git
将 session state 加入 Git
提交包含 secret 的文件
修改 .gitignore 中 Harness OS 保护规则
```

高风险操作：

```text id="fr6mxl"
把 .project/context/ 加入 Git
把 .project/checkpoints/ 加入 Git
把 .project/sessions/ 加入 Git
关闭 secret redaction
关闭 storage policy check
```

---

# 26. Observability Integration

Storage Policy 相关事件必须记录：

```text id="azr6yp"
storage.policy.checked
storage.policy.allowed
storage.policy.blocked
storage.gitignore.generated
storage.gitignore.updated
storage.secret.detected
storage.large-artifact.blocked
storage.runtime-artifact.ignored
storage.report.tracked
storage.report.ignored
```

Event payload 必须包含：

```text id="ncxvmj"
path
storage class
git policy
decision
reason
risk level
redacted details
```

---

# 27. Repair Behavior

`harness repair` 必须检查：

```text id="v9a5az"
.project/ required directories
required tracked state files
.gitignore Harness OS block
missing schemas/templates
invalid storage config
accidentally tracked runtime artifacts
missing redaction policy
```

Repair 可以自动：

```text id="m4af68"
创建缺失目录
创建 .gitignore Harness OS block
恢复默认 storage policy
生成缺失 README 占位文件
```

Repair 不得无审批：

```text id="k8eocb"
删除用户文件
修改 AGENTS.md
修改 accepted ADR
清理 Git 历史
删除已提交文件
```

---

# 28. Migration Behavior

Storage policy 变更时必须迁移。

例如：

```text id="nbt1sp"
从 v1 到 v2:
  .project/runs/ -> .project/reports/runs/
  .project/logs/ -> .project/reports/events/
```

迁移必须：

```text id="y1kmr9"
创建 pre-migration checkpoint
写 migration report
更新 .gitignore
记录 migration events
保留可恢复路径
```

---

# 29. Security Rules

提交前必须检查：

```text id="qkpi3m"
secrets
private keys
.env
raw environment variables
database URLs
cloud credentials
raw stdout/stderr
absolute local paths in tracked reports
oversized tracked files
```

如果发现：

```text id="q8dmvi"
阻止提交
提示 redaction
提示移入 ignored artifact
写 security event
```

---

# 30. CLI Commands

## 30.1 Storage Commands

```bash id="o41sws"
harness storage status
harness storage policy
harness storage check
harness storage repair
```

---

## 30.2 Git Policy Commands

```bash id="h9rzbv"
harness git-policy check
harness git-policy doctor
harness git-policy write-gitignore
```

---

## 30.3 Example Output

```text id="ubt4yl"
Storage Policy Check

Tracked facts:
  AGENTS.md
  .project/state/manifest.json
  .project/decisions/ADR-0001.md

Ignored runtime:
  .project/context/run_123.json
  .project/checkpoints/checkpoint_123.json

Blocked:
  .project/context/run_124.json contains possible secret

Result:
  blocked
```

---

# 31. Testing Requirements

必须测试：

```text id="ptgec4"
default .gitignore generated
tracked facts are not ignored
runtime artifacts are ignored
context snapshots are ignored
checkpoints are ignored
sessions are ignored
raw artifacts are ignored
secrets are blocked
storage policy config loads
delivery blocked when ignored artifacts are staged
repair adds missing gitignore block
Context Builder marks storage class
```

---

# 32. Implementation Checklist

## P0

```text id="k11xhf"
storage policy schema
default .project layout
.gitignore template
storage classifier
Git preflight check
secret/path/large file check
Delivery integration
Governance integration
Context source storage class
repair gitignore block
storage events
```

---

## P1

```text id="bd4ucs"
storage CLI commands
optional tracking config
report size limit enforcement
migration behavior
CI storage policy check
artifact export
storage report
```

---

## P2

```text id="u7f5rc"
remote artifact storage
team storage policy
advanced Git history scanner
encrypted local state
storage dashboard
automatic archive pruning
```

---

# 33. Acceptance Criteria

Project Storage and Git Policy 完成标准：

```text id="k4s3fl"
1. .project/ 目录分类明确
2. tracked / ignored / optional tracked 规则明确
3. 默认 .gitignore 模板可生成
4. AGENTS.md 必须被 tracked
5. manifest/policy/skills 配置必须被 tracked
6. accepted ADR 必须被 tracked
7. runtime.json 默认 ignored
8. context snapshots 默认 ignored
9. checkpoints 默认 ignored
10. sessions 默认 ignored
11. event logs/traces 默认 ignored
12. raw artifacts 必须 ignored
13. secrets 必须 blocked
14. Delivery 前必须执行 storage policy check
15. Context Pack 必须标记 storage class
16. Governance 必须保护 storage policy 变更
17. Repair 能恢复 .gitignore block
18. Migration 能处理 storage layout 变化
19. 测试覆盖 Git policy matrix
20. 不允许 Codex 自动提交 ignored runtime artifacts
```

---

# 34. Final Definition

Harness OS Project Storage and Git Policy 的最终定义：

```text id="br9kaf"
Project Storage and Git Policy
=
把 .project/ 中的长期项目事实、可审查项目记忆、本地运行状态、敏感与大体积产物明确分层，
确保 Git 只保存应该成为项目历史的内容。
```

边界关系：

```text id="nmmgjr"
Git 负责长期事实。
.project/ 负责项目本地状态。
AGENTS.md 负责项目协议。
Decision Records 负责架构事实。
Context Snapshots 负责运行时上下文，不默认进 Git。
Checkpoints 负责本地恢复，不默认进 Git。
Reports 负责审计摘要，可按策略进入 Git。
Governance 负责阻止不安全追踪。
Delivery 负责交付前检查 Git policy。
```
