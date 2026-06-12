# P0-05 CLI JSON 输出契约修复需求

## 1. 目标

保证任何支持全局或命令级 `--json` 的 CLI 调用，其 stdout 仅包含一个合法 JSON 文档；错误、warning、progress 和调试信息不能污染 stdout。

## 2. 涉及模块

- `src/cli/index.ts`
- `src/cli/formatter.ts`
- 所有 CLI command handlers
- `src/runtime/index.ts`
- `src/skills/index.ts`
- `src/verification/index.ts`
- `src/delivery/index.ts`
- `src/observability/index.ts`
- CLI process tests

## 3. 修复节点

### CLI-01 全局 Output Context

- Commander parse 后建立唯一 Output Context。
- 全局 `harness --json status` 与命令级 `harness status --json` 语义一致。
- handler 不得自行猜测 mode。
- 子命令和嵌套命令必须继承全局 option。

### CLI-02 禁止直接输出

- 所有 command handler 禁止直接调用 `console.log/error`。
- handler 返回数据对象或通过统一 formatter 输出。
- 第三方库日志必须重定向到 stderr 或关闭。
- JSON 模式 progress 默认关闭；stream 模式使用明确 NDJSON 合约。

### CLI-03 JSON Envelope

所有非 stream JSON 输出包含：

- `ok`
- `command`
- `status`
- `data`
- `error`
- `warnings`
- `meta`

规则：

- 成功时 `error` 缺省或 null。
- 失败时 `ok=false` 且具有稳定 error code。
- 禁止输出 `undefined` 导致字段契约漂移。
- 输出必须经过深度 Secret Redactor。

### CLI-04 stdout/stderr 契约

- stdout：唯一 JSON 文档。
- stderr：可选诊断信息，但不得含秘密。
- JSON 错误仍输出合法 JSON，并设置非零 exit code。
- Commander usage/help 错误需要结构化处理。

### CLI-05 Exit Code

至少稳定定义：

- success
- usage/config error
- governance denied
- approval required
- verification failed
- delivery blocked
- internal error

JSON envelope 的 status 与 exit code 必须一致。

### CLI-06 覆盖全部命令

至少验证：

- create
- open
- init
- repair
- check
- run
- resume
- status
- verify
- report
- deliver
- decision list/propose/accept/reject/supersede
- skills list
- checkpoint
- rollback
- config

对于不支持 JSON 的命令，应明确拒绝 `--json`，不能静默输出 pretty。

### CLI-07 Stream 模式

- 普通 `--json` 只能输出单 JSON。
- `--stream` 明确输出 NDJSON，每行可独立解析。
- progress event 与 final event 使用稳定 type。
- 禁止把单 JSON 和 NDJSON 混用。

## 4. 测试要求

测试必须通过真实子进程执行构建后的 CLI，而不是只测 formatter 函数。

每个命令断言：

1. stdout 可由 `JSON.parse()` 解析。
2. stdout 前后无 banner、空白日志或 progress。
3. stderr 不影响 stdout。
4. 成功/失败 exit code 正确。
5. 全局和命令级 `--json` 行为一致。
6. 注入秘密后 stdout/stderr 均不泄露。

关键回归用例：

```text
harness --json status
harness status --json
harness config --json
harness --json skills list
harness --json verify
harness --json deliver
```

## 5. 完成定义

- `harness --json status` 等所有声明支持的命令均返回合法 JSON。
- JSON 模式 stdout 不含任何非 JSON 字符。
- CLI process contract tests 纳入 RC gate。
- JSON 与 secret redaction、exit code 和 error code 契约一致。

