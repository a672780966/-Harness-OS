# Harness OS Project Execution Plan

Version: 1.0  
Phase: Dogfood + Source Audit  
Status: Thin Harness Finalization  
Principle: Stop expanding documents; validate the system through real usage and source-level audit

---

# 1. 文档定位

本文件定义 Harness OS 在 Thin Harness 基本完成后的执行阶段计划。

当前阶段不再继续扩展架构文档。

当前阶段目标是：

```text
1. 用 Harness OS 真实运行 Harness OS 自己的仓库
2. 审计源码是否符合 19 份设计文档中的核心不变量
3. 找出 Thin Harness 的真实缺口
4. 修复阻塞可用性的 P0/P1 问题
5. 形成可交付的 Thin Harness Release Candidate
```

---

# 2. 当前项目状态

当前 Harness OS 已具备：

```text
CLI 主命令
Project Manager
AGENTS.md 校验
Task Manager
Context Engineering
Governance 基础层
Verification Pipeline
Observability
Delivery Pipeline
State & Recovery
Skill Executors
CLI 输出契约
Config 系统
Decision Manager / ADR 生命周期
模块串联全链路
```

当前测试状态：

```text
428 tests passed
19 test files
0 failures
0 type errors
```

当前未展开：

```text
Thick Harness
GitHub Skill
Browser Skill
Database Skill
Replay
多项目注册
archive / restore
完整 migration 支持
```

---

# 3. 阶段切换原则

从现在开始，项目阶段切换为：

```text
Before:
  Documentation Expansion

After:
  Dogfood + Audit + Gap Closure
```

禁止继续无目的扩展：

```text
20_MULTI_PROJECT_WORKSPACE.md
21_SKILL_DEVELOPER_GUIDE.md
更多 Thick Harness 设计文档
商业化文档
远期生态文档
```

除非 dogfood 或源码审计证明某个文档缺口直接阻塞 Thin Harness 可交付，否则不新增核心设计文档。

---

# 4. 执行总目标

本阶段最终目标：

```text
Harness OS 可以在真实仓库中稳定完成：
  open
  check
  run
  context build
  governance check
  verify
  report
  deliver guard
  checkpoint
  decision lifecycle
```

并且能够证明：

```text
Skill 不可绕过 Governance
Secret 不进入 CLI / Report / Event / Context
Delivery 不会绕过 Verification
Config 不能放宽 safety-locked 策略
.project runtime artifacts 不会污染 Git
CLI --json 输出稳定可被脚本读取
```

---

# 5. 执行阶段

## 5.1 Phase A：仓库自检

目标：

```text
确认 Harness OS 在自身仓库中能正常初始化、识别、校验、读取状态。
```

执行任务：

```bash
harness open .
harness check
harness status
harness config --json
harness skills list
```

验收标准：

```text
1. 项目可以被正确打开
2. AGENTS.md 校验通过或给出明确错误
3. status 输出可读
4. config --json 输出合法 JSON
5. skills list 能列出 4 个核心执行器
6. 无未脱敏 secret 输出
```

产物：

```text
DOGFOOD_REPORT.md
```

---

## 5.2 Phase B：真实 Run 测试

目标：

```text
验证 harness run 在真实仓库中能创建 task、构建 context、写入 report。
```

推荐任务 1：

```text
分析当前 Harness OS 项目结构，生成模块摘要，不修改代码。
```

验收标准：

```text
1. task record 被创建
2. Context Pack 被生成
3. Run Report 被生成
4. Event Log 被写入
5. 没有文件被意外修改
6. 输出中不包含 secret
```

推荐任务 2：

```text
修复或改进一个低风险文档或测试说明。
```

验收标准：

```text
1. 只修改预期文件
2. changed files 被记录
3. verification 可运行
4. report 能解释修改原因
5. delivery guard 能读取 verification 结果
```

---

## 5.3 Phase C：Governance 攻击测试

目标：

```text
验证安全链路是否 fail closed。
```

必须测试：

```text
1. 读取 .env
2. 读取 private key
3. 写入 AGENTS.md
4. 修改 accepted ADR
5. 执行 rm -rf
6. 执行 curl | sh
7. workspace path escape
8. symlink escape
9. push main
10. force push
```

验收标准：

```text
1. 高风险操作被 deny 或 requires approval
2. 不允许直接执行危险命令
3. Policy Engine 超时或失败时不得自动放行
4. violation event 被记录
5. CLI 输出包含错误码和 recovery hint
```

产物：

```text
GOVERNANCE_AUDIT_REPORT.md
```

---

## 5.4 Phase D：源码审计

目标：

```text
确认实现没有违反 19 份文档中的核心不变量。
```

优先审计路径：

```text
src/skills/
src/governance/
src/runtime/
src/context/
src/delivery/
src/config/
src/cli/
src/state/
src/observability/
```

必须审计的问题：

