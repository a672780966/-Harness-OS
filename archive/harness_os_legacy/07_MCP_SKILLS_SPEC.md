# Harness OS MCP Skills Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Skills are tools, not agents

---

# 1. 模块定位

MCP Skills 是 Harness OS 的内部工具能力层。

它不是外挂插件市场，不是多 Agent 系统，也不是 workflow 节点系统。

它的目标是把 Codex 可以使用的工程能力标准化、权限化、可观测化、可恢复化。

最终定义：

```text
Codex = 唯一执行 Agent

MCP Skills = Codex 可调用的受控工具能力

Harness OS = 管理 Skills 的运行时、权限、日志、审批、验证和状态
```

---

# 2. 设计目标

MCP Skills 必须实现以下目标：

```text
1. 为 Codex 暴露受控工具能力
2. 统一 Skill 输入输出协议
3. 为每次调用记录事件
4. 为高风险工具调用接入 Approval Gate
5. 为文件、Shell、Git、GitHub、Browser、Repo Scanner、Database、Delivery 提供标准能力
6. 禁止 Skill 自行推理和规划
7. 禁止 Skill 变成 Agent
8. 支持任务恢复、回放和审计
9. 支持 Context Pack 声明可用 Skills
10. 支持按项目启用和禁用 Skills
```

---

# 3. 非目标

MCP Skills 不做：

```text
多 Agent 调度
Planner / Worker / Reviewer 拆分
模型路由
独立推理
自主规划
任务拆解
自动决策
外部插件市场
未审批远程执行
无治理 shell 执行
```

所有推理、规划、总结、Review 仍由 Codex 完成。Skills 只负责执行确定性工具能力。

---

# 4. 核心原则

## 4.1 Skills Are Tools

Skill 是工具，不是智能体。

```text
Skill 可以：
  读取文件
  写入文件
  执行命令
  查询 Git
  创建 PR
  扫描仓库
  运行测试
  写报告

Skill 不可以：
  自己决定项目目标
  自己拆任务
  自己改架构
  自己跳过审批
  自己调用模型推理
```

## 4.2 Codex Owns Reasoning

所有语义判断由 Codex 完成：任务理解、方案选择、代码修改、错误分析、架构判断、上下文压缩、Review、总结。Skill 只返回事实结果。

## 4.3 Harness Owns Governance

Harness OS 负责 Skill 注册、权限、风险级别、审批、日志、事件、超时、输出脱敏和错误处理。

## 4.4 Project-Scoped Execution

所有 Skill 调用默认限制在当前项目 workspace 内，禁止默认访问 workspace 外文件、系统敏感路径、未授权网络、未授权环境变量、未授权凭据。

## 4.5 Observable by Default

每一次 Skill 调用都必须记录 run id、task id、skill name、tool name、input summary、output summary、status、duration、risk level、approval event、error。

---

# 5. 总体架构

```text
MCP Skill Runtime
│
├── Skill Registry
├── Skill Manifest Loader
├── Skill Permission Manager
├── Skill Execution Engine
├── Approval Gate Adapter
├── Secret Redactor
├── Event Logger
├── Timeout Manager
├── Result Normalizer
└── Skill Implementations
    ├── Filesystem Skill
    ├── Shell Skill
    ├── Git Skill
    ├── GitHub Skill
    ├── Browser Skill
    ├── Repo Scanner Skill
    ├── Test Runner Skill
    ├── Database Skill
    └── Delivery Skill
```

---

# 6. Skill Registry

Skill Registry 负责注册 Skill、加载 manifest、校验 schema、按项目启用或禁用 Skill、向 Context System 暴露可用 Skill 列表、向 Agent Runtime Adapter 暴露工具定义。

## Skill Manifest

```ts
export interface SkillManifest {
  name: string
  version: string
  description: string
  category:
    | "filesystem"
    | "shell"
    | "git"
    | "github"
    | "browser"
    | "repo-scanner"
    | "test-runner"
    | "database"
    | "delivery"
    | "custom"
  tools: SkillToolManifest[]
  defaultEnabled: boolean
  requiresNetwork: boolean
  requiresFilesystem: boolean
  riskLevel: "low" | "medium" | "high"
  permissions: SkillPermission[]
}
```

```ts
export interface SkillToolManifest {
  name: string
  description: string
  inputSchema: unknown
  outputSchema: unknown
  riskLevel: "low" | "medium" | "high"
  requiresApproval: boolean
  timeoutMs: number
}
```

项目 Skill 配置位于 `.project/state/manifest.json`：

