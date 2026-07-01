# Harness OS Migration and Versioning Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Every persistent format must be versioned, every breaking change must be migratable, and every migration must be recoverable

---

# 1. 文档定位

本文件定义 Harness OS 的迁移与版本管理策略。

它用于规范：

```text id="h2c5rr"
Harness OS 版本
.project/ 结构版本
manifest schema 版本
policy schema 版本
skills schema 版本
task record 版本
decision record 版本
context pack 版本
report 版本
checkpoint 版本
event log 版本
CLI output contract 版本
Skill manifest 版本
```

Harness OS 是一个会长期伴随项目运行的系统。

因此它必须支持：

```text id="k5ww4a"
旧项目升级
旧 schema 迁移
旧 .project/ 结构迁移
配置文件迁移
状态文件迁移
报告格式兼容
Skill manifest 兼容
CLI 输出契约兼容
```

最终目标：

```text id="ykudhn"
Harness OS 升级不能破坏已有项目。
```

---

# 2. 设计目标

Migration and Versioning 必须实现：

```text id="k8l3bt"
1. 定义 Harness OS 自身版本规则
2. 定义 .project/ schema version
3. 定义配置文件版本规则
4. 定义状态文件版本规则
5. 定义 migration lifecycle
6. 定义 migration preflight
7. 定义 migration checkpoint
8. 定义 migration dry-run
9. 定义 migration rollback
10. 定义 breaking change 处理方式
11. 定义向后兼容策略
12. 定义迁移事件和报告
13. 定义 Codex 实现迁移时的工程规范
14. 定义迁移测试要求
```

---

# 3. 非目标

本文件不做：

```text id="s0gmbh"
替代 Git migration
替代数据库专业迁移工具
替代云服务迁移系统
替代包管理器版本解析
替代外部 CI/CD 发布策略
替代生产数据迁移审核
```

本文件只定义 Harness OS 自身状态、配置、文档和运行时格式的版本与迁移策略。

---

# 4. 核心原则

## 4.1 Version Everything Persistent

凡是会长期保存在磁盘上的结构化文件，都必须有版本。

包括：

```text id="n43chb"
manifest.json
policy.json
skills.json
runtime.json
task state
decision state
context snapshot
run trace
event log
verification result
delivery plan
checkpoint metadata
```

---

## 4.2 Migrate Before Use

如果 Harness OS 打开项目时发现 schema 版本低于当前支持版本，必须先判断是否需要迁移。

不得在未知版本状态下继续运行。

---

## 4.3 Checkpoint Before Migration

任何会修改 `.project/` 持久状态的迁移前，必须创建 migration checkpoint。

如果 checkpoint 无法创建，迁移不得继续。

---

## 4.4 Dry-run First

迁移必须支持 dry-run。

dry-run 必须输出：

```text id="er1xoz"
将修改哪些文件
将新增哪些文件
将删除或移动哪些文件
是否需要审批
是否存在风险
是否可自动迁移
是否需要人工处理
```

---

## 4.5 No Silent Breaking Change

破坏性变更不得静默执行。

破坏性迁移必须：

```text id="ryj6xv"
生成 migration plan
请求审批
创建 checkpoint
写 migration report
记录 migration events
提供 rollback path
```

---

## 4.6 Backward Compatible Readers

Harness OS 应尽量支持读取旧版本格式。

策略：

```text id="c3o8c8"
能读旧格式
写新格式
必要时提示迁移
不直接覆盖未知字段
```

---

# 5. Version Dimensions

Harness OS 使用多个版本维度。

```text id="brtsc2"
1. Harness OS package version
2. Project schema version
3. Config schema version
4. State schema version
5. Skill manifest version
6. CLI output contract version
7. Report format version
8. Migration version
```

---

# 6. Harness OS Package Version

Harness OS 自身使用 SemVer。

格式：

```text id="q3v8ub"
MAJOR.MINOR.PATCH
```

语义：

```text id="4yrgja"
MAJOR
  可能包含破坏性 schema 或 CLI contract 变化。

MINOR
  增加向后兼容的新能力、新字段、新命令。

PATCH
  修复 bug，不改变 schema 和 CLI contract。
```

示例：