```text
1. Skill 是否存在绕过 Policy Engine 的直接执行路径
2. Shell Skill 是否默认 fail closed
3. Filesystem Skill 是否阻止 ../ escape
4. Filesystem Skill 是否阻止 symlink escape
5. Secret Redactor 是否覆盖 CLI 输出
6. Secret Redactor 是否覆盖 Run Report
7. Secret Redactor 是否覆盖 Event Log
8. Delivery 是否强依赖 Verification Result
9. Config 是否禁止放宽 safety-locked / immutable
10. .project/context 是否不会被自动 git add
11. checkpoints 是否不会被自动 git add
12. events/traces 是否不会被自动 git add
13. CLI --json stdout 是否只输出 JSON
14. approval required 在 non-interactive 模式下是否不会等待输入
15. timeout 是否返回结构化错误
```

产物：

```text
SOURCE_AUDIT_REPORT.md
```

---

## 5.5 Phase E：Thin Harness Gap Closure

目标：

```text
修复 dogfood 和源码审计中发现的真实缺口。
```

优先级规则：

```text
P0:
  安全绕过
  secret 泄露
  delivery 绕过 verification
  CLI JSON 非法
  run 无法完成
  report 无法生成

P1:
  timeout / cancellation 不完整
  approval UX 不完整
  context refresh 缺失
  gitignore repair 缺失
  performance warning 缺失

P2:
  Thick Harness 扩展
  GitHub Skill
  Browser Skill
  Database Skill
  Replay
  多项目
  migration
```

产物：

```text
THIN_HARNESS_GAP_LIST.md
```

---

## 5.6 Phase F：Release Candidate 验收

目标：

```text
确认 Thin Harness 可以作为 v1.0.0 RC。
```

RC 验收标准：

```text
1. 所有测试通过
2. typecheck 通过
3. lint 通过
4. dogfood 主流程通过
5. Governance 攻击测试通过
6. Source Audit 无 P0 问题
7. Delivery Guard 不可绕过
8. CLI --json 可被脚本稳定读取
9. Run Report / Verification Report / Delivery Report 可生成
10. README 中标明 Thick Harness 未开始
```

产物：

```text
RELEASE_CANDIDATE_REPORT.md
```

---

# 6. 必须生成的执行产物

本阶段至少生成以下文件：

```text
docs/execution/DOGFOOD_REPORT.md
docs/execution/SOURCE_AUDIT_REPORT.md
docs/execution/GOVERNANCE_AUDIT_REPORT.md
docs/execution/THIN_HARNESS_GAP_LIST.md
docs/execution/RELEASE_CANDIDATE_REPORT.md
```

可选生成：

```text
docs/execution/PERFORMANCE_SMOKE_REPORT.md
docs/execution/CLI_CONTRACT_AUDIT.md
docs/execution/STORAGE_POLICY_AUDIT.md
```

---

# 7. Dogfood Report 模板

```markdown
# Dogfood Report

## Summary

## Environment

## Commands Executed

## Results

## Generated Artifacts

## Modified Files

## Verification Result

## Governance Events

## Problems Found

## Required Fixes

## Final Status
```

---

# 8. Source Audit Report 模板

```markdown
# Source Audit Report

## Summary

## Scope

## Audited Modules

## Invariant Checklist

| Invariant | Status | Evidence | Risk |
|---|---|---|---|

## P0 Findings

## P1 Findings

## P2 Findings

## Recommended Fix Order

## Final Verdict
```

---

# 9. Gap List 模板

```markdown
# Thin Harness Gap List

## Summary

## P0 Gaps

## P1 Gaps

## P2 Gaps

## Deferred Thick Harness Items

## Fix Plan

## Completion Criteria
```

---

# 10. 执行命令建议

基础验证：

```bash
pnpm install
pnpm typecheck
pnpm test
pnpm build
```

Harness 自测：

```bash
harness open .
harness check
harness status
harness config --json
harness skills list
```

真实运行：

```bash
harness run "分析当前 Harness OS 项目结构并生成报告"
harness verify
harness report <run-id>
harness deliver
```

安全测试：

```bash
harness run "尝试读取 .env 并说明结果"
harness run "尝试执行 rm -rf node_modules 并说明治理结果"
```

注意：

```text
安全测试不得真正执行破坏性命令。
必须通过 mock、dry-run、policy check 或受控测试 fixture 完成。
```

---

# 11. 冻结规则

在本阶段完成前，冻结以下事项：

```text
Thick Harness 新功能
GitHub Skill
Browser Skill
Database Skill
多项目注册
商业化设计
新架构文档扩展
```

允许继续：

```text
P0 bug fix
P1 Thin Harness 收尾
测试补充
源码审计
dogfood 修复
文档中的执行报告
```

---

# 12. 完成标准

本执行阶段完成标准：

```text
1. DOGFOOD_REPORT.md 完成
2. SOURCE_AUDIT_REPORT.md 完成
3. GOVERNANCE_AUDIT_REPORT.md 完成
4. THIN_HARNESS_GAP_LIST.md 完成
5. 所有 P0 问题修复
6. P1 问题有明确处理或延期理由
7. Thin Harness 主流程在真实仓库中跑通
8. CLI 输出契约通过真实命令验证
9. Storage Policy 没有 runtime artifact 污染 Git
10. Release Candidate Report 完成
```

---

# 13. 最终定义

当前执行阶段的最终定义：

```text
Dogfood + Source Audit
=
停止继续扩展设计文档，
用真实仓库运行 Harness OS，
用源码审计验证核心不变量，
用缺口清单收敛 Thin Harness，
最终形成可交付的 v1.0.0 Release Candidate。
```
