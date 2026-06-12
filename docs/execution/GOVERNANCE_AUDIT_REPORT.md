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

## Invariant Checklist

| # | Invariant | Status | Evidence | Risk |
|---|---|---|---|---|
| 1 | 高风险操作被 deny 或 requires approval | ✅ | policy.ts 内置规则: rm -rf → needs_approval, credential → deny | Low |
| 2 | 不允许直接执行危险命令 | ✅ | pre_tool_guard.py 会拦截, policy.ts 也拦截 | Low |
| 3 | Policy Engine 超时或失败时不得自动放行 | ⚠️ | pipeline.ts fail 时返回 needs_approval, 但无超时测试 | Medium |
| 4 | violation event 被记录 | ✅ | 08_GOVERNANCE.md 定义了事件类型, observability 写入 JSONL | Low |
| 5 | CLI 输出包含错误码和 recovery hint | ⚠️ | formatter.ts 实现, 但部分命令尚未使用 | Medium |

## P0 Findings

| # | Finding | File | Status |
|---|---|---|---|
| 1 | Filesystem Skill 没有 enforce workspace 边界 (`../` 逃逸) | `src/skills/filesystem/index.ts` | ❌ 未处理 |
| 2 | Shell Skill 不检查危险命令 | `src/skills/shell/index.ts` | ❌ 依赖 Policy 但未直接检查 |
| 3 | Secret Redactor 未应用于 CLI 输出 | `src/cli/formatter.ts` | ⚠️ 调用了 redactText 但未验证覆盖 |

## P1 Findings

| # | Finding | File | Status |
|---|---|---|---|
| 1 | Policy Engine 未接入 Skill 执行器 | `src/skills/registry.ts` | ❌ execute() 不走 checkPolicy |
| 2 | Filesystem write_file 允许写入 AGENTS.md 无需审批 | `src/skills/filesystem/index.ts` | ❌ requiresApproval: false |
| 3 | 全局 `--json` 选项未传递给子命令 | `src/cli/index.ts` | ❌ |

## P2 Findings

| # | Finding | File | Status |
|---|---|---|---|
| 1 | CLI 输出 secret redaction 调用但缺乏验证 | `src/cli/formatter.ts` | ⚠️ 调用 redactText 但无法确认覆盖 |
| 2 | Delivery 未强制 verification 结果 | `src/delivery/index.ts` | ⚠️ guard 检查但无硬性阻止 |

## Recommended Fix Order

1. P0: Filesystem Skill `safeResolve` — 添加 `../` 逃逸检测
2. P0: Shell Skill — 添加危险命令检查 (或接入 Policy Engine)
3. P1: Policy Engine 接入 Skill 执行 (`registry.execute` → `checkPolicy`)
4. P1: write_file 对 AGENTS.md 和 ADR 文件需要审批
5. P2: CLI `--json` 选项传递修复

## Final Verdict

Governance 基础层（Policy + Approval + Redactor）实现完整。但存在 3 个 P0 级安全缺陷：Filesystem path escape、Shell 无危险命令检查、Secret redactor 未全覆盖。修复后方可 RC。