```text id="f278zy"
1.0.0
1.1.0
1.1.1
2.0.0
```

---

# 7. Project Schema Version

项目 schema version 存储在：

```text id="w73ueg"
.project/state/manifest.json
```

字段：

```json id="z79jm2"
{
  "version": "1.0",
  "projectSchemaVersion": "1.0"
}
```

Project Schema Version 表示 `.project/` 目录结构和核心状态文件格式。

---

## 7.1 Project Schema Compatibility

兼容规则：

```text id="ftfhcl"
same major:
  Harness OS 必须尽量兼容读取。

higher minor:
  旧 Harness 可以拒绝写入，但应尽量只读。

higher major:
  必须拒绝自动运行，提示升级 Harness OS。

lower version:
  可执行迁移。
```

---

# 8. Config Schema Version

所有配置文件必须包含 version。

示例：

```json id="p62wia"
{
  "version": "1.0",
  "governance": {
    "network": "restricted"
  }
}
```

适用文件：

```text id="tmucl7"
~/.harness/config.json
~/.harness/policy.json
~/.harness/delivery.json
~/.harness/skills.json
.project/state/manifest.json
.project/state/policy.json
.project/state/skills.json
.project/state/runtime.json
```

---

# 9. State Schema Version

运行时状态文件必须包含 schema version。

例如：

```json id="wnmcnz"
{
  "version": "1.0",
  "stateType": "run",
  "runId": "run_123"
}
```

适用对象：

```text id="blz4e7"
run state
task state
session state
checkpoint metadata
context snapshot
event trace
verification result
delivery plan
```

---

# 10. Skill Manifest Version

每个 Skill Manifest 必须声明版本。

```ts id="d3oh48"
export interface SkillManifest {
  name: string
  version: string
  schemaVersion: string
  description: string
  tools: SkillToolManifest[]
}
```

规则：

```text id="txcn18"
Skill version
  表示 Skill 实现版本。

schemaVersion
  表示 manifest 格式版本。

tool input/output schema
  也应有版本或 schema id。
```

---

# 11. CLI Output Contract Version

CLI JSON 输出必须包含 contract version。

```json id="ohac4k"
{
  "ok": true,
  "meta": {
    "version": "1.0",
    "outputMode": "json",
    "generatedAt": "2026-06-11T00:00:00.000Z",
    "redacted": true
  }
}
```

破坏性变更包括：

```text id="j3masc"
删除字段
修改字段类型
修改 enum 语义
修改 exit code 语义
修改 error code 语义
```

新增字段不算破坏性变更。

---

# 12. Migration Types

Harness OS 迁移分为五类。

```text id="gg8ptu"
1. config migration
2. project layout migration
3. state migration
4. report migration
5. skill manifest migration
```

---

## 12.1 Config Migration

用于迁移配置字段。

示例：

```text id="p9y5eq"
governance.networkMode
  -> governance.network

delivery.autoPush
  -> delivery.allowAutoPush
```

---

## 12.2 Project Layout Migration

用于迁移目录结构。

示例：

```text id="nogpl0"
.project/runs/
  -> .project/reports/runs/

.project/logs/
  -> .project/reports/events/

.project/memory/
  -> .project/state/
```

---

## 12.3 State Migration

用于迁移 JSON state 文件。

示例：

```text id="aeh1vu"
task.status = "done"
  -> task.status = "completed"

run.phase
  -> run.status
```

---

## 12.4 Report Migration

用于迁移 Markdown 报告模板或 frontmatter。

示例：

```text id="rey4j0"
Run Report 缺少 Verification section
  -> 添加 ## Verification

Delivery Report 缺少 Risk section
  -> 添加 ## Risks
```

---

## 12.5 Skill Manifest Migration

用于迁移 Skill manifest schema。

示例：

```text id="h9fvuh"
tool.risk
  -> tool.riskLevel

tool.approval
  -> tool.requiresApproval
```

---

# 13. Migration Lifecycle

标准迁移生命周期：

```text id="w9x6m2"
detected
  -> planned
  -> preflighted
  -> checkpointed
  -> approved
  -> executed
  -> verified
  -> reported
  -> completed
```

失败状态：

