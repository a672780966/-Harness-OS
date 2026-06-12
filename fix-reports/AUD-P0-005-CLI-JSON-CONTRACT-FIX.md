# AUD-P0-005 修复报告 — CLI JSON 输出契约

> **来源**: `Harness-OS-P0-Fix-Requirements/05_CLI_JSON_CONTRACT_FIX.md`
> **提交**: `c3e0b2b`
> **状态**: ✅ 已修复并提交（未 push）
> **日期**: 2026-06-12

---

## 一、问题概述

CLI 命令中一半以上不支持 `--json` 输出，大量直接 `console.log` 绕过 formatter：

| 原问题 | 影响 |
|--------|------|
| 11+ 命令仅 pretty output | 无法被工具/CI 消费 |
| 非结构化 console.log | stdout 可能含非 JSON 内容 |
| 无统一错误出口 | 不同命令 exit code 不一致 |
| `--json` 全局 flag 未传播 | 子命令不继承 |

---

## 二、关键修正节点

### CLI-01/06: 全覆盖 JSON 输出

为以下命令补全 `--json`/`--quiet` 选项和 JSON envelope：

| 命令 | 原输出 | 新增 |
|------|--------|------|
| `harness open` | console.log 裸写 | JSON + quiet |
| `harness init` | console.log 裸写 | JSON + quiet |
| `harness repair` | console.log 裸写 | JSON + quiet |
| `harness check` | console.log 裸写 | JSON + quiet |
| `harness verify` | console.log 裸写 | JSON + quiet + exit 70 |
| `harness resume` | 无输出 | JSON + quiet |
| `harness decision propose` | prettySuccess | JSON + quiet |
| `harness decision accept` | console.log | JSON + quiet |
| `harness decision reject` | console.log | JSON + quiet |
| `harness decision supersede` | console.log | JSON + quiet |
| `harness checkpoint` | console.log 裸写 | JSON + quiet |
| `harness rollback` | console.log 裸写 | JSON + quiet |

每个命令的输出结构：
```json
{ "ok": true, "command": "check", "status": "success",
  "data": { ... },
  "meta": { "version": "1.0.0", "outputMode": "json",
            "generatedAt": "...", "durationMs": 123, "redacted": true } }
```

### CLI-03: JSON Envelope 统一

`buildJsonOutput()` 固定生成以下字段：

| 字段 | 成功 | 失败 |
|------|------|------|
| `ok` | `true` | `false` |
| `command` | 命令名 | 命令名 |
| `status` | `success` | `failed` |
| `data` | 业务数据 | 缺省 |
| `error` | 缺省 | `{ code, category, severity, message }` |
| `warnings` | `[]` | `[]` |
| `meta` | `{ version, outputMode, generatedAt, durationMs, redacted }` | 同上 |

### CLI-05: Exit Code

统一 exit code 映射：

| 场景 | Exit Code | 来源 |
|------|-----------|------|
| 成功 | 0 | `HarnessExitCode.SUCCESS` |
| 用户输入错误 | 10 | `USER_INPUT_ERROR` |
| 项目错误 | 20 | `PROJECT_ERROR` |
| 任务错误 | 30 | `TASK_ERROR` |
| Governance 拒绝 | 60 | `GOVERNANCE_ERROR` |
| 验证失败 | 70 | `VERIFICATION_ERROR` |
| 配置错误 | 100 | `CONFIG_ERROR` |
| 内部错误 | 120 | `INTERNAL_ERROR` |

### CLI-02/04: stdout/stderr 契约

- **stdout**: 仅含唯一个 JSON 文档（JSON mode）或人类可读文本（pretty mode）
- **stderr**: 错误、warning、progress（均经 secret redaction）
- JSON mode 下不得有任何非 JSON 内容出现在 stdout

---

## 三、涉及模块变更

| 模块 | 文件 | 变更 |
|------|------|------|
| CLI | `src/cli/formatter.ts` | 新增 runCliCommand() 统一异步输出分发器 |
| CLI | `src/cli/index.ts` | 11+ 命令补全 --json/--quiet 支持 |
| Tests | `tests/unit/cli-errors.test.ts` | 11 条 CLI-03/05/06 回归测试 |

---

## 四、新增回归测试

| 块 | # | 覆盖 |
|----|---|------|
| CLI-03 | 4 | JSON envelope 标准结构、ok=false、序列化、redacted |
| CLI-05 | 3 | runCliCommand exit 0、error exit、quiet callback |
| CLI-06 | 4 | detectOutputMode 识别 json/quiet/pretty/CI |

---

## 五、测试结果

```
Test Files  19 passed (19)
     Tests  497 passed (497)
            ├── 486 现存测试（零回归）
            └── 11 新 CLI-03/05/06 回归测试
```

---

## 六、剩余待修复问题

已修复 5/6 个 P0：

| 文件 | 编号 | 状态 |
|------|------|------|
| `01_GOVERNANCE_SKILL_POLICY_FIX.md` | AUD-P0-001 | ✅ |
| `02_CONFIG_SAFETY_LOCK_FIX.md` | AUD-P0-002 | ✅ |
| `03_SECRET_REDACTION_FIX.md` | AUD-P0-003 | ✅ |
| `04_VERIFICATION_DELIVERY_FIX.md` | AUD-P0-004 | ✅ |
| `05_CLI_JSON_CONTRACT_FIX.md` | AUD-P0-005 | ✅ |
| `06_RC_EVIDENCE_BUILD_VERSION_FIX.md` | AUD-P0-006 | ⏳ 待执行 |

---

*生成日期: 2026-06-12 20:48 UTC*