```ts
export interface ProjectSkillConfig {
  enabled: string[]
  disabled: string[]
  overrides: Record<string, SkillPolicyOverride>
}
```

---

# 7. Skill Contract

```ts
export interface Skill {
  manifest: SkillManifest
  execute(input: SkillExecutionInput): Promise<SkillExecutionResult>
}

export interface SkillExecutionInput {
  projectId: string
  taskId: string
  runId: string
  sessionId?: string
  skillName: string
  toolName: string
  workspacePath: string
  args: unknown
  policy: RuntimePolicy
  context: SkillExecutionContext
}

export interface SkillExecutionContext {
  currentBranch?: string
  currentTaskPath?: string
  contextPackId?: string
  checkpointId?: string
  env: Record<string, string>
  cwd: string
  requestApproval: ApprovalRequestFn
  emitEvent: EventEmitFn
  redact: RedactionFn
}

export interface SkillExecutionResult {
  skillName: string
  toolName: string
  status: "success" | "failed" | "blocked" | "requires-approval"
  output?: unknown
  summary: string
  riskLevel: "low" | "medium" | "high"
  approvalId?: string
  startedAt: string
  endedAt: string
  durationMs: number
  error?: { code: string; message: string; recoverable: boolean }
  artifacts?: SkillArtifact[]
}

export interface SkillArtifact {
  type: "file" | "diff" | "report" | "log" | "test-output" | "build-output" | "pr" | "release"
  path?: string
  contentType?: string
  summary: string
}
```

---

# 8. Risk Model

```text
low
  只读操作，低风险。

medium
  写入项目文件、运行普通命令、修改任务状态。

high
  删除文件、部署、推送、数据库迁移、修改安全规则、修改 AGENTS.md。
```

Low risk examples：`read_file`、`list_dir`、`git_status`、`git_diff`、`scan_files`、`detect_test_commands`、`read_report`。

Medium risk examples：`write_file`、`edit_file`、`run_test`、`run_build`、`git_commit`、`create_task_report`、`create_context_snapshot`。

High risk examples：`delete_file`、`modify_AGENTS_md`、`git_reset_hard`、`git_clean`、`push_main`、`force_push`、`deploy`、`database_migration`、`modify_accepted_ADR`、`change_security_policy`。

---

# 9. Approval Rules

## Always Requires Approval

```text
删除文件
修改 AGENTS.md
修改 accepted ADR
修改 project manifest 核心字段
新增重大依赖
数据库迁移
部署
push main
force push
git reset --hard
git clean -fd
执行 sudo
执行 curl | sh
执行 wget | sh
访问 workspace 外路径
读取敏感环境变量
修改安全策略
启用未授权网络访问
```

## Auto Allowed

```text
读取 workspace 内文件
列出目录
搜索文本
读取 git status
读取 git diff
运行已声明测试命令
运行已声明 lint 命令
运行已声明 typecheck 命令
写入 .project/reports/
写入 .project/context/
写入 .project/tasks/active/
创建 checkpoint
```

```ts
export interface ApprovalRequest {
  id: string
  projectId: string
  taskId: string
  runId: string
  skillName: string
  toolName: string
  action: string
  riskLevel: "medium" | "high"
  reason: string
  argsSummary: string
  affectedPaths: string[]
  status: "pending" | "approved" | "denied"
  requestedAt: string
  resolvedAt?: string
}
```

---

# 10. Skill Execution Flow

```text
1. Codex requests tool call
2. Agent Runtime Adapter receives tool call
3. Skill Runtime resolves skill and tool
4. Skill Runtime validates input schema
5. Permission Manager checks project policy
6. Risk Model classifies operation
7. Approval Gate blocks if required
8. Skill Execution Engine executes tool
9. Secret Redactor sanitizes output
10. Result Normalizer formats result
11. Event Logger records execution
12. Result returns to Codex
```

---

# 11. Filesystem Skill

Purpose：项目文件读写。

Tools：`read_file`、`read_many_files`、`list_dir`、`glob`、`search_text`、`write_file`、`edit_file`、`move_file`、`delete_file`、`create_dir`。

Rules：所有路径必须限制在 workspace 内；默认禁止访问 workspace 外路径；读取大文件必须支持 excerpt；写文件必须记录 diff；删除文件必须审批；修改 AGENTS.md 必须审批；修改 `.project/decisions/accepted` 必须审批。

```ts
export interface ReadFileInput { path: string; startLine?: number; endLine?: number }
export interface WriteFileInput { path: string; content: string; createIfMissing: boolean }
export interface EditFileInput { path: string; edits: { oldText: string; newText: string }[] }
```

