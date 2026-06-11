# Harness OS Governance and Security Specification

Version: 1.0  
System: Harness OS  
Primary Agent: Codex  
Principle: Governed execution, explicit approval, secure-by-default project operations

---

# 1. 模块定位

Governance and Security 是 Harness OS 的安全与治理核心。它确保 Codex 在真实项目中执行任务时可控、可审计、可恢复、可审批、不越权、不泄密、不破坏项目、不绕过项目规则。

Harness OS 不假设 Codex 永远不会犯错。Harness OS 必须通过确定性策略、权限检查、审批门、审计日志、路径限制、命令限制、Secret 脱敏和状态记录，约束 Codex 的所有高风险行为。

最终定义：Codex 负责执行；Skills 负责工具能力；Governance 负责边界；Security 负责防护；Observability 负责审计；Git 负责事实和恢复。

---

# 2. 设计目标

```text
1. 定义项目级安全边界
2. 定义 Skill 调用权限
3. 定义高风险操作审批规则
4. 定义文件路径保护规则
5. 定义 Shell 命令风险规则
6. 定义 Git 操作安全规则
7. 定义 Secret 检测与脱敏规则
8. 定义网络访问策略
9. 定义交付和部署审批规则
10. 定义事件审计和追踪规则
11. 定义策略优先级
12. 定义失败、拒绝、冲突时的处理方式
```

---

# 3. 非目标

不做多 Agent 管理、模型路由、复杂 IAM 平台、企业级 SSO、外部安全扫描平台、完整 SIEM 系统、云权限编排、自动安全审计替代人工审查。

---

# 4. 核心原则

Secure by Default：无法判断安全时阻止执行、请求审批、记录原因，不能默认放行。

Least Privilege：Codex 和 Skills 只能获得当前任务所需的最小权限。默认允许读取项目文件、搜索项目文件、读取 git status/diff、运行已声明测试命令、写入任务报告和上下文快照；默认不允许删除文件、修改 AGENTS.md、修改 accepted ADR、推送 main、部署、读取 secrets、访问 workspace 外路径、执行危险 shell 命令、修改安全策略。

Explicit Approval：所有高风险行为必须明确审批，记录谁请求、请求什么、为什么需要、影响路径、风险等级、审批结果和审批时间。

Project-Scoped Execution：默认限制在项目 workspace 内，禁止默认访问用户主目录、系统目录、其他项目目录、SSH keys、.env secrets、云凭据、浏览器缓存、操作系统敏感路径。

Git as Recovery Boundary：高风险修改前必须读取 git status、检测未提交修改、必要时创建 checkpoint、记录 changed files 和 diff summary。

Observable by Default：policy.checked、policy.allowed、policy.denied、approval.requested、approval.granted、approval.denied、secret.redacted、command.blocked、path.blocked、security.violation 必须进入 Observability System。

---

# 5. Governance 总架构

```text
Governance System
│
├── Policy Engine
├── Permission Manager
├── Approval Gate
├── Protected Path Manager
├── Command Risk Classifier
├── Git Safety Guard
├── Secret Redactor
├── Network Policy Manager
├── Delivery Guard
├── Audit Logger
└── Violation Handler
```

---

# 6. Policy Sources

优先级：

```text
1. 用户当前明确指令
2. Harness Global Safety Policy
3. AGENTS.md
4. .project/state/manifest.json
5. .project/decisions/accepted ADR
6. Skill default policy
7. Harness default policy
```

用户当前明确指令可以收紧权限，但不能绕过 Harness Global Safety Policy。AGENTS.md 是项目级协议。Accepted ADR 是长期项目约束。Skill default policy 是最低层默认行为。

---

# 7. Policy Engine

Policy Engine 负责判断 operation、skill name、tool name、project id、task id、run id、affected paths、command、risk level、current policy context 是否允许。

输出：allowed、denied、requires approval。

