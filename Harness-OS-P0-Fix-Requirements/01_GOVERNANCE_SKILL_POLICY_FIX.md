# P0-01 Governance 与 Skill Policy 修复需求

## 1. 目标

确保所有 Skill 执行路径统一经过 Policy Engine 和 Approval Gate，任何未匹配、异常或无法确认的操作均 fail closed。修复 Filesystem 路径逃逸、保护文件直写以及 Shell 任意命令执行问题。

## 2. 涉及模块

- `src/skills/registry.ts`
- `src/skills/executor.ts`
- `src/skills/filesystem/index.ts`
- `src/skills/shell/index.ts`
- `src/skills/git/index.ts`
- `src/runtime/pipeline.ts`
- `src/governance/policy.ts`
- `src/governance/approval-gate.ts`
- `tests/unit/skills.test.ts`
- `tests/unit/governance.test.ts`
- `tests/integration/thin-harness-e2e.test.ts`

## 3. 修复节点

### GOV-01 统一 Skill 执行入口

- `registry.execute()` 必须在调用 executor 前执行 `checkPolicy()`。
- Policy Context 必须包含规范化后的 tool、command、affected paths、skill name 和风险等级。
- 禁止通过 `getExecutor()` 或直接导入 executor 绕过治理入口。
- 若需保留 `getExecutor()`，必须限制为内部接口，并在 executor 内再次执行不可绕过的 gate。

验收点：

- `filesystem.write_file`、`shell.run_command`、`git_commit` 均产生 policy decision。
- 未知 Skill、未知 Tool、缺失 manifest 或 Policy 异常均返回 blocked/deny。

### GOV-02 Approval Gate 接线

- `needs_approval` 不得被转换为普通 blocked 后丢失审批上下文。
- 必须创建 pending approval，返回 approval ID、TTL、理由和影响路径。
- 只有状态为 approved 且未过期的审批可继续执行。
- approved 输入若被 operator 修改，executor 必须使用 `modifiedInput`。

验收点：

- pending、approved、rejected、expired 四种状态均有端到端测试。
- 重放旧 approval、跨 tool 使用 approval、过期后批准均失败。

### GOV-03 Filesystem 路径边界

- 使用 `resolve()` 后通过 `relative(base, target)` 判断边界。
- 拒绝绝对路径、`..` escape、同前缀 sibling 路径和 Windows 大小写/盘符变体。
- 对已存在目标执行 `realpath` 校验。
- 对新文件校验最近存在父目录的 realpath，防止父目录 symlink escape。
- 路径比较必须按平台语义处理，不能使用裸 `startsWith(basePath)`。

必须覆盖：

- `../outside/file`
- `workspace-escape/file`
- symlink/junction 指向 workspace 外
- Windows `C:\...`、UNC path、混合分隔符
- workspace 根目录自身

### GOV-04 保护文件与不可变文档

- `.env*`、credentials、private keys、token 文件默认 deny。
- `AGENTS.md`、accepted ADR、governance/config policy 文件必须 needs_approval。
- 读取敏感文件同样需要策略判断，不能只保护写入。
- 路径判断应按规范化 path component 匹配，避免字符串误判。

### GOV-05 Shell 命令治理

- Shell 不得只依赖字符串 denylist。
- 命令必须由 Policy Engine 分类，再决定 allow/deny/needs_approval。
- `run_test`、`run_build` 只能运行验证计划中声明的命令。
- 处理 shell control operators、大小写、空白、引号、环境变量和编码绕过。
- 网络请求、发布、push、删除、权限变更、下载后执行必须进入高风险策略。

### GOV-06 Git 操作治理

- `git_commit` 必须检查分支、staged 内容和 runtime artifacts。
- `git_push`、push main/master、force push 必须独立策略控制。
- 不得仅依靠 manifest 中的 `requiresApproval`。

### GOV-07 Policy 故障 fail closed

- `checkPolicy()` 抛错、超时、返回非法值时统一 deny。
- Policy 结果必须写入 event/trace，且先脱敏。
- 禁止在 catch 中默认执行 executor。

## 4. 测试要求

新增测试至少覆盖：

1. Registry 确实调用 Policy Engine。
2. Policy deny 时 executor 未被调用。
3. needs_approval 未批准时 executor 未被调用。
4. approved 后仅执行一次。
5. `.env` 和 accepted ADR 直写失败。
6. sibling-prefix、symlink/junction escape 失败。
7. Policy 抛错和超时均 deny。
8. Shell 编码、大小写、引号和 control operator 绕过失败。
9. 未知 tool fail closed。

## 5. 完成定义

- 所有 Skill 只有一个受治理的生产执行入口。
- 无法通过直接 executor、manifest 配置或路径技巧绕过 Policy。
- 新增测试通过，原 428 项测试无回归。
- 安全事件包含 policy source、decision、approval ID 和脱敏后的影响范围。