输出必须包含 affected path、operation、success/failure、diff summary if changed、error if failed。

---

# 12. Shell Skill

Purpose：执行受控命令。

Tools：`run_command`、`run_declared_command`、`run_install`、`run_build`、`run_lint`、`run_typecheck`、`run_test`、`run_e2e`。

Rules：默认 cwd = workspace root；所有命令必须 timeout；所有命令必须记录 stdout/stderr；危险命令必须审批；禁止默认执行 sudo、curl | sh、wget | sh；禁止打印 secret；命令结果必须进入 Observability。

Dangerous Commands：`rm -rf`、`sudo`、`chmod -R`、`chown -R`、`git reset --hard`、`git clean -fd`、`git push --force`、`curl | sh`、`wget | sh`、`docker system prune`、`kubectl delete`、`terraform apply`、`terraform destroy`。

```ts
export interface ShellCommandResult {
  command: string
  cwd: string
  exitCode: number
  stdout: string
  stderr: string
  durationMs: number
  timedOut: boolean
}
```

---

# 13. Git Skill

Purpose：Git 状态、diff、提交和恢复。

Tools：`git_status`、`git_branch`、`git_diff`、`git_diff_stat`、`git_log`、`git_add`、`git_commit`、`git_restore`、`git_revert`、`git_checkout`、`git_create_branch`、`git_push`。

Rules：任何任务开始前必须允许读取 git status；任何编辑前必须读取 git status；不得覆盖用户未提交修改；git commit 前必须有 verification result；push main 必须审批；force push 禁止或必须最高级审批；git reset --hard 必须审批；git clean -fd 必须审批。

```ts
export interface GitStatusOutput {
  branch: string
  statusShort: string
  changedFiles: string[]
  untrackedFiles: string[]
  hasUserChanges: boolean
}
```

---

# 14. GitHub Skill

Purpose：issue、PR、review、release 等远端协作能力。

Tools：`list_issues`、`read_issue`、`create_issue`、`comment_issue`、`create_pr`、`update_pr`、`comment_pr`、`request_review`、`read_pr`、`create_release`。

Rules：创建 PR 前必须有 run report 和 verification result；创建或修改 release 必须审批；关闭 issue 必须记录原因；向远端写入必须记录 delivery report。

PR Body 必须包含：Task、Summary、Changed Files、Verification、Decisions、Risks、Follow-up、Run Report。

---

# 15. Browser Skill

Purpose：读取外部网页、官方文档、issue 页面。

Tools：`fetch_url`、`read_page`、`search_docs`、`summarize_page`、`extract_links`。

Rules：默认只读；外部访问必须记录来源；优先官方文档；不得把网页内容直接写成项目长期事实；需要 Codex 总结后进入 report；访问需要认证的页面必须审批；不得提交敏感数据到外部网站。

---

# 16. Repo Scanner Skill

Purpose：仓库结构、依赖、符号、测试命令发现。

Tools：`scan_files`、`scan_directories`、`scan_dependencies`、`scan_symbols`、`build_repository_map`、`detect_package_manager`、`detect_commands`、`detect_test_files`、`find_related_files`。

Implementation Basis：ripgrep、tree-sitter、package manifest parser、lockfile parser、language-specific scanners。

```ts
export interface RepositoryMap {
  rootPath: string
  sourceDirs: string[]
  testDirs: string[]
  docDirs: string[]
  configFiles: string[]
  packageFiles: string[]
  entrypoints: string[]
  majorModules: string[]
  commands: { install?: string; dev?: string; build?: string; lint?: string; typecheck?: string; test?: string; e2e?: string }
}
```

---

# 17. Test Runner Skill

Purpose：执行验证命令，可以复用 Shell Skill，但必须以验证语义输出结果。

Tools：`run_lint`、`run_typecheck`、`run_unit_tests`、`run_integration_tests`、`run_e2e_tests`、`run_build`、`run_verification_pipeline`。

Rules：优先使用 AGENTS.md 声明命令；其次使用 manifest.json；最后从 package 文件推断；不能凭空编造测试命令；测试失败必须保留 stdout/stderr 摘要；验证结果必须写入 `.project/reports/verification/`。

```ts
export interface VerificationResult {
  runId: string
  taskId: string
  status: "passed" | "failed" | "partial" | "skipped"
  commands: { name: string; command: string; exitCode: number; summary: string }[]
  risks: string[]
  reportPath: string
}
```

---

# 18. Database Skill

Purpose：数据库连接、查询、迁移检查和只读诊断。