```ts
export interface PolicyDecision {
  decision: "allow" | "deny" | "requires-approval"
  reason: string
  riskLevel: "low" | "medium" | "high"
  policySource: "user-instruction" | "global-policy" | "agents-md" | "manifest" | "decision" | "skill-default" | "harness-default"
  affectedPaths: string[]
  requiredApproval?: ApprovalRequirement
}
```

Policy Check Flow：收集操作上下文，读取 policy sources，标准化操作类型，判断路径、命令、Git、Secret、网络、交付风险，输出 PolicyDecision，记录 policy.checked event。

---

# 8. Risk Levels

Low Risk：read_file、list_dir、search_text、git_status、git_diff、git_log、scan_files、read_context、read_task、read_report。

Medium Risk：write_file、edit_file、run_test、run_build、git_add、git_commit、write_task_report、write_context_snapshot、create_checkpoint。

High Risk：delete_file、modify_AGENTS_md、modify_accepted_ADR、modify_project_manifest_core_fields、add_major_dependency、database_migration、deploy、push_main、force_push、git_reset_hard、git_clean_fd、run_sudo、curl_pipe_shell、wget_pipe_shell、access_workspace_outside、read_sensitive_env、change_security_policy、introduce_multi_agent、introduce_model_router、introduce_external_memory_or_vector_system。

---

# 9. Approval Gate

Always Requires Approval：修改 AGENTS.md、修改 accepted ADR、修改 project manifest 核心字段、删除文件、删除测试、新增重大依赖、修改架构规则、修改安全策略、数据库迁移、访问生产数据库、部署、回滚部署、push main、force push、git reset --hard、git clean -fd、执行 sudo、执行 curl | sh、执行 wget | sh、访问 workspace 外路径、读取敏感环境变量、启用未授权网络访问、引入 multi-agent 架构、引入 model router、引入外部 memory/vector 系统。

Auto Allowed：读取 workspace 内文件、列出目录、搜索文本、读取 git status/diff/log、运行 AGENTS.md 声明的测试命令、运行 manifest 声明的 lint/typecheck/build 命令、写入 `.project/tasks/active/`、`.project/reports/`、`.project/context/`、创建 checkpoint、生成 run report、生成 verification report。

```ts
export interface ApprovalRequest {
  id: string
  projectId: string
  taskId: string
  runId: string
  requester: "codex" | "skill" | "harness"
  action: string
  reason: string
  riskLevel: "medium" | "high"
  affectedPaths: string[]
  command?: string
  policyDecision: PolicyDecision
  status: "pending" | "approved" | "denied" | "expired"
  requestedAt: string
  resolvedAt?: string
  resolvedBy?: string
  resolutionNote?: string
}
```

Approval Flow：请求操作，Policy Engine 返回 requires-approval，Approval Gate 创建请求，Observability 记录，CLI/UI 展示，用户 approve/deny，记录结果，approved 继续，denied 阻止并返回 blocked。

---

# 10. Protected Path Policy

Protected Files：AGENTS.md、`.project/state/manifest.json`、`.project/state/project.md`、`.project/decisions/*.md`、`.project/decisions/*.json`、`.project/tasks/completed/*`、`.project/tasks/failed/*`、`.env`、`.env.*`、`*.pem`、`*.key`、`id_rsa`、`id_ed25519`。

Protected Directories：`.git/`、`.ssh/`、`.project/decisions/`、`.project/state/`、`node_modules/`、`vendor/`、`dist/`、`build/`、`coverage/`。

Workspace Boundary：target path starts with workspace root；resolved path is not outside workspace root；symlink cannot escape workspace。必须防止 `../` escape、absolute path escape、symlink escape。

---

# 11. Shell Command Security

Dangerous Commands：`rm -rf`、`sudo`、`chmod -R`、`chown -R`、`git reset --hard`、`git clean -fd`、`git push --force`、`curl | sh`、`wget | sh`、`docker system prune`、`kubectl delete`、`terraform apply`、`terraform destroy`、`npm publish`、`pnpm publish`、`yarn publish`。

