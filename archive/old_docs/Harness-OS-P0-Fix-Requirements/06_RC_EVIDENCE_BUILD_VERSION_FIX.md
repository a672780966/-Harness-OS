# P0-06 RC Build、版本与执行证据修复需求

## 1. 目标

修复生产构建失败和 RC 版本不一致，建立可复现、绑定 commit、非空且可审计的执行报告，使 RC 结论与实际仓库状态一致。

## 2. 涉及模块

- `package.json`
- `pnpm-lock.yaml`
- `tsconfig.json`
- `src/cli/index.ts`
- `src/cli/formatter.ts`
- `.project/reports/verification/`
- `.project/state/runs/`
- `docs/execution/`
- CI / release workflow
- 版本与验收设计文档

## 3. 修复节点

### RC-01 修复生产构建

- `pnpm build` 必须 ESM 和 DTS 两阶段均成功。
- 处理 TypeScript 6 `baseUrl` deprecation，优先移除无用配置；不要仅长期静默忽略。
- 构建后检查 `dist/index.js`、声明文件和 bin entry。
- 在干净 checkout 中执行构建。

### RC-02 统一版本

以下位置必须一致：

- Git tag
- `package.json`
- CLI `--version`
- JSON meta.version
- manifest/schema version策略
- RC 报告标题

目标版本为 `1.0.0-rc.1`，除非重新发布新的 RC 版本。

### RC-03 Verification Gate

RC 必须按顺序执行：

1. install with frozen lockfile
2. typecheck
3. unit tests
4. integration tests
5. full tests
6. build
7. CLI smoke tests
8. security regression tests

任一步 failed、partial 或 skipped，RC 结论不得为 allowed。

### RC-04 修正命令检测

- 不把 `dev`、watch、format-write 作为验证步骤。
- lint 占位脚本不能算有效 lint。
- 空 e2e suite 需明确标注 not-applicable，而不是混入通过统计。
- 构建不能被 fail-fast 意外跳过后仍宣称 RC ready。

### RC-05 执行报告证据

每份执行报告至少记录：

- 完整 commit SHA 和 tag
- UTC 时间
- OS、Node、pnpm、Git 版本
- 精确命令
- exit code
- passed/failed/skipped 数量
- duration
- 关键输出摘要
- artifact/report path
- 报告生成器版本

禁止只写结论而没有原始命令证据。

### RC-06 状态一致性

- Verification 结束后更新 run state。
- RC 报告只引用 completed run。
- task/run/trace/report 的状态必须一致。
- 检测到 `running`、`PARTIAL` 或缺失 report 时，自动阻断 RC。

### RC-07 报告真实性

- 删除或修正“Policy bypass 已解决”等与源码不符的声明。
- 报告必须由自动化结果生成，人工结论不得覆盖机器状态。
- 每个 claimed invariant 都应链接到测试或静态证据。
- 报告不得把已知 P0 降级为非阻断 P1。

### RC-08 Tag 与源码冻结

- tag 必须指向完成全部 gate 的 commit。
- tag 后不得用 main 上的新报告补充 tag 的证据而混淆审计对象。
- 重新发布应使用新 RC tag，不移动既有 tag。

### RC-09 Git Artifact Policy

- `.project/context/`
- `.project/checkpoints/`
- `.project/reports/events/`
- `.project/reports/traces/`

继续保持 ignored，并增加 staged artifact 检查。Reviewable verification/delivery report 是否跟踪应由明确 policy 决定。

## 4. RC 验收清单

- [ ] `pnpm install --frozen-lockfile` 成功
- [ ] `pnpm typecheck` 成功
- [ ] 428 项或更新后的全部测试成功
- [ ] `pnpm build` 成功，包括 DTS
- [ ] 所有 CLI JSON smoke tests 成功
- [ ] 六个 P0 对应的安全回归测试成功
- [ ] package、CLI、JSON meta 与 tag 版本一致
- [ ] 运行状态为 completed
- [ ] verification 状态为 passed
- [ ] 报告包含 commit SHA、环境、命令和 exit code
- [ ] 无 Thick Harness 范围误报

## 5. 完成定义

- 从干净环境可一键复现完整 RC gate。
- 构建、测试和报告结论完全一致。
- 不再存在 `PARTIAL` 报告或 `running` 状态支撑 RC allowed 的情况。
- 新 RC tag 只在全部 P0 修复并验证后创建。

