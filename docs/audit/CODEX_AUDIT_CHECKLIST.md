# Codex Audit Checklist

25 items to verify during read-only audit.

| # | Checklist Item | Status | Notes |
|---|---|---|---|
| 1 | Governance 是否默认 fail closed | ☐ | Policy Engine default = needs_approval |
| 2 | Policy Engine 是否覆盖所有高风险操作 | ☐ | rm -rf, sudo, credential, path, git push... |
| 3 | Approval Gate 是否支持 pending / approved / rejected / TTL | ☐ | approval-gate.ts |
| 4 | Skill 是否存在绕过 Policy Engine 的执行路径 | ☐ | registry.ts execute() → checkPolicy? |
| 5 | Shell Skill 是否阻止危险命令 | ☐ | shell/index.ts dangerous patterns |
| 6 | Filesystem Skill 是否阻止 path escape (`../`) | ☐ | filesystem/index.ts safeResolve |
| 7 | Filesystem Skill 是否阻止 symlink escape | ☐ | realpathSync usage |
| 8 | Git Skill 是否阻止 push main / force push | ☐ | git_push → blocked |
| 9 | Secret Redactor 是否覆盖 CLI 输出 | ☐ | formatter.ts redactText calls |
| 10 | Secret Redactor 是否覆盖 Run Report | ☐ | report.ts redactObject |
| 11 | Secret Redactor 是否覆盖 Event Log | ☐ | events.ts logEvent → redactObject |
| 12 | Secret Redactor 是否覆盖 Context Pack | ☐ | build.ts → redacted? |
| 13 | Delivery Guard 是否强依赖 Verification Result | ☐ | guard.ts checkVerification |
| 14 | Verification Pipeline 是否接入 task run | ☐ | task run → verification flow |
| 15 | Observability 是否记录 event / trace / report | ☐ | events.ts, trace.ts, report.ts |
| 16 | State & Recovery 是否支持 checkpoint / rollback | ☐ | checkpoint.ts |
| 17 | CLI --json 是否只输出合法 JSON | ☐ | formatter.ts jsonOutput |
| 18 | Config 系统是否支持分层加载 | ☐ | loader.ts 5-layer resolution |
| 19 | Config 是否不能放宽 safety-locked 策略 | ☐ | loader.ts mergeConfig governance check |
| 20 | Decision Manager 是否支持 ADR 全生命周期 | ☐ | propose/accept/reject/supersede |
| 21 | `.project/context` 是否不会被 git add | ☐ | .gitignore |
| 22 | checkpoints / events / traces 是否不会污染 Git | ☐ | .gitignore |
| 23 | execution reports 是否真实、非空、可审计 | ☐ | docs/execution/ 5 reports |
| 24 | 428 tests / 19 files / 0 failures 是否能复现 | ☐ | `pnpm test` |
| 25 | Thick Harness 是否没有被错误标记为完成 | ☐ | project report + docs |