Shell Rules：所有命令必须设置 cwd = workspace root、timeout、记录 command/stdout/stderr 摘要、脱敏输出、记录 exit code、duration、进入 event log。禁止默认 sudo、pipe installer、读取 secrets、执行 workspace 外脚本、持久修改系统环境。

```ts
export interface CommandRiskResult {
  command: string
  riskLevel: "low" | "medium" | "high"
  allowed: boolean
  requiresApproval: boolean
  reasons: string[]
}
```

---

# 12. Git Safety Guard

任务开始前必须执行 `git status --short` 和 `git branch --show-current`。涉及代码修改时必须读取 `git diff --stat` 和 `git diff`。

如果存在未提交修改：Codex 不得覆盖用户修改，Context Pack 必须标记 hasUserChanges，修改前必须确认相关文件是否由当前任务产生，高风险修改前必须 checkpoint。

受限 Git 操作：`git reset --hard`、`git clean -fd`、`git push origin main`、`git push --force`、`git rebase`、`git cherry-pick` 到 protected branch、`git tag release` 必须审批。

默认允许：git status、git diff、git log、git branch --show-current。

---

# 13. Secret Security

Secret Types：API keys、tokens、passwords、private keys、SSH keys、OAuth tokens、database URLs、cloud credentials、.env values、JWT tokens、session cookies。

Redaction Rule：统一替换为 `[REDACTED]`。不得把 secret 写入 Context Pack、Run Report、Task Report、Verification Report、Event Log、PR Body、Commit Message。

Secret Access：读取 `.env`、`.env.*`、`*.pem`、`*.key`、`id_rsa`、`id_ed25519`、`credentials.json`、`service-account.json` 必须审批或默认拒绝。确需环境变量时只允许读取变量是否存在，不允许输出值。

---

# 14. Network Security

默认网络策略：Browser Skill 只读；外部访问必须记录 URL；优先官方文档；不向外部提交项目代码或 secrets；认证页面访问需审批；未知下载脚本需审批。

禁止默认执行：curl | sh、wget | sh、下载并执行未知二进制、上传项目源码到未知服务、发送 secrets 到外部 endpoint、访问未授权私有资源。

---

# 15. Dependency Security

新增依赖必须记录 dependency name、version、purpose、why needed、risk、alternative considered。重大依赖必须审批。

Major Dependency Examples：runtime framework、database client、ORM、auth library、cloud SDK、deployment SDK、agent framework、workflow engine、vector database client、model router。

不得无审批切换 package manager，例如 pnpm -> npm、npm -> yarn、pip -> poetry、poetry -> uv。

---

# 16. Architecture Governance

以下架构变化必须生成或更新 ADR，并需要审批：引入 multi-agent、model router、外部 memory repo、vector database、workflow DAG、改变状态存储、Context System 规则、Task Manager 生命周期、Decision Manager 生命周期、权限模型、交付流程、部署方式。

Codex 可以创建 proposed ADR，但不得自动接受重大 ADR。

---

# 17. Delivery Security

Commit 前必须有 git diff、task summary、verification result、risk summary。Codex 不得自动 commit，除非用户或项目策略允许。

PR 前必须有 run report、verification report、changed files list、risk notes、related decisions。

Release 必须审批，且通过验证、生成 release notes、记录 changelog、确认版本号、确认目标分支。

Deploy 必须审批，且通过 verification、确认环境、确认 rollback path、生成 delivery report、记录 deployment event。

---

# 18. Audit and Observability

事件类型：policy.checked、policy.allowed、policy.denied、approval.requested、approval.granted、approval.denied、path.blocked、command.blocked、secret.redacted、network.accessed、dependency.added、architecture.change.proposed、security.violation、delivery.blocked。

```ts
export interface GovernanceEvent {
  eventId: string
  projectId: string
  taskId?: string
  runId?: string
  type: string
  timestamp: string
  actor: "codex" | "skill" | "harness" | "user"
  action: string
  decision?: "allow" | "deny" | "requires-approval"
  riskLevel?: "low" | "medium" | "high"
  affectedPaths?: string[]
  summary: string
}
```

