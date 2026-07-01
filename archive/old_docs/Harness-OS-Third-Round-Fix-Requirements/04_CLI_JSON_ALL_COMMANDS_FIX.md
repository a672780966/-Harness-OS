# 第三轮修复 04：CLI `--json` 全命令契约

## 执行提示词

读取本文件执行。只修 `AUD3-P0-004`，补回归测试，完成后提交；不 push，不打 tag，不启动 Thick Harness。

## 1. 修复目标

任何支持全局或局部 `--json` 的 CLI 命令，stdout 必须只包含一个合法 JSON 文档；进度、日志和诊断不得污染 stdout。

## 2. 已确认问题

以下命令实测无法作为 JSON 解析：

```text
harness --json status
harness status --json
harness --json report missing-run
```

`status`、`report`、`deliver` 等入口仍调用会直接 `console.log()` 的模块。

## 3. 允许修改范围

- `src/cli/index.ts`
- `src/cli/formatter.ts`
- 各命令 CLI adapter
- 必要时将业务模块改为“返回数据、不直接打印”
- CLI unit/process integration tests

不得修改业务安全判定、Verification 状态或版本号。

## 4. 详细修复节点

### CLI3-01 单一输出路由

- 所有命令统一通过一个 CLI output router。
- 业务模块返回结构化值，不得自行决定输出模式。
- JSON 模式 stdout 只写一次最终 envelope。
- stderr 可写诊断，但不得写第二个 JSON envelope 或 stack trace。
- pretty/quiet 行为不得反向污染 JSON。

### CLI3-02 Envelope

成功与失败统一包含：

```json
{
  "ok": true,
  "command": "status",
  "status": "success",
  "data": {},
  "warnings": [],
  "meta": {
    "version": "1.0.0-rc.2",
    "outputMode": "json",
    "generatedAt": "ISO-8601",
    "durationMs": 0,
    "redacted": true
  }
}
```

- 失败时 `ok=false`，提供结构化 `error`。
- `status` 必须与 exit code 一致。
- JSON 生成前必须深度脱敏。
- `undefined`、BigInt、Error、循环引用必须有明确安全处理。

### CLI3-03 全命令覆盖

至少覆盖：

- create/open/init/repair/check
- run/resume/status
- verify/report/deliver
- decision list/propose/accept/reject/supersede
- checkpoint/rollback/config
- skills/runtime 相关子命令
- `--version` 与 `--help` 的契约需要明确记录；若不承诺 JSON，必须不接受该组合并给出稳定错误。

### CLI3-04 参数位置

- `--json command` 与 `command --json` 行为一致。
- 全局和子命令 option 合并不得丢失。
- `--json --quiet` 时 JSON 优先，且只输出 JSON。
- CI/HARNESS_OUTPUT_MODE 不得覆盖显式 `--json`。

### CLI3-05 Exit Code

- 成功为 0。
- 参数/输入错误、verification blocked、delivery blocked、internal error 使用稳定非零码。
- 禁止在深层模块直接 `process.exit()`；由最外层设置 `process.exitCode`。
- 即使失败，JSON 仍必须完整写出后再退出。

## 5. 必须新增的回归测试

使用真实子进程执行构建后的 CLI，不得只测试 formatter：

1. 对所有命令分别测试 `--json command` 和 `command --json`。
2. stdout 使用 `JSON.parse()` 成功，且不存在前后额外文本。
3. 成功和失败 envelope 字段完整。
4. exit code 与 `ok/status` 一致。
5. progress、业务模块 console 输出不进入 stdout。
6. stderr 中的 secret 被脱敏。
7. `--json --quiet` 仍只输出一个 JSON。
8. status/report/deliver 必须包含本轮已确认的复现用例。
9. Windows 路径和中文工作目录下仍可解析。

## 6. 验收命令

```powershell
pnpm.cmd typecheck
pnpm.cmd test
pnpm.cmd build
node dist/index.js --json status
node dist/index.js --json config
node dist/index.js --json report missing-run
```

最后三个命令的 stdout 必须可直接交给 `ConvertFrom-Json`。

## 7. 完成定义

- 全部承诺 `--json` 的命令只有一个合法 JSON stdout。
- 失败路径同样满足 JSON 契约并返回非零码。
- 存在真实子进程测试，而非仅 formatter mock。
- 全量测试 0 failure。

## 8. 提交要求

提交信息：

```text
fix: AUD3-P0-004 enforce CLI JSON contract
```

完成报告必须附命令矩阵、每个命令的 exit code、JSON parse 结果、测试总数和 commit SHA。
