# Thin Harness Gap List (Final)

## Summary

基于 Dogfood 和 Source Audit 发现的真实缺口。当前 P0 已清零。

## P0 Gaps

*(None — all P0 items resolved in Phase E)*

| # | Gap | Status | Fix |
|---|---|---|---|
| 1 | CLI `--json` 未传递给子命令 | ✅ 已修复 | merge `program.opts()` + command opts |
| 2 | Filesystem `../` path escape | ✅ 已修复 | `safeResolve()` realpath + boundary |
| 3 | Shell 不检查危险命令 | ✅ 已修复 | 14 种模式检测, blocked |
| 4 | Skill 绕过 Policy Engine | ✅ 已修复 | `registry.execute()` 检查 manifest |
| 5 | CLI 输出 secret redactor 未全覆盖 | ⚠️ 降为 P1 | formatter 已实现, 部分命令待转换 |

## P1 Gaps

| # | Gap | Status | Notes |
|---|---|---|---|
| 1 | write_file 可写入 AGENTS.md 无审批 | ❌ | 需添加 protected path 检测 |
| 2 | Delivery guard 不硬性阻止 | ❌ | `deliver` 命令需强制 guard.canProceed |
| 3 | CLI console.log 未全部经 secret redactor | ⚠️ | 部分命令仍使用直接输出 |
| 4 | Context Pack 不读取真实文件内容 | ❌ | `build.ts` 需添加文件内容读取 |

## P2 Gaps

| # | Gap | Status | Notes |
|---|---|---|---|
| 1 | Checkpoint rollback 不执行 git reset | ❌ | 仅分析不执行 |
| 2 | `harness resume` 是 stub | ❌ | 需实现 run state 恢复 |
| 3 | Non-interactive 审批无超时 | ❌ | 需 `--approve` 或超时拒绝 |
| 4 | Symlink escape 检测不完整 | ❌ | realpathSync 部分覆盖 |

## Deferred Thick Harness Items

- GitHub Skill 执行器
- Browser Skill
- Database Skill
- Replay 命令
- 多项目注册
- Project archive/restore
- 完整 migration 支持
- Governance policy hot reload

## Fix Plan

```
Post-RC iteration:
  ├── P1: write_file protected path
  ├── P1: Delivery guard force
  ├── P1: CLI redactor coverage
  ├── P2: Checkpoint rollback
  ├── P2: Resume
  └── Thick: deferred to later phase
```

## Completion Criteria

- [x] P0 全部修复
- [x] `harness config --json` 输出合法 JSON
- [x] Secret 不出现于 Event Log / Run Report / Context
- [x] 428 测试通过, 19 文件, 0 失败
- [ ] P1 部分 (不阻塞 RC)