Tools：`connect`、`inspect_schema`、`run_readonly_query`、`run_migration_check`、`run_migration`、`backup_database`、`restore_database`。

Rules：默认只读；写操作、migration、restore 必须审批；不得打印 secrets；不得把连接字符串写入报告；生产数据库访问必须最高风险级别。

---

# 19. Delivery Skill

Purpose：交付产物生成和发布动作。

Tools：`generate_commit_message`、`create_commit`、`generate_pr_body`、`create_pr`、`generate_release_notes`、`create_release`、`deploy`、`rollback_deploy`。

Rules：commit 前必须有 verification result；PR 前必须有 run report；release、deploy、rollback deploy 必须审批；所有交付动作必须写 delivery report。

---

# 20. Skill Events

Event Types：`skill.called`、`skill.approval_required`、`skill.approval_granted`、`skill.approval_denied`、`skill.completed`、`skill.failed`、`skill.blocked`。

```ts
export interface SkillEvent {
  eventId: string
  projectId: string
  taskId: string
  runId: string
  skillName: string
  toolName: string
  type: string
  timestamp: string
  inputSummary: string
  outputSummary?: string
  riskLevel: "low" | "medium" | "high"
  approvalId?: string
  durationMs?: number
  error?: string
}
```

---

# 21. Secret Redaction

Skill Runtime 必须对输入、输出、日志、报告进行脱敏。

Secret Patterns：API keys、tokens、passwords、private keys、.env values、database URLs、cloud credentials、SSH keys、OAuth tokens。

统一替换为：`[REDACTED]`。

---

# 22. Timeout and Cancellation

Default Timeout：read/list/search 30s；test/build/lint/typecheck 10m；install 15m；browser fetch 60s；database query 60s；deploy 根据 project policy。

当 run 被暂停或取消：正在执行的 Skill 必须尝试终止，记录 cancellation event，保留 stdout/stderr 摘要，保存 checkpoint。

---

# 23. Context Pack Integration

Context Pack 必须声明当前 run 可用 Skills。

```ts
export interface ContextSkillEntry {
  name: string
  category: string
  description: string
  tools: { name: string; description: string; riskLevel: "low" | "medium" | "high"; requiresApproval: boolean }[]
}
```

Codex 不能调用未出现在 Context Pack 中的 Skill。

---

# 24. Project Policy Integration

Skill Runtime 必须读取 AGENTS.md、`.project/state/manifest.json`、`.project/state/project.json`、Harness global policy、User current instruction。

优先级：用户当前明确指令、Harness global safety policy、AGENTS.md、project manifest、skill default policy。

---

# 25. Error Handling

Tool Not Found：返回 failed，记录 skill.failed，提示当前 Context Pack 中未声明该 Skill。

Permission Denied：返回 blocked，记录 skill.blocked，说明需要审批或策略禁止。

Timeout：终止执行，返回 failed，记录 stdout/stderr 摘要，标记 recoverable。

Invalid Input：返回 failed，记录 schema validation error，不执行工具。

---

# 26. Implementation Checklist

P0：Skill interface、Skill manifest schema、Skill registry、Skill execution engine、Approval check、Event logging、Secret redaction、Filesystem skill、Shell skill、Git skill、Repo Scanner skill、Context Pack skill declaration。

P1：GitHub skill、Test Runner skill、Delivery skill、Browser skill、Timeout manager、Cancellation、Skill policy overrides、Skill execution reports。

P2：Database skill、Advanced repository symbol index、Replay UI、Skill sandboxing、Remote skill registry、Project-specific custom skills。

---

# 27. Acceptance Criteria

```text
1. 每个 Skill 必须有 manifest
2. 每个 Tool 必须有 input/output schema
3. Codex 只能调用 Context Pack 声明的 Skills
4. 每次 Skill 调用必须记录 event
5. 高风险调用必须进入 Approval Gate
6. Filesystem Skill 必须限制 workspace
7. Shell Skill 必须支持 timeout
8. Shell Skill 必须拦截危险命令
9. Git Skill 必须支持 status/diff
10. Repo Scanner Skill 必须生成 repository map
11. Test Runner Skill 必须写 verification report
12. Secret 必须 redacted
13. Skill 失败必须返回 recoverable 信息
14. Skill 调用必须可用于 replay
15. Skill 不能自行推理或规划
```

---

# 28. Final Definition

```text
MCP Skills
=
Codex 在项目工作区内可调用的、受 Harness 治理的确定性工程工具能力层。
```

边界：Codex 负责思考；Skill 负责执行；Harness 负责治理；Git 负责事实；Context Pack 负责声明可用能力。
