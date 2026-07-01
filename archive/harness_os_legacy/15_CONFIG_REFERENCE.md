# Harness OS Config Reference

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Configuration must be explicit, typed, layered, governed, and observable

---

# 1. 文档定位

本文件定义 Harness OS 的统一配置参考。

它用于规范：

```text id="ixv1lm"
Global Config
Project Config
Runtime Config
Policy Config
Skill Config
Context Config
Verification Config
Observability Config
Delivery Config
Migration Config
CLI Config
```

本文件是 Harness OS 配置项的单一参考入口。

其他模块文档可以定义各自需要的配置，但最终必须映射到本文件中的配置结构、默认值、作用域、权限等级和治理规则。

---

# 2. 设计目标

Config Reference 必须实现：

```text id="nf6hzi"
1. 统一所有配置文件路径
2. 统一配置项命名
3. 统一配置项类型
4. 统一默认值
5. 统一配置优先级
6. 统一配置修改权限
7. 统一配置校验方式
8. 统一配置迁移方式
9. 统一配置错误处理
10. 统一配置进入 Context Pack 的规则
11. 统一配置进入 Observability 的规则
12. 防止配置散落在多个模块中无人维护
```

---

# 3. 非目标

本文件不做：

```text id="s80jqw"
替代 AGENTS.md
替代用户当前指令
替代环境变量管理器
替代 secret manager
替代企业级配置中心
替代外部 Feature Flag 平台
替代云权限系统
```

Harness OS 的配置系统只负责 Harness 自身运行行为。

项目协议仍由 `AGENTS.md` 表达。

Secrets 不应直接写入配置文件。

---

# 4. 核心原则

## 4.1 Explicit over Implicit

所有影响执行、安全、交付、验证的行为都必须有显式配置或显式默认值。

不得依赖隐藏规则。

---

## 4.2 Safe by Default

默认配置必须保守。

默认应当：

```text id="66tlg0"
禁止自动 push
禁止自动 deploy
禁止 force push
限制网络访问
限制 workspace 外访问
启用 secret redaction
启用 event log
启用 policy check
高风险操作要求审批
```

---

## 4.3 Layered Configuration

Harness OS 配置分层：

```text id="duo9pe"
1. User Current Instruction
2. Harness Global Safety Policy
3. Global Config
4. Project AGENTS.md
5. Project Manifest
6. Project Runtime State
7. Skill Default Config
8. Harness Default Config
```

---

## 4.4 Governance Cannot Be Disabled by Project Config

项目配置不能关闭全局安全策略。

例如：

```text id="j7ior9"
项目不能通过 manifest 允许无审批 deploy
项目不能通过 manifest 允许读取 secrets
项目不能通过 manifest 绕过 Policy Engine
项目不能通过 manifest 允许 Skill 直接执行
```

项目配置只能在全局策略允许范围内收紧或选择性启用能力。

---

## 4.5 Configuration Is Observable

配置加载、校验、覆盖、迁移、拒绝都必须记录事件。

例如：

```text id="v85w39"
config.loaded
config.validated
config.override.applied
config.override.denied
config.migration.required
config.migration.completed
config.invalid
```

---

# 5. 配置文件总览

Harness OS 使用以下配置文件。

```text id="qacmxt"
Global:
  ~/.harness/config.json
  ~/.harness/policy.json
  ~/.harness/delivery.json
  ~/.harness/skills.json

Project:
  AGENTS.md
  .project/state/manifest.json
  .project/state/project.json
  .project/state/runtime.json
  .project/state/skills.json
  .project/state/policy.json

Generated / Runtime:
  .project/context/<run-id>.json
  .project/reports/events/<run-id>.jsonl
  .project/reports/traces/<run-id>.json
  .project/checkpoints/<checkpoint-id>.json
```

---

# 6. 配置优先级

## 6.1 Resolution Order

配置解析顺序：