---

# 19. Violation Handling

Violation Types：policy_violation、path_violation、command_violation、secret_violation、network_violation、git_violation、delivery_violation、architecture_violation。

发现违规时立即阻止操作，返回 blocked，记录 violation event，写入 run report，提供修复建议，必要时创建 checkpoint。

---

# 20. Governance Integration with Context Pack

Context Pack 必须包含 approval rules、protected paths、dangerous commands、available skills、disallowed actions、secret rules、network rules、delivery rules。

---

# 21. Governance Integration with Skills

所有 Skill 调用必须经过 Policy Engine、Permission Manager、Approval Gate、Secret Redactor、Event Logger。Skill 不得绕过 Governance System。

---

# 22. Governance Integration with Project Manager

Project Manager 必须保护 AGENTS.md、`.project/state/manifest.json`、`.project/state/project.md`、`.project/decisions/`。创建项目时写入默认安全策略，打开项目时校验安全相关结构。

---

# 23. Governance Integration with Task Manager

Task Manager 必须在任务记录中保存 approval events、blocked events、security notes、risk notes、verification status。任务完成前必须输出风险摘要。

---

# 24. Governance Integration with Decision Manager

accepted ADR 不能无审批修改；重大架构决策必须审批；supersede accepted ADR 必须审批；rejected ADR 不进入 active constraints。

---

# 25. Governance Integration with Delivery System

Delivery System 必须确保 commit 前检查 verification，PR 前检查 run report，release/deploy/rollback 前请求审批。

---

# 26. Configuration

Global Policy Config：`~/.harness/policy.json`。

```json
{
  "defaultNetwork": "restricted",
  "allowWorkspaceOutsideAccess": false,
  "requireApprovalForDeploy": true,
  "requireApprovalForPushMain": true,
  "requireApprovalForDependencyAdd": true,
  "redactSecrets": true
}
```

Project Policy Config：`.project/state/manifest.json`。

```json
{
  "policy": {
    "protectedBranches": ["main", "master"],
    "allowAutoCommit": false,
    "allowAutoPush": false,
    "allowDeploy": false,
    "network": "restricted",
    "secretRedaction": true
  }
}
```

---

# 27. Implementation Checklist

P0：Policy Engine、Approval Gate、Protected Path Manager、Command Risk Classifier、Secret Redactor、Skill permission checks、Governance events、Context Pack governance summary、Git safety checks。

P1：Network policy manager、Dependency risk policy、Delivery guard、Project policy config、Global policy config、Violation reports、Approval CLI/UI。

P2：Policy packs、Team approval workflow、Remote approval service、Advanced secret detection、External security scanner integration、Audit dashboard。

---

# 28. Acceptance Criteria

```text
1. 所有 Skill 调用必须经过 Policy Engine
2. 高风险操作必须审批
3. 修改 AGENTS.md 必须审批
4. 修改 accepted ADR 必须审批
5. 删除文件必须审批
6. push main 必须审批
7. deploy 必须审批
8. Shell 命令必须支持风险分类
9. 危险命令必须阻止或审批
10. 文件操作必须限制在 workspace 内
11. symlink escape 必须被阻止
12. secrets 必须 redacted
13. .env 不得进入 Context Pack
14. governance events 必须进入 Observability
15. violation 必须阻止执行并写入报告
16. Context Pack 必须包含治理摘要
17. Codex 不能绕过 Skill 权限调用工具
18. 架构变更必须进入 Decision Manager
19. 重大依赖新增必须审批
20. 任务完成前必须输出风险摘要
```

---

# 29. Final Definition

```text
Governance and Security
=
把 Codex 的项目执行限制在明确、可审计、可审批、可恢复的工程边界内。
```

边界关系：Codex 负责执行；Skills 负责工具；Governance 负责权限；Security 负责保护；Observability 负责审计；Decision Manager 负责长期约束；Git 负责恢复。
