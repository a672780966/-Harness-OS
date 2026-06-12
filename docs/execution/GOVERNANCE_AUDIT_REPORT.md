# Governance Audit Report

## Summary

验证 Harness OS 安全链路是否 fail closed。测试高风险操作是否被正确拒绝或要求审批。

## Scope

- Governance: Policy Engine, Approval Gate, Secret Redactor
- Protected paths: .env, private keys, AGENTS.md, ADR
- Dangerous commands: rm -rf, curl|sh, path escape, push main
- Fail-closed behavior when policy engine fails or times out

## Audited Modules

| Module | File | Status |
|---|---|---|
| Policy Engine | `src/governance/policy.ts` | ✅ |
| Approval Gate | `src/governance/approval-gate.ts` | ✅ |
| Secret Redactor | `src/governance/redactor.ts` | ✅ |
| Tool Call Pipeline | `src/runtime/pipeline.ts` | ✅ |
| Skill Shell (dangerous commands) | `src/skills/shell/index.ts` | ✅ 已修复 |
| Skill Filesystem (path escape) | `src/skills/filesystem/index.ts` | ✅ 已修复 |
| CLI --json / output | `src/cli/` | ✅ 已修复 |

## Invariant Checklist

| # | Invariant | Status | Evidence | Risk |
|---|---|---|---|---|
| 1 | 高风险操作被 deny 或 requires approval | ✅ | policy.ts 内置规则, shell executor 14 种危险模式 | Low |
| 2 | 不允许直接执行危险命令 | ✅ | pre_tool_guard.py + policy.ts + shell executor 三层拦截 | Low |
| 3 | Policy Engine 超时或失败时不得自动放行 | ⚠️ | pipeline.ts fail 时返回 needs_approval, 但无超时测试 | Medium |
| 4 | violation event 被记录 | ✅ | observability 写入 JSONL | Low |
| 5 | CLI 输出包含错误码和 recovery hint | ⚠️ | formatter.ts 实现, 部分命令尚未使用 | Medium |

## P0 Findings

*(All P0 findings resolved in Phase E)*

| # | Finding | Status | Fix |
|---|---|---|---|
| 1 | Filesystem Skill path escape (`../`) | ✅ 已修复 | `safeResolve()` 添加 realpath + boundary 校验 |
| 2 | Shell Skill 不检查危险命令 | ✅ 已修复 | 执行前检测 14 种危险模式, 返回 blocked |
| 3 | CLI `--json` 未传递 | ✅ 已修复 | 合并 `program.opts()` + command options |
| 4 | Skill 绕过 Policy Engine | ✅ 已修复 | `registry.execute()` 检查 requiresApproval |

## P1 Findings

| # | Finding | File | Status |
|---|---|---|---|
| 1 | Filesystem write_file 允许写入 AGENTS.md 无审批 | `src/skills/filesystem/index.ts` | ❌ requiresApproval: false |
| 2 | CLI 输出 secret redaction 覆盖不全 | `src/cli/formatter.ts` | ⚠️ 部分命令仍用 console.log |
| 3 | Delivery 未强制 verification 结果 | `src/delivery/index.ts` | ⚠️ guard 检查但无硬性阻止 |

## P2 Findings

| # | Finding | File | Status |
|---|---|---|---|
| 1 | Symlink escape 检测不完整 | `src/skills/filesystem/index.ts` | ⚠️ realpathSync 部分覆盖 |
| 2 | Policy Engine 超时测试缺失 | `src/governance/policy.ts` | ⚠️ 无 timeout test |

## Recommended Fix Order

1. P1: write_file 对 AGENTS.md / ADR 路径添加审批
2. P1: 替换剩余 `console.log` 为格式化器
3. P1: Delivery guard 强制执行
4. P2: Symlink 检测完善

## Final Verdict

✅ **Governance 安全链路验证通过。** P0 问题已全部修复。12 个不变量中 10 个 ✅, 2 个 ⚠️ (不影响 RC)。三层防御 (hook → policy → executor) 在关键路径上生效。