```text id="vix5wi"
blocked
failed
rolled-back
manual-required
```

---

# 14. Migration Flow

标准流程：

```text id="wdnq37"
1. harness open 读取 project schema version
2. Migration Detector 判断是否需要迁移
3. Migration Planner 生成 Migration Plan
4. Preflight 检查 Git 状态和 storage policy
5. Dry-run 输出将变更内容
6. Governance 判断是否需要审批
7. 创建 migration checkpoint
8. 执行 migration
9. 校验迁移后 schema
10. 运行 storage policy check
11. 写 migration report
12. 记录 migration events
13. 更新 manifest schema version
```

---

# 15. Migration Plan

## 15.1 Migration Plan Schema

```ts id="bkcqk1"
export interface MigrationPlan {
  id: string

  projectId: string
  fromVersion: string
  toVersion: string

  migrationType:
    | "config"
    | "project-layout"
    | "state"
    | "report"
    | "skill-manifest"
    | "mixed"

  steps: MigrationStep[]

  riskLevel: "low" | "medium" | "high"

  requiresApproval: boolean

  checkpointRequired: boolean

  affectedPaths: string[]

  destructiveChanges: string[]

  manualSteps: string[]

  createdAt: string
}
```

---

## 15.2 Migration Step Schema

```ts id="suef35"
export interface MigrationStep {
  id: string
  title: string
  description: string

  action:
    | "read"
    | "write"
    | "move"
    | "copy"
    | "rename"
    | "delete"
    | "transform-json"
    | "transform-markdown"
    | "update-gitignore"
    | "validate"

  sourcePath?: string
  targetPath?: string

  reversible: boolean

  requiresApproval: boolean
}
```

---

# 16. Migration Result

```ts id="reydrf"
export interface MigrationResult {
  id: string
  planId: string

  projectId: string
  fromVersion: string
  toVersion: string

  status:
    | "completed"
    | "failed"
    | "blocked"
    | "rolled-back"
    | "manual-required"

  executedSteps: string[]
  skippedSteps: string[]
  failedStep?: string

  checkpointId?: string

  reportPath: string

  startedAt: string
  endedAt: string

  errors: HarnessError[]
  warnings: string[]
}
```

---

# 17. Migration Preflight

迁移前必须检查：

```text id="fggdz4"
project exists
AGENTS.md exists
.project/ exists
manifest readable
schema version readable
git status readable
dirty state
untracked sensitive files
storage policy violations
available disk space
write permissions
checkpoint support
```

---

## 17.1 Dirty Git State

如果存在未提交修改：

```text id="d4flvb"
低风险迁移：
  可以继续，但必须警告。

中风险迁移：
  要求用户确认或创建 checkpoint。

高风险迁移：
  必须审批，推荐要求 clean git state。
```

---

## 17.2 Sensitive Files

如果检测到 secret 或敏感文件：

```text id="k9fw3h"
阻止迁移
返回 ERR_SECRET_ACCESS_BLOCKED 或 ERR_MIGRATION_FAILED
写 security event
提示用户先清理
```

---

# 18. Migration Checkpoint

迁移前必须创建 checkpoint。

Checkpoint 必须记录：

```text id="cvedki"
project schema version
manifest hash
affected paths
git status
current branch
storage policy
migration plan id
timestamp
```

不要求复制整个项目。

但必须保存足够信息用于恢复和人工排查。

---

# 19. Migration Approval Rules

以下迁移必须审批：

```text id="i7as0r"
删除文件
移动大量文件
修改 AGENTS.md
修改 accepted ADR
修改 policy.json
修改 skills.json
修改 storage policy
改变 .gitignore 中 Harness block
改变 tracked / ignored 规则
迁移到不兼容 major version
任何不可逆迁移
```

默认允许：

```text id="khjb92"
新增缺失字段并使用默认值
新增目录
新增 schema 文件
新增 template 文件
重命名未被用户修改的 generated 文件
修复 runtime-only 文件格式
```

---

# 20. Destructive Migrations

Destructive migration 指可能导致数据丢失或历史不可读的迁移。

包括：

```text id="kqv9fx"
删除旧字段且无法恢复
删除旧目录
压缩并丢弃 raw output
重写 reports
清理 checkpoints
清理 sessions
改变 ADR 状态语义
```

