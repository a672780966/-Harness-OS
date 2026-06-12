# 第三轮修复 01：Governance、Skill、Filesystem 与 Hook Fail-Closed

## 执行提示词

读取本文件执行。只修 `AUD3-P0-001`，补回归测试，完成后提交；不 push，不打 tag，不启动 Thick Harness。

## 1. 修复目标

消除所有绕过 Policy Engine 的生产执行路径，并使 Skill、Filesystem、Shell、Git、Pre/Post Hook 在异常、未知或不可判定时统一 fail closed。

## 2. 已确认问题

- `SkillRegistry.getExecutor()` 公开返回原始 executor，测试将其明确标记为治理绕过。
- 各 Skill 仍导出可直接调用的 `execute()`。
- `Write AGENTS.md`、PowerShell `Remove-Item`、`GitCommit` 当前策略实测为 `allow`。
- Shell 主要依赖字符串 denylist，存在大小写、引号、PowerShell、控制符及编码绕过。
- `safeResolve()` 使用 `startsWith(basePath)`，同前缀兄弟目录及 symlink/junction 可逃逸。
- approval 只创建 pending ID，缺少绑定、恢复、单次消费和 `modifiedInput` 执行闭环。
- `post_tool_trace.py` 捕获所有异常并始终退出 0，与 Hook fail-closed 约束冲突。

## 3. 允许修改范围

- `src/skills/registry.ts`
- `src/skills/executor.ts`
- `src/skills/filesystem/index.ts`
- `src/skills/shell/index.ts`
- `src/skills/git/index.ts`
- `src/governance/policy.ts`
- `src/governance/approval-gate.ts`
- `src/runtime/pipeline.ts`
- `.claude/hooks/pre_tool_guard.py`
- `.claude/hooks/post_tool_trace.py`
- 对应 unit/integration tests

不得顺手修改 Config、Redactor、Verification、Delivery、CLI 或版本文件。

## 4. 详细修复节点

### GOV3-01 单一受治理执行入口

- 生产代码只能通过一个受治理入口调用 Skill。
- 删除、私有化或封装 `getExecutor()`，不得向生产调用方返回原始函数。
- Skill 原始 executor 不得由公共 barrel export 暴露。
- 即使内部误调用 executor，也必须存在不可绕过的 policy capability/token 校验。
- 未注册 Skill、未注册 Tool、缺失 manifest、输入 schema 不合法均返回 deny/blocked，不得执行。

### GOV3-02 Policy 决策完整性

- Policy 返回值必须运行时校验为 `allow | deny | needs_approval`。
- Policy 抛错、超时、返回空值或非法结构时统一 `needs_approval` 或 deny。
- 高风险操作不得命中宽泛的 default allow。
- `AGENTS.md`、accepted ADR、governance/config policy 修改必须 `needs_approval`。
- credential、private key、token、`.env*` 写入默认 deny。
- 敏感文件读取同样必须经过策略，不得被首条 read-only allow 抢先放行。

### GOV3-03 Approval 强绑定

- approval 必须绑定：skill、tool、规范化输入摘要、project、task、run、session、affected paths。
- approved 只能消费一次；rejected、expired、已消费 approval 不得重放。
- approval 不得跨 tool、跨 project、跨输入使用。
- operator 提供 `modifiedInput` 时，只能执行该输入并重新做 schema/path/policy 校验。
- approval 解决和消费必须写入脱敏 event/trace。

### GOV3-04 Filesystem 边界

- 使用 canonical base 和 target，通过 `relative(base, target)` 判断边界。
- 拒绝绝对路径、UNC、跨盘符、`..` 逃逸和同前缀兄弟目录。
- 已存在目标必须校验 `realpath`。
- 新文件必须校验最近存在父目录的 `realpath`，防止父目录 symlink/junction 逃逸。
- Windows 比较需处理大小写和路径分隔符语义。
- 不得把 `realpath` 失败简单等同于安全。

### GOV3-05 Shell 治理

- `run_command` 默认 `needs_approval`；只有结构化 allowlist 中的明确命令可自动 allow。
- `run_test`、`run_build` 只能执行 Verification Plan 声明的精确 argv/cwd。
- cwd 必须位于 project workspace。
- 禁止未经审批的删除、权限变更、credential 修改、网络下载后执行、publish、deploy、push、commit。
- 处理 PowerShell、cmd、bash、引号、大小写、环境变量、管道、重定向、子命令和命令连接符。
- 不得仅用 `includes()` 作为最终安全判定。

### GOV3-06 Git 治理

- `git_commit` 不得默认 allow。
- commit 前检查当前分支、staged 文件、runtime artifacts、secret scan 和 verification binding。
- push main/master、force push、tag、release 操作必须独立进入 approval/deny。
- approval 不得替代 verification passed。

### GOV3-07 Hook Fail-Closed

- PreToolUse 输入解析失败必须 deny 或 `needs_approval`。
- 安全决策 Hook 抛错不得返回 allow。
- PostToolUse 审计写入失败必须产生可见失败状态；不得静默伪装为成功记录。
- 区分“阻止工具执行的安全 Hook”和“工具已执行后的审计 Hook”，但两者都必须记录错误。

## 5. 必须新增的回归测试

1. 生产代码无法取得或直接调用 raw executor。
2. Policy 抛错、超时、非法返回值时 executor 未被调用。
3. `AGENTS.md` 和 accepted ADR 写入不是 allow。
4. PowerShell `Remove-Item`、大小写变体、引号和管道绕过被阻断。
5. shell cwd 指向 workspace 外被阻断。
6. sibling-prefix、`../`、绝对路径、UNC、symlink/junction 逃逸被阻断。
7. approval 跨 tool、跨输入、过期、重复消费全部失败。
8. `modifiedInput` 被重新校验并成为唯一实际输入。
9. git commit 在 protected branch、包含 runtime artifacts 或未验证时被阻断。
10. Hook malformed input 和内部异常均不返回 allow。

## 6. 验收命令

```powershell
pnpm.cmd typecheck
pnpm.cmd test
pnpm.cmd build
```

所有新增安全测试必须真实调用公开生产入口，禁止只 mock 掉 Policy Engine。

## 7. 完成定义

- 不存在公开 raw executor 绕过路径。
- 未知、异常、超时和非法决策全部 fail closed。
- Filesystem 无 workspace escape。
- Shell/Git 高风险操作无默认 allow。
- approval 可审计、强绑定、单次消费。
- 全量测试 0 failure。

## 8. 提交要求

提交信息：

```text
fix: AUD3-P0-001 governance execution boundary
```

完成报告必须列出修改文件、攻击路径测试、测试总数、exit code 和 commit SHA。
