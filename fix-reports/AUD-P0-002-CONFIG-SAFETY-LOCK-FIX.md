# AUD-P0-002 修复报告 — Config Safety-Locked & Immutable 策略

> **来源**: `Harness-OS-P0-Fix-Requirements/02_CONFIG_SAFETY_LOCK_FIX.md`
> **提交**: `7d00e68`
> **状态**: ✅ 已修复并提交（未 push）
> **日期**: 2026-06-12

---

## 一、问题概述

Config 系统的 `mergeConfig()` 只保护了 `governance` 字段的 true→false 弱化，存在以下安全缺口：

1. **仅 governance 节有保护** — `delivery.requireApprovalForDeploy`、`observability.secretRedaction` 等可被任意覆盖
2. **仅 boolean 有保护** — `defaultNetwork` enum 无校验、`dangerousCommands` 数组可被清空
3. **无 immutable 机制** — 关键安全字段无防篡改保护
4. **无 schema 校验** — 非法值静默通过
5. **无来源追踪** — 无法追溯每个字段的最终来源

---

## 二、关键修正节点

### CFG-01: Safety Field Registry（安全字段注册表）

**文件**: `src/config/types.ts` — `SAFETY_FIELDS` 常量

为每个安全字段声明安全类型、收紧方向、不可变标志、默认值和合法值。

登记 15 个安全字段：

| 字段 | 类型 | 不可变 | 收紧方向 |
|------|------|--------|---------|
| `governance.requireApprovalForDeploy` | boolean | ✅ | true→false 阻止 |
| `governance.requireApprovalForPushMain` | boolean | — | true→false 阻止 |
| `governance.requireApprovalForDependencyAdd` | boolean | — | true→false 阻止 |
| `governance.requireApprovalForDeleteFile` | boolean | — | true→false 阻止 |
| `governance.requireApprovalForModifyAgentsMd` | boolean | — | true→false 阻止 |
| `governance.redactSecrets` | boolean | ✅ | true→false 阻止 |
| `delivery.requireApprovalForPr` | boolean | — | true→false 阻止 |
| `delivery.requireApprovalForRelease` | boolean | — | true→false 阻止 |
| `delivery.requireApprovalForDeploy` | boolean | ✅ | true→false 阻止 |
| `observability.secretRedaction` | boolean | ✅ | true→false 阻止 |
| `governance.allowWorkspaceOutsideAccess` | boolean-allow | — | false→true 阻止 |
| `project.allowAutoCommit` | boolean-allow | — | false→true 阻止 |
| `project.allowAutoPush` | boolean-allow | ✅ | false→true 阻止 |
| `governance.defaultNetwork` | enum | — | restricted→allowed 阻止 |
| `governance.dangerousCommands` | array | — | 仅追加，不删除 |
| `project.protectedBranches` | array | — | 保留 main/master |

### CFG-02: 布尔安全语义

**文件**: `src/config/loader.ts` — `checkSafetyOverride()`

- `boolean` 类型：`true→false` 被拒绝（true 更严格）
- `boolean-allow` 类型：`false→true` 被拒绝（false 更严格）
- 拒绝时：保留原值、生成 warning、记录 field source

### CFG-03: Enum 安全语义

- `defaultNetwork` 从 `restricted` 改为 `allowed` → 拒绝
- 非法 enum 值 → 拒绝并给出合法值列表
- 统一使用 `restricted→allowed` 方向判断

### CFG-04: 数组 Union Merge

- `dangerousCommands`：override 与原值执行并集合并，仅拒绝空数组清空
- `protectedBranches`：始终保留 `main`/`master`，新分支追加
- 使用去重合并，防止重复项

### CFG-05: 跨模块安全锁

以下字段标记为 `immutable`，任何来源均无法修改：

| 字段 | 原因 |
|------|------|
| `governance.requireApprovalForDeploy` | 必须保留审批 |
| `governance.redactSecrets` | 必须保持脱敏 |
| `observability.secretRedaction` | 必须保持脱敏 |
| `delivery.requireApprovalForDeploy` | 必须保留审批 |
| `project.allowAutoPush` | 禁止自动推送 |

### CFG-06: Schema 校验

- `loadConfig()` 返回 `validation` 字段：`{ valid, errors }`
- 校验 enum、数组类型、protectedBranches 必含 main/master

### CFG-07: 字段级来源追踪

- `LoadedConfig` 新增 `fieldSources: ConfigFieldSource[]`
- 每个安全字段记录最终值和来源（default/global/project/env/cli）
- 被拒绝的 override 记录 `{ rejected: true, rejectedReason }`

### CFG-08: Immutable 字段保护

- 任何来源对 `immutable` 字段的修改都被拒绝
- 在类型特定规则之前检查 immutable 标志

---

## 三、新增回归测试

在 `tests/unit/config.test.ts` 中新增 28 个测试（CFG-01~08）：

| 测试块 | 数量 | 覆盖 |
|--------|------|------|
| CFG-01 | 3 | Registry 完整性、类型、默认值 |
| CFG-02 | 6 | boolean 收紧/减弱、boolean-allow 收紧/减弱 |
| CFG-03 | 3 | enum 减弱拒绝、同值允许、非法值拒绝 |
| CFG-04 | 3 | 数组追加、并集保留、保护分支保留 |
| CFG-05 | 3 | 跨模块 immutable 拒绝 |
| CFG-06 | 1 | validation 字段存在 |
| CFG-07 | 3 | fieldSources 存在、来源正确、拒绝记录 |
| CFG-08 | 2 | immutable 警告、非 immutable 可收紧 |
| 非安全字段 | 3 | 普通字段仍可正常覆盖 |

---

## 四、测试结果

```
Test Files  19 passed (19)
     Tests  468 passed (468)
            ├── 440 现存测试（零回归，含 AUD-P0-001）
            ├── 12  GOV-01 回归测试
            └── 28  CFG-01~08 回归测试
```

---

## 五、剩余待修复问题

已修复 2/6 个 P0：

| 文件 | 编号 | 状态 |
|------|------|------|
| `01_GOVERNANCE_SKILL_POLICY_FIX.md` | AUD-P0-001 | ✅ 已提交 |
| `02_CONFIG_SAFETY_LOCK_FIX.md` | AUD-P0-002 | ✅ 已提交 |
| `03_SECRET_REDACTION_FIX.md` | AUD-P0-003 | ⏳ 待执行 |
| `04_VERIFICATION_DELIVERY_FIX.md` | AUD-P0-004 | ⏳ 待执行 |
| `05_CLI_JSON_CONTRACT_FIX.md` | AUD-P0-005 | ⏳ 待执行 |
| `06_RC_EVIDENCE_BUILD_VERSION_FIX.md` | AUD-P0-006 | ⏳ 待执行 |

---

*生成日期: 2026-06-12 19:31 UTC*