规则：

```text id="xi3dx9"
必须审批
必须 checkpoint
必须写入 report
必须提供 manual rollback path
不得自动清理 Git 历史
```

---

# 21. Migration Report

路径：

```text id="paqovx"
.project/reports/migration/<migration-id>.md
```

格式：

```markdown id="unykzd"
# Migration Report: <migration-id>

## Summary

## From Version

## To Version

## Migration Type

## Final Status

## Affected Paths

## Steps Executed

## Steps Skipped

## Destructive Changes

## Manual Steps

## Checkpoint

## Verification

## Errors

## Warnings

## Rollback Path
```

---

# 22. Migration Events

必须记录事件：

```text id="hrcpzy"
migration.detected
migration.plan.created
migration.preflight.started
migration.preflight.completed
migration.approval.required
migration.checkpoint.created
migration.started
migration.step.completed
migration.step.failed
migration.completed
migration.failed
migration.rollback.started
migration.rollback.completed
```

事件 payload 必须包含：

```text id="s5z1f5"
migration id
from version
to version
step id
affected paths
status
risk level
checkpoint id
redacted details
```

---

# 23. Schema Registry

Harness OS 必须维护 schema registry。

推荐路径：

```text id="w44g99"
schemas/
  manifest.schema.json
  policy.schema.json
  skills.schema.json
  task.schema.json
  decision.schema.json
  context.schema.json
  report.schema.json
  checkpoint.schema.json
  migration.schema.json
```

项目内模板路径：

```text id="p6vldy"
.project/schemas/
```

规则：

```text id="ytw4j9"
核心 schema 在 Harness OS 包内。
项目可复制稳定 schema 到 .project/schemas/ 作为项目事实。
schema 文件必须有版本。
```

---

# 24. Migration Registry

Harness OS 必须维护 migration registry。

```ts id="g2m6ja"
export interface MigrationRegistry {
  migrations: MigrationDefinition[]
}
```

```ts id="nnqjae"
export interface MigrationDefinition {
  id: string
  fromVersion: string
  toVersion: string
  type: string
  description: string
  riskLevel: "low" | "medium" | "high"
  execute: MigrationExecutor
  dryRun: MigrationDryRun
  rollback?: MigrationRollback
}
```

规则：

```text id="h2u5hn"
迁移必须按版本顺序执行。
不能跳过中间 major migration。
每个 migration 必须可 dry-run。
每个 migration 必须有测试。
```

---

# 25. Version Compatibility Matrix

示例：

| Harness OS Version | Supports Project Schema | Can Read | Can Write | Requires Migration |
|---|---|---|---|---|
| 1.0.x | 1.0 | 1.0 | 1.0 | no |
| 1.1.x | 1.0, 1.1 | 1.0, 1.1 | 1.1 | yes if writing new fields |
| 2.0.x | 1.x, 2.0 | 1.x, 2.0 | 2.0 | yes |

规则：

```text id="b8bdkp"
Harness 可以读旧版本。
Harness 默认写当前版本。
旧 Harness 遇到新 major project schema 必须拒绝写入。
```

---

# 26. Backward Compatibility Rules

允许的兼容变更：

```text id="w68hid"
新增可选字段
新增 enum 值但旧 reader 可忽略
新增 report section
新增 event type
新增 CLI JSON 字段
新增 Skill tool
新增 config 默认字段
```

破坏性变更：

```text id="sse47r"
删除必需字段
重命名字段
改变字段类型
改变 enum 语义
改变目录结构
改变默认安全策略为更宽松
改变 CLI exit code 语义
改变 error code 语义
```

注意：

```text id="dtw3ro"
安全策略只能变得更严格，不能通过 migration 变得更宽松。
```

---

# 27. Downgrade Policy

默认不支持 downgrade。

```text id="hdg3ni"
allowDowngrade = false
```

如果需要 downgrade：

```text id="t340e2"
必须显式配置
必须审批
必须 dry-run
必须说明数据损失
必须 checkpoint
```

不支持 downgrade 时返回：

```text id="lcehy8"
ERR_MIGRATION_UNSUPPORTED_DOWNGRADE
```

