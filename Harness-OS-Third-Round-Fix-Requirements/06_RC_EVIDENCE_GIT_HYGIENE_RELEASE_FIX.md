# 第三轮修复 06：RC 证据、Git Hygiene 与发布准备

## 执行提示词

读取本文件执行。只修 `AUD3-P0-006`。本轮只建立证据和发布准备；提交但不 push、不打 tag、不启动 Thick Harness。

前置条件：`AUD3-P0-001` 至 `AUD3-P0-005` 已分别提交，工作树干净。

## 1. 修复目标

生成真实、非空、可复现、绑定完整 commit SHA 的 rc.2 审计证据；确认 runtime artifacts 不污染 Git，并形成“可打 tag”而不是“已经打 tag”的发布结论。

## 2. 已确认问题

- 仓库现有 Verification Report 状态为 `PARTIAL`。
- 现有 run state 状态为 `running`。
- 旧文档仍声称 428/497 tests 全通过，与二次审计复现不一致。
- 旧 `v1.0.0-rc.1` tag 指向修复前提交。
- `.project/context/`、`.project/checkpoints/`、`.project/reports/events/`、`.project/reports/traces/` 已忽略；`.project/events`、`.project/traces` 并非实际运行路径。
- execution/verification reports 的跟踪策略缺少清晰区分。

## 3. 允许修改范围

- `docs/audit/` 下第三轮完成报告
- 明确允许跟踪的 reviewable RC evidence 目录
- `.gitignore`
- `.project` 模板及 repair/create 所生成的 `.gitignore` 片段
- 必要的证据生成脚本或文档

不得修改业务代码；若发现前五轮仍有代码缺陷，立即停止本轮并退回对应修复轮次。

## 4. 详细修复节点

### EVD3-01 审计对象绑定

报告必须记录：

- repository URL
- branch
- 完整 40 位 commit SHA
- parent commits
- dirty/clean 状态
- Node、pnpm、Git、OS
- 审计开始和结束时间
- 目标版本 `1.0.0-rc.2`

禁止只写短 SHA 或“latest main”。

### EVD3-02 命令级证据

逐项记录：

- command
- cwd
- startedAt / finishedAt
- exit code
- passed / failed / skipped 数量
- 关键 stdout/stderr 摘要
- 原始日志位置

至少包含：

```text
pnpm install --frozen-lockfile
pnpm typecheck
pnpm test（三次）
pnpm build
CLI JSON contract matrix
security regression matrix
git ignore/staged artifact checks
version consistency checks
```

### EVD3-03 报告真实性

- 最终 Verification 必须为 `PASSED`，不得把 partial 描述为通过。
- 不得保留 `running` 状态作为 RC 完成证据。
- failed/skipped 必须如实列出；required step skipped 时整体不能 passed。
- execution report 不得为空、不得使用 placeholder、不得复制旧测试数字。
- 报告中的测试总数必须来自本轮实际输出。

### EVD3-04 Git Hygiene

确认以下实际运行目录被忽略：

```text
.project/context/
.project/checkpoints/
.project/sessions/
.project/tasks/active/
.project/reports/events/
.project/reports/traces/
.project/reports/artifacts/
raw stdout/stderr
node_modules/
dist/
coverage/
```

- 同步检查根 `.gitignore`、project create 模板和 repair 逻辑。
- 增加 staged artifact guard，阻止 runtime files、secret files、raw outputs 进入 commit。
- reviewable verification/RC report 如需跟踪，必须位于单独明确目录，不得与 runtime logs 混用。

### EVD3-05 RC Readiness 报告

生成四类报告：

```text
THIRD_ROUND_FULL_AUDIT.md
THIRD_ROUND_SECURITY_VERIFICATION.md
RC2_READINESS_REVIEW.md
RC2_RELEASE_CHECKLIST.md
```

每个 finding 必须包含 Severity、Module、File、Evidence、Risk、Fix、Test 和 Blocks RC。

### EVD3-06 Tag 准备

- 本轮不得创建 tag。
- 报告只允许给出 `READY_FOR_TAG` 或 `NOT_READY`。
- 只有全部 P0 关闭、工作树干净、证据 passed 时才可标记 `READY_FOR_TAG`。
- 后续人工确认后使用新 tag `v1.0.0-rc.2`。
- 禁止移动或覆盖 `v1.0.0-rc.1`。

## 5. 必须执行的检查

```powershell
git status --short
git diff --check
git ls-files .project
git check-ignore -v .project/context/probe.json
git check-ignore -v .project/checkpoints/probe.json
git check-ignore -v .project/reports/events/probe.jsonl
git check-ignore -v .project/reports/traces/probe.json
git diff --cached --name-only
git tag --list
```

需要额外验证 staged artifact guard 对 runtime、secret 和 raw output 路径返回阻断。

## 6. 完成定义

- 所有证据绑定同一个完整 commit SHA。
- Verification 为 passed，run/task/trace 状态一致且非 running。
- 报告非空，命令和 exit code 可审计。
- runtime artifacts 不污染 Git。
- 版本、测试、构建、CLI 和安全矩阵全部通过。
- 结论为 `READY_FOR_TAG` 时仍未创建 tag。

## 7. 提交要求

提交信息：

```text
docs: AUD3-P0-006 RC2 evidence and release readiness
```

最终提交后再次运行关键 gate，并在报告中记录“证据提交 SHA”和“复验 SHA”。不 push，不打 tag。

## 8. 全部修复完成后的统一提示词

```text
读取第三轮 01 至 06 的修复报告和提交记录，执行最终只读复验。
不得修改代码，不得提交，不得 push，不得打 tag，不得启动 Thick Harness。
只有全部 P0 关闭、测试与构建通过、证据绑定当前完整 SHA 时，输出 READY_FOR_TAG v1.0.0-rc.2。
```