```text id="ls20yj"
1. Harness Default Config
2. Skill Default Config
3. Global Config
4. Global Policy Config
5. Project Manifest
6. Project Policy Config
7. Project Runtime State
8. AGENTS.md Rules
9. User Current Instruction
```

---

## 6.2 Conflict Rule

如果配置冲突：

```text id="q92osr"
更安全的配置优先
更明确的配置优先
更高层级的安全策略优先
用户当前指令可以收紧权限
用户当前指令不能绕过全局安全策略
项目配置不能放宽全局安全策略
```

---

## 6.3 Example

```text id="wu7bfl"
Global policy:
  requireApprovalForDeploy = true

Project manifest:
  allowDeploy = true

Final decision:
  deploy 仍然需要审批
```

---

# 7. Config Schema Root

统一根结构：

```ts id="ocb3zx"
export interface HarnessConfigRoot {
  version: string

  project?: ProjectConfig
  runtime?: RuntimeConfig
  context?: ContextConfig
  skills?: SkillsConfig
  governance?: GovernanceConfig
  verification?: VerificationConfig
  observability?: ObservabilityConfig
  delivery?: DeliveryConfig
  state?: StateConfig
  cli?: CliConfig
  migration?: MigrationConfig
}
```

---

# 8. Global Config

路径：

```text id="g1ehxa"
~/.harness/config.json
```

用途：

```text id="qk2fo6"
定义用户机器级 Harness OS 默认行为。
```

示例：

```json id="ybzgtc"
{
  "version": "1.0",
  "runtime": {
    "defaultWorkspaceMode": "local",
    "maxConcurrentRuns": 1,
    "defaultTimeoutMs": 300000
  },
  "cli": {
    "defaultOutputMode": "pretty",
    "interactive": true,
    "color": true
  },
  "observability": {
    "eventLog": true,
    "runTrace": true,
    "redactSecrets": true
  }
}
```

---

## 8.1 Global Config Fields

| Field | Type | Default | Scope | Permission |
|---|---|---:|---|---|
| version | string | "1.0" | global | user |
| runtime.defaultWorkspaceMode | "local" \| "remote" | "local" | global | user |
| runtime.maxConcurrentRuns | number | 1 | global | user |
| runtime.defaultTimeoutMs | number | 300000 | global | user |
| cli.defaultOutputMode | "pretty" \| "json" \| "quiet" | "pretty" | global | user |
| cli.interactive | boolean | true | global | user |
| cli.color | boolean | true | global | user |
| observability.eventLog | boolean | true | global | safety-locked |
| observability.runTrace | boolean | true | global | safety-locked |
| observability.redactSecrets | boolean | true | global | safety-locked |

---

# 9. Global Policy Config

路径：

```text id="o7dji6"
~/.harness/policy.json
```

用途：

```text id="l7n9xm"
定义不能被项目配置绕过的全局安全策略。
```

示例：

```json id="qnp6ac"
{
  "version": "1.0",
  "governance": {
    "defaultNetwork": "restricted",
    "allowWorkspaceOutsideAccess": false,
    "requireApprovalForDeploy": true,
    "requireApprovalForPushMain": true,
    "requireApprovalForForcePush": true,
    "requireApprovalForDependencyAdd": true,
    "requireApprovalForAgentsMdEdit": true,
    "requireApprovalForAcceptedAdrEdit": true,
    "redactSecrets": true,
    "allowPolicyBypass": false
  }
}
```

---

## 9.1 Global Policy Fields

| Field | Type | Default | Permission |
|---|---|---:|---|
| governance.defaultNetwork | "restricted" \| "allowlist" \| "open" | "restricted" | safety-locked |
| governance.allowWorkspaceOutsideAccess | boolean | false | safety-locked |
| governance.requireApprovalForDeploy | boolean | true | safety-locked |
| governance.requireApprovalForPushMain | boolean | true | safety-locked |
| governance.requireApprovalForForcePush | boolean | true | safety-locked |
| governance.requireApprovalForDependencyAdd | boolean | true | safety-locked |
| governance.requireApprovalForAgentsMdEdit | boolean | true | safety-locked |
| governance.requireApprovalForAcceptedAdrEdit | boolean | true | safety-locked |
| governance.redactSecrets | boolean | true | safety-locked |
| governance.allowPolicyBypass | boolean | false | immutable |

