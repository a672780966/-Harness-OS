# P0-03 Secret Redactor 全链路修复需求

## 1. 目标

确保秘密在 CLI、Report、Event、Context、Trace 和 Delivery 的所有输出及持久化边界被统一脱敏，并保证 `redacted` 元数据真实可信。

## 2. 涉及模块

- `src/governance/redactor.ts`
- `src/cli/formatter.ts`
- `src/context/build.ts`
- `src/observability/events.ts`
- `src/observability/report.ts`
- `src/observability/trace.ts`
- `src/verification/report.ts`
- `src/delivery/report.ts`
- `src/delivery/pr.ts`
- `src/task/index.ts`
- 相关 unit/integration tests

## 3. 修复节点

### SEC-01 统一输出边界

建立单一安全序列化接口，例如：

- `safeJsonStringify(value)`
- `safeTextOutput(value)`
- `safeWriteJson(path, value)`
- `safeWriteText(path, text)`

所有 CLI 和文件写入边界必须使用该接口，禁止直接：

- `JSON.stringify(untrustedData)`
- `writeFileSync(...raw...)`
- `console.log(untrustedData)`
- `process.stdout.write(raw)`

### SEC-02 CLI JSON 深度脱敏

- `jsonOutput()` 必须对完整 output 执行 `redactObject()`。
- `data`、`error`、`warnings`、`metaOverrides` 全部纳入。
- `meta.redacted=true` 仅在脱敏函数成功执行后设置。
- 脱敏失败时不得输出原始内容，应返回安全的结构化错误。

### SEC-03 Pretty/Quiet/Progress 输出

- 所有直接 `console.log/error` 迁移到 formatter。
- quiet 输出同样必须脱敏。
- progress、table、approval prompt 和异常 stack 不得泄露秘密。
- JSON 模式不得将 warning/progress 输出到 stdout。

### SEC-04 Run 与 Verification Report

- Report 对象在格式化前深度脱敏。
- command、stdout、stderr、summary、risks、paths 和 changed files 全部处理。
- 原始输出如需保留，应放在明确受保护且默认 ignored 的 artifact 中，并执行访问控制。
- Markdown code fence 内内容同样需要脱敏。

### SEC-05 Context Pack

- `userInstruction`、task、AGENTS.md 摘要、git diff、文件内容、路径和 notes 全部脱敏。
- protected-sensitive 来源不得进入 Context Pack。
- Context JSON 与 Markdown 必须使用同一个已脱敏对象生成，避免双路径不一致。

### SEC-06 Trace 与 Event

- Event 保留当前 redaction，并修正返回值：调用方获得的 event 也应为脱敏版本。
- Trace 保存前执行深度脱敏。
- tool input、approval reason、related command 和 paths 都必须覆盖。

### SEC-07 Delivery 与 PR

- commit message、PR body、delivery report、verification摘要均需脱敏。
- 检测到秘密时，默认阻断 delivery，并记录 security event。
- 不得把 `[REDACTED]` 前的原文保存在 report 元数据中。

### SEC-08 Redactor 正确性

- 敏感 key 应保留字段名、仅替换值，避免把多个 key 统一改名为 `[REDACTED]` 后发生属性覆盖。
- 支持无引号 `.env`、Bearer token、Basic auth、URL credentials、常见云 key、multiline private key。
- 对循环引用、Date、Error、Buffer 和非 JSON 类型定义安全行为。

## 4. 测试要求

建立秘密注入矩阵，将同一批 canary secrets 注入：

1. CLI JSON data/error/warning。
2. Pretty、quiet 和 progress。
3. Event payload 与 relatedCommand。
4. Run Report。
5. Verification stdout/stderr。
6. Context JSON/Markdown。
7. Trace。
8. Delivery Report 和 PR body。

每个测试必须同时断言：

- 原秘密不存在。
- `[REDACTED]` 存在或流程被阻断。
- 输出仍是合法 JSON/Markdown。
- `redacted` 元数据与事实一致。

## 5. 完成定义

- 除明确隔离的原始 artifact 外，仓库和 runtime 输出中找不到 canary secret。
- CLI / Report / Event / Context 四项重点链路全部有端到端测试。
- 脱敏失败时 fail closed。
- Secret 检测会生成不含秘密本身的审计事件。