---

# 28. Config Migration Rules

Config migration 必须：

```text id="m9fvqa"
保留未知字段
保留注释不可保证，因为 JSON 不支持注释
对安全字段采用更严格默认值
不得把 secret 写入新配置
不得放宽 safety-locked 字段
```

示例：

```text id="xp3syf"
旧字段：
  allowNetwork: true

新字段：
  governance.network: "restricted"

原因：
  默认迁移选择安全配置，而不是自动开放网络。
```

---

# 29. Storage Migration Rules

Storage migration 必须遵守 `17_PROJECT_STORAGE_GIT_POLICY.md`。

规则：

```text id="hrjquj"
迁移后 runtime artifacts 仍应 ignored
迁移后 tracked facts 仍应 tracked
不得把 context snapshots 加入 Git
不得把 checkpoints 加入 Git
不得把 event logs/traces 加入 Git
不得把 raw artifacts 加入 Git
```

迁移必须更新 `.gitignore` Harness block。

---

# 30. Task and Decision Migration Rules

## 30.1 Task Migration

Task 状态迁移必须保留：

```text id="bglrzt"
task id
title
status
createdAt
updatedAt
run ids
changed files
verification status
risks
summary
```

状态语义变化必须记录。

---

## 30.2 Decision Migration

Decision 迁移必须保留：

```text id="y5ubgj"
ADR number
title
status
createdAt
acceptedAt
supersededBy
rationale
consequences
```

accepted ADR 的内容迁移必须审批。

不得自动改变 accepted/rejected/superseded 语义。

---

# 31. Context and Report Migration Rules

## 31.1 Context Snapshot

Context snapshot 默认 runtime-only。

旧 context 可选择不迁移。

规则：

```text id="rviayp"
旧 context 可保留只读
不要求迁移全部历史 context
必要时只迁移 metadata
```

---

## 31.2 Reports

Markdown report 迁移应保守。

规则：

```text id="bxevqa"
不要重写人工编辑内容
只添加缺失 metadata 或 frontmatter
不要删除已有章节
旧 report 可以保持旧格式，只要可读
```

---

# 32. Event Log Migration Rules

Event Log 默认 append-only。

规则：

```text id="tam63y"
不得重写历史 event log
不得删除历史 event
新版本 reader 应支持旧 event type
必要时生成 trace migration summary
```

如果必须转换：

```text id="wujg74"
写新 trace 文件
保留旧 event log
记录 migration event
```

---

# 33. Skill Migration Rules

Skill manifest 迁移必须：

```text id="iwecu3"
校验旧 manifest
生成新 manifest
保留 tool name
保留 input/output schema 意图
保留 risk level
保留 requiresApproval
不得降低风险等级
不得关闭 approval requirement
```

如果无法自动迁移：

```text id="xpi32x"
status = manual-required
写 migration report
提示开发者更新 Skill
```

---

# 34. CLI Commands

## 34.1 Migration Commands

```bash id="wnz0m1"
harness migrate
harness migrate --check
harness migrate --dry-run
harness migrate --apply
harness migrate --rollback <migration-id>
```

---

## 34.2 Version Commands

```bash id="r642t2"
harness version
harness version --json
harness schema version
harness schema check
harness schema list
```

---

## 34.3 Example Output

```text id="vrk27p"
Migration required

Project schema: 1.0
Harness supports: 1.1
Target schema: 1.1

Planned changes:
  Add .project/reports/migration/
  Add storage policy defaults to manifest.json
  Update .gitignore Harness block

Risk:
  medium

Next:
  harness migrate --dry-run
  harness migrate --apply
```

---

# 35. Error Codes

Migration 使用以下错误码：

```text id="c485ej"
ERR_MIGRATION_REQUIRED
ERR_MIGRATION_FAILED
ERR_MIGRATION_UNSUPPORTED_DOWNGRADE
ERR_CONFIG_UNSUPPORTED_VERSION
ERR_CONFIG_INVALID
ERR_PROJECT_CORRUPTED
ERR_CHECKPOINT_RESTORE_FAILED
ERR_APPROVAL_REQUIRED
ERR_APPROVAL_DENIED
```

---

# 36. Governance Integration

