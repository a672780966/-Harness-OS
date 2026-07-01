# 第三轮修复 03：Verification 与 Delivery 强绑定

## 执行提示词

读取本文件执行。只修 `AUD3-P0-003`，补回归测试，完成后提交；不 push，不打 tag，不启动 Thick Harness。

## 1. 修复目标

Task completion 和 Delivery 只能依赖当前 project/task/run/source tree 的持久化 Verification Result。任何调用方字符串、Markdown 文本、旧报告或其他任务报告都不能形成 passed。

## 2. 已确认问题

- `completeTask()` 仍接受 `verificationStatus: "passed"` 并直接完成任务。
- Verification 只保存 Markdown，没有生成 guard 所需的结构化结果。
- Delivery 收不到或不传递 `verId`。
- Guard 会回退扫描任意“最新”Markdown。
- `guard.canProceed=false` 后仍生成 commit message、PR body 和 delivery report。

## 3. 允许修改范围

- `src/verification/*`
- `src/task/index.ts`
- `src/task/complete.ts`
- `src/delivery/guard.ts`
- `src/delivery/index.ts`
- 必要的 run/task/trace 类型和状态关联
- 对应 unit/integration tests

不得修改 Governance、Redactor 算法、CLI 其他命令或版本号。

## 4. 详细修复节点

### VER3-01 结构化 Verification Result

定义并落盘不可歧义的 JSON：

```text
verificationId
schemaVersion
projectId
taskId
runId
sourceCommit
sourceTree
status
requiredSteps
stepResults
startedAt
finishedAt
reportPath
integrity
```

- JSON 是安全状态的唯一事实来源；Markdown 仅供阅读。
- `status` 只能由 runner 根据 step result 计算。
- required step 失败、跳过、超时或缺失时不得为 passed。
- 无验证命令时默认 blocked，除非任务类型存在明确且可审计的非代码例外策略。

### VER3-02 完成任务时重新加载验证

- 删除 `verificationStatus` legacy 成功入口。
- `completeTask()` 只接收 `verificationId`。
- 函数内部从受控目录加载 JSON，并校验 schema/integrity。
- 校验 projectId、taskId、runId、source commit/tree 和 freshness。
- 只有完全匹配且 status=passed 才能转为 completed。
- 调用方传入对象或字符串不得覆盖持久化结果。

### VER3-03 Run/Task/Trace 一致性

- Verification ID 写入 task state、run state 和 trace。
- 非 passed 时调用 fail/block 流程，不得记录 `task.completed` 或 `run.completed`。
- 异常路径必须关闭 running 状态，写入 endedAt、failure reason 和真实 report 引用。
- 不得留下“task failed 但 run completed”的矛盾状态。

### VER3-04 Delivery Guard

- Delivery 必须显式取得唯一 verificationId。
- 禁止目录扫描选“最新报告”。
- 禁止解析 Markdown 决定安全状态。
- 校验 verification 与当前 project/task/run/commit/tree 的绑定。
- report 缺失、JSON 非法、integrity 不符、过期、状态未知均 block。
- approval 不能把 failed/partial/skipped 改为 passed。

### VER3-05 Guard 后行为

- `guard.canProceed=false` 时立即返回结构化 blocked result。
- CLI 设置非零 exit code。
- 不生成 ready commit、PR、release 或 deploy 输出。
- 可生成 `status=blocked` 的审计报告，但不得描述为 ready。
- blocked report 必须列出准确 guard reason 和 verificationId。

### VER3-06 Verification 命令选择

- 排除 `dev`、watch、format write、publish、deploy 等命令。
- `lint` 占位脚本不能视为真实 lint。
- 空 e2e 目录必须按明确策略标记 skipped/unsupported，不得伪造 passed。
- build 必须实际执行。

## 5. 必须新增的回归测试

1. 伪造 `verificationStatus: "passed"` 无法完成任务。
2. 伪造内存 VerificationRef 无法完成任务。
3. 当前 task/run/tree 的真实 passed JSON 可以完成。
4. 其他 task、其他 run、旧 commit/tree、过期结果全部被阻断。
5. failed、partial、skipped、running、unknown、缺失 report 全部被阻断。
6. Markdown 含 `PASSED` 但 JSON 为 failed 时被阻断。
7. guard blocked 后不生成 ready PR/release/deploy 输出，exit code 非零。
8. 非 passed run 最终状态不是 running/completed。
9. approval 无法覆盖 verification status。
10. required step 被 skipped 时总体不是 passed。

## 6. 验收命令

```powershell
pnpm.cmd typecheck
pnpm.cmd test
pnpm.cmd build
```

必须额外展示至少一个真实 Verification JSON，以及 task/run/trace 中相同 ID 的引用证据。

## 7. 完成定义

- Task、Run、Trace、Verification、Delivery 使用同一组强绑定 ID。
- Markdown 不参与安全判定。
- 任意非 passed 或不匹配结果均不能形成 completed/ready。
- 全量测试 0 failure。

## 8. 提交要求

提交信息：

```text
fix: AUD3-P0-003 bind delivery to verification evidence
```

完成报告必须列出验证 JSON schema、阻断矩阵、exit code、测试总数和 commit SHA。
