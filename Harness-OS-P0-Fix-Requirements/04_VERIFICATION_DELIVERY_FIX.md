# P0-04 Verification 与 Delivery 强绑定修复需求

## 1. 目标

保证 Task Completion 和 Delivery 只能依赖当前 task/run 的已通过 Verification Result。`failed`、`partial`、`skipped`、未知、过期或不匹配的结果必须阻断。

## 2. 涉及模块

- `src/verification/runner.ts`
- `src/verification/report.ts`
- `src/verification/index.ts`
- `src/task/index.ts`
- `src/task/complete.ts`
- `src/delivery/guard.ts`
- `src/delivery/index.ts`
- `src/state/run.ts`
- `src/observability/trace.ts`
- 相关 tests

## 3. 修复节点

### VER-01 Verification Result 结构化

定义稳定的 Verification Result：

- verification ID
- project ID
- task ID
- run ID
- source commit/tree hash
- status
- required steps
- command、exit code、duration
- created/finished timestamps
- report path
- integrity/version 字段

Delivery 不得通过解析 Markdown 文本判断状态。

### VER-02 状态语义

- 只有 `passed` 可以完成任务或进入 delivery。
- `failed`、`partial`、`skipped`、`running`、`unknown` 均不通过。
- required step 被 skipped 时整体不得为 passed。
- 没有检测到验证命令时，默认阻断代码类任务；仅显式批准的非代码任务可例外。

### VER-03 Task Completion Gate

- `completeTask()` 自身必须验证 Verification Result，不应信任调用者传入字符串。
- `runTask()` 遇到非 passed 状态必须调用 fail/block 流程。
- 不得记录 `task.completed` 或 `run.completed`。
- run state、trace、task state 必须保持一致。

### VER-04 Delivery Guard 强绑定

- Guard 必须接收 verification ID 或从 run state 获取唯一结果。
- 校验 project/task/run、commit/tree hash 和 freshness。
- 禁止扫描目录后选择任意“最新文件”。
- 不得以文件名排序代替创建时间或明确引用。
- 未识别的报告内容必须阻断。

### VER-05 Guard 后行为

- `guard.canProceed=false` 时立即返回结构化错误。
- 不生成 ready 状态、PR body、release/deploy 输出。
- 可以生成 blocked report，但必须明确 status=blocked。
- CLI 以非零 exit code 结束。

### VER-06 Governance Approval

- Approval 不能把失败 verification 改成 passed。
- 对验证例外只能生成明确 waiver，包含审批人、理由、范围和 TTL。
- RC 默认不允许 deploy/release waiver。

### VER-07 Verification 命令检测

- 不得把 `dev`、`format --write`、watch 命令当作 verification。
- `test:e2e` 目录为空应有明确策略。
- lint 占位脚本 `echo "eslint pending"` 不应视为真实 lint 通过。
- build 必须实际执行并通过。

## 4. 测试矩阵

| 场景 | Task Complete | Delivery |
|---|---|---|
| 当前 run passed | 允许 | 允许进入后续审批 |
| failed | 阻断 | 阻断 |
| partial | 阻断 | 阻断 |
| skipped | 阻断 | 阻断 |
| 未知状态 | 阻断 | 阻断 |
| 其他 task 的 passed | 阻断 | 阻断 |
| 旧 commit 的 passed | 阻断 | 阻断 |
| 报告缺失 | 阻断 | 阻断 |
| Markdown 含 PASSED 但结构化状态 failed | 阻断 | 阻断 |
| guard blocked | 不生成 ready delivery | 非零退出 |

## 5. 完成定义

- Task、Run、Trace、Verification 和 Delivery 使用同一组 ID 关联。
- 任何非 passed 结果都不能形成 completed/ready 状态。
- Delivery 不再解析任意 Markdown 报告决定安全状态。
- 动态测试证明旧报告、错 task 和 partial 均无法交付。