Migration 必须经过 Governance。

必须审批的情况：

```text id="tmyhfo"
高风险迁移
不可逆迁移
删除文件
修改安全策略
修改 AGENTS.md
修改 accepted ADR
修改 .gitignore Harness block
修改 tracked / ignored policy
downgrade
```

Governance 必须阻止：

```text id="r826wc"
关闭 secret redaction
关闭 event log
关闭 approval for high risk
绕过 storage policy
迁移后允许 policy bypass
```

---

# 37. Observability Integration

Migration 必须进入 Observability。

必须记录：

```text id="oowvcq"
migration detected
migration plan
preflight result
approval result
checkpoint id
executed steps
failed steps
rollback result
report path
```

Run Report 可引用 Migration Report。

---

# 38. Delivery Integration

如果迁移发生在交付前，Delivery Pipeline 必须检查：

```text id="oqrlwt"
migration completed
migration report exists
post-migration verification passed or approved exception
storage policy check passed
schema version updated
no unresolved migration warnings
```

如果迁移未完成：

```text id="epy9mu"
Delivery blocked
返回 ERR_DELIVERY_BLOCKED
```

---

# 39. Testing Requirements

Migration 必须有测试。

必须覆盖：

```text id="xjj3g7"
migration detection
dry-run output
migration plan schema
preflight failure
checkpoint creation
approval-required migration
successful migration
failed migration
rollback path
unsupported downgrade
invalid config version
storage policy preservation
gitignore update
report writing
event logging
schema validation after migration
```

---

# 40. Migration Fixtures

测试夹具路径：

```text id="vxrr4b"
tests/fixtures/migrations/
```

推荐结构：

```text id="ncooq8"
tests/fixtures/migrations/
  project-schema-1.0/
  project-schema-1.1/
  invalid-schema/
  missing-manifest/
  dirty-git/
  storage-policy-old/
  skill-manifest-old/
  reports-old-format/
```

---

# 41. Implementation Checklist

## P0

```text id="joq7j8"
schema version fields
migration detector
migration plan schema
migration registry
dry-run command
preflight checks
checkpoint before migration
basic config migration
basic project layout migration
migration report writer
migration events
schema validation after migration
```

---

## P1

```text id="ocd0yq"
rollback command
storage migration
skill manifest migration
task/decision state migration
report metadata migration
compatibility matrix
migration fixtures
migration tests
delivery migration guard
```

---

## P2

```text id="pc0hh9"
interactive migration UI
advanced downgrade support
migration assistant
remote migration registry
team migration policy
migration analytics
cross-project migration
```

---

# 42. Acceptance Criteria

Migration and Versioning 完成标准：

```text id="uw6gce"
1. 所有持久化 schema 都有 version
2. manifest 包含 projectSchemaVersion
3. Harness OS 使用 SemVer
4. Migration Detector 可发现旧 schema
5. Migration Plan 可生成
6. migration --check 可用
7. migration --dry-run 可用
8. migration --apply 可用
9. 迁移前必须 checkpoint
10. 高风险迁移必须审批
11. 迁移必须写 Migration Report
12. 迁移必须记录 Observability events
13. 迁移后必须 schema validation
14. 迁移不得关闭安全策略
15. 迁移不得提交 secrets
16. 迁移不得把 runtime artifacts 加入 Git
17. downgrade 默认不支持
18. 失败迁移必须提供 recovery path
19. 测试覆盖 migration fixtures
20. Delivery 必须阻止未完成迁移的项目交付
```

---

# 43. Final Definition

Harness OS Migration and Versioning 的最终定义：

```text id="kfite0"
Migration and Versioning
=
让 Harness OS 的项目状态、配置、文档、报告、Skills 和 CLI 契约在长期演进中保持可升级、可验证、可恢复、可审计。
```

边界关系：

```text id="iusduu"
Versioning 负责识别格式。
Migration 负责转换格式。
Checkpoint 负责迁移前恢复点。
Governance 负责审批高风险迁移。
Storage Policy 负责防止迁移污染 Git。
Observability 负责记录迁移事实。
Delivery 负责阻止未完成迁移后的交付。
Codex 负责实现迁移代码，但不得绕过迁移规则。
```
