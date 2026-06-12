# AUD-P0-001 修复报告 — Governance Skill Policy 整合

> **来源**: `Harness-OS-P0-Fix-Requirements/01_GOVERNANCE_SKILL_POLICY_FIX.md`
> **提交**: `76a627a`
> **状态**: ✅ 已修复并提交（未 push）
> **日期**: 2026-06-12

---

## 一、问题概述

Skill Registry 的 `execute()` 方法在执行技能工具前**未经过 Policy Engine 治理**，存在以下安全缺口：

1. `execute()` 只检查 manifest 中的 `requiresApproval` 标记，未调用 `checkPolicy()`
2. 危险 shell 命令（如 `rm -rf`）直接到达 executor，无策略拦截
3. 敏感文件写入（credentials、.env）无策略拦截
4. `getExecutor()` 公开暴露，可直接绕过 execute() 调用 executor
5. 未知工具、策略异常时无 fail closed 机制
6. 缺少 approval 提交流程，`needs_approval` 被降级为普通 `blocked`

---

## 二、关键修正节点

### GOV-01-A: Policy Engine 接入 execute() 入口

**文件**: `src/skills/registry.ts`

在 `execute()` 中调用 executor 之前，增加三层治理门：

```
execute(skill, tool, input, context)
  ├─ ═══ Layer 1: Executor 存在性检查 ═══
  │    无 executor → failedResult
  ├─ ═══ Layer 2: Manifest 校验 ═══
  │    工具不在 manifest.tools[] 中 → blockedResult
  ├─ ═══ Layer 3: Policy Gate ═══
  │    ├─ checkPolicy() → deny → blockedResult
  │    ├─ checkPolicy() → needs_approval → submitApproval + requiresApprovalResult
  │    └─ checkPolicy() → allow → 继续
  │    └─ 策略异常 → blockedResult (fail closed)
  └─ ═══ Executor 执行 ═══
        executor(toolName, input, context)
```

### GOV-01-B: Action 名称规范化

**文件**: `src/skills/registry.ts` — `normalizeSkillAction()`

将 skill 工具名称映射为 Policy Engine 可识别的动作分类：

| Skill | Tool | 规范化 Action |
|-------|------|--------------|
| filesystem | read_file, list_dir, search_text | `Read` |
| filesystem | write_file, create_dir | `Write` |
| filesystem | delete_file | `Delete` |
| shell | run_command, run_test, run_build | `Bash` |
| git | git_status, git_diff, git_log | `GitRead` |
| git | git_commit | `GitCommit` |
| git | git_push | `GitPush` |
| repo-scanner | 全部 | `Read` |
| 未知 skill/tool | — | `{skill}:{tool}` → 无规则匹配 → `needs_approval` |

### GOV-01-C: PolicyContext 构建

**文件**: `src/skills/registry.ts` — `buildSkillPolicyContext()`

从工具输入中提取策略上下文：

- `toolName`：原始工具名
- `skillName`：所属 skill
- `command`：从 `input.command` 提取（shell 工具）
- `affectedPaths`：从 `input.path` / `file_path` / `filePath` 提取

### GOV-01-D: PolicyContext.skillName 字段

**文件**: `src/governance/policy.ts`

在 `PolicyContext` 接口中增加 `skillName?: string` 字段，使策略规则可感知调用来源 skill。

### GOV-01-E: 默认策略规则扩展

**文件**: `src/governance/policy.ts` — `DEFAULT_RULES`

新增 6 条规则（按优先级排序）：

| 规则 | 匹配 Action | 决策 | 用途 |
|------|-----------|------|------|
| `write-default-allow` | `Write` | allow | 非敏感文件写入默认允许 |
| `bash-default-allow` | `Bash` | allow | 安全 shell 命令默认允许 |
| `git-read-allow` | `GitRead` | allow | Git 读操作允许 |
| `git-commit-allow` | `GitCommit` | allow | Git 提交允许 |
| `git-push-deny` | `GitPush` | deny | Git 推送默认拒绝 |
| `delete-default-deny` | `Delete` | deny | 删除操作默认拒绝 |

这些规则放在 credential-write / high-risk-bash / protected-paths 等高优先级规则之后，确保敏感操作先被拦截，非敏感操作正常放行。

### GOV-01-F: requiresApprovalResult() helper

**文件**: `src/skills/executor.ts`

新增 `requiresApprovalResult()` 函数，生成 `requires-approval` 状态的结果，包含 `approvalId` 供后续审批流程使用。

### GOV-01-G: getExecutor() 治理说明

**文件**: `src/skills/registry.ts`