---

# 10. Global Delivery Config

路径：

```text id="bnk9r1"
~/.harness/delivery.json
```

示例：

```json id="l8qg7s"
{
  "version": "1.0",
  "delivery": {
    "defaultPRProvider": "github",
    "requireApprovalForPushMain": true,
    "requireApprovalForProductionDeploy": true,
    "allowForcePush": false,
    "defaultBaseBranch": "main"
  }
}
```

---

## 10.1 Global Delivery Fields

| Field | Type | Default | Permission |
|---|---|---:|---|
| delivery.defaultPRProvider | "github" \| "gitlab" \| "none" | "github" | user |
| delivery.requireApprovalForPushMain | boolean | true | safety-locked |
| delivery.requireApprovalForProductionDeploy | boolean | true | safety-locked |
| delivery.allowForcePush | boolean | false | safety-locked |
| delivery.defaultBaseBranch | string | "main" | user |

---

# 11. Global Skills Config

路径：

```text id="rymisb"
~/.harness/skills.json
```

示例：

```json id="nd2fgx"
{
  "version": "1.0",
  "skills": {
    "globallyEnabled": [
      "filesystem",
      "shell",
      "git",
      "repo-scanner"
    ],
    "globallyDisabled": [],
    "allowCustomSkills": false,
    "allowRemoteSkills": false
  }
}
```

---

## 11.1 Global Skills Fields

| Field | Type | Default | Permission |
|---|---|---:|---|
| skills.globallyEnabled | string[] | ["filesystem","shell","git","repo-scanner"] | user |
| skills.globallyDisabled | string[] | [] | user |
| skills.allowCustomSkills | boolean | false | safety-locked |
| skills.allowRemoteSkills | boolean | false | safety-locked |

---

# 12. Project Manifest

路径：

```text id="wkiloz"
.project/state/manifest.json
```

用途：

```text id="flkrg2"
定义项目级 Harness OS 配置，是项目内最重要的机器可读配置。
```

示例：

```json id="xfm9vn"
{
  "version": "1.0",
  "project": {
    "id": "project-demo",
    "name": "demo",
    "root": ".",
    "type": "application",
    "language": ["typescript"],
    "packageManager": "pnpm"
  },
  "runtime": {
    "maxConcurrentRuns": 1,
    "requireCleanGitBeforeRun": false
  },
  "context": {
    "tokenBudget": 120000,
    "includeGitDiff": true,
    "includeAcceptedDecisions": true,
    "includeAvailableSkills": true,
    "writeMarkdownSnapshot": true,
    "writeJsonSnapshot": true
  },
  "skills": {
    "enabled": ["filesystem", "shell", "git", "repo-scanner"],
    "disabled": [],
    "strictDeclaredCommands": true
  },
  "governance": {
    "network": "restricted",
    "protectedBranches": ["main", "master"],
    "allowAutoCommit": false,
    "allowAutoPush": false,
    "allowDeploy": false,
    "secretRedaction": true
  },
  "verification": {
    "commands": {
      "lint": "pnpm lint",
      "typecheck": "pnpm typecheck",
      "test": "pnpm test",
      "build": "pnpm build"
    },
    "required": ["lint", "typecheck", "test"],
    "optional": ["build"]
  },
  "observability": {
    "eventLog": true,
    "runTrace": true,
    "recordToolCalls": true,
    "recordContextUsage": true,
    "retainRawOutputs": false
  },
  "delivery": {
    "defaultBaseBranch": "main",
    "allowAutoCommit": false,
    "allowAutoPush": false,
    "allowAutoPR": false,
    "allowDeploy": false,
    "commitMessageFormat": "conventional"
  }
}
```

