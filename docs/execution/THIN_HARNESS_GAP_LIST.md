# Thin Harness Gap List

## Summary

基于 Dogfood 自检和 Source Audit 发现的 Thin Harness 真实缺口。仅包含阻塞 Thin Harness 可交付的问题。

## P0 Gaps

| # | Gap | Source | Fix |
|---|---|---|---|
| 1 | CLI `--json` 全局选项未传递给子命令处理函数 | Dogfood + Audit | 修复 `src/cli/index.ts` — 全局选项需手动传递给 action handler |
| 2 | Skill 执行绕过 Policy Engine | Source Audit | `registry.execute()` 必须调 `checkPolicy()` |
| 3 | Filesystem Skill 允许 `../` path escape | Source Audit | `safeResolve()` 必须验证 resolved path 在 workspace 内 |
| 4 | Shell Skill 不检查危险命令 | Source Audit | `execute()` 执行前检测 rm -rf / sudo 等 |
| 5 | CLI 输出未全部经过 Secret Redactor | Source Audit | 替换剩余 `console.log` 为格式化器 |

## P1 Gaps

| # | Gap | Source | Fix |
|---|---|---|---|
| 1 | Verification runner Windows shell 兼容性 | Dogfood | 已修复 (exec vs execFile) |
| 2 | write_file 可写入 AGENTS.md 无审批 | Source Audit | filesystem executor 中 protected path 检测 |
| 3 | Delivery guard 不硬性阻止 | Source Audit | `deliver` 命令中强制执行 guard.canProceed |
| 4 | AGENTS.md 缺少 8 个标准章节 | Dogfood | 更新项目自身 AGENTS.md 以通过 check |
| 5 | Run Report 未生成 (因 verification 未完成) | Dogfood | 提高 verification 超时或跳过空命令 |

## P2 Gaps

| # | Gap | Source | Fix |
|---|---|---|---|
| 1 | Context Pack 不读取真实文件内容 | Source Audit | `build.ts` 添加文件内容读取 |
| 2 | Checkpoint rollback 不执行 git reset | Source Audit | 添加实际 git checkout/reset |
| 3 | `harness resume` 是 stub | Source Audit | 实现 run state 恢复 |
| 4 | Non-interactive 模式审批无超时 | Source Audit | 添加 `--approve` 或超时拒绝 |
| 5 | AGENTS.md validator 只检查标题不检查内容 | Source Audit | 可选增强 |

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
Phase E.1 (P0 fixes):
  ├── CLI --json: 修复全局选项传递
  ├── Filesystem path escape: safeResolve + realpath
  ├── Shell dangerous command: 添加检查
  └── Policy Engine → Skill execute: registry 接入 policy

Phase E.2 (P1 fixes):
  ├── write_file protected path: AGENTS.md/ADR 检测
  ├── Delivery guard 强制执行
  └── Runner Windows 兼容 (已修复)

Phase E.3 (P2 fixes):
  ├── Context file content
  ├── Checkpoint actual rollback
  └── Resume implementation
```

## Completion Criteria

- [ ] P0 全部修复
- [ ] `harness config --json` 输出合法 JSON
- [ ] `harness run "analyze"` 在真实仓库中完成全流程
- [ ] Secret 不出现于 CLI / Report / Event / Context
- [ ] CLI --json stdout 只包含 JSON
- [ ] 总计测试数不减少
