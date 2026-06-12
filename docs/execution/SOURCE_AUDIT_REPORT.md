# Source Audit Report

## Summary

对 Harness OS 源码进行核心不变量审计，确认实现是否违反 19 份设计文档中的约束。

## Scope

| Module | Path | Lines |
|---|---|---|
| Skills | `src/skills/` | 4 executors + registry |
| Governance | `src/governance/` | policy, approval-gate, redactor |
| Runtime | `src/runtime/` | session, pipeline, orchestrator |
| Context | `src/context/` | sources, relevance, budget, build |
| Delivery | `src/delivery/` | guard, commit, pr, report |
| Config | `src/config/` | types, loader |
| CLI | `src/cli/` | formatter, index |
| State | `src/state/` | store, run, checkpoint |
| Observability | `src/observability/` | events, trace, report |

## Invariant Checklist

| # | Invariant | Status | Evidence | Risk |
|---|---|---|---|---|
| 1 | Skill 无绕过 Policy Engine 的直接执行路径 | ❌ | `src/skills/registry.ts` — `execute()` 不调 `checkPolicy()` | **P0** |
| 2 | Shell Skill 默认 fail closed | ❌ | `src/skills/shell/index.ts` — 不检查危险命令 | **P0** |
| 3 | Filesystem Skill 阻止 `../` escape | ❌ | `safeResolve` 只解析相对路径, 无 `../` 检测 | **P0** |
| 4 | Filesystem Skill 阻止 symlink escape | ❌ | 未实现 symlink 检测 | P2 |
| 5 | Secret Redactor 覆盖 CLI 输出 | ⚠️ | formatter.ts 调用 `redactText()`, 但大量 `console.log` 未覆盖 | **P0** |
| 6 | Secret Redactor 覆盖 Run Report | ✅ | report.ts 通过 redactObject → redactText | Low |
| 7 | Secret Redactor 覆盖 Event Log | ✅ | events.ts `logEvent()` 调用 `redactObject` | Low |
| 8 | Delivery 强依赖 Verification Result | ⚠️ | guard 检查但无硬性阻止 | P1 |
| 9 | Config 禁止放宽 safety-locked 策略 | ✅ | loader.ts `mergeConfig` governance 安全检查 | Low |
| 10 | .project/context 不会被自动 git add | ✅ | .gitignore 包含 `.project/context/` | Low |
| 11 | checkpoints 不会被自动 git add | ✅ | .gitignore 包含 `.project/checkpoints/` | Low |
| 12 | events/traces 不会被自动 git add | ✅ | .gitignore 包含 `.project/reports/events/` | Low |
| 13 | CLI --json stdout 只输出 JSON | ❌ | `--json` 未传递给子命令处理函数 | **P0** |
| 14 | non-interactive 模式不等待审批输入 | ⚠️ | detectOutputMode 检查 CI/env, 但无超时机制 | P2 |
| 15 | timeout 返回结构化错误 | ⚠️ | runner 捕获 timeout 但无定制错误码 | P2 |

## P0 Findings

| # | Finding | File | Impact |
|---|---|---|---|
| 1 | Skill execute() 不经过 Policy Engine | `src/skills/registry.ts` | Skill 可直接执行任何操作绕过治理 |
| 2 | Filesystem `safeResolve` 无 `../` 逃逸检测 | `src/skills/filesystem/index.ts` | 可读取 workspace 外文件 |
| 3 | Shell executor 不检查危险命令 | `src/skills/shell/index.ts` | rm -rf 等可直接执行 |
| 4 | CLI `--json` 选项未传递 | `src/cli/index.ts` | `harness config --json` 输出 non-JSON |
| 5 | CLI `console.log` 多处未通过 redactor | `src/cli/` | Secret 可能泄露 |

## P1 Findings

| # | Finding | File | Impact |
|---|---|---|---|
| 1 | write_file 可写入 AGENTS.md 无审批 | `src/skills/filesystem/index.ts` | 绕过 Governance |
| 2 | Delivery guard 无硬性阻止 | `src/delivery/guard.ts` | verification 未通过也可 deliver |
| 3 | `pnpm dev` 作为 harness CLI 入口与 dev 命令混淆 | `.claude/hooks/pre_tool_guard.py` | 影响 UX（已修复） |

## P2 Findings

| # | Finding | File | Impact |
|---|---|---|---|
| 1 | Context Pack 不读取真实文件内容 | `src/context/build.ts` | files 仅 metadata |
| 2 | Run Report 未记录 skill 调用 | `src/observability/report.ts` | 缺少执行详情 |
| 3 | Checkpoint rollback 不执行 git reset | `src/state/checkpoint.ts` | 仅分析不执行 |
| 4 | 测试中大量使用 `console.log` | 多处 | 无法结构化输出 |

## Recommended Fix Order

1. **P0**: CLI `--json` — 修复全局选项传递
2. **P0**: Filesystem `safeResolve` — 添加 `../` 逃逸检测 + `realpath.native` 验证
3. **P0**: Shell executor — 添加危险命令检查
4. **P0**: Policy Engine 接入 Skill registry.execute()
5. **P1**: write_file 对 protected 路径添加审批
6. **P1**: Delivery guard 硬性阻止
7. **P2**: 后续修复

## Final Verdict

**5 个 P0 问题** 需要在 RC 前修复。核心问题: Skill 执行绕过 Policy Engine、无 path escape 保护、CLI --json 损坏。