---

# 13. Project Config Fields

## 13.1 Project

```ts id="z1mwey"
export interface ProjectConfig {
  id: string
  name: string
  root: string
  type: "application" | "library" | "service" | "monorepo" | "unknown"
  language: string[]
  packageManager?: "npm" | "pnpm" | "yarn" | "pip" | "poetry" | "uv" | "cargo" | "go" | "unknown"
}
```

| Field | Required | Default | Permission |
|---|---|---:|---|
| project.id | yes | generated | protected |
| project.name | yes | directory name | user |
| project.root | yes | "." | protected |
| project.type | yes | "unknown" | user |
| project.language | yes | [] | user |
| project.packageManager | no | "unknown" | user |

---

## 13.2 Runtime

```ts id="p5p9j2"
export interface RuntimeConfig {
  maxConcurrentRuns: number
  requireCleanGitBeforeRun: boolean
  defaultTimeoutMs: number
  allowResume: boolean
  allowCheckpoint: boolean
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| runtime.maxConcurrentRuns | number | 1 | user |
| runtime.requireCleanGitBeforeRun | boolean | false | user |
| runtime.defaultTimeoutMs | number | 300000 | user |
| runtime.allowResume | boolean | true | protected |
| runtime.allowCheckpoint | boolean | true | protected |

---

## 13.3 Context

```ts id="a2204q"
export interface ContextConfig {
  tokenBudget: number
  includeGitStatus: boolean
  includeGitDiff: boolean
  includeAgentsRules: boolean
  includeAcceptedDecisions: boolean
  includeAvailableSkills: boolean
  includeVerificationCommands: boolean
  writeMarkdownSnapshot: boolean
  writeJsonSnapshot: boolean
  trimStrategy: "priority" | "size" | "none"
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| context.tokenBudget | number | 120000 | user |
| context.includeGitStatus | boolean | true | protected |
| context.includeGitDiff | boolean | true | user |
| context.includeAgentsRules | boolean | true | protected |
| context.includeAcceptedDecisions | boolean | true | protected |
| context.includeAvailableSkills | boolean | true | protected |
| context.includeVerificationCommands | boolean | true | protected |
| context.writeMarkdownSnapshot | boolean | true | protected |
| context.writeJsonSnapshot | boolean | true | protected |
| context.trimStrategy | "priority" \| "size" \| "none" | "priority" | user |

---

## 13.4 Skills

```ts id="scn879"
export interface SkillsConfig {
  enabled: string[]
  disabled: string[]
  strictDeclaredCommands: boolean
  allowCustomSkills: boolean
  allowRemoteSkills: boolean
  defaultTimeoutMs: number
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| skills.enabled | string[] | P0 skills | user |
| skills.disabled | string[] | [] | user |
| skills.strictDeclaredCommands | boolean | true | protected |
| skills.allowCustomSkills | boolean | false | safety-locked |
| skills.allowRemoteSkills | boolean | false | safety-locked |
| skills.defaultTimeoutMs | number | 300000 | user |

---

## 13.5 Governance

```ts id="mucn62"
export interface GovernanceConfig {
  network: "restricted" | "allowlist" | "open"
  protectedBranches: string[]
  allowWorkspaceOutsideAccess: boolean
  allowAutoCommit: boolean
  allowAutoPush: boolean
  allowDeploy: boolean
  secretRedaction: boolean
  requireApprovalForHighRisk: boolean
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| governance.network | "restricted" \| "allowlist" \| "open" | "restricted" | safety-locked |
| governance.protectedBranches | string[] | ["main","master"] | protected |
| governance.allowWorkspaceOutsideAccess | boolean | false | safety-locked |
| governance.allowAutoCommit | boolean | false | user |
| governance.allowAutoPush | boolean | false | safety-locked |
| governance.allowDeploy | boolean | false | safety-locked |
| governance.secretRedaction | boolean | true | immutable |
| governance.requireApprovalForHighRisk | boolean | true | immutable |

---

## 13.6 Verification

```ts id="oorscs"
export interface VerificationConfig {
  commands: Record<string, string>
  required: string[]
  optional: string[]
  timeoutMs: Record<string, number>
  allowSkippedVerification: boolean
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| verification.commands | Record<string,string> | {} | user |
| verification.required | string[] | ["lint","typecheck","test"] | user |
| verification.optional | string[] | ["build"] | user |
| verification.timeoutMs | Record<string,number> | {} | user |
| verification.allowSkippedVerification | boolean | false | protected |

---

## 13.7 Observability

```ts id="cf3kb8"
export interface ObservabilityConfig {
  eventLog: boolean
  runTrace: boolean
  recordToolCalls: boolean
  recordContextUsage: boolean
  recordFileChanges: boolean
  recordApprovals: boolean
  redactSecrets: boolean
  retainRawOutputs: boolean
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| observability.eventLog | boolean | true | immutable |
| observability.runTrace | boolean | true | protected |
| observability.recordToolCalls | boolean | true | protected |
| observability.recordContextUsage | boolean | true | protected |
| observability.recordFileChanges | boolean | true | protected |
| observability.recordApprovals | boolean | true | protected |
| observability.redactSecrets | boolean | true | immutable |
| observability.retainRawOutputs | boolean | false | user |

---

## 13.8 Delivery

```ts id="tq6jyj"
export interface DeliveryConfig {
  defaultBaseBranch: string
  allowAutoCommit: boolean
  allowAutoPush: boolean
  allowAutoPR: boolean
  allowDeploy: boolean
  requireApprovalForRelease: boolean
  requireApprovalForDeploy: boolean
  protectedBranches: string[]
  commitMessageFormat: "conventional" | "plain"
}
```

| Field | Type | Default | Permission |
|---|---|---:|---|
| delivery.defaultBaseBranch | string | "main" | user |
| delivery.allowAutoCommit | boolean | false | user |
| delivery.allowAutoPush | boolean | false | safety-locked |
| delivery.allowAutoPR | boolean | false | user |
| delivery.allowDeploy | boolean | false | safety-locked |
| delivery.requireApprovalForRelease | boolean | true | safety-locked |
| delivery.requireApprovalForDeploy | boolean | true | safety-locked |
| delivery.protectedBranches | string[] | ["main","master"] | protected |
| delivery.commitMessageFormat | "conventional" \| "plain" | "conventional" | user |

---

# 14. Project Policy Config

路径：

```text id="kh5fj9"
.project/state/policy.json
```

用途：

```text id="te44wu"
保存项目级安全策略。该文件可以收紧权限，但不能放宽全局安全策略。
```

示例：

```json id="kcth4r"
{
  "version": "1.0",
  "policy": {
    "network": "restricted",
    "allowBrowserFetch": false,
    "allowExternalDocs": true,
    "allowWorkspaceOutsideAccess": false,
    "requireApprovalForDependencyAdd": true,
    "requireApprovalForPackageManagerChange": true,
    "requireApprovalForArchitectureChange": true
  }
}
```

---

# 15. Project Runtime Config

路径：

```text id="enx7ko"
.project/state/runtime.json
```

用途：

```text id="h6u3tz"
保存当前项目运行时状态，不作为长期架构事实。
```

示例：

```json id="owvp7a"
{
  "version": "1.0",
  "runtime": {
    "activeRunId": "run_123",
    "activeTaskId": "task_123",
    "lastOpenedAt": "2026-06-11T00:00:00.000Z",
    "lastContextPackId": "ctx_123"
  }
}
```

说明：

```text id="hv5b8d"
runtime.json 是运行状态，不应被视为项目长期事实。
是否纳入 Git 追踪由 17_PROJECT_STORAGE_GIT_POLICY.md 定义。
```

---

# 16. Project Skills Config

路径：

```text id="ydgz6e"
.project/state/skills.json
```

用途：

```text id="ohqlap"
保存项目启用的 Skills、禁用的 Skills、Skill overrides。
```

示例：

```json id="mq5idp"
{
  "version": "1.0",
  "skills": {
    "enabled": ["filesystem", "shell", "git", "repo-scanner", "test-runner"],
    "disabled": ["database"],
    "overrides": {
      "shell.run_command": {
        "requiresApproval": true,
        "timeoutMs": 120000
      }
    }
  }
}
```

---

# 17. Config Permission Levels

配置项权限等级：

```text id="kzivxp"
user
  用户或项目可以修改。

protected
  可以修改，但需要通过 Governance 检查，部分场景需要审批。

safety-locked
  默认不可由项目放宽，只能由全局安全策略或用户明确审批收紧/配置。

immutable
  Harness OS 安全不变量，不允许关闭。

generated
  Harness 自动生成，用户不应手动修改。
```

---

## 17.1 Permission Table

| Permission | Can User Modify | Can Project Modify | Approval Required | Example |
|---|---:|---:|---:|---|
| user | yes | yes | no | context.tokenBudget |
| protected | yes | yes | maybe | protectedBranches |
| safety-locked | yes | no loosen | yes | allowDeploy |
| immutable | no | no | n/a | observability.redactSecrets=false |
| generated | no manual | no manual | n/a | project.id |

---

# 18. Environment Variables

环境变量只用于运行时覆盖，不作为长期项目事实。

推荐变量：

```text id="ky6y90"
HARNESS_CONFIG_HOME
HARNESS_OUTPUT_MODE
HARNESS_NO_COLOR
HARNESS_NON_INTERACTIVE
HARNESS_LOG_LEVEL
HARNESS_DEFAULT_TIMEOUT_MS
HARNESS_ALLOW_NETWORK
HARNESS_TEST_MODE
```

---

## 18.1 Environment Variable Rules

```text id="wq8mrh"
环境变量可以收紧配置。
环境变量不能放宽 safety-locked 配置。
环境变量不得包含 secret 值并进入报告。
环境变量值写入日志前必须 redacted。
```

---

## 18.2 Environment Variable Table

| Env | Type | Effect | Default |
|---|---|---|---|
| HARNESS_CONFIG_HOME | path | config root | ~/.harness |
| HARNESS_OUTPUT_MODE | pretty/json/quiet | CLI output mode | pretty |
| HARNESS_NO_COLOR | boolean | disable color | false |
| HARNESS_NON_INTERACTIVE | boolean | disable prompts | false |
| HARNESS_LOG_LEVEL | debug/info/warn/error | logging level | info |
| HARNESS_DEFAULT_TIMEOUT_MS | number | default timeout | 300000 |
| HARNESS_ALLOW_NETWORK | boolean | request network openness | false |
| HARNESS_TEST_MODE | boolean | enable test behavior | false |

---

# 19. CLI Config

```ts id="ko7f1y"
export interface CliConfig {
  defaultOutputMode: "pretty" | "json" | "quiet"
  interactive: boolean
  color: boolean
  logLevel: "debug" | "info" | "warn" | "error"
  preserveFailedWorkspace: boolean
}
```

默认值：

```json id="pm9mid"
{
  "cli": {
    "defaultOutputMode": "pretty",
    "interactive": true,
    "color": true,
    "logLevel": "info",
    "preserveFailedWorkspace": true
  }
}
```

---

# 20. State Config

```ts id="dab9sg"
export interface StateConfig {
  backend: "filesystem" | "sqlite"
  checkpointEnabled: boolean
  checkpointBeforeHighRisk: boolean
  resumeEnabled: boolean
  maxCheckpoints: number
}
```

默认值：

```json id="uleku7"
{
  "state": {
    "backend": "filesystem",
    "checkpointEnabled": true,
    "checkpointBeforeHighRisk": true,
    "resumeEnabled": true,
    "maxCheckpoints": 50
  }
}
```

---

# 21. Migration Config

```ts id="kkk4kk"
export interface MigrationConfig {
  schemaVersion: string
  autoMigrate: boolean
  requireCheckpointBeforeMigration: boolean
  allowDowngrade: boolean
}
```

默认值：

```json id="rm4qbd"
{
  "migration": {
    "schemaVersion": "1.0",
    "autoMigrate": false,
    "requireCheckpointBeforeMigration": true,
    "allowDowngrade": false
  }
}
```

---

# 22. Config Validation

所有配置加载后必须校验。

必须校验：

```text id="cmux54"
schema version
required fields
unknown fields
type correctness
permission level
global policy compatibility
project policy compatibility
secret leakage
path safety
command safety
```

---

## 22.1 Unknown Fields

未知字段处理策略：

```text id="e0knka"
P0:
  warning but continue

P1:
  configurable strict mode

P2:
  schema migration suggestions
```

---

## 22.2 Invalid Config

非法配置必须返回：

```text id="6az9f0"
ERR_CONFIG_INVALID
```

不支持版本必须返回：

```text id="q6wiba"
ERR_CONFIG_UNSUPPORTED_VERSION
```

需要迁移必须返回：

```text id="2tte79"
ERR_MIGRATION_REQUIRED
```

---

# 23. Config Redaction

配置写入日志、报告、Context Pack 前必须脱敏。

禁止进入配置的内容：

```text id="puwqum"
API keys
tokens
passwords
private keys
database URLs
OAuth tokens
cloud credentials
session cookies
```

统一输出：

```text id="s2b4l5"
[REDACTED]
```

---

# 24. Config and Context Pack

Context Pack 可以包含配置摘要，但不得包含完整配置。

允许包含：

```text id="l25fvi"
enabled skills
disabled skills
verification command names
policy summary
delivery policy summary
context budget
protected branches
network mode
```

禁止包含：

```text id="pldzz8"
secret values
raw environment variables
full global config
user home path if sensitive
credentials
tokens
```

---

# 25. Config and Observability

必须记录以下事件：

```text id="h1q1cx"
config.loaded
config.validated
config.invalid
config.override.applied
config.override.denied
config.migration.required
config.migration.started
config.migration.completed
config.redacted
```

事件 payload 必须包含：

```text id="xqpkoj"
config scope
config path
schema version
validation status
override summary
redacted details
```

---

# 26. Config and Governance

修改以下配置必须经过 Governance：

```text id="qacfr6"
governance.*
delivery.allowAutoPush
delivery.allowDeploy
delivery.requireApprovalForDeploy
delivery.requireApprovalForRelease
skills.allowCustomSkills
skills.allowRemoteSkills
skills.strictDeclaredCommands
observability.eventLog
observability.redactSecrets
context.includeAgentsRules
context.includeAcceptedDecisions
state.checkpointEnabled
migration.allowDowngrade
```

修改以下配置必须默认拒绝：

```text id="rm5tz3"
governance.allowPolicyBypass = true
observability.redactSecrets = false
governance.secretRedaction = false
governance.requireApprovalForHighRisk = false
skills.directExecution = true
delivery.allowForcePush = true without approval
```

---

# 27. Config and AGENTS.md

AGENTS.md 是项目协议，不是普通配置文件。

关系：

```text id="rnl1k5"
AGENTS.md 定义人类可读项目规则。
manifest.json 定义机器可读项目配置。
policy.json 定义项目安全策略。
Context Pack 组合三者摘要给 Codex。
```

冲突处理：

```text id="lxzjza"
AGENTS.md 比 manifest 更接近项目协议。
Global Safety Policy 比 AGENTS.md 更高。
用户当前指令可以收紧 AGENTS.md。
用户当前指令不能绕过 Global Safety Policy。
```

---

# 28. Config and Skills

Skill 启用必须满足：

```text id="b78c7j"
Skill 已注册
Skill manifest 合法
Skill 未被全局禁用
Skill 未被项目禁用
Skill 出现在 Context Pack 中
Skill 通过 Governance 检查
```

Skill override 示例：

```json id="upg3hb"
{
  "skills": {
    "overrides": {
      "shell.run_command": {
        "timeoutMs": 60000,
        "requiresApproval": true,
        "riskLevel": "medium"
      }
    }
  }
}
```

---

# 29. Config and Verification

Verification 配置优先级：

```text id="lwdnfs"
1. AGENTS.md declared commands
2. manifest.verification.commands
3. package manifests
4. Makefile / CI config
5. inferred commands marked uncertain
```

规则：

```text id="zuhcia"
不得凭空编造验证命令。
verification.required 缺失时使用默认质量门。
verification.skipped 必须写 reason。
verification.failed 必须阻止 task completion。
```

---

# 30. Config and Delivery

Delivery 配置必须遵守：

```text id="jh6gas"
allowAutoCommit 可由项目决定。
allowAutoPush 默认 false。
allowDeploy 默认 false。
release 必须审批。
deploy 必须审批。
push main 必须审批。
force push 默认禁止。
```

---

# 31. Config Migration

配置结构变化必须通过 migration。

规则：

```text id="o5h6x4"
配置 schema version 必须明确。
重大迁移前必须创建 checkpoint。
迁移必须写 migration report。
迁移失败必须可恢复。
不支持 downgrade，除非明确支持。
```

CLI：

```bash id="f6eqmj"
harness migrate
harness migrate --check
harness migrate --dry-run
```

---

# 32. Config Testing Requirements

必须测试：

```text id="h3c6ll"
default config loads
global config loads
project manifest loads
project policy loads
invalid config returns ERR_CONFIG_INVALID
unsupported version returns ERR_CONFIG_UNSUPPORTED_VERSION
safety-locked config cannot be loosened by project
secret values are redacted
config summary enters Context Pack
config events enter Observability
migration required is detected
```

---

# 33. Implementation Checklist

## P0

```text id="inxq5y"
Config schema
default config
global config loader
project manifest loader
project policy loader
config merge
config validation
permission-level enforcement
secret redaction
config error codes
Context Pack config summary
```

---

## P1

```text id="u3p30n"
global delivery config
global skills config
runtime config
observability config events
config migration check
CLI config output
strict unknown field mode
```

---

## P2

```text id="h9ts4h"
team config
remote config registry
policy packs
config UI
config diff viewer
config migration assistant
```

---

# 34. Acceptance Criteria

Config Reference 完成标准：

```text id="j7cst4"
1. 所有配置文件路径已定义
2. 所有配置项有类型
3. 所有配置项有默认值
4. 所有配置项有作用域
5. 所有配置项有权限等级
6. 配置优先级明确
7. Global Safety Policy 不能被项目配置绕过
8. Project manifest 可校验
9. Project policy 可校验
10. 配置加载失败返回结构化错误
11. 配置迁移有明确策略
12. 配置摘要可以进入 Context Pack
13. Secret 不得进入配置摘要
14. 配置事件进入 Observability
15. 高风险配置修改经过 Governance
16. safety-locked 配置不能被项目放宽
17. immutable 配置不能被关闭
18. CLI 可以展示有效配置
19. 测试覆盖配置合并和冲突
20. 新增配置必须先登记到本文件
```

---

# 35. Final Definition

Harness OS Config Reference 的最终定义：

```text id="pcixgp"
Config Reference
=
把 Harness OS 分散在各模块中的配置项统一成可校验、可合并、可治理、可迁移、可审计的单一配置体系。
```

边界关系：

```text id="jdlb6a"
AGENTS.md 负责项目协议。
Manifest 负责机器可读项目配置。
Policy Config 负责安全边界。
Runtime Config 负责运行状态。
Global Config 负责用户机器默认行为。
Governance 负责配置修改权限。
Observability 负责记录配置事件。
Migration 负责配置版本演进。
```