`getExecutor()` 保留但标记为治理绕过路径，JSDoc 中明确说明：
> "bypasses governance — use execute() for production paths"

---

## 三、涉及模块变更

| 模块 | 文件 | 变更类型 |
|------|------|---------|
| Skills | `src/skills/registry.ts` | **核心** — execute() 政策门+Action映射+Context构建 |
| Skills | `src/skills/executor.ts` | 新增 requiresApprovalResult() |
| Governance | `src/governance/policy.ts` | PolicyContext 扩展 + 6 条新默认规则 |
| Tests | `tests/unit/skills.test.ts` | 12 条回归测试 + 1 条现有测试更新 |

---

## 四、新增回归测试

在 `tests/unit/skills.test.ts` 中新增 `GOV-01: registry.execute() policy integration` 测试块，覆盖 12 个场景：

| # | 测试 | 验证路径 | 期望状态 |
|---|------|---------|---------|
| 1 | 允许只读文件操作 | Read → allow | `success` |
| 2 | 允许安全写入 | Write(非敏感) → allow | `success` |
| 3 | 允许安全 shell | Bash(安全命令) → allow | `success` |
| 4 | 阻止凭证文件写入 | Write(credentials.json) → deny | `blocked` |
| 5 | 阻止 token 文件写入 | Write(token.json) → deny | `blocked` |
| 6 | 阻止删除操作 | Delete → deny | `blocked` |
| 7 | .env 写入需审批 | Write(.env) → needs_approval | `requires-approval` + approvalId |
| 8 | 危险 shell 需审批 | Bash(rm -rf) → needs_approval | `requires-approval` + approvalId |
| 9 | 未知工具被阻止 | Manifest 校验 | `blocked` |
| 10 | 未知 skill 失败 | 无 executor | `failed` |
| 11 | 策略上下文含 skillName | 间接验证 | `success` |
| 12 | getExecutor 仍可用 | 文档化绕过 | 函数存在 |

---

## 五、测试结果

```
Test Files  19 passed (19)
     Tests  440 passed (440)
            ├── 428 现存测试（零回归）
            └── 12 新增 GOV-01 回归测试
```

TypeScript 编译：**零错误**

---

## 六、剩余待修复问题

本文件 `01_GOVERNANCE_SKILL_POLICY_FIX.md` 中还有 GOV-02 至 GOV-07 未修复：

| 编号 | 模块 | 描述 | 优先级 |
|------|------|------|--------|
| GOV-02 | approval-gate | Approval Gate 接线（needs_approval → pending → resolve） | P0 |
| GOV-03 | filesystem | 路径边界校验（symlink escape、Windows 盘符、.. 逃逸） | P0 |
| GOV-04 | filesystem | 保护文件与不可变文档（.env、credentials、ADR） | P0 |
| GOV-05 | shell | Shell 命令治理增强（编码绕过、大小写、control operator） | P0 |
| GOV-06 | git | Git 操作治理（分支检查、staged 内容、force push） | P0 |
| GOV-07 | policy | 故障 fail closed 强化（timeout、非法值） | P0 |

还有 5 个其他 P0 待修复文件：

| 文件 | 编号 | 概述 |
|------|------|------|
| `02_CONFIG_SAFETY_LOCK_FIX.md` | AUD-P0-002 | 安全配置锁 + Immutable 策略 |
| `03_SECRET_REDACTION_FIX.md` | AUD-P0-003 | Secret Redactor 全链路修复 |
| `04_VERIFICATION_DELIVERY_FIX.md` | AUD-P0-004 | Verification 与 Delivery 强绑定 |
| `05_CLI_JSON_CONTRACT_FIX.md` | AUD-P0-005 | CLI JSON 输出契约 |
| `06_RC_EVIDENCE_BUILD_VERSION_FIX.md` | AUD-P0-006 | 构建、版本与执行证据 |

每个修复将按相同工作流执行：读需求 → 分析代码 → 实现修正 → 补回归测试 → 全量跑测 → 提交（不 push）。

---

## 七、修复清单

- [x] `registry.execute()` 调用 `checkPolicy()` 前置于 executor
- [x] Policy Context 含规范化 tool、command、affected paths、skill name
- [x] `deny` → blockedResult，executor 不被调用
- [x] `needs_approval` → submitApproval + requiresApprovalResult（含 approvalId）
- [x] 策略异常 → blockedResult（fail closed）
- [x] 未知工具 manifest 校验 → blocked
- [x] `getExecutor()` 保留但标注为治理绕过
- [x] 新增 12 条回归测试覆盖全部路径
- [x] 全量 440 测试通过

---

*生成日期: 2026-06-12 19:23 UTC*
