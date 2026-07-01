# AUD-P0-003 修复报告 — Secret Redactor 全链路修复

> **来源**: `Harness-OS-P0-Fix-Requirements/03_SECRET_REDACTION_FIX.md`
> **提交**: `8fcd23b`
> **状态**: ✅ 已修复并提交（未 push）
> **日期**: 2026-06-12

---

## 一、问题概述

秘密脱敏仅在 CLI pretty 输出和 Event 写入时执行，**6 个关键模块完全缺失脱敏**，`jsonOutput()` 更是设置了 `meta.redacted=true` 却不执行实际脱敏。

缺失脱敏的输出边界：

| 模块 | 输出路径 | 风险 |
|------|---------|------|
| `cli/formatter.ts` — jsonOutput | stdout | **误导**：声称已脱敏但未执行 |
| `cli/formatter.ts` — quiet modes | stdout/stderr | 直接输出明文 |
| `verification/report.ts` | .project/reports/verification/*.md | stdout/stderr/command 原始输出 |
| `context/build.ts` | .project/context/*.json/*.md | userInstruction 原始用户输入 |
| `observability/report.ts` | .project/reports/runs/*.md | summary/risks 明文 |
| `observability/trace.ts` | .project/reports/traces/*.json | summary 明文 |
| `delivery/report.ts` | .project/reports/delivery/*.md | commit message / PR body 明文 |

---

## 二、关键修正节点

### SEC-01: 统一安全序列化接口

**文件**: `src/governance/redactor.ts`

新增 4 个脱敏门控输出函数：

| 函数 | 用途 | 脱敏时机 |
|------|------|---------|
| `safeJsonStringify(value, space?)` | JSON 序列化 | `redactObject()` 后 `JSON.stringify` |
| `safeWriteJson(path, value, space?)` | JSON 文件写入 | 写入前深度脱敏整个对象 |
| `safeWriteText(path, text)` | 文本文件写入 | 写入前 `redactText()` |
| `safeTextOutput(text)` | 标准输出格式化 | `redactText()` 后返回 |

### SEC-02: CLI JSON 深度脱敏

**文件**: `src/cli/formatter.ts` — `buildJsonOutput()` / `jsonOutput()`

- `buildJsonOutput()` 现在对 `data`、`error`、`warnings[].message`、`warnings[].recoveryHint` 执行 `redactObject()` / `redactText()`
- `jsonOutput()` 在 `JSON.stringify()` 前对整个 output 执行 `redactObject()`
- `jsonProgress()` 对 event 执行 `redactObject()`

### SEC-03: Quiet 模式脱敏

- `quietSuccess()`: `process.stdout.write(redactText(message))`
- `quietError()`: `process.stderr.write(`${code}: ${redactText(message)}`)`

### SEC-04: Verification Report 脱敏

**文件**: `src/verification/report.ts` — `formatReport()`

对 failure 段的命令、stdout、stderr、risk 文字执行 `redactText()`:
- `## Failures > command`: `redactText(f.command)`
- `## Failures > stdout/stderr`: `redactText(f.stdout.slice(0, 1000))`
- `## Risks`: `redactText(r)`

### SEC-05: Context Pack 脱敏

**文件**: `src/context/build.ts` — `saveContextPack()`

JSON 和 Markdown 两份快照均在写入前对整个 `ContextPack` 对象执行 `redactObject()`, 覆盖 userInstruction、git diff、file paths、AGENTS.md 内容等。

### SEC-06: Trace & Run Report 脱敏

**文件**: 
- `src/observability/trace.ts` — `saveTrace()`: `redactObject(trace)` 后写入
- `src/observability/report.ts` — `saveRunReport()`: summary、contextUsed、contextExcluded、contextRisks、risks、followUp、approvals[].action 逐字段 `redactText()` 后格式化

### SEC-07: Delivery Report 脱敏

**文件**: `src/delivery/report.ts` — `formatDeliveryReport()`

- commitMessage.full: `redactText()`
- prBody.body: `redactText()`
- guard check reasons: `redactText()`
- blockedBy: `redactText()`

### SEC-08: Redactor 新模式

**文件**: `src/governance/redactor.ts` — `SECRET_PATTERNS`

新增 2 个模式：

| 模式名 | 正则 | 用途 |
|--------|------|------|
| `bearer-token` | `Bearer\s+[A-Za-z0-9_\-.]{20,}` | HTTP Bearer token |
| `basic-auth` | `Basic\s+[A-Za-z0-9+/=]{20,}` | HTTP Basic auth |

---

## 三、涉及模块变更

| 模块 | 文件 | 变更 |
|------|------|------|
| Governance | `src/governance/redactor.ts` | 新增 safeJsonStringify/safeWriteJson/safeWriteText/safeTextOutput；新增 Bearer/Basic 模式 |
| CLI | `src/cli/formatter.ts` | jsonOutput/buildJsonOutput/quietSuccess/quietError/jsonProgress 深度脱敏 |
| Verification | `src/verification/report.ts` | formatReport 对 command/stdout/stderr/risks 脱敏 |
| Context | `src/context/build.ts` | saveContextPack 对完整 pack 深度脱敏 |
| Observability | `src/observability/report.ts` | saveRunReport 逐字段脱敏 |
| Observability | `src/observability/trace.ts` | saveTrace 深度脱敏 |
| Delivery | `src/delivery/report.ts` | formatDeliveryReport 对 commit/PR/guards 脱敏 |
| Tests | `tests/unit/redactor-learning.test.ts` | 12 条 SEC-01~08 回归测试 |

---

## 四、新增回归测试

在 `tests/unit/redactor-learning.test.ts` 中新增 12 个测试：

| 块 | # | 覆盖 |
|----|---|------|
| SEC-01 | 3 | safeJsonStringify 脱敏、JSON 合法性、safeTextOutput |
| SEC-02 | 4 | data 脱敏、error 脱敏、warning 脱敏、meta.redacted=true |
| SEC-03 | 2 | quietSuccess 脱敏、quietError 脱敏 |
| SEC-08 | 3 | Bearer token、Basic auth、inline Bearer |

---

## 五、测试结果

```
Test Files  19 passed (19)
     Tests  480 passed (480)
            ├── 468 现存测试（零回归）
            └── 12 新 SEC-01~08 回归测试
```

---

## 六、剩余待修复问题

已修复 3/6 个 P0：

| 文件 | 编号 | 状态 |
|------|------|------|
| `01_GOVERNANCE_SKILL_POLICY_FIX.md` | AUD-P0-001 | ✅ 已提交 |
| `02_CONFIG_SAFETY_LOCK_FIX.md` | AUD-P0-002 | ✅ 已提交 |
| `03_SECRET_REDACTION_FIX.md` | AUD-P0-003 | ✅ 已提交 |
| `04_VERIFICATION_DELIVERY_FIX.md` | AUD-P0-004 | ⏳ 待执行 |
| `05_CLI_JSON_CONTRACT_FIX.md` | AUD-P0-005 | ⏳ 待执行 |
| `06_RC_EVIDENCE_BUILD_VERSION_FIX.md` | AUD-P0-006 | ⏳ 待执行 |

---

*生成日期: 2026-06-12 19:44 UTC*
